---
name: repo-velocity
description: Measure the development speed / velocity / activity of any GitHub repository using objective metrics from the GitHub API — commits, lines added/deleted, merged-PR throughput, active contributors, time-to-merge, and release cadence. Compares multiple repos side by side.
when_to_use: Use when someone wants an objective read on how fast a GitHub project is moving — "how active is repo X", "is this project still maintained", "compare the velocity of these repos", "how many lines/commits/PRs per week", evaluating a dependency's health, or benchmarking OSS projects against each other.
argument-hint: "OWNER/REPO[@BRANCH] [more repos…] [--window-days N] [--branch B] [--json]"
allowed-tools: Bash, Read
user-invocable: true
metadata:
  version: "1.5"
  author: Ability.ai
  changelog:
    - "1.5: Per-contributor leverage metrics — LOC+ per contributor per week and commits per contributor per week, in the JSON, the single-repo table, and the comparison table (+Lines/dev/wk column). Same caveats as the inputs: contributor counts are sampled on busy repos, LOC is churn, and solo-repo per-capita numbers are trivially inflated — read alongside absolute volume."
    - "1.4: Honest LOC — lines added/deleted now come from summing per-commit line stats on the measured branch (GraphQL history; merge commits excluded to avoid double-counting merged branches). The compare endpoint is GONE from the LOC path: GitHub silently caps compare diffs at ~300 files, so on any large window it summed an arbitrary file subset — verified: Trinity 90d showed net -6,015 via compare vs ground-truth +213,589 (base..head diff) / +311,877 (churn) from a local clone; the new method matches the clone's no-merge churn to the digit. Repos beyond 2,000 in-window commits are extrapolated from the most recent 2,000 commits' date span and flagged."
    - "1.3: Branch-aware measurement — commits/lines/contributors are no longer blindly measured on the default branch. The tool enumerates ALL branch heads (paginated GraphQL; GitHub's TAG_COMMIT_DATE ref ordering is unreliable for branches — verified it buried an active `dev` below stale feature branches), batch-counts in-window commits on every active branch, and measures the busiest development line. Stable-branch preference (default/dev/release names win unless a feature branch is >10% busier) stops short-lived feature branches — which contain the dev line's whole history — from stealing the headline. The default branch's in-window count is always reported alongside; `owner/repo@branch` and `--branch` pin it explicitly. Repos that develop on dev and merge to main at release (e.g. Trinity: 811 commits/90d on dev vs 294 on main) are no longer ~3x undercounted."
    - "1.2: Drop the LAST /stats dependency — commit counts now use the Link-header rel=last trick (one request, exact, no 202). This also fixed a silent accuracy bug: /stats/commit_activity was undercounting commits ~40% vs ground-truth enumeration (verified: fd 90d = 73 both methods). The tool now makes ZERO 202-prone calls — every metric returns on the first run."
    - "1.1: Stop depending on GitHub's flaky /stats/* endpoints — /stats/contributors and /stats/code_frequency both 202 indefinitely on some repos. Lines added/deleted now come from the compare endpoint (net diff base..head); active contributors from the commits list."
    - "1.0: Initial version — objective repo velocity via gh api (commits, lines ±, merged-PR throughput, contributors, time-to-merge, release cadence); single-repo report, multi-repo comparison, and --json modes"
category: research-and-analysis
---

# Repo Velocity

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `repo-velocity vX.Y — recent: <summary>`. Then proceed.

## Purpose

Give an **objective, reproducible** measure of how fast a GitHub repository is being developed — the kind of question "which OSS project ships faster?" actually deserves. It reports the components of [CHAOSS Project Velocity](https://chaoss.community/kb/metric-project-velocity/) (commits, merged PRs, contributors) plus raw code throughput (lines added/deleted per week) and flow metrics (time-to-merge, release cadence), for one repo or several side by side.

All data comes through the **GitHub CLI (`gh api`)**, so it inherits the user's existing `gh` authentication and rate limits — no tokens to configure, and every run computes identically. The heavy lifting lives in a deterministic Python script (stdlib only), not in ad-hoc API calls, so results are consistent across runs.

## State Dependencies

| Source | Location | Read | Write |
|--------|----------|:----:|:-----:|
| GitHub REST API | via `gh api` (repo meta, `stats/*`, `search/issues`, `pulls`, `releases`) | ✅ | — |
| Analysis engine | `~/.claude/skills/repo-velocity/scripts/repo_velocity.py` | ✅ | — |

This skill is **read-only** — it never writes to any repo or to GitHub. It only emits a report to the conversation (and, with `--json`, machine-readable output).

## Prerequisites

- **GitHub CLI authenticated**: `gh auth status` should show a logged-in account. If not, tell the user to run `gh auth login` (do not attempt the interactive login yourself — suggest they type `! gh auth login`).
- Python 3 (stdlib only — no pip installs).

## Process

1. **Parse the target(s)** from the argument string. Accept any mix of `owner/repo`, full `https://github.com/owner/repo` URLs, or `git@github.com:owner/repo.git` — the script normalizes all of these, so pass them through verbatim. An optional `@branch` suffix (`Abilityai/trinity@dev`) pins the measured branch; without it the script auto-detects the busiest development branch per repo. Pull out an optional `--window-days N` (default 90), `--branch B` (pin one branch for all repos), and `--json` if the user asked for raw output.

2. **(Optional) confirm auth** with `gh auth status` if you have any reason to think `gh` isn't logged in.

3. **Run the engine:**
   ```bash
   python3 ~/.claude/skills/repo-velocity/scripts/repo_velocity.py <repo> [<repo> …] [--window-days N] [--json]
   ```
   - One repo → a full single-repo report.
   - Two or more → a sorted comparison table first, then per-repo detail.
   - `--json` → raw JSON (single object for one repo, array for many) for programmatic reuse / saving / cross-run comparison.

4. **Expect a complete result on the first run.** The tool makes **zero** `/stats/*` calls, so there's no 202 warm-up to wait out — every metric returns immediately. If something *does* appear under **"⚠️ Unavailable this run"**, it's a genuine condition (a private/empty repo, a transient network error, or a compare range too large to diff), not a cache miss. A re-run only helps for transient errors. Mention to the user when a metric stays blank.

5. **Present the result.** Show the markdown report as-is. For multiple repos, lead with the comparison table and a one-line takeaway (who's moving fastest, who's dormant). Keep the activity-index caveat (see below) in mind — don't present any single number as the absolute truth.

6. **Offer the obvious follow-ups** when useful: a different `--window-days` (30 for "right now", 365 for "over the year"), `--json` to save/compare, or adding more repos to the comparison.

## Outputs

- **Single repo**: header (stars/forks/age/last-push + a one-line verdict), a *Development speed* table (commits, lines ±, merged/opened PRs, issues closed, active contributors — each with a per-week rate), a *Cadence & flow* table (median time-to-merge, release cadence, 30/90/365-day commit trend), and the composite activity index.
- **Multiple repos**: a comparison table sorted by activity index, then each repo's full report.
- **`--json`**: the same metrics as structured data, for saving or feeding into another tool.

## Metric reference & honest caveats

- **Lines added/deleted** is the literal "lines of code they push out" — the **sum of per-commit line stats** on the measured branch over the window (GraphQL `history`, paginated), with **merge commits excluded** (a merge's diff vs its first parent repeats the merged branch's changes). This measures *churn*: a line written then rewritten counts on both sides, so "net lines" here is churn-net, not a base..head diff. Repos with more than 2,000 in-window commits are extrapolated from the most recent 2,000 commits' actual date span and flagged. **Never compute LOC via the compare endpoint** — GitHub silently caps compare diffs at ~300 files and returns an arbitrary subset on large windows (this produced a wrong *sign* on a real repo: net -6K reported vs +214K actual). And **raw LOC is a famously weak measure** regardless — treat it as one signal, never the verdict.
- **Activity index** = commits + merged PRs + closed issues in the window. It's a CHAOSS-style composite for *relative* comparison across repos, deliberately simple and explicitly labelled — not an absolute productivity score.
- **Active contributors** counts distinct commit authors in the window, from the commits list (sampled from the most recent ~500 commits on very busy repos — flagged when sampled).
- **Per-contributor rates** (LOC+ per contributor per week, commits per contributor per week) divide the weekly rates by active contributors — a team-leverage view. Inherit every caveat of their inputs: sampled contributor denominators on busy repos, churn-based LOC numerators, and solo repos posting trivially huge per-capita numbers. Present them next to absolute volume, never alone.
- **Median time-to-merge** is sampled from up to the 50 most-recently-updated closed PRs (those actually merged) — an estimate, with its sample size shown.
- **`open_issues_count`** from GitHub includes open PRs; the report labels it accordingly and prefers the windowed search counts for throughput.
- **Commit counts** are exact for any window — counted via the `Link: rel="last"` header on a `per_page=1` commits query (one request, no `/stats`). Independently verified against full SHA enumeration. They count commits **on the measured branch** by committer date.
- **Measured branch (v1.3)**: commits, lines, and contributors are measured on the **busiest development line**, not blindly on the default branch. Detection: enumerate all branch heads (paginated GraphQL, capped at 1,000 branches), batch-count in-window commits on every branch whose head moved inside the window (capped at the 150 most recent, but the default branch and conventional dev names are never dropped), then pick the branch with the most in-window commits — with a **stable-branch preference**: a branch that is not the default and not conventionally named (`dev`, `develop`, `release/*`, `next`, …) only wins if it is >10% busier than the best stable branch, because short-lived feature branches contain the whole history of the line they forked from and would otherwise always win by a few commits. When the measured branch differs from the default, the report shows both commit counts and labels the branch everywhere. Caveats: this measures ONE line of development — parallel unmerged work on *other* branches is still not summed (that would double-count shared history); merged-PR throughput is branch-inclusive by nature (PRs merged into any base branch). `owner/repo@branch` or `--branch` overrides detection; a failed scan falls back to the default branch with an explicit warning in the report.

## Consistency notes (why this stays reliable)

- **Never use the `/stats/*` endpoints**: `/stats/code_frequency`, `/stats/contributors`, AND `/stats/commit_activity` all return `202 Accepted` for minutes or *indefinitely* on real repos (confirmed in testing), and `commit_activity` also undercounts when it does answer (~40% low vs ground-truth enumeration on fd). This skill uses none of them: commit counts via the `Link: rel="last"` trick, lines via **compare**, contributors via the **commits list** — all exact and 202-free. **Don't "fix" a blank metric by reaching back to any `/stats/*` endpoint** — that's the trap this tool was rebuilt twice to avoid.
- **Always GET**: `gh api` silently switches to **POST** the moment a `-f` field is present — which turns read calls into create attempts (422/404). The script forces `-X GET` so `-f k=v` become query params. Don't hand-roll `gh api … -f …` read calls without `-X GET`.
- **Search rate limit** is 30 req/min; the script makes ≤3 search calls per repo and pauses 2s between repos, so a handful of repos per run is safe. For a long list, run in smaller batches.
- **Never trust `refs(orderBy: TAG_COMMIT_DATE)` for branches**: GitHub's GraphQL ref ordering is unreliable on branch refs (verified: it buried an actively-updated `dev` branch below stale feature branches). The branch scan therefore enumerates all heads with plain pagination and filters by head-commit date itself. Don't "optimize" it back to a top-N ordered query.
- **Graceful degradation**: any single endpoint failing (private, too-large, transient) is recorded under "Unavailable" rather than aborting the whole report.
