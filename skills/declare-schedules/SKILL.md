---
name: declare-schedules
description: "Reconcile this agent's repo template.yaml `schedules:` block against its live Trinity schedules so the repo declares exactly what runs - every field including `model:`. Reads live state via list_agent_schedules on SELF, patches only the schedules block (preserving human-authored purpose/description prose), commits and pushes. Declares reality - it never edits a live schedule and never rewrites a message."
category: workspace
automation: autonomous
argument-hint: "[--dry-run]"
allowed-tools: [Bash, Read, Write, Edit, Glob, Grep, mcp__trinity__list_agent_schedules, mcp__trinity__report]
user-invocable: true
requires:
  binaries: [git, python3]
metadata:
  version: "1.1"
  changelog:
    - "1.1: Promoted to the library from an agent-level playbook that had been copied unchanged into many agent repos. Made portable: no reference to a private protocol, the live dump goes to the agent's temp folder, the bundled script is called from the skill's own directory, the push goes to the branch the agent works on"
    - "1.0: Initial version (2026-08-19). Reads live state on SELF so nobody transcribes schedules by hand; message text is copied verbatim, never normalized, because on an agent with no session-start refresh the `git pull` preamble inside a message is still load-bearing"
---

# Declare Schedules

> ℹ️ **First, set expectations:** print one line with this skill's version and its most recent change - e.g. `declare-schedules v1.1 - recent: promoted to the library`. Then proceed.

## Purpose

Make `template.yaml` tell the truth about what this agent runs unattended.

An agent's repo is the reviewed declaration of what it runs. That is only meaningful if
the repo declares what is actually running. Two things break it in practice:

- **Under-declaration.** Most templates list a fraction of their live schedules, so most
  live schedules are unreviewable by construction.
- **Undeclared `model:` pins.** A pin changes cost and answer quality on every run. Left
  live-only it dies at the next redeploy-from-template and nobody ever reviewed it.

## What this does NOT do

- **Never edits a live schedule.** It reads live and writes the repo, one direction only.
- **Never rewrites a message.** Prose messages are copied verbatim. Normalizing them to a
  bare `/playbook` call is a separate, later job with a hard prerequisite: on an agent with
  no `SessionStart` refresh hook, the `git pull` preamble inside a message is the only
  thing refreshing skills before the run. Strip it first and you break the loop.
- **Never deletes a declared-but-not-live entry.** It keeps and flags it - that entry may
  be an intended cron nobody created yet, and removing it is the owner's call.

## Process

### Step 1: Read live state (authoritative source)

```
mcp__trinity__list_agent_schedules(agent_name="<this agent's Trinity name>")
```

Write the response **verbatim** to `${TMPDIR:-/tmp}/schedules_live.json`. Without the
Trinity MCP tool (a local session), stop and say so: there is no live state to read. Do not summarize or
hand-retype it - transcription is where errors enter.

### Step 2: Reconcile

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/reconcile_template.py \
  --template template.yaml --live "${TMPDIR:-/tmp}/schedules_live.json" --agent <name>
```

Dry-run by default: it prints every change and exits 1 when the declaration is stale.
Review the diff. Then re-run with `--write`.

Matching is by `[id]` name prefix, then by name, then by cron+message - so an entry keeps
its human-authored `purpose:` / `description:` prose across the reconcile.

### Step 3: Verify

Re-read the block and confirm: one entry per live schedule, `model:` present wherever live
has a pin, and any `DECLARED-NOT-LIVE` entries carry their flag comment. Run the script once more
without `--write`: it must report nothing to change.

### Step 4: Commit and push

Scoped commit, `template.yaml` only, pushed to the branch the agent works on:

```bash
git add template.yaml
git commit -m "chore(schedules): declare live schedules incl. model pins"
git push
```

Report: live count, declared-before count, fields changed, model pins declared, any
`DECLARED-NOT-LIVE` entries, commit SHA.

## Error Recovery

| symptom | action |
|---|---|
| `pyyaml` missing | `pip install --user pyyaml`, or report and stop - never hand-edit the block as a workaround |
| No `schedules:` block in template.yaml | The script appends one. ⚠️ Note in the report: on repo-based `create_agent`, a `schedules:` block auto-materializes at deploy **without** `[id]` prefixes - the owner should reconcile by cron+message after the next deploy |
| push rejected (no write access) | Report the exact remote and stop; do not fork or open a PR unless asked |
| live schedule count is 0 | Nothing to declare. Exit clean, no commit |
