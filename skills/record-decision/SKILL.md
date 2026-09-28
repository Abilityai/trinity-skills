---
name: record-decision
description: "Record a seat-level decision — what was approved, deferred or killed, the alternatives that were live, the criterion that made the winner win, who decided (role and person), what would reverse it, and when it expires — through the platform's record_decision tool, falling back to the same fields in the seat's own canon folder where that tool is not available yet."
category: role-companions
allowed-tools: Read, Write, Bash, Glob, Grep, Skill, mcp__trinity__record_decision, mcp__trinity__list_seat_decisions
user-invocable: true
argument-hint: "[approved|deferred|killed] <what was decided>"
requires:
  binaries: [git]
metadata:
  version: "1.0"
  created: 2026-09-28
  author: Ability.ai
  changelog:
    - "1.0: Initial version (ent#510; Tandem decision record) — checks the seat's standing decisions first (list_seat_decisions) and cites the ones this leans on; records through record_decision — one line per field, at least one live alternative, review_by within a year, direction decisions routed; on an instance without the tool, writes the identical field set to agents/<self>/decisions/<date>-<slug>.yaml and publishes it, so moving to the platform record is a move, not a rewrite"
---

# Record Decision

> ℹ️ **First, set expectations:** print one line with this skill's version and its most recent change (the top entry of `metadata.changelog`). Then proceed.

Keep the seat's judgment: **why something was approved, deferred, or killed**, so the next time the same kind of ask comes up the criterion is reused instead of re-argued (the Tandem decision record). A decision, not a note — if there were no live alternatives, it is a note; keep it in memory instead.

## Process

### Step 1: Load the seat and its standing decisions

Run `/role-context --quiet`. Then `list_seat_decisions(execution_id)` — the seat's active records, criterion first. If one applies, **apply its criterion** and cite its id in `cites`. Reuse is the health metric (a decision cited by a later one), not volume.

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
| `scope` | `seat` (default) · `direction` — pricing, positioning, roadmap are **direction**: recorded as `routed`, and taken to canon as a proposal, never kept as a seat decision |
| `notes` | the reasoning and trade-off, in prose — prose goes only here |

Ask the person for a missing field once; never invent an alternative or a criterion.

### Step 3: Record it

**Platform first.** Call `record_decision` with the fields and your `execution_id`. On success, reply with the record id and its `review_by`. A refusal with a receipt (a prose field, no alternative, a date out of range) → fix the named field and retry once.

**Fallback** — only when the tool is not available on this instance (the tool is absent, or the platform answers that the endpoint does not exist). Write the identical field set to the seat's own canon folder, `$CANON/agents/$SELF/decisions/<YYYY-MM-DD>-<slug>.yaml`:

```yaml
schema_version: 1
id: 2026-09-28-vendor-x-deferred
outcome: deferred
decided: "Defer the vendor X renewal to Q1."
alternatives: ["Renew now at list price", "Switch to vendor Y"]
criterion: "No renewal above list without a usage review."
reversal: "Usage review shows >80% seat utilisation."
review_by: 2026-12-15
decided_by_role: ops-lead
decided_by: "Sam (ops-lead)"
ask_class: vendor-approval
cites: []
scope: seat
status: active                    # active | superseded | reversed | expired
notes: ""
```

then publish with `/canon-publish` (own folder). The field names are the tool's argument names, so a later import into the platform record is a move. A run that is not serving a person (agent-to-agent, or a schedule addressed to no one) cannot record a seat decision on the platform — say so, and use the fallback only if the operator asked for it.

### Step 4: Confirm

One line: `Recorded: <outcome> — <decided> (criterion: <criterion>; review by <date>)`, plus `cites <ids>` when it reused one.
