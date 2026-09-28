---
name: capture-feedback
description: "Capture structured feedback on what this companion produced — who, about which output, what was wrong, what good looks like — into the seat's own canon folder, and route it: a calibration note the next run reads before acting, a playbook change proposed through the operator queue (applied only after approval), or a report-a-problem alert. Used by the human, the reviewer during calibration, or the companion after a rated output."
category: role-companions
allowed-tools: Read, Write, Bash, Glob, Grep, Skill
user-invocable: true
argument-hint: "[--calibration] [about <execution-id | brief YYYY-MM-DD>] <what was wrong / what good looks like>"
requires:
  binaries: [git]
metadata:
  version: "1.0"
  created: 2026-09-28
  author: Ability.ai
  changelog:
    - "1.0: Initial version (ent#510, Tandem framework) — one lintable feedback entry per capture in agents/<self>/feedback/<date>-<slug>.yaml (rating, about, what_was_wrong, what_good_looks_like, action, status); calibration notes are read by role-context before every run; a proposed change to the companion's own playbooks goes to the operator queue and is applied only after approval; a negative rating the platform has not already escalated raises one bounded operator-queue alert; published through /canon-publish (own folder only). Generalises the capture → sheet → alert feedback loop"
---

# Capture Feedback

> ℹ️ **First, set expectations:** print one line with this skill's version and its most recent change (the top entry of `metadata.changelog`). Then proceed.

Turn "that was wrong" into something the seat learns from. Every capture becomes **one lintable entry** in this companion's own canon folder and is **routed** — it never just sits in a chat.

**Who calls it:** the primary human or a reviewer (`/capture-feedback …`, or natural language — "note that the brief should lead with pipeline"), and the companion itself when a person rated one of its outputs negatively in the conversation. During calibration (`x-role.status: calibrating`) every reviewed output's note comes through here with `--calibration`.

> Ratings are not delivered to the agent by the platform today — the companion sees a rating only when the person says it in the conversation. Capture what you are told; never claim to have read a rating you were not given.

## Process

### Step 1: Load the seat

Run `/role-context --quiet`. Resolve `CANON` and `SELF` from `template.yaml` (`x-canon.clone_path`, `x-canon.folder`) the same way it does. No canon clone → stop and point at `/canon-doctor`.

### Step 2: Structure the feedback

Ask only for what is missing (one question at most — the person's time is the scarce input):

| Field | Meaning |
|---|---|
| `about` | the output: an execution id, `brief <date>`, or a one-line description |
| `rating` | `negative` · `neutral` · `positive` |
| `what_was_wrong` | one line — the defect, not the person |
| `what_good_looks_like` | one line — the correction the next run should apply |
| `category` | `accuracy` · `relevance` · `tone` · `format` · `timeliness` · `scope` · `other` |
| `from` | the role of the person giving it (`role:<id>`), and their name — never an email (the canon is open to the whole company) |

Positive feedback is captured too: it tells the seat what to keep.

### Step 3: Decide the action

- **`calibration-note`** — default while calibrating, and for any correction the next run should apply. `/role-context` loads open notes before every run.
- **`playbook-change`** — the fix is a change to this companion's own skills or playbooks. **Do not edit them.** Raise it through the operator queue (a decision request: what would change, why, the feedback id) the way your platform prompt describes; it is applied only after approval. Until the platform re-triggers on the answer, the item says "applied at the next wake-up".
- **`report-problem`** — a person flagged an output as wrong and it is not a simple correction (wrong data, a missed commitment, harm): raise **one** operator-queue alert (not a decision request) with a one-line summary and the feedback id, the way your platform prompt describes the queue. A negative rating given in the Workspace already raises the platform's own report-a-problem item — then do not raise a second one; capture the entry and reference it. One alert per output; never repeat it for the same `about`.
- **`none`** — positive or informational.

A correction that is really about **direction** (pricing, positioning, roadmap) is not a seat correction: record `action: none`, and tell the person it belongs in a canon proposal to the direction's owner.

### Step 4: Write the entry

`$CANON/agents/$SELF/feedback/<YYYY-MM-DD>-<slug>.yaml` — restricted grammar (flat scalars, quoted values containing `: `, prose only in `notes`):

```yaml
schema_version: 1
id: 2026-09-28-brief-lead-with-pipeline
date: 2026-09-28
from: "role:sales-lead (Jordan)"
about: "brief 2026-09-28"
rating: negative
category: relevance
what_was_wrong: "Led with web traffic, which the seat does not own."
what_good_looks_like: "Lead with the pipeline gap; traffic only when it moves the pipeline."
action: calibration-note          # calibration-note | playbook-change | report-problem | none
status: open                      # open | applied | declined
notes: ""
```

An earlier open note the new one supersedes → set the old one to `status: applied` (or `declined`, with the reason in `notes`) in the same commit. Never delete an entry.

### Step 5: Publish and confirm

Publish with `/canon-publish` (own folder, lint-gated). Reply in one or two lines: what was captured, what happens next ("I'll apply this from the next run", "proposed to the operator — applied once approved", "reported to the operator").

## Error handling

| Situation | Action |
|---|---|
| No canon clone | Stop — `/canon-doctor` |
| The person is vague | One clarifying question, then capture what you have — never drop it |
| Same output already reported (by you or by the platform's rating flow) | Capture the entry; do not raise a second alert |
| `/canon-publish` refuses (lint) | Fix the entry's fields and re-run; never leave feedback only in chat |
