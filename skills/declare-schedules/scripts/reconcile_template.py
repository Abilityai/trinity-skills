#!/usr/bin/env python3
"""Reconcile an agent repo's template.yaml `schedules:` block against live Trinity state.

A repo is only an honest declaration of what an agent runs unattended if its
template.yaml lists every live schedule. In practice templates under-declare, and a
`model:` pin set on a live schedule but declared in no reviewed file is silently dropped
by the next redeploy from the template.

This writes live state into the declaration, preserving the human-authored `purpose:` /
`description:` prose on entries it can match.

Matching order (first hit wins):
  1. live name prefix `[id]` == declared `id`
  2. declared `name` == live name (with or without the `[id] ` prefix)
  3. declared `cron` == live cron AND declared `message` == live message

Entries declared but NOT live are KEPT and flagged, never silently deleted - a disabled
declaration may be an intended-but-uncreated cron, and deleting it is a judgment call for
the owner, not this script.

Usage:
    reconcile_template.py --template <path> --live <live.json> [--agent <name>] [--write]

Without --write it prints the diff and exits 1 if changes are needed (dry-run default).
"""
from __future__ import annotations

import argparse
import json
import re
import sys

ID_RE = re.compile(r"^\[([a-z0-9][a-z0-9-]*)\]\s*(.*)$")
FIELD_ORDER = ["id", "name", "cron", "timezone", "message", "model", "purpose", "description", "enabled", "timeout_seconds", "allowed_tools"]


def split_name(live_name):
    m = ID_RE.match(live_name or "")
    return (m.group(1), m.group(2).strip()) if m else (None, (live_name or "").strip())


def load_live(path):
    raw = json.load(open(path))
    out = []
    for s in raw.get("schedules", raw if isinstance(raw, list) else []):
        sid, bare = split_name(s.get("name"))
        out.append({
            "_id": sid,
            "_bare_name": bare,
            "_live_name": s.get("name"),
            "cron": s.get("cron_expression"),
            "timezone": s.get("timezone") or "UTC",
            "message": s.get("message"),
            "model": s.get("model"),
            "enabled": bool(s.get("enabled")),
            "timeout_seconds": s.get("timeout_seconds"),
            "allowed_tools": s.get("allowed_tools"),
        })
    return out


def match(live, declared):
    for d in declared:
        if live["_id"] and d.get("id") == live["_id"]:
            return d
    for d in declared:
        dn = (d.get("name") or "").strip()
        if dn and dn in (live["_bare_name"], live["_live_name"]):
            return d
    for d in declared:
        if d.get("cron") == live["cron"] and (d.get("message") or "").strip() == (live["message"] or "").strip():
            return d
    return None


def yaml_scalar(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, list):
        return "[" + ", ".join(json.dumps(str(x)) for x in v) + "]"
    s = str(v)
    if "\n" in s:
        body = "\n".join("      " + ln for ln in s.split("\n"))
        return "|-\n" + body
    return json.dumps(s)  # always quote: safe for colons, #, leading /


def render(entries):
    lines = []
    for e in entries:
        first = True
        for k in FIELD_ORDER:
            if k not in e or e[k] is None and k in ("purpose", "description", "allowed_tools", "timeout_seconds", "model"):
                continue
            prefix = "  - " if first else "    "
            lines.append(f"{prefix}{k}: {yaml_scalar(e[k])}")
            first = False
        if e.get("_orphan"):
            lines.append("    # NOT LIVE on Trinity as of this reconcile - kept, not deleted.")
            lines.append("    # Either create it or remove this entry; that call belongs to the owner.")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True)
    ap.add_argument("--live", required=True)
    ap.add_argument("--agent", default="")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    try:
        import yaml
    except ImportError:
        sys.stderr.write("FATAL: pyyaml required\n")
        return 2

    text = open(a.template).read()
    doc = yaml.safe_load(text) or {}
    declared = doc.get("schedules") or []
    live = load_live(a.live)

    out, changes, matched_ids = [], [], set()
    for l in live:
        d = match(l, declared)
        e = {}
        if d:
            matched_ids.add(id(d))
            for k in ("purpose", "description"):
                if d.get(k):
                    e[k] = d[k]
        e["id"] = l["_id"] or (d or {}).get("id") or re.sub(r"[^a-z0-9]+", "-", l["_bare_name"].lower()).strip("-")
        e["name"] = l["_bare_name"]
        for k in ("cron", "timezone", "message", "model", "enabled", "timeout_seconds", "allowed_tools"):
            e[k] = l[k]
        if not d:
            changes.append(f"  + NEW declaration (live but undeclared): [{e['id']}] {e['name']}")
        else:
            for k in ("cron", "timezone", "message", "model", "enabled", "timeout_seconds"):
                dv, lv = d.get(k), l[k]
                if k == "timezone" and dv is None:
                    dv = "UTC"
                if k == "enabled" and dv is None:
                    dv = True
                if dv != lv:
                    short = lambda x: (str(x)[:48] + "…") if x and len(str(x)) > 48 else x
                    changes.append(f"  ~ [{e['id']}] {k}: {short(dv)!r} -> {short(lv)!r}")
        out.append(e)

    for d in declared:
        if id(d) not in matched_ids:
            e = {k: d[k] for k in FIELD_ORDER if k in d}
            # Force enabled:false. A declared-but-not-live entry has no `enabled` key on
            # many templates, and absent defaults to TRUE - so a redeploy-from-template
            # would CREATE and START a schedule nobody has running today. Off is the only
            # safe default for something we are keeping purely as a record.
            e["enabled"] = False
            e["_orphan"] = True
            e.setdefault("id", re.sub(r"[^a-z0-9]+", "-", str(d.get("name", "unknown")).lower()).strip("-"))
            out.append(e)
            changes.append(f"  ! DECLARED-NOT-LIVE (kept + flagged): {d.get('id') or d.get('name')}")

    header = (
        "# Declared schedules - the repo declares what runs on Trinity.\n"
        "#\n"
        "#   A schedule message is a CALL - `/playbook [flags]`, one line, nothing else.\n"
        "#   Policy lives in the playbook. `model:` is declared because a pin changes cost\n"
        "#   and answer quality on every run, and an undeclared pin dies on redeploy.\n"
        "#\n"
        f"# Reconciled against live Trinity{' for ' + a.agent if a.agent else ''} by\n"
        "# /declare-schedules. Do not hand-edit a live schedule; edit here and re-apply.\n"
        "schedules:\n"
    )
    block = header + render(out) + "\n"

    m = re.search(r"^schedules:\s*$.*?(?=^[a-zA-Z#]|\Z)", text, re.M | re.S)
    if m:
        # keep any comment lines immediately above the block that are not ours
        new_text = text[: m.start()] + block + text[m.end():]
    else:
        new_text = text.rstrip("\n") + "\n\n" + block

    if not changes:
        print(f"OK - {a.agent or a.template}: {len(live)} live schedules already declared correctly")
        return 0

    print(f"{a.agent or a.template}: {len(live)} live / {len(declared)} declared - {len(changes)} change(s)")
    for c in changes:
        print(c)
    if a.write:
        open(a.template, "w").write(new_text)
        print("  -> written")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
