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

Credentials: set $VERCEL_TOKEN for headless/agent runs (the CLI's non-interactive auth
path). A CLI already logged in via `vercel login` also works for a human at a terminal.

Usage:
    python3 share_vercel.py path/to/page.html [--slug name] [--project full-name]

Stages index.html + sibling assets/ into a temp dir named after the project
(`vercel deploy --yes` auto-creates/links the project from the dir name),
deploys, then prints JSON: {"url", "alias", "project", "remove"}.
Exit 0 on success, 3 on deploy failure.
"""
import argparse
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


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("page", help="built microsite HTML file")
    ap.add_argument("--slug", help="name fragment for the project (default: html filename)")
    ap.add_argument("--project", help="full project name override (skips the unique suffix)")
    ap.add_argument("--scope", help="Vercel team/scope slug (auto-resolved when the account has exactly one)")
    a = ap.parse_args()

    page = Path(a.page).resolve()
    if not page.is_file():
        sys.exit(f"error: no such file: {page}")

    # slug is deliberately NOT in the name: no content hint in the hostname, and
    # short names survive Vercel's URL truncation with all 96 bits intact
    project = a.project or "ms-{}".format(secrets.token_hex(12))

    # $VERCEL_TOKEN is the headless auth path: an injected agent has no browser to
    # complete `vercel login` with. Falls back to an already-logged-in CLI.
    token = os.environ.get("VERCEL_TOKEN", "").strip()
    auth = ["--token", token] if token else []

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
    (stage / "index.html").write_text(html, encoding="utf-8")
    (stage / "vercel.json").write_text(json.dumps(NOINDEX_JSON, indent=2), encoding="utf-8")
    assets = page.parent / "assets"
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
    }, indent=2))


if __name__ == "__main__":
    main()
