---
name: report-observation
description: "At the end of a cycle, write what this seat tried and what it measurably changed — role, team, objective, the specific action, a before/after delta with window and sample size, and the local conditions — as an observation in the seat's own canon folder, publish it, and hand it to the fleet's brain for intake. Prose-only or unmeasured claims are refused, not sent."
category: role-companions
allowed-tools: Read, Write, Bash, Glob, Grep, Skill, mcp__trinity__get_metrics, mcp__trinity__chat_with_agent
user-invocable: true
argument-hint: "[<existing observation path> | <what changed, in words>]  (no argument = scheduled cycle scan)"
requires:
  binaries: [git]
metadata:
  version: "1.0"
  created: 2026-09-28
  author: Ability.ai
  changelog:
    - "1.0: Initial version (ent#510, Tandem framework, observation grammar) — builds the observation from the seat (role-context) and the metric's own points (get_metrics — the delta is measured, never estimated), refuses a claim with no measured before/after, window or n; writes agents/<self>/observations/<date>-<slug>.yaml, publishes it (/canon-publish, own folder), then hands the path@sha to the brain named in x-role.brain for intake (/synthesise-lessons --intake) and relays its receipt; ruin-class objectives are marked for same-day review"
---

# Report Observation

> ℹ️ **First, set expectations:** print one line with this skill's version and its most recent change (the top entry of `metadata.changelog`). Then proceed.

The up-flow of the learning loop (Tandem framework): **companion → observation → brain**. An observation is evidence, not advice — what this seat did, and the measured change it made, under stated conditions. The brain decides whether it corroborates anything; a single observation never becomes a lesson on its own.

## Calling modes

- **`<what changed, in words>`** — a person describes the change; build one observation from it (Steps 2–5).
- **`<existing observation path>`** — re-run Steps 4–5 for an observation already written (e.g. its brain hand-off failed).
- **No argument** — the weekly scheduled call (`/report-observation` in the `role-pack` set). Nobody is present to answer, so **never ask a question**. Scan the cycle since this seat's newest observation (or the last 7 days when there is none): this companion's own recorded work — its run notes, `/record-decision` records, and adopted lessons it applied — joined to the objectives' metrics. Build an observation (Steps 2–4) for each concrete action that passes Step 2's checks, **at most three per run**, skipping any action an existing observation already covers. When none qualifies, write nothing and reply with one line: `No reportable observation this cycle — <reason>` (e.g. `no action with a measured before/after`, `objectives unavailable`). A refusal in this mode goes into that line, not to "the person".

## Process

### Step 1: Load the seat

Run `/role-context --quiet` (it stops on an empty `SELF` — never write under `agents//`). Keep `role`, the team (the agent's `team:` tag or the role file's context), the objectives, and `x-role.brain`. No brain declared → still write and publish the observation, and say `no brain declared (x-role.brain) — the observation waits in canon for one`.

### Step 2: Build the observation

Required, and each is **checked, not assumed**:

| Field | Rule |
|---|---|
| `role`, `team` | the seat and the team it serves |
| `objective` | an objective id this seat owns or supports (from `get_objectives`) |
| `action` | the specific change made — one line, concrete ("moved first follow-up from 5 days to 2") |
| `delta.metric` | a declared metric |
| `delta.before`, `delta.after` | **measured** from that metric's points (`get_metrics metric=<name>`), not from memory |
| `delta.window_days`, `delta.n` | the window compared and the sample size behind `after` |
| `context` | the local conditions (team size, tooling, season, promotions running…) — the brain keeps them on any lesson |
| `confidence_local` | `low` · `medium` · `high` — the seat's own view |

**Refuse, with a reason, and write nothing** when the before/after cannot be measured, the window or n is unknown, or the claim is prose only ("it felt faster"). Tell the person what measurement would make it reportable (in a no-argument run, put it in the one-line reply instead). The brain rejects such reports at intake anyway (Tandem framework); refusing here keeps the canon clean.

An objective the role files mark ruin-class (compliance, safety, money — the objective's `notes` or the role's) → add `urgent: true`; the brain reviews it the same day.

### Step 3: Write and publish

`$CANON/agents/$SELF/observations/<YYYY-MM-DD>-<slug>.yaml`:

```yaml
schema_version: 1
id: 2026-09-24-followup-cadence
role: sales-lead
team: team-a
objective: q4-close-rate
action: "Moved first follow-up from 5 days to 2 days for ICP-A inbound leads."
delta:
  metric: reply_rate
  before: 0.12
  after: 0.21
  window_days: 14
  n: 38
context:
  team_size: 5
  tooling: hubspot
  conditions: "inbound only, September, no promo running"
confidence_local: medium
urgent: false
status: raw                       # raw | received | synthesised | rejected — the brain's receipt moves it
```

Publish with `/canon-publish` (own folder, lint-gated). Keep the resulting `canon@<sha>`. `/canon-publish` not available → leave the file written in the local clone, uncommitted; do **not** commit or push to the canon yourself; skip Step 4 (the brain needs a published sha) and confirm with `written locally, not published — /canon-publish unavailable`.

### Step 4: Hand it to the brain

`chat_with_agent` to the brain (`x-role.brain`), async: `/synthesise-lessons --intake agents/<self>/observations/<file>@<sha>`. The brain answers with a receipt — `created · updated · superseded · flagged · rejected (reason)`. Record it on the observation (`status: received` / `rejected`, plus `receipt:` one line) and publish again. A `rejected(belongs-to-canon)` receipt means the observation implies a pricing, positioning or roadmap change: tell the person it goes to the direction's owner as a canon proposal.

Brain unreachable → leave `status: raw`; the brain's weekly synthesis reads every raw observation anyway. Say so; never retry in a loop.

### Step 5: Confirm

One line: `Observation <id> published (canon@<sha>) → <brain>: <receipt | pending weekly synthesis>`.

## Error handling

| Situation | Action |
|---|---|
| `SELF` empty (no `x-canon.folder`) | Stop — `/role-context` refuses it; never write under `agents//…`, which is shared |
| `/canon-publish` not available | Leave the observation written locally, uncommitted; no hand-off; say `written locally, not published` |
| No argument and nothing measurable this cycle | Write nothing; one line `No reportable observation this cycle — <reason>` |
| Brain unreachable | Leave `status: raw`; never retry in a loop |
