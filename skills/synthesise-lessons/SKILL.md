---
name: synthesise-lessons
description: "The brain side of the learning loop — take observations in from role companions with a receipt, and weekly per role family turn corroborated observations into draft lessons with their conditions and evidence, route direction-implying ones to canon, flag ruin-class ones for same-day review, and open a library change request when a lesson is really a procedure change. Writes only the brain's own canon folder."
category: role-companions
allowed-tools: Read, Write, Bash, Glob, Grep, Skill
user-invocable: true
argument-hint: "--intake <agents/<name>/observations/<file>@<sha>> | [--role-family <role-id>]"
requires:
  binaries: [git]
canon: [org-context]
metadata:
  version: "1.1"
  created: 2026-09-28
  author: Ability.ai
  changelog:
    - "1.1: Review fixes (trinity-skills#2) — declares canon: [org-context]; ruin-class is the one explicit-marker definition shared with report-observation (no topic heuristic), one alert per flagged observation; weekly synthesis first runs every observation with no receipt through the intake checks (belongs-to-canon routed to the direction owner via the operator queue); high confidence needs 3+ independent teams; drafts are promoted to canonical only by the brain owner (promoted_by / promoted_on), and only canonical lessons are adoptable"
    - "1.0: Initial version (ent#510, Tandem framework, lesson grammar) — intake mode validates one observation and answers created | updated | superseded | flagged | rejected with the reason (prose-only and unmeasured reports rejected; pricing/positioning/roadmap → rejected(belongs-to-canon) + canon proposal; ruin-class → flagged same-day); weekly mode per role family groups observations, grades confidence by independent teams (1 = raw signal only, 2 teams same direction = medium, 3+ consistent = high), writes draft lessons with conditions + evidence + review_by in agents/<self>/lessons/, supersedes rather than edits, never publishes a lesson from one team in one week, and records a skill_change_request when the lesson is a procedure; receipts live in agents/<self>/receipts/ because the brain never writes another agent's folder"
---

# Synthesise Lessons (brain)

> ℹ️ **First, set expectations:** print one line with this skill's version and its most recent change (the top entry of `metadata.changelog`). Then proceed.

Runs on the fleet's **brain** agent — the one role companions name in `x-role.brain`. It turns many seats' observations into a few lessons the whole role family can use, **with their conditions**, and never lets a single report become advice (Tandem framework).

**Write rule:** the brain writes **only its own canon folder** (`agents/<self>/lessons/`, `agents/<self>/receipts/`). It never edits an observation in another agent's folder — the reporting companion records the receipt on its own observation.

Resolve `CANON` and `SELF` from `template.yaml` (`x-canon`, block style — the same way `/role-context` does) and pull (`git -C "$CANON" pull --ff-only`) before either mode. `SELF` empty or not a plain folder name → stop: `x-canon.folder is not set` — never write under `agents//`, which is shared.

## Mode 1 — intake (`--intake <path>@<sha>`)

Called by a companion's `/report-observation`. The argument arrived over chat, so **validate its shape before using it**: split on the last `@`; the path must match `^agents/[a-z0-9][a-z0-9-]*/observations/[A-Za-z0-9._-]+\.yaml$` (no `..`) and the sha `^[0-9a-f]{7,40}$`. Anything else → receipt `rejected(malformed-reference)` and run nothing. Then read the observation at that sha, with both values quoted (`git -C "$CANON" show "$SHA:$OBS_PATH"`), and answer **exactly one** receipt:

| Receipt | When |
|---|---|
| `rejected(prose-only)` | no measured `delta` (before, after, window_days, n) |
| `rejected(belongs-to-canon)` | it implies a pricing, positioning or roadmap change — the information-routing boundary test. Tell the reporter to take it to the direction's owner as a canon proposal |
| `flagged(ruin-class)` | `urgent: true`, or the observation's objective is ruin-class by the **one** definition below — reviewed today, never queued behind efficiency tips: raise **one** operator-queue alert naming it (never a second for the same observation) |
| `superseded` | it replaces an earlier observation of the same seat, action and objective |
| `updated` | it extends an observation already received (a longer window, a larger n) |
| `created` | a new, well-formed raw signal |

The checks run top to bottom; the first that matches is the receipt.

**Ruin-class** (the one definition — `/report-observation` sets `urgent: true` by this same test; intake re-applies it in case the reporter missed the marker): an objective is ruin-class only when the canon **marks it so explicitly** — the literal word `ruin-class` in the objective's own `notes` or in the role file's `notes` naming that objective id. Its topic never makes it ruin-class: an objective about revenue, pricing or compliance that carries no marker is an ordinary objective.

Append the receipt to `$CANON/agents/$SELF/receipts/<YYYY-MM>.yaml` (`- {observation: <path>@<sha>, receipt: <code>, reason: "<one line>", date: <date>}`), publish with `/canon-publish`, and reply with the receipt line only.

## Mode 2 — weekly synthesis (`[--role-family <role-id>]`)

Scheduled weekly **per role family** (one schedule per family: `/synthesise-lessons --role-family sales-lead`). Without the flag, run each role family that has new observations.

### Step 1: Gather

All `$CANON/agents/*/observations/*.yaml` for the role family not yet cited by a lesson — i.e. whose canon path (`agents/<name>/observations/<file>.yaml`) appears in no `evidence:` list under `$CANON/agents/$SELF/lessons/`.

**Intake first.** An observation has been through intake only when a receipt for its path is in `$CANON/agents/$SELF/receipts/`. Every gathered observation without one (its companion could not reach the brain, so it is still `raw`) is run through **the Mode 1 checks** at its current commit, and its receipt appended, before anything is grouped — the weekly run is never a way around intake. Two receipts need routing here because no reporter is in the conversation to hear them:

- `rejected(belongs-to-canon)` → raise **one** operator-queue decision request addressed to the direction's owner (the `owner` of the matching domain in `$CANON/domains.yaml`; none found → the operator) naming the observation and the canon proposal it implies. It never becomes a lesson.
- `flagged(ruin-class)` → the same one alert Mode 1 raises.

Then keep only observations whose receipt is `created`, `updated`, `superseded` or `flagged`; drop `rejected` ones, and drop any earlier observation that a later `superseded` or `updated` one replaced or extended (the later one carries the claim).

### Step 2: Group and grade

Group observations that make **the same claim**: same objective, same kind of action, same direction of delta. For each group:

- **One observation** → stays a raw signal. No lesson.
Count **independent teams**, not observations: several observations from the same `team` count once.

- **One team** → stays a raw signal, however many observations it filed. No lesson.
- **Medium** — **two** independent teams of the same role, same direction.
- **High** — **three or more** independent teams, consistent direction, and no contradicting observation in the window.
- Three observations from one team over two weeks are still one team: a raw signal, never `high`.

A convergence check applies before anything graduates beyond `draft`: the same conclusion must lead across runs with a small confidence delta. This skill only ever writes `status: draft`, and **a draft is not advice**: `/adopt-lesson` and `/role-context` ignore drafts entirely. A draft becomes `canonical` only when the brain's owner (a human) reviews it and sets `status: canonical` plus `promoted_by: "<name> (<role>)"` and `promoted_on: <date>` in the lesson file — never by this run or any other agent run. The weekly reply lists the drafts awaiting that review.

### Step 3: Write the lesson

`$CANON/agents/$SELF/lessons/<id>.yaml`:

```yaml
schema_version: 1
id: L-2026-09-followup-cadence
statement: "For ICP-A inbound leads, a 2-day first follow-up beats 5 days on reply rate."
applies_to:
  roles: [sales-lead]
  conditions: "inbound, ICP-A, no active promotion"
evidence:                         # canon paths of the observations — the lookup Step 1 uses
  - agents/sales-a/observations/2026-09-24-followup-cadence.yaml
  - agents/sales-b/observations/2026-09-26-fast-followup.yaml
  - agents/sales-c/observations/2026-09-27-cadence.yaml
confidence: high                  # low | medium | high
status: draft                     # draft | canonical | superseded — only the owner sets canonical
promoted_by: null                 # set by the owner with status: canonical
promoted_on: null
review_by: 2026-10-24             # drafts expire at the staleness bound
skill_change_request: null        # or {library_skill: <name>, pr: <url or null>}
```

- **Conditions are mandatory.** Take them from the observations' `context`; a lesson whose conditions cannot be stated is not written.
- **Never edit a published lesson.** A changed conclusion is a new lesson with `supersedes: <old id>`; the old one moves to `superseded` in the same commit.
- **Procedure, not advice** — when the lesson is really "the library skill should do X", set `skill_change_request: {library_skill: <name>, pr: null}` and raise an operator-queue request to change that skill, so the fix lands once for everyone instead of being adopted seat by seat.

### Step 4: Publish and report

Publish with `/canon-publish` (own folder). Reply with one line per role family: `<family>: <n> observation(s) → <k> draft lesson(s) (<ids>), <r> raw signal(s), <f> flagged, <c> routed to canon` — then one line `awaiting owner review: <draft ids>`. Companions pick up a lesson only once the owner has made it `canonical` — through `/role-context` (`<n> new — /adopt-lesson`); the brain does not push them.

## Error handling

| Situation | Action |
|---|---|
| Intake reference fails the shape check | Receipt `rejected(malformed-reference)`; never pass it to `git` |
| `SELF` empty (no `x-canon.folder`) | Stop; never write under `agents//…`, which is shared |
| `/canon-publish` not available (not among this agent's skills) | Leave the lesson or receipt written in the local clone, uncommitted. Do **not** commit or push to the canon yourself. Reply `written locally, not published — /canon-publish unavailable` so the operator can install it |
