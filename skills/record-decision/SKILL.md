---
name: record-decision
description: "Record a seat-level decision — what was approved, deferred or killed, the alternatives that were live, the criterion that made the winner win, who decided (role and person), what would reverse it, and when it expires — through the platform's record_decision tool, falling back to the same fields in the seat's own canon folder where that tool is not available yet."
category: role-companions
allowed-tools: Read, Write, Bash, Glob, Grep, Skill, mcp__trinity__record_decision, mcp__trinity__list_seat_decisions
user-invocable: true
argument-hint: "[approved|deferred|killed] <what was decided>"
requires:
  binaries: [git]
canon: [org-context]
metadata:
  version: "1.1"
  created: 2026-09-28
  author: Ability.ai
  changelog:
    - "1.1: Review fixes (trinity-skills#2) — declares canon: [org-context]; routed is defined: a direction decision keeps outcome approved | deferred | killed and gets status routed (the platform's own value), never active; the fallback file takes the platform record's shape — decided_by {role, person} and decided_at — so the import is a move"
    - "1.0: Initial version (ent#510; Tandem decision record) — checks the seat's standing decisions first (list_seat_decisions) and cites the ones this leans on; records through record_decision — one line per field, at least one live alternative, review_by within a year, direction decisions routed; on an instance without the tool, writes the tool's field set (plus file-only schema_version, id, decided_by, status) to agents/<self>/decisions/<date>-<slug>.yaml and publishes it, so moving to the platform record is a named mapping, not a rewrite"
---

# Record Decision

> ℹ️ **First, set expectations:** print one line with this skill's version and its most recent change (the top entry of `metadata.changelog`). Then proceed.

Keep the seat's judgment: **why something was approved, deferred, or killed**, so the next time the same kind of ask comes up the criterion is reused instead of re-argued (the Tandem decision record). A decision, not a note — if there were no live alternatives, it is a note; keep it in memory instead.

## Process

### Step 1: Load the seat and its standing decisions

Run `/role-context --quiet` (it stops on an empty `SELF` — never write under `agents//`). Then `list_seat_decisions(execution_id)` — the seat's active records, criterion first. If one applies, **apply its criterion** and cite its id in `cites`. Reuse is the health metric (a decision cited by a later one), not volume.

### Step 2: Fill the record — one line per field

| Field | Rule |
|---|---|
| `outcome` | `approved` · `deferred` · `killed` |
| `decided` | what was decided — one line |
| `alternatives` | the options that were live besides the winner — **at least one** |
| `criterion` | what made the winner win — the reusable part, one line |
| `reversal` | what would reverse it — one line; a decision nothing could reverse is not falsifiable |
| `review_by` | `YYYY-MM-DD`, after today, within a year — it expires rather than accreting |
| `decided_by_role` | the role id; the person is the one this session serves |
| `ask_class` | a slug for the kind of ask (e.g. `vendor-approval`) — groups the evidence the autonomy dial reads |
| `cites` | ids of earlier decisions this leans on |
| `scope` | `seat` (default) · `direction` — pricing, positioning, roadmap are **direction**. `routed` is a **status**, not an outcome: a direction decision keeps its `outcome` and is stored with `status: routed` (the platform does this itself for `scope: direction`; the fallback file writes it), and you take it to canon as a proposal to the direction's owner. A routed record is never an `active` seat decision and is never cited as one |
| `notes` | the reasoning and trade-off, in prose — prose goes only here |

Ask the person for a missing field once; never invent an alternative or a criterion.

### Step 3: Record it

**Platform first.** Call `record_decision` with the fields and your `execution_id`. On success, reply with the record id and its `review_by`. A refusal with a receipt (a prose field, no alternative, a date out of range) → fix the named field and retry once.

**Fallback** — only when the tool is not available on this instance (the tool is absent, or the platform answers that the endpoint does not exist). Write the tool's field set, plus four file-only fields, to the seat's own canon folder, `$CANON/agents/$SELF/decisions/<YYYY-MM-DD>-<slug>.yaml`:

```yaml
schema_version: 1
id: 2026-09-28-vendor-x-deferred
outcome: deferred
decided: "Defer the vendor X renewal to Q1."
alternatives: ["Renew now at list price", "Switch to vendor Y"]
criterion: "No renewal above list without a usage review."
reversal: "Usage review shows >80% seat utilisation."
review_by: 2026-12-15
decided_by:
  role: ops-lead
  person: "Sam"
decided_at: 2026-09-28
ask_class: vendor-approval
cites: []
scope: seat
status: active                    # active | routed | superseded | reversed | closed — scope: direction → routed; expired is computed from review_by, never written
notes: ""
```

then publish with `/canon-publish` (own folder). The file is the platform record's shape (tandem decision record, §7a): every field except `schema_version`, `id`, `decided_by`, `decided_at` and `status` is a `record_decision` argument under the same name, and `decided_by.role` is the `decided_by_role` argument — so a later import is a mapping, not a rewrite. `schema_version` and `id` are file-only (the platform assigns the id); `decided_by.person`, `decided_at` and `status` are what the platform records itself (from the session, the clock, and `scope`) and are carried over as-is; `request_id` (the operator-queue item this answers) is added when there is one; `execution_id` is the importing run's. A run that is not serving a person (agent-to-agent, or a schedule addressed to no one) cannot record a seat decision on the platform — say so, and use the fallback only if the operator asked for it.

### Step 4: Confirm

One line: `Recorded: <outcome> — <decided> (criterion: <criterion>; review by <date>)`, plus `cites <ids>` when it reused one.

## Error handling

| Situation | Action |
|---|---|
| `record_decision` refuses with a receipt | Fix the named field, retry once |
| `SELF` empty (no `x-canon.folder`) | Stop — `/role-context` refuses it; never write under `agents//…`, which is shared |
| `/canon-publish` not available (not among this agent's skills) | Leave the entry written in the local clone, uncommitted. Do **not** commit or push to the canon yourself. Reply `written locally, not published — /canon-publish unavailable` so the operator can install it |
