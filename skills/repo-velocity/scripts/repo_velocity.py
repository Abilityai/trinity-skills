#!/usr/bin/env python3
"""
repo-velocity — objective development-speed metrics for any GitHub repository.

All data is fetched through the GitHub CLI (`gh api`), so authentication, host
config, and rate limits are inherited from the user's existing `gh` login —
nothing to configure, identical behaviour every run.

Usage:
    repo_velocity.py OWNER/REPO[@BRANCH] [OWNER/REPO[@BRANCH] ...] [--window-days N] [--branch B] [--json]

Accepts owner/repo, a full https URL, or an ssh URL for each argument, with an
optional @branch suffix to pin the measured branch:
    repo_velocity.py facebook/react
    repo_velocity.py Abilityai/trinity@dev
    repo_velocity.py https://github.com/vllm-project/vllm --window-days 30
    repo_velocity.py langchain-ai/langchain openai/openai-python --json

Branch handling: by default the tool auto-detects the busiest development
branch in the window (one GraphQL call over the 100 most recently-committed
branches) and measures commits / lines / contributors on that line — repos that
develop on `dev` and merge to the default branch only at release are no longer
undercounted. The default branch's in-window commit count is always reported
alongside when it differs.

Exit codes: 0 ok · 1 usage error · 2 gh/auth failure or nothing analyzed.
"""
import argparse
import json
import re
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta


def eprint(*a):
    print(*a, file=sys.stderr)


class GhError(Exception):
    def __init__(self, path, msg):
        self.path = path
        self.msg = msg
        super().__init__(f"{path}: {msg}")


# ---------------------------------------------------------------- gh plumbing

def run_gh(args, timeout=90):
    try:
        p = subprocess.run(["gh", "api", *args], capture_output=True,
                           text=True, timeout=timeout)
    except FileNotFoundError:
        eprint("error: `gh` CLI not found. Install GitHub CLI and run `gh auth login`.")
        sys.exit(2)
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    return p.returncode, p.stdout, p.stderr


def gh_json(path, params=None, paginate=False):
    """GET an endpoint, return parsed JSON (or None on empty body).

    NOTE: `gh api` switches to POST as soon as any `-f` field is present, so we
    force `-X GET` — that turns `-f k=v` fields into (url-encoded) query params.
    """
    args = ["-X", "GET"]
    if paginate:
        args.append("--paginate")
    args.append(path)
    for k, v in (params or {}).items():
        args += ["-f", f"{k}={v}"]
    code, out, err = run_gh(args)
    if code != 0:
        blob = (err or "")
        if "404" in blob or "Not Found" in blob:
            raise GhError(path, "not found")
        raise GhError(path, blob.strip().splitlines()[-1] if blob.strip() else f"exit {code}")
    return json.loads(out) if out.strip() else None


def gh_graphql(query, **fields):
    """POST a GraphQL query via `gh api graphql` (string variables only)."""
    args = ["graphql", "-f", f"query={query}"]
    for k, v in fields.items():
        args += ["-f", f"{k}={v}"]
    code, out, err = run_gh(args)
    if code != 0:
        blob = (err or "")
        raise GhError("graphql", blob.strip().splitlines()[-1] if blob.strip() else f"exit {code}")
    return json.loads(out) if out.strip() else None


def commit_count_since(repo, since_iso, sha=None):
    """Exact commit count since `since_iso` via the Link-header rel="last" trick on a
    per_page=1 query: one request, no /stats endpoint, so it never 202s. With one item
    per page, the last page number IS the total commit count. `sha` selects the branch
    (GitHub defaults to the default branch when omitted)."""
    args = ["-i", "-X", "GET", f"repos/{repo}/commits",
            "-f", f"since={since_iso}", "-f", "per_page=1"]
    if sha:
        args += ["-f", f"sha={sha}"]
    code, out, err = run_gh(args)
    head, sep, body = out.partition("\r\n\r\n")
    if not sep:
        head, sep, body = out.partition("\n\n")
    if code != 0:
        blob = err or ""
        if "404" in blob or "Not Found" in blob:
            raise GhError("commits", "not found")
        if "409" in blob or "empty" in blob.lower():
            return 0  # empty repository
        raise GhError("commits",
                      blob.strip().splitlines()[-1] if blob.strip() else f"exit {code}")
    m = re.search(r'[?&]page=(\d+)>;\s*rel="last"', head)
    if m:
        return int(m.group(1))
    try:
        arr = json.loads(body) if body.strip() else []
    except json.JSONDecodeError:
        return 0
    return len(arr) if isinstance(arr, list) else 0


def search_count(q):
    data = gh_json("search/issues", {"q": q, "per_page": "1"})
    return (data or {}).get("total_count")


COMMIT_AUTHOR_SAMPLE = 500  # cap pages of commits we scan for distinct authors


def list_commits_window(repo, since_iso, sha=None):
    """List commits since `since_iso` (newest first), capped. Never 202s — unlike
    /stats/contributors, which 202s indefinitely on some repos."""
    commits, page = [], 1
    while True:
        params = {"since": since_iso, "per_page": "100", "page": str(page)}
        if sha:
            params["sha"] = sha
        batch = gh_json(f"repos/{repo}/commits", params)
        if not batch:
            break
        commits.extend(batch)
        if len(batch) < 100 or len(commits) >= COMMIT_AUTHOR_SAMPLE:
            break
        page += 1
    return commits


LOC_COMMIT_SAMPLE_MAX = 2000  # per-commit stat pages cap (100/page)


def lines_via_commit_stats(repo, cutoff_iso, branch, window_days):
    """Lines added/deleted over the window: sum of per-commit line stats on the
    measured branch (GraphQL history pagination). Merge commits are skipped —
    their diff vs first parent repeats the merged branch's changes.

    This replaced the compare-endpoint net diff: GitHub's compare API silently
    caps the file list at ~300 files, so on any large window it summed an
    arbitrary subset (verified: Trinity 90d showed net -6,015 vs ground-truth
    +213,589 from a local clone). Per-commit sums never truncate; they measure
    churn (rewrites count on both sides), which is the honest 'lines pushed'
    signal. Beyond LOC_COMMIT_SAMPLE_MAX commits the most recent sample's date
    span scales to the full window (flagged as extrapolated)."""
    if not branch:
        return None
    owner, name = repo.split("/")
    expr = json.dumps(branch)
    adds = dels = counted = 0
    newest = oldest = None
    cursor, has_more, total = None, False, 0
    for _ in range(LOC_COMMIT_SAMPLE_MAX // 100):
        after = f', after:"{cursor}"' if cursor else ""
        q = """
        query($owner:String!,$name:String!,$since:GitTimestamp!){
          repository(owner:$owner,name:$name){
            object(expression:%s){ ... on Commit {
              history(since:$since,first:100%s){
                totalCount
                pageInfo{ hasNextPage endCursor }
                nodes{ committedDate additions deletions parents(first:1){ totalCount } }
              } } }
          }
        }""" % (expr, after)
        data = gh_graphql(q, owner=owner, name=name, since=cutoff_iso)
        hist = ((((data or {}).get("data") or {}).get("repository") or {})
                .get("object") or {}).get("history") or {}
        total = hist.get("totalCount") or total
        nodes = hist.get("nodes") or []
        for nd in nodes:
            counted += 1
            d = iso(nd.get("committedDate"))
            if d:
                newest = newest or d
                oldest = d
            if ((nd.get("parents") or {}).get("totalCount") or 1) > 1:
                continue
            adds += nd.get("additions") or 0
            dels += nd.get("deletions") or 0
        page = hist.get("pageInfo") or {}
        has_more = bool(page.get("hasNextPage"))
        if not has_more or not nodes:
            break
        cursor = page.get("endCursor")
    if not counted:
        return None
    if has_more and newest and oldest and newest > oldest:
        # sample capped — scale the sampled span up to the full window
        span_days = max((newest - oldest).total_seconds() / 86400, 1)
        factor = window_days / span_days
        return {"added": round(adds * factor), "deleted": round(dels * factor),
                "extrapolated": True, "commits_sampled": counted}
    return {"added": adds, "deleted": dels,
            "extrapolated": False, "commits_sampled": counted}


# ------------------------------------------------------- branch auto-detection

BRANCH_HEAD_PAGES_MAX = 10   # heads scan cap: 10 pages × 100 = 1,000 branches
ACTIVE_BRANCH_CAP = 150      # in-window commit counting cap (most recent heads first)
HISTORY_BATCH = 50           # branches per aliased history-count GraphQL query
DEV_BRANCH_HINTS = ("dev", "develop", "development", "next", "canary", "staging",
                    "release", "beta", "unstable", "edge", "trunk", "master")


def _is_dev_hint(name):
    n = name.lower()
    return any(n == h or n.startswith(h + "/") or n.startswith(h + "-")
               for h in DEV_BRANCH_HINTS)


def scan_branch_activity(repo, cutoff_iso, default_branch=None):
    """Find every branch active in the window and count its in-window commits.

    Two phases, all GraphQL (cheap — no /stats, no 202s):
      1. page through ALL branch heads (name + head commit date); GitHub's
         TAG_COMMIT_DATE ref ordering is unreliable for branches, so we
         enumerate rather than trust a top-N ordering (verified: it buried an
         actively-updated `dev` below stale feature branches).
      2. batch-count `history(since:)` only for branches whose head moved
         inside the window (aliased object(expression:) queries, 50/batch).

    Returns (counts_by_branch, total_branches, truncated_flag)."""
    owner, name = repo.split("/")
    cutoff_dt = iso(cutoff_iso)
    heads, total, cursor, truncated = {}, None, None, False
    for _ in range(BRANCH_HEAD_PAGES_MAX):
        after = f', after:"{cursor}"' if cursor else ""
        q = """
        query($owner:String!,$name:String!){
          repository(owner:$owner,name:$name){
            refs(refPrefix:"refs/heads/",first:100%s){
              totalCount
              pageInfo{ hasNextPage endCursor }
              nodes{ name target{ ... on Commit { committedDate } } }
            }
          }
        }""" % after
        data = gh_graphql(q, owner=owner, name=name)
        refs = (((data or {}).get("data") or {}).get("repository") or {}).get("refs") or {}
        total = refs.get("totalCount")
        for node in refs.get("nodes") or []:
            d = (node.get("target") or {}).get("committedDate")
            heads[node["name"]] = iso(d) if d else None
        page = refs.get("pageInfo") or {}
        if not page.get("hasNextPage"):
            break
        cursor = page.get("endCursor")
    else:
        truncated = True  # >1,000 branches — heads scan capped

    active = sorted((n for n, d in heads.items() if d and d >= cutoff_dt),
                    key=lambda n: heads[n], reverse=True)
    if len(active) > ACTIVE_BRANCH_CAP:
        active, truncated = active[:ACTIVE_BRANCH_CAP], True
    # never drop the default branch or conventional dev branches from the count
    for b in heads:
        if (b == default_branch or _is_dev_hint(b)) and heads[b] and \
                heads[b] >= cutoff_dt and b not in active:
            active.append(b)
    # a capped heads scan (>1,000 branches) can miss the default/dev branches
    # entirely (late alphabetical position) — probe them by name regardless;
    # nonexistent names resolve to null in the batch query and are ignored
    if default_branch and default_branch not in active:
        active.append(default_branch)
    if truncated:
        active += [b for b in DEV_BRANCH_HINTS if b not in active]

    counts = {}
    for i in range(0, len(active), HISTORY_BATCH):
        chunk = active[i:i + HISTORY_BATCH]
        parts = ["b%d: object(expression:%s){ ... on Commit { history(since:$since){ totalCount } } }"
                 % (j, json.dumps(b)) for j, b in enumerate(chunk)]
        q = ("query($owner:String!,$name:String!,$since:GitTimestamp!){"
             "repository(owner:$owner,name:$name){ %s } }" % " ".join(parts))
        data = gh_graphql(q, owner=owner, name=name, since=cutoff_iso)
        repo_obj = (((data or {}).get("data") or {}).get("repository")) or {}
        for j, b in enumerate(chunk):
            n = (((repo_obj.get(f"b{j}") or {}).get("history")) or {}).get("totalCount")
            if n:
                counts[b] = n
    return counts, total, truncated


STABLE_PREFERENCE = 0.9  # a stable branch within 90% of the busiest branch wins


def pick_measured_branch(counts, default_branch):
    """The busiest branch in the window is the development line we measure —
    with a stable-branch preference: short-lived feature branches contain the
    whole history of the dev line they forked from, so they beat it by a few
    commits every time. A non-stable branch (not the default, not a
    conventional dev name) only wins if it is meaningfully busier (>10%) than
    the best stable branch — i.e. genuinely divergent work."""
    if not counts:
        return default_branch
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    best_any_n = ranked[0][1]
    stable = {k: v for k, v in counts.items()
              if k == default_branch or _is_dev_hint(k)}
    if stable:
        best_stable = sorted(stable.items(),
                             key=lambda kv: (-kv[1],
                                             0 if kv[0] == default_branch else 1,
                                             kv[0]))[0]
        if best_stable[1] >= STABLE_PREFERENCE * best_any_n:
            return best_stable[0]
    return ranked[0][0]


# ----------------------------------------------------------------- utilities

def parse_repo(s):
    """Normalize owner/repo, https URL, or ssh URL; an optional @branch suffix
    pins the measured branch. Returns (owner/repo, branch_or_None)."""
    s = s.strip()
    s = re.sub(r"^git@github\.com:", "", s)
    s = re.sub(r"^https?://github\.com/", "", s)
    s = re.sub(r"^github\.com/", "", s)
    s = re.sub(r"\.git$", "", s).strip("/")
    branch = None
    if "@" in s:
        s, branch = s.rsplit("@", 1)
    parts = s.split("/")
    if len(parts) < 2 or not parts[0] or not parts[1]:
        raise ValueError(f"can't parse repo from '{s}' (expected owner/repo)")
    return f"{parts[0]}/{parts[1]}", (branch or None)


def iso(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def days_between(a, b):
    return round((b - a).total_seconds() / 86400)


def per_week(total, window_days, ndigits=1):
    if total is None:
        return None
    return round(total / max(window_days / 7, 1), ndigits)


# ------------------------------------------------------------------- metrics

def fetch(repo, window_days, branch_override=None):
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=window_days)
    cutoff_iso = cutoff.isoformat()
    cutoff_date = cutoff.date().isoformat()
    unavailable = []
    M = {"repo": repo, "window_days": window_days,
         "fetched_at": now.isoformat()}

    # repo meta (404 here aborts the whole repo)
    meta = gh_json(f"repos/{repo}")
    M["description"] = meta.get("description")
    M["language"] = meta.get("language")
    M["stars"] = meta.get("stargazers_count")
    M["forks"] = meta.get("forks_count")
    M["open_issues_and_prs"] = meta.get("open_issues_count")
    M["archived"] = meta.get("archived")
    M["is_fork"] = meta.get("fork")
    M["created_at"] = meta.get("created_at")
    M["pushed_at"] = meta.get("pushed_at")
    M["age_days"] = days_between(iso(meta["created_at"]), now) if meta.get("created_at") else None
    M["days_since_push"] = days_between(iso(meta["pushed_at"]), now) if meta.get("pushed_at") else None

    default_branch = meta.get("default_branch")
    M["default_branch"] = default_branch

    # Which branch do we measure? Explicit override wins; otherwise one GraphQL
    # scan finds the busiest branch in the window (falls back to the default
    # branch if the scan is unavailable).
    branch_counts = {}
    if branch_override:
        measured = branch_override
        M["branch_selection"] = "explicit"
    else:
        try:
            branch_counts, M["branches_total"], M["branch_scan_truncated"] = \
                scan_branch_activity(repo, cutoff_iso, default_branch)
            measured = pick_measured_branch(branch_counts, default_branch)
            M["branch_selection"] = "auto"
        except GhError:
            unavailable.append("branch_scan")
            measured = default_branch
            M["branch_selection"] = "fallback_default"
    M["measured_branch"] = measured
    M["branch_activity_top"] = dict(sorted(branch_counts.items(),
                                           key=lambda kv: -kv[1])[:5])

    # Commit counts via the Link-header trick — exact, one request each, NO /stats
    # endpoint, so no 202 risk. All counts are on the measured branch; the default
    # branch's in-window count is kept alongside when it differs.
    sha = measured if measured != default_branch else None
    try:
        def since(days):
            return (now - timedelta(days=days)).isoformat()
        M["commits_window"] = commit_count_since(repo, cutoff_iso, sha=sha)
        M["commits_per_week"] = per_week(M["commits_window"], window_days)
        M["commits_30d"] = commit_count_since(repo, since(30), sha=sha)
        M["commits_90d"] = commit_count_since(repo, since(90), sha=sha)
        M["commits_365d"] = commit_count_since(repo, since(365), sha=sha)
        M["commits_window_default_branch"] = (
            M["commits_window"] if measured == default_branch
            else commit_count_since(repo, cutoff_iso))
    except GhError:
        unavailable.append("commits")
        for k in ("commits_window", "commits_per_week", "commits_30d",
                  "commits_90d", "commits_365d", "commits_window_default_branch"):
            M[k] = None

    # Active contributors: distinct authors in the commits list (measured branch).
    # We deliberately avoid /stats/contributors — it 202s indefinitely on some repos.
    try:
        commits = list_commits_window(repo, cutoff_iso, sha=sha)
        authors = set()
        for c in commits:
            login = (c.get("author") or {}).get("login")
            email = (c.get("commit", {}).get("author", {}) or {}).get("email")
            authors.add(login or email or "?")
        M["active_contributors_window"] = len(authors)
        M["contributors_sampled"] = len(commits) >= COMMIT_AUTHOR_SAMPLE
    except GhError:
        unavailable.append("active_contributors")
        M["active_contributors_window"] = None
        M["contributors_sampled"] = False

    # Lines added/deleted: sum of per-commit line stats on the measured branch
    # (merges excluded). NOT the compare endpoint (~300-file cap = subset garbage
    # on large windows) and NOT /stats/code_frequency (202s forever).
    try:
        lines = lines_via_commit_stats(repo, cutoff_iso, measured or default_branch,
                                       window_days)
    except GhError:
        lines = None
    if lines:
        M["lines_added_window"] = lines["added"]
        M["lines_deleted_window"] = lines["deleted"]
        M["net_lines_window"] = lines["added"] - lines["deleted"]
        M["lines_added_per_week"] = per_week(lines["added"], window_days, 0)
        M["lines_extrapolated"] = lines["extrapolated"]
        M["lines_commits_sampled"] = lines["commits_sampled"]
    else:
        unavailable.append("lines")
        for k in ("lines_added_window", "lines_deleted_window",
                  "net_lines_window", "lines_added_per_week"):
            M[k] = None
        M["lines_extrapolated"] = False

    # merged PR / issue throughput via search — branch-inclusive by nature
    # (counts PRs merged into ANY base branch)
    try:
        M["merged_prs_window"] = search_count(f"repo:{repo} is:pr is:merged merged:>={cutoff_date}")
        M["merged_prs_per_week"] = per_week(M["merged_prs_window"], window_days)
    except GhError:
        unavailable.append("merged_prs")
        M["merged_prs_window"] = M["merged_prs_per_week"] = None
    try:
        M["opened_prs_window"] = search_count(f"repo:{repo} is:pr created:>={cutoff_date}")
    except GhError:
        unavailable.append("opened_prs")
        M["opened_prs_window"] = None
    try:
        M["closed_issues_window"] = search_count(f"repo:{repo} is:issue is:closed closed:>={cutoff_date}")
    except GhError:
        unavailable.append("closed_issues")
        M["closed_issues_window"] = None

    # median time-to-merge, sampled from recent merged PRs
    try:
        pulls = gh_json(f"repos/{repo}/pulls",
                        {"state": "closed", "sort": "updated",
                         "direction": "desc", "per_page": "50"})
        ttm = [(iso(pr["merged_at"]) - iso(pr["created_at"])).total_seconds() / 3600
               for pr in (pulls or []) if pr.get("merged_at")]
        M["ttm_sample_size"] = len(ttm)
        M["median_ttm_hours"] = round(statistics.median(ttm), 1) if ttm else None
    except GhError:
        unavailable.append("time_to_merge")
        M["ttm_sample_size"] = 0
        M["median_ttm_hours"] = None

    # release cadence
    try:
        rels = gh_json(f"repos/{repo}/releases", {"per_page": "100"})
        dates = sorted((iso(r["published_at"]) for r in (rels or [])
                        if r.get("published_at")), reverse=True)
        M["total_releases"] = len(dates)
        yr_ago = now - timedelta(days=365)
        M["releases_last_year"] = sum(1 for d in dates if d >= yr_ago)
        gaps = [(dates[i] - dates[i + 1]).days for i in range(len(dates) - 1)][:20]
        M["median_release_interval_days"] = round(statistics.median(gaps), 1) if gaps else None
        M["latest_release_at"] = dates[0].isoformat() if dates else None
    except GhError:
        unavailable.append("releases")
        for k in ("total_releases", "releases_last_year",
                  "median_release_interval_days", "latest_release_at"):
            M[k] = None

    # per-contributor rates (team-leverage view; same caveats as the inputs —
    # sampled contributor counts on busy repos, churn-based LOC)
    ac = M.get("active_contributors_window")
    M["loc_added_per_contributor_per_week"] = (
        round(M["lines_added_per_week"] / ac)
        if ac and M.get("lines_added_per_week") is not None else None)
    M["commits_per_contributor_per_week"] = (
        round(M["commits_per_week"] / ac, 1)
        if ac and M.get("commits_per_week") is not None else None)

    # CHAOSS-style composite (clearly labelled, not an absolute truth)
    M["activity_index"] = sum(
        v for v in (M.get("commits_window"), M.get("merged_prs_window"),
                    M.get("closed_issues_window")) if isinstance(v, (int, float))
    )
    M["unavailable"] = unavailable
    return M


# ------------------------------------------------------------------ rendering

def fmt(v, suffix=""):
    if v is None:
        return "—"
    if isinstance(v, bool):
        return ("yes" if v else "no") + suffix
    if isinstance(v, float):
        return f"{v:,.1f}{suffix}"
    if isinstance(v, int):
        return f"{v:,}{suffix}"
    return f"{v}{suffix}"


def verdict(M):
    if M.get("archived"):
        return "🗄️  Archived — no longer developed."
    d = M.get("days_since_push")
    if d is not None and d > 180:
        return f"💤 Dormant — no pushes in {d} days."
    if d is not None and d > 60:
        return f"🐢 Slowing — last push {d} days ago."
    c30, c90 = M.get("commits_30d"), M.get("commits_90d")
    trend = ""
    if c30 is not None and c90:
        avg = c90 / 3
        if avg > 0:
            r = c30 / avg
            trend = "accelerating" if r >= 1.25 else "cooling off" if r <= 0.7 else "steady"
    cpw = M.get("commits_per_week") or 0
    level = ("very active" if cpw >= 20 else "active" if cpw >= 5
             else "moderate" if cpw >= 1 else "low-activity")
    tail = f", {trend}" if trend else ""
    return f"🚀 {level.capitalize()}{tail} — {fmt(cpw)} commits/wk."


def branch_label(M):
    """`dev` when non-default, empty when measuring the default branch."""
    mb, db = M.get("measured_branch"), M.get("default_branch")
    return mb if (mb and mb != db) else ""


def render_one(M):
    w = M["window_days"]
    L = []
    head = f"## {M['repo']}"
    if branch_label(M):
        head += f" @ {M['measured_branch']}"
    if M.get("language"):
        head += f"  ·  {M['language']}"
    L.append(head)
    if M.get("description"):
        L.append(f"_{M['description']}_")
    L.append("")
    L.append(f"⭐ {fmt(M.get('stars'))}  ·  🍴 {fmt(M.get('forks'))}  ·  "
             f"age {fmt(M.get('age_days'))}d  ·  last push {fmt(M.get('days_since_push'))}d ago"
             + ("  ·  ⚠️ fork" if M.get("is_fork") else ""))
    L.append("")
    L.append(f"**{verdict(M)}**")
    L.append("")
    L.append(f"### Development speed — last {w} days")
    L.append("| Metric | Value | Per week |")
    L.append("|---|--:|--:|")
    L.append(f"| Commits | {fmt(M.get('commits_window'))} | {fmt(M.get('commits_per_week'))} |")
    if branch_label(M) and M.get("commits_window_default_branch") is not None:
        L.append(f"| Commits on default `{M['default_branch']}` | "
                 f"{fmt(M.get('commits_window_default_branch'))} | "
                 f"{fmt(per_week(M.get('commits_window_default_branch'), w))} |")
    L.append(f"| Lines added | {fmt(M.get('lines_added_window'))} | {fmt(M.get('lines_added_per_week'))} |")
    L.append(f"| Lines deleted | {fmt(M.get('lines_deleted_window'))} | |")
    L.append(f"| Net lines | {fmt(M.get('net_lines_window'))} | |")
    L.append(f"| PRs merged | {fmt(M.get('merged_prs_window'))} | {fmt(M.get('merged_prs_per_week'))} |")
    L.append(f"| PRs opened | {fmt(M.get('opened_prs_window'))} | |")
    L.append(f"| Issues closed | {fmt(M.get('closed_issues_window'))} | |")
    L.append(f"| Active contributors | {fmt(M.get('active_contributors_window'))} | |")
    L.append(f"| LOC+ per contributor | | {fmt(M.get('loc_added_per_contributor_per_week'))} |")
    L.append(f"| Commits per contributor | | {fmt(M.get('commits_per_contributor_per_week'))} |")
    L.append("")
    L.append("### Cadence & flow")
    L.append("| Metric | Value |")
    L.append("|---|--:|")
    L.append(f"| Median time-to-merge | {fmt(M.get('median_ttm_hours'))} h "
             f"_(n={M.get('ttm_sample_size', 0)})_ |")
    L.append(f"| Releases (last year) | {fmt(M.get('releases_last_year'))} |")
    L.append(f"| Median release interval | {fmt(M.get('median_release_interval_days'))} d |")
    L.append(f"| Latest release | {fmt((M.get('latest_release_at') or '—')[:10])} |")
    L.append(f"| Commits 30d / 90d / 365d | {fmt(M.get('commits_30d'))} / "
             f"{fmt(M.get('commits_90d'))} / {fmt(M.get('commits_365d'))} |")
    L.append("")
    L.append(f"**Activity index (window):** {fmt(M.get('activity_index'))}  "
             f"— commits + merged PRs + closed issues (CHAOSS-style composite).")
    notes = []
    if branch_label(M):
        why = {"explicit": "pinned", "auto": "busiest branch this window"}.get(
            M.get("branch_selection"), "")
        notes.append(f"commits/lines/contributors measured on `{M['measured_branch']}`"
                     + (f" ({why})" if why else "")
                     + f"; default is `{M.get('default_branch')}`")
    elif M.get("branch_selection") == "fallback_default":
        notes.append("⚠️ branch scan unavailable — measured the default branch; "
                     "dev-branch work (if any) not counted")
    if M.get("lines_added_window") is not None:
        notes.append("lines = sum of per-commit line stats on the measured branch, "
                     "merges excluded (churn — rewrites count on both sides)")
    if M.get("lines_extrapolated"):
        notes.append(f"⚠️ line stats extrapolated from the most recent "
                     f"{fmt(M.get('lines_commits_sampled'))} commits — approximate")
    if M.get("contributors_sampled"):
        notes.append(f"active contributors sampled from the most recent "
                     f"{COMMIT_AUTHOR_SAMPLE} commits")
    if notes:
        L.append("_" + "; ".join(notes) + "._")
    if M.get("unavailable"):
        L.append("")
        L.append(f"> ⚠️ Unavailable this run (GitHub still computing or repo too "
                 f"large): {', '.join(M['unavailable'])}. Re-run to retry.")
    return "\n".join(L)


def render_compare(rows):
    rows = sorted(rows, key=lambda m: m.get("activity_index") or 0, reverse=True)
    w = rows[0]["window_days"]
    L = [f"## Comparison — last {w} days (sorted by activity index)", ""]
    L.append("| Repo | Branch | Commits/wk | +Lines/wk | +Lines/dev/wk | Merged PR/wk | "
             "Active contrib | Median TTM (h) | Activity idx | Last push |")
    L.append("|---|---|--:|--:|--:|--:|--:|--:|--:|--:|")
    for m in rows:
        L.append("| {repo} | {br} | {cpw} | {lpw} | {lpcw} | {ppw} | {ac} | {ttm} | {ai} | {dsp}d |".format(
            repo=m["repo"], br=branch_label(m) or (m.get("default_branch") or "—"),
            cpw=fmt(m.get("commits_per_week")),
            lpw=fmt(m.get("lines_added_per_week")),
            lpcw=fmt(m.get("loc_added_per_contributor_per_week")),
            ppw=fmt(m.get("merged_prs_per_week")),
            ac=fmt(m.get("active_contributors_window")), ttm=fmt(m.get("median_ttm_hours")),
            ai=fmt(m.get("activity_index")), dsp=fmt(m.get("days_since_push"))))
    return "\n".join(L)


# ----------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(
        description="Objective development-speed metrics for GitHub repos via `gh api`.")
    ap.add_argument("repos", nargs="+", metavar="OWNER/REPO[@BRANCH]",
                    help="one or more repos (owner/repo, https URL, or ssh URL; "
                         "@branch pins the measured branch)")
    ap.add_argument("--window-days", type=int, default=90,
                    help="analysis window in days (default 90)")
    ap.add_argument("--branch",
                    help="measure this branch on ALL repos (per-repo @branch wins); "
                         "default: auto-detect the busiest branch per repo")
    ap.add_argument("--json", action="store_true",
                    help="emit raw JSON instead of a markdown report")
    a = ap.parse_args()
    if a.window_days < 1:
        eprint("error: --window-days must be >= 1")
        sys.exit(1)

    results = []
    for i, raw in enumerate(a.repos):
        try:
            repo, branch = parse_repo(raw)
        except ValueError as e:
            eprint(f"skip: {e}")
            continue
        if i > 0:
            time.sleep(2)  # be gentle on the search rate limit (30/min)
        try:
            results.append(fetch(repo, a.window_days, branch_override=branch or a.branch))
        except GhError as e:
            eprint(f"error [{repo}]: {e.msg}")
            results.append({"repo": repo, "error": e.msg})

    if a.json:
        payload = results[0] if len(results) == 1 else results
        print(json.dumps(payload, indent=2, default=str))
        return

    ok = [r for r in results if "error" not in r]
    if not ok:
        eprint("no repos analyzed.")
        sys.exit(2)
    if len(ok) > 1:
        print(render_compare(ok))
        print()
    for r in ok:
        print(render_one(r))
        print()


if __name__ == "__main__":
    main()
