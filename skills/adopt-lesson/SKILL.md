---
name: adopt-lesson
description: "Decide what this seat does with a lesson the fleet's brain synthesised — adopt, adapt, or decline, always with the why — and record it in the seat's adoptions.yaml. Advisory and additive: a lesson that contradicts the seat's own canonical facts becomes a human decision, never a silent merge; a lesson already decided is never redelivered."
category: role-companions
allowed-tools: Read, Write, Bash, Glob, Grep, Skill
user-invocable: true
argument-hint: "[<lesson-id>] | --pending | --next"
requires:
  binaries: [git]
canon: [org-context]
metadata:
  version: "1.1"
  created: 2026-09-28
  author: Ability.ai
  changelog:
    - "1.1: Review fixes (trinity-skills#2) — only canonical lessons (promoted by the brain owner) are adoptable; drafts are listed as awaiting review and never decided; --next is the scheduled one-a-day call (the role-pack set suggests it) that takes the oldest pending canonical lesson, and in an unattended run never self-decides where the role only recommends"
    - "1.0: Initial version (ent#510, Tandem framework, lesson/adoption grammar) — reads the brain's lessons for this seat's role (--pending lists the undecided ones), checks applies_to and conditions against the seat, refuses a lesson stripped of its conditions, turns a contradiction with the seat's own canonical facts into an operator-queue decision instead of a merge, and appends adopt | adapt | decline with the why to agents/<self>/adoptions.yaml (never redecides one already recorded); role-context loads adopted lessons into every run"
---

# Adopt Lesson

> ℹ️ **First, set expectations:** print one line with this skill's version and its most recent change (the top entry of `metadata.changelog`). Then proceed.

The down-flow of the learning loop (Tandem framework): **brain → lesson → this seat's decision**. Adoption is **advisory and additive** — the seat decides, with a reason, and the record is what the fleet learns from next.

## Process

### Step 1: Load the seat and the lessons

Run `/role-context --quiet` (it stops on an empty `SELF` — never write under `agents//`). The brain is `x-role.brain`; its lessons are `$CANON/agents/<brain>/lessons/*.yaml` (grammar: the Tandem framework). A lesson is **for this seat** when `applies_to.roles` contains this role and `status` is **`canonical`** (never past `review_by`). A `draft` is the brain's unreviewed synthesis: it is **never adoptable** — not by the companion, not by the primary human through this skill — until the brain's owner promotes it (`status: canonical`, `promoted_by`, `promoted_on`). A lesson marked `canonical` without `promoted_by` is treated as a draft. `superseded` lessons are never decided.

- `--pending` → list the seat's canonical lessons with no entry in `$CANON/agents/$SELF/adoptions.yaml`: `<id> · <confidence> · <statement> · conditions: <…>`; then one line `<n> draft(s) awaiting the brain owner's review` (ids only), and stop.
- `<lesson-id>` → decide that one. A draft id → stop: `<id> is a draft — not adoptable until the brain owner promotes it`. Unknown id → list the pending ones and stop.
- `--next` → the scheduled call (`/adopt-lesson --next` in the `role-pack` set, weekday mornings): take the **oldest** pending canonical lesson (by `promoted_on`) and decide that one; none pending → reply `No pending lesson` and stop. Nobody is present, so it never asks a question.

### Step 2: Guardrails (Tandem framework) — before deciding

1. **Already decided** — the id has an adoption entry → stop: `already <decision> on <date>`. Lessons are never redelivered; a changed lesson arrives as a new id that supersedes the old.
2. **Context retained** — a lesson with no `applies_to.conditions` or no `evidence` is invalid: record `decline` with `why: lesson carries no conditions or evidence`.
3. **Contradiction** — the lesson contradicts one of the seat's own canonical facts (`agents/<self>/facts.yaml` or a canonical doc) → **do not decide.** Raise an operator-queue decision request (the lesson, the fact it contradicts, the two options) the way your platform prompt describes, and stop. It is a human decision.
4. **Cooldown** — at most one adoption decision per seat per day. The brain's weekly synthesis produces lessons in a batch; the daily `--next` schedule drains that batch one lesson per day, and an entry already dated today in `adoptions.yaml` stops any further decision (`one lesson per day — next: <id>`). The rest wait (`--pending` shows them).

### Step 3: Decide — with the why

Compare the lesson's `conditions` to this seat's (team, tooling, segment, season — from the role file, `org-context`, and the seat's own facts):

- **`adopt`** — the conditions hold here; apply as stated.
- **`adapt`** — part holds; `why` states the scope ("our leads are outbound; applying the 2-day rule only to the inbound slice"). The `why` is what scopes it in every later run.
- **`decline`** — the conditions do not hold, or the seat's evidence says otherwise; `why` names which.

Where the seat's role `decides` in the responsibility the lesson touches, the companion may decide and tell the primary human. Where it only `recommends`, propose the decision to the primary human first and record their answer — in a `--next` run nobody is present, so raise it as an operator-queue decision request (the lesson, its conditions, adopt/adapt/decline with your recommendation) and stop without recording; the answer is recorded by the next run that sees it.

### Step 4: Record and publish

Append to `$CANON/agents/$SELF/adoptions.yaml` (a list; never rewrite an earlier entry):

```yaml
- lesson: L-2026-09-followup-cadence
  decision: adapt                 # adopt | adapt | decline
  why: "Our leads are outbound; applying the 2-day rule only to the inbound slice."
  date: 2026-09-30
  decided_by: "role:sales-lead (Jordan)"
```

Publish with `/canon-publish` (own folder). From the next run, `/role-context` loads the lesson (with its conditions and your `why`) as guidance in force.

### Step 5: Confirm

One line: `<lesson-id>: <decision> — <why>`; for an adopt/adapt, one more line saying what the companion will do differently.

## Error handling

| Situation | Action |
|---|---|
| `SELF` empty (no `x-canon.folder`) | Stop — `/role-context` refuses it; never write under `agents//…`, which is shared |
| `/canon-publish` not available (not among this agent's skills) | Leave the entry written in the local clone, uncommitted. Do **not** commit or push to the canon yourself. Reply `written locally, not published — /canon-publish unavailable` so the operator can install it |
