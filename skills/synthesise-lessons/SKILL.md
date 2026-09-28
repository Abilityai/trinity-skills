---
name: synthesise-lessons
description: "The brain side of the learning loop — take observations in from role companions with a receipt, and weekly per role family turn corroborated observations into draft lessons with their conditions and evidence, route direction-implying ones to canon, flag ruin-class ones for same-day review, and open a library change request when a lesson is really a procedure change. Writes only the brain's own canon folder."
category: role-companions
allowed-tools: Read, Write, Bash, Glob, Grep, Skill
user-invocable: true
argument-hint: "--intake <agents/<name>/observations/<file>@<sha>> | [--role-family <role-id>]"
requires:
  binaries: [git]
metadata:
  version: "1.0"
  created: 2026-09-28
  author: Ability.ai
  changelog:
    - "1.0: Initial version (ent#510, Tandem framework, lesson grammar) — intake mode validates one observation and answers created | updated | superseded | flagged | rejected with the reason (prose-only and unmeasured reports rejected; pricing/positioning/roadmap → rejected(belongs-to-canon) + canon proposal; ruin-class → flagged same-day); weekly mode per role family groups observations, grades confidence by independent teams (1 = raw signal only, 2 teams same direction = medium, 3+ consistent = high), writes draft lessons with conditions + evidence + review_by in agents/<self>/lessons/, supersedes rather than edits, never publishes a lesson from one team in one week, and records a skill_change_request when the lesson is a procedure; receipts live in agents/<self>/receipts/ because the brain never writes another agent's folder"
---

# Synthesise Lessons (brain)

> ℹ️ **First, set expectations:** print one line with this skill's version and its most recent change (the top entry of `metadata.changelog`). Then proceed.

Runs on the fleet's **brain** agent — the one role companions name in `x-role.brain`. It turns many seats' observations into a few lessons the whole role family can use, **with their conditions**, and never lets a single report become advice (Tandem framework).

**Write rule:** the brain writes **only its own canon folder** (`agents/<self>/lessons/`, `agents/<self>/receipts/`). It never edits an observation in another agent's folder — the reporting companion records the receipt on its own observation.

Resolve `CANON` and `SELF` from `template.yaml` (`x-canon`) and pull (`git -C "$CANON" pull --ff-only`) before either mode.

## Mode 1 — intake (`--intake <path>@<sha>`)

Called by a companion's `/report-observation`. Read the observation at that sha (`git -C "$CANON" show <sha>:<path>`), then answer **exactly one** receipt:

| Receipt | When |
|---|---|
| `rejected(prose-only)` | no measured `delta` (before, after, window_days, n) |
| `rejected(belongs-to-canon)` | it implies a pricing, positioning or roadmap change — the information-routing boundary test. Tell the reporter to take it to the direction's owner as a canon proposal |
| `flagged(ruin-class)` | `urgent: true`, or the objective touches compliance, safety or money — reviewed today, never queued behind efficiency tips: raise an operator-queue alert naming it |
| `superseded` | it replaces an earlier observation of the same seat, action and objective |
| `updated` | it extends an observation already received (a longer window, a larger n) |
| `created` | a new, well-formed raw signal |

Append the receipt to `$CANON/agents/$SELF/receipts/<YYYY-MM>.yaml` (`- {observation: <path>@<sha>, receipt: <code>, reason: "<one line>", date: <date>}`), publish with `/canon-publish`, and reply with the receipt line only.

## Mode 2 — weekly synthesis (`[--role-family <role-id>]`)

Scheduled weekly **per role family** (one schedule per family: `/synthesise-lessons --role-family sales-lead`). Without the flag, run each role family that has new observations.

### Step 1: Gather

All `$CANON/agents/*/observations/*.yaml` for the role family, received (or raw and well-formed) and not yet cited by a lesson. Drop `rejected` ones.

### Step 2: Group and grade

Group observations that make **the same claim**: same objective, same kind of action, same direction of delta. For each group:

- **One observation** → stays a raw signal. No lesson.
- **Medium** — two independent observations from **different teams** of the same role, same direction.
- **High** — three or more, consistent direction, and no contradicting observation in the window.
- Observations from one team in one week never make a lesson on their own, however many there are.

A convergence check applies before anything graduates beyond `draft`: the same conclusion must lead across runs with a small confidence delta. This skill only ever writes `status: draft`; a draft becomes `canonical` by the brain's owner's review, not by this run.

### Step 3: Write the lesson

`$CANON/agents/$SELF/lessons/<id>.yaml`:

```yaml
schema_version: 1
id: L-2026-09-followup-cadence
statement: "For ICP-A inbound leads, a 2-day first follow-up beats 5 days on reply rate."
applies_to:
  roles: [sales-lead]
  conditions: "inbound, ICP-A, no active promotion"
evidence: [team-a/2026-09-24-followup-cadence, team-b/2026-09-26-fast-followup, team-c/2026-09-27-cadence]
confidence: high                  # low | medium | high
status: draft                     # draft | canonical | superseded
review_by: 2026-10-24             # drafts expire at the staleness bound
skill_change_request: null        # or {library_skill: <name>, pr: <url or null>}
```

- **Conditions are mandatory.** Take them from the observations' `context`; a lesson whose conditions cannot be stated is not written.
- **Never edit a published lesson.** A changed conclusion is a new lesson with `supersedes: <old id>`; the old one moves to `superseded` in the same commit.
- **Procedure, not advice** — when the lesson is really "the library skill should do X", set `skill_change_request: {library_skill: <name>, pr: null}` and raise an operator-queue request to change that skill, so the fix lands once for everyone instead of being adopted seat by seat.

### Step 4: Publish and report

Publish with `/canon-publish` (own folder). Reply with one line per role family: `<family>: <n> observation(s) → <k> draft lesson(s) (<ids>), <r> raw signal(s), <f> flagged`. Companions pick up new lessons through `/role-context` (`<n> new — /adopt-lesson`); the brain does not push them.
