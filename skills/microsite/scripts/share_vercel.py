#!/usr/bin/env python3
"""Deploy a built microsite to Vercel as a PRIVATE shareable page.

Private-share semantics - the link is for the people it's sent to, nobody else:

- **Hard to guess**: one share = one Vercel project named ms-<24 hex chars>
  (96 bits from `secrets`) - the URL cannot be enumerated or guessed, and
  carries no hint of its content. The name is kept short (27 chars) because
  Vercel truncates long project names in the served URL, which would silently
  cut the entropy. `*.vercel.app` uses a wildcard TLS cert, so the hostname
  does not leak via certificate-transparency logs either.
- **Non-indexable**: the deploy carries `X-Robots-Tag: noindex, nofollow,
  noarchive` on every response (via a staged vercel.json) AND a
  `<meta name="robots">` tag injected into the staged copy of the page
  (the local source file is never touched).
- Production deploy, deliberately not a preview: new-project preview URLs sit
  behind Vercel Authentication by default, which would wall out the recipient.

The page does not auto-expire - "temporary" means removable in one command:

    vercel project rm <project> --yes

Usage:
Credentials: set $VERCEL_TOKEN for headless/agent runs (the CLI's non-interactive auth
path). A CLI already logged in via `vercel login` also works for a human at a terminal.

    python3 share_vercel.py path/to/page.html [--slug name] [--project full-name] [--gate]

`--gate` puts the page behind a mandatory email step and records who reads it:
a middleware serves only the gate page until an email is given (signed cookie,
90 days), and a first-party tracker posts time-per-section and link clicks to
the project's own /api/t - visitors are tracked anonymously from the first hit
and their earlier visits are named once they give an email. Append `?r=<tag>`
to a link you send to know which send a visit came from. The kit lives in
`gate/`; events go to one shared Postgres. The project needs three env vars
(GATE_SECRET, GATE_DATABASE_URL, GATE_REPORT_TOKEN): the secret is generated,
the other two come from the environment (or, failing that, `~/.config/microsite/gate.env`)
the first time a project is gated, and redeploys reuse what the project already has.

`--gate --soft` keeps the tracking but drops the wall: the page opens for anyone
with the link, and after ~45 active seconds a small dismissible card asks for an
email (`gate/ask.js`). No middleware is deployed, so the page and its assets are
served to everyone. A redeploy keeps the mode only if it repeats `--soft`.

Stages index.html + sibling assets/ into a temp dir named after the project
(`vercel deploy --yes` auto-creates/links the project from the dir name),
deploys, then prints JSON: {"url", "alias", "project", "remove"}.
Exit 0 on success, 3 on deploy failure.
"""
import argparse
import html as htmllib
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

NOINDEX_META = '<meta name="robots" content="noindex, nofollow, noarchive">'
NOINDEX_JSON = {
    "headers": [
        {"source": "/(.*)",
         "headers": [{"key": "X-Robots-Tag", "value": "noindex, nofollow, noarchive"}]}
    ]
}


def sanitize(s):
    s = re.sub(r"[^a-z0-9-]+", "-", s.lower()).strip("-")
    return re.sub(r"-{2,}", "-", s) or "page"


GATE_KIT = Path(__file__).resolve().parent / "gate"
GATE_CONF = Path(os.environ.get("MICROSITE_GATE_ENV", "~/.config/microsite/gate.env")).expanduser()
GATE_VARS = ("GATE_SECRET", "GATE_DATABASE_URL", "GATE_REPORT_TOKEN", "GATE_PAGE")


def gate_conf():
    """Gate config: environment first (agent credentials), then the local config file."""
    conf = {}
    if GATE_CONF.is_file():
        for line in GATE_CONF.read_text().splitlines():
            k, sep, v = line.partition("=")
            if sep and not k.strip().startswith("#"):
                conf[k.strip()] = v.strip().strip('"\'')
    for k in ("GATE_DATABASE_URL", "GATE_REPORT_TOKEN"):
        if os.environ.get(k, "").strip():
            conf[k] = os.environ[k].strip()
    return conf


def vercel_auth():
    """$VERCEL_TOKEN is the headless auth path: an injected agent has no browser to
    complete `vercel login` with. Falls back to an already-logged-in CLI."""
    token = os.environ.get("VERCEL_TOKEN", "").strip()
    return ["--token", token] if token else []


def stage_gate(stage, page_html, assets, soft=False):
    """Lay the staged dir out as public/ (static) + middleware + api functions."""
    pub = stage / "public"
    pub.mkdir()
    tracker = "<script>\n" + (GATE_KIT / "tracker.js").read_text() + "</script>\n"
    if soft:
        tracker += "<script>\n" + (GATE_KIT / "ask.js").read_text() + "</script>\n"
    i = page_html.lower().rfind("</body>")
    page_html = page_html[:i] + tracker + page_html[i:] if i >= 0 else page_html + tracker
    (pub / "index.html").write_text(page_html, encoding="utf-8")
    if not soft:
        t = re.search(r"<title>(.*?)</title>", page_html, re.IGNORECASE | re.DOTALL)
        title = htmllib.unescape(t.group(1)).strip() if t else "Private page"
        # "Headline · Brand" titles: the headline is the h1, the brand joins the tag
        head, _, brand = title.rpartition(" · ")
        gate = (GATE_KIT / "gate.html").read_text()
        gate = gate.replace("__TITLE__", htmllib.escape(title)).replace("__HEAD__", htmllib.escape(head or title))
        gate = gate.replace("__TAG__", htmllib.escape(brand + " · private page" if head else "Private page"))
        (pub / "_gate.html").write_text(gate, encoding="utf-8")
        shutil.copy(GATE_KIT / "middleware.js", stage / "middleware.js")
    if assets.is_dir():
        shutil.copytree(assets, pub / "assets")
    shutil.copy(GATE_KIT / "package.json", stage / "package.json")
    shutil.copytree(GATE_KIT / "api", stage / "api")


def project_is_gated(stage, project, scope):
    """True when an existing project already carries the gate (its GATE_SECRET is set)."""
    sc = ["--scope", scope] if scope else []
    r = subprocess.run(["vercel", "link", "--yes", "--project", project] + sc + vercel_auth(),
                       cwd=stage, capture_output=True, text=True)
    if r.returncode != 0:
        return False
    ls = subprocess.run(["vercel", "env", "ls", "production"] + sc + vercel_auth(), cwd=stage, capture_output=True, text=True)
    return "GATE_SECRET" in ls.stdout + ls.stderr


def ensure_gate_env(stage, project, scope):
    """Link the staged dir to the project (creating it) and set any missing gate env vars."""
    sc = ["--scope", scope] if scope else []
    r = subprocess.run(["vercel", "link", "--yes", "--project", project] + sc + vercel_auth(),
                       cwd=stage, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("error: vercel link failed: " + (r.stderr or r.stdout))
    ls = subprocess.run(["vercel", "env", "ls", "production"] + sc + vercel_auth(), cwd=stage, capture_output=True, text=True)
    have = set(re.findall(r"\bGATE_[A-Z_]+\b", ls.stdout + ls.stderr))
    conf = gate_conf()
    values = {"GATE_SECRET": secrets.token_hex(32), "GATE_PAGE": project,
              "GATE_DATABASE_URL": conf.get("GATE_DATABASE_URL"),
              "GATE_REPORT_TOKEN": conf.get("GATE_REPORT_TOKEN")}
    for name in GATE_VARS:
        if name in have:
            continue
        if not values[name]:
            sys.exit("error: {} is not set on the project, in the environment, or in {}".format(name, GATE_CONF))
        r = subprocess.run(["vercel", "env", "add", name, "production"] + sc + vercel_auth(),
                           cwd=stage, input=values[name], capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit("error: could not set {}: {}".format(name, r.stderr or r.stdout))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("page", help="built microsite HTML file")
    ap.add_argument("--slug", help="name fragment for the project (default: html filename)")
    ap.add_argument("--project", help="full project name override (skips the unique suffix)")
    ap.add_argument("--scope", help="Vercel team/scope slug (auto-resolved when the account has exactly one)")
    ap.add_argument("--gate", action="store_true",
                    help="require an email to view and track time per section (needs --scope)")
    ap.add_argument("--soft", action="store_true",
                    help="with --gate: open the page to anyone with the link and ask for an "
                         "email after ~45 active seconds instead of requiring it up front")
    ap.add_argument("--ungate", action="store_true",
                    help="deliberately redeploy a gated project without the gate")
    a = ap.parse_args()
    if a.soft and not a.gate:
        sys.exit("error: --soft goes with --gate")

    page = Path(a.page).resolve()
    if not page.is_file():
        sys.exit(f"error: no such file: {page}")

    # slug is deliberately NOT in the name: no content hint in the hostname, and
    # short names survive Vercel's URL truncation with all 96 bits intact
    project = a.project or "ms-{}".format(secrets.token_hex(12))

    auth = vercel_auth()
    who = subprocess.run(["vercel", "whoami"] + auth, capture_output=True, text=True)
    if who.returncode != 0:
        sys.exit("error: vercel CLI missing or not authenticated - install the CLI, then "
                 "set VERCEL_TOKEN (headless) or run `vercel login` (interactive)")

    root = Path(tempfile.mkdtemp(prefix="microsite_share_"))
    stage = root / project  # dir name = project name; --yes auto-creates the project
    stage.mkdir()
    html = page.read_text(encoding="utf-8")
    m = re.search(r"<head[^>]*>", html, re.IGNORECASE)
    if m:  # inject noindex into the staged copy only; local source stays clean
        html = html[:m.end()] + "\n" + NOINDEX_META + html[m.end():]
    (stage / "vercel.json").write_text(json.dumps(NOINDEX_JSON, indent=2), encoding="utf-8")
    assets = page.parent / "assets"
    if a.gate:
        stage_gate(stage, html, assets, a.soft)
        ensure_gate_env(stage, project, a.scope)
    else:
        if a.project and not a.ungate and project_is_gated(stage, project, a.scope):
            shutil.rmtree(root, ignore_errors=True)
            sys.exit("error: project is gated - {} requires an email to view. Redeploy with --gate "
                     "(or --ungate to remove the gate on purpose).".format(project))
        (stage / "index.html").write_text(html, encoding="utf-8")
        if assets.is_dir():
            shutil.copytree(assets, stage / "assets")

    cmd = ["vercel", "deploy", "--prod", "--yes"] + auth
    if a.scope:
        cmd += ["--scope", a.scope]
    try:
        r = subprocess.run(cmd, cwd=stage, capture_output=True, text=True, timeout=600)
        if r.returncode != 0 and not a.scope and "missing_scope" in (r.stdout + r.stderr):
            # non-interactive mode applies no default scope - retry with the only team
            scopes = re.findall(r'"name":\s*"([^"]+)"', r.stdout + r.stderr)
            if len(set(scopes)) == 1:
                r = subprocess.run(cmd + ["--scope", scopes[0]],
                                   cwd=stage, capture_output=True, text=True, timeout=600)
            else:
                sys.exit("error: multiple Vercel scopes {} - pass --scope".format(sorted(set(scopes))))
    finally:
        shutil.rmtree(root, ignore_errors=True)

    if r.returncode != 0:
        sys.stderr.write(r.stderr or r.stdout)
        sys.exit(3)

    # CLI output format varies by version (bare URL vs structured) - regex, don't split lines
    hits = re.findall(r"https://[A-Za-z0-9.-]+\.vercel\.app", r.stdout + r.stderr)
    url = hits[-1] if hits else "https://{}.vercel.app".format(project)
    print(json.dumps({
        "url": url,
        "project": project,
        "remove": "echo y | vercel project rm {}".format(project),
        "noindex": True,
        "gated": a.gate,
        "gate_mode": ("soft" if a.soft else "hard") if a.gate else None,
    }, indent=2))


if __name__ == "__main__":
    main()
