---
name: reconcile-fleet
description: The Architect's scheduled tick — fetch the fleet's target view at a sha, observe the live fleet over Trinity MCP (agents, kinds, library skills, schedules, assignments, skill gates, systems), diff view against observation with tools/diff_view.py, then apply within the view under the Architect's own grants, ask the role the view names for gated moves, escalate person-only rows, propose view changes to its own canon folder, and publish one digest line per open gap with its age. Status is observed, never inferred; edges and self-change grants read unobserved until the platform exposes them.
category: agent-development
user-invocable: true
argument-hint: "[<fleet>] [--check] [--view <path-or-url>]"
when_to_use: On the Architect's `architect.reconcile` cron (headless, never asks mid-run), or by hand — "reconcile the fleet", "what drifted from the view", "is the live fleet what the view says", after a person merged a view change, after a deploy. `--check` observes, diffs and digests without applying, asking or proposing. Not a general skill installer, not a fleet designer (`/compile-view` compiles; a person merges the view).
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill, mcp__trinity__list_agents, mcp__trinity__get_agent_info, mcp__trinity__get_agent_skills, mcp__trinity__list_agent_schedules, mcp__trinity__get_agent_assignments, mcp__trinity__list_skill_gates, mcp__trinity__list_systems, mcp__trinity__get_system_manifest, mcp__trinity__assign_skill_to_agent, mcp__trinity__set_skill_gate, mcp__trinity__clear_skill_gate, mcp__trinity__toggle_agent_schedule, mcp__trinity__deploy_system, mcp__trinity__ask_operator, mcp__trinity__get_my_ask, mcp__trinity__list_operator_queue, mcp__trinity__report, mcp__trinity__list_reports, mcp__trinity__record_metrics
requires:
  env: [GITHUB_TOKEN, INSTANCE_API_KEY, ARCHITECT_INSTANCE_KEY]   # the two keys matter only in remote placement (a Regent / a control-plane Architect); unset = local placement, not a fault
  binaries: [git, python3]
metadata:
  mirror: "tandem-blueprint@fcf4d60 skills/reconcile-fleet"
  version: "1.1"
  created: 2026-10-28
  author: architect
  changelog:
    - "1.1: remote placement — when the agent holds a governed instance's URL and admin key (Regent: INSTANCE_URL / INSTANCE_MCP_URL / INSTANCE_API_KEY; or ARCHITECT_INSTANCE_URL / ARCHITECT_INSTANCE_MCP_URL / ARCHITECT_INSTANCE_KEY) every Step 2 observation is made against THAT instance over its REST/MCP door with curl, never through this agent's own trinity MCP handle (which would observe the control plane); --check also lists live-only agents (on the instance, not in the view) as a `live-only` section of the digest before any apply is ever considered; fleet slug may come from ARCHITECT_FLEET or INSTANCE_NAME; 1.0 behaviour unchanged for local placement"
    - "1.0: Initial version — observe → diff (tools/diff_view.py) → apply / ask / escalate / propose per PRD §2 → digest with gap ages, architect.reconcile report, three declared metrics; idempotent by stable request_ids; edges and grants unobserved (trinity-enterprise#991); abilityai/trinity-enterprise#992"
---

# Reconcile Fleet

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `reconcile-fleet vX.Y — recent: <summary>`. Then proceed.

## Purpose

Bring the live fleet to its **target view** — the file people merge and the fleet may not change about itself (PRD `trinity-pm prds/target-view-and-reconciler.md` §2–§4; schema `tandem-blueprint/schema/target-view.yaml`). Every tick answers one question from live evidence: *what does Trinity run that differs from what the view says, and which of those differences may the Architect close itself?*

Four verbs, one boundary (PRD §2):

| verb | when | how |
|---|---|---|
| **apply** | the gap is inside the view and the Architect's own grants cover it | the MCP call named in the row — assign a gated skill, set or clear a gate, toggle the tick, deploy what the view names and the fleet lacks; **never delete** |
| **ask** | the move is gated, or it touches the Architect's own gates | one `ask_operator` per row, to the role the view's `approval_map` names |
| **escalate** | person-only: a seat, a credential value, an assignment, the Architect's own grants | an `ask_operator` question with no options — a person acknowledges |
| **propose** | the view itself should change (an agent the view does not name, a gate approved by a kind, an ended engagement) | `proposals/target-view.next.yaml` in the Architect's **own canon folder** — at most one per fleet per day; never a write to `fleet-targets` |

`--check` runs observe + diff + digest only. Headless runs never ask mid-run: every decision is an ask in the operator queue, parked, and read back next tick.

## Rules this skill encodes

- **Status is observed, never inferred.** A row is `in sync` only when a tool returned the matching fact this run. A tool error, a permission refusal, an agent outside the key's reach, or a fact no tool exposes → `unobserved`, with the error in the note. No retry loop: one call, one outcome.
- **Edges and self-change grants are not readable over MCP today** (trinity-enterprise#991). Their rows read `unobserved · platform-issue` — never `in sync`, never "probably fine". A grant becomes known only through an outcome: a `403 *_management_not_permitted` on an apply records it as refused; a successful apply records it as held.
- **Under an agent key, `list_agents` returns only the key's reach** — self, permission edges, spawned agents (ent#629) — and a denied `get_agent_info` reads the same as a missing agent (`not found or not accessible`). So an agent the view names but the tick cannot see is `unobserved`, not absent; absence is established only by a person with an owner key. `deploy_system` for a "missing" agent therefore runs only when the Architect spawned the fleet (the agents are in its reach by construction).
- **An agent cannot set or lift its own gate** (`set_skill_gate` / `clear_skill_gate`: "never on the calling agent itself"). Every `approval_map` row whose executor is the Architect is an **ask**, never an apply.
- **Skill management is a grant** (ent#596). `assign_skill_to_agent`, `set_skill_gate`, `clear_skill_gate` under an agent key need `skills.manage`; a `403 skill_management_not_permitted` stops every apply of that class for the run, records the grant as refused, and is reported — never retried. Same for `schedule_management_not_permitted` (another agent's schedule) and `agent_management_not_permitted` (`deploy_system`).
- **Additive, single-skill, never a wipe.** Assignments go through `assign_skill_to_agent` one skill at a time; `set_agent_skills` is never called (it replaces the whole list). A live skill the view does not name is not touched — plain assignments are outside the view by design (schema README: capability is out, authority is in).
- **Credentials compare names only.** The tick never reads a value and never injects one: credential injection rewrites the whole `.env` (`/api/credentials/inject`), so a missing name is an **escalate** row, full stop.
- **Idempotent.** Re-running on an unchanged fleet applies nothing and asks nothing twice. Every ask carries a stable `request_id` (`reconcile:<fleet>:<section>:<key>`); `ask_operator` replays the first receipt for a repeated id (`status: replayed`), and the run reads `get_my_ask(request_id)` before raising. Dedupe only on the agent-scoped read — `list_operator_queue(agent_name=<self>, status=pending)` — never the broad listing, which applies `limit` fleet-wide before the scope filter and under-returns.
- **An ask receipt's `resolved: true` means a Workspace will show it, not that a person saw it.** `to: operator` is Operating-Room-only; a role several people fill reaches all, first answer wins. Before escalating "parked and unanswered", confirm the ask is reachable (`to_role` on the receipt), not merely filed.
- **`agent_busy` vs `rate_limited`** on any delegation this skill makes: busy = nothing ran, re-send later; rate-limited = it ran, never re-send. This skill delegates nothing by default; the rule is here for the `/compile-view` call it makes.
- **Cold start.** The view and the tools come from two private repos. `GITHUB_TOKEN` not set → say so by name and stop: `GITHUB_TOKEN not set — add it to this agent's credentials (Settings → Credentials)`. Nothing is observed without the view.

## State dependencies

| Source | Location | Read | Write |
|---|---|---|---|
| Target view (authoritative) | `fleet-targets/<fleet>/target-view.yaml` — side clone of `github:Abilityai/fleet-targets` (gitignored, self-healed) | ✓ | never |
| Target view (Trinity-held, installs without git — ruling 7) | `views/<fleet>/target-view.yaml` in this agent's own repo, written only by `/apply-view` | ✓ | never (here) |
| Schema, validator, diff, compiler, hygiene checks | `tandem-blueprint/` — side clone of `github:Abilityai/tandem-blueprint` (gitignored, self-healed; `tools/validate.py`, `tools/diff_view.py`, `tools/compile_view.py`, `tools/hygiene_checks.py`) | ✓ | never |
| Live fleet | Trinity MCP (tools in `allowed-tools`) | ✓ | apply rows only |
| Observation, gap ledger, ask/grant memory | `state/reconcile/<fleet>.observed.json`, `state/reconcile/<fleet>.json`, `state/reconcile/<fleet>.ledger.jsonl` (gitignored) | ✓ | ✓ |
| Proposals | `canon/<x-canon.folder>/proposals/target-view.next.yaml` (own canon folder; `template.yaml x-canon: folder`) | ✓ | ✓ (propose) — published by `/canon-publish`, never pushed here |
| Compiled manifest | `build/<fleet>.system.yaml` + `build/<fleet>.apply.json` via `/compile-view` (gitignored) | ✓ | via `/compile-view` |

## Process

### Step 0: Arguments and side clones

- `<fleet>`: the first bare argument. Default: `${ARCHITECT_FLEET}`, else `${INSTANCE_NAME}` (a Regent), else the only `<fleet>/` directory in `fleet-targets/`, else the `fleet:` of the only file under `views/`; if none resolves to exactly one, stop and say what is missing.
- **Placement** (decided once, printed in the digest header): **remote** when `INSTANCE_URL` + `INSTANCE_API_KEY` (Regent) or `ARCHITECT_INSTANCE_URL` + `ARCHITECT_INSTANCE_KEY` are set — this agent runs on a control plane and observes *another* instance; **local** otherwise — it observes the instance it runs on through its own `trinity` MCP tools. In remote placement the MCP tools in `allowed-tools` are **never** used for observation (they would read the control plane, not the fleet); every call in Step 2 goes over the governed instance's own door instead, see **Remote door** below.
- `--check`: observe + diff + digest; Step 4 is skipped entirely.
- `--view <path-or-url>`: use this file (or a raw URL fetched once) instead of the clone. Record its source and sha256 as the view sha.

Self-heal the two side clones (plain https — the agent's git credential helper supplies the token; `test -n "${GITHUB_TOKEN}" || echo "GITHUB_TOKEN not set — add it to this agent's credentials"` first, and stop when unset):

```bash
[ -d tandem-blueprint/.git ] || git clone --quiet https://github.com/Abilityai/tandem-blueprint tandem-blueprint
git -C tandem-blueprint pull --quiet --ff-only
[ -d fleet-targets/.git ] || git clone --quiet https://github.com/Abilityai/fleet-targets fleet-targets
git -C fleet-targets pull --quiet --ff-only
mkdir -p state/reconcile
```

A clone that is refused is a stop: nothing below runs without the view, and the report says `view unreachable: <error>`.

### Step 1: Fetch and validate the view

```bash
VIEW=fleet-targets/<fleet>/target-view.yaml           # or views/<fleet>/target-view.yaml, or --view
VIEW_SHA=$(git -C fleet-targets rev-parse --short HEAD)   # sha256 of the file when not from the clone
python3 tandem-blueprint/tools/validate.py --view "$VIEW"
```

A view that fails validation is **not a source**: stop, report `view invalid at <sha>: <errors>`, publish the digest with that single line, record nothing else. The Architect never upgrades or repairs a view — a person merges the rewritten file.

Precedence when both exist: `--view` > `fleet-targets/` clone > `views/<fleet>/` (the Trinity-held copy). If the clone and the held copy differ, note it in the digest (`held copy behind <sha>`); the clone wins.

### Step 2: Observe the live fleet — one call per section, every outcome recorded

**Remote door (remote placement only).** `URL=${INSTANCE_URL:-$ARCHITECT_INSTANCE_URL}`, `MCP=${INSTANCE_MCP_URL:-${ARCHITECT_INSTANCE_MCP_URL:-$URL/mcp}}`, `BEARER=${INSTANCE_API_KEY:-$ARCHITECT_INSTANCE_KEY}`. The same bearer opens REST and MCP. Each MCP tool in the table becomes one JSON-RPC `tools/call` (initialize → `notifications/initialized` → the call, one session per run); REST reads are plain `GET`. Confirm identity first — `GET $URL/api/users/me/` must answer with a user whose role is `admin`; anything else is printed and the run stops, because a non-admin census cannot be trusted as a fleet count.

```bash
H=(-H "Authorization: Bearer $BEARER" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream")
SID=$(curl -sS -m 20 -X POST "$MCP" "${H[@]}" -D - -o /dev/null -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"reconcile-fleet","version":"1.1"}}}' | awk 'tolower($(1))=="mcp-session-id:"{print $(2)}' | tr -d '\r')
curl -sS -m 20 -X POST "$MCP" "${H[@]}" -H "Mcp-Session-Id: $SID" -o /dev/null -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
mcp() { curl -sS -m 120 -X POST "$MCP" "${H[@]}" -H "Mcp-Session-Id: $SID" -d "{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/call\",\"params\":{\"name\":\"${1}\",\"arguments\":${2:-{\}}}}" | sed -n 's/^data: //p'; }
rest() { curl -sS -m 30 "${H[@]}" "${URL}${1}"; }
# e.g.  mcp list_agents '{}'   ·   rest /api/agents/<a>/schedules   ·   rest /api/agents/<a>/permissions
```

In remote placement the admin key sees the whole instance, so three rows that are `unobserved` locally become observable: **schedules of every agent** (`rest /api/agents/<a>/schedules`), **edges** (`rest /api/agents/<a>/permissions` — `permitted: true` per target), and **assignments / shares** (`rest /api/agents/<a>/shares`, `rest /api/settings/email-whitelist`). Record them in the same sections with `source: rest`. Grants (self-change permissions) stay `unobserved · platform-issue` in both placements.

**Live-only (both placements, always).** After `list_agents`, every agent on the instance that the view does not name goes into `observed.live_only[]` with its status, template and tags. The digest prints them first, under `live-only (not in the view)`, before any gap row. A live-only agent is never touched by Step 4 and never inferred to be unwanted: it is a question for the view's owner (keep → add a row; retire → a person's act). Platform agents (`trinity-system`) are listed once with `platform: true` and excluded from the count.


Assemble `state/reconcile/<fleet>.observed.json` in the shape documented at the top of `tandem-blueprint/tools/diff_view.py`. Every section is filled from exactly the calls below; a failed call puts its error text in that section's `error` and moves on. Nothing is carried over from a previous run except the `grants.known` outcomes (Step 4 writes them; keep them dated).

| section | call | keys kept |
|---|---|---|
| `agents` | `list_agents` (the key's reach), then `get_agent_info(name)` for every view agent the list lacks | `kind` (`list_agents[].kind`; null = platform default), `status`, `template`/`github_repo`; a denied or missing `get_agent_info` → that agent's `error: "not found or not accessible — reach (ent#629) or absent"` |
| `skills` | `get_agent_skills(agent_name)` per view agent | `skill_name` list, `sets`, `delivery_status` (informational: a gated skill the executor does not hold "gates nothing until it does") |
| `gates` | `list_skill_gates(agent_name)` per executor in `approval_map` + the Architect | `gates[].skill_name / approver / origin / approver_reachable`; `approvers[]` kept aside for Step 4's role resolution |
| `schedules` | `list_agent_schedules(agent_name)` for the Architect (self) and any agent the reach allows | `id`, `name`, `cron`, `message`, `enabled` |
| `assignments` | `get_agent_assignments(agent_name=<self>)` — **own roster only** under an agent key; another agent's roster answers a uniform 404 | per role: `role`, `kind` (primary/approver/collaborator/viewer), `person` |
| `credentials` | from `get_agent_info` template metadata when it lists a `credentials` block — **names only**; otherwise `names: null` | names |
| `systems` | `list_systems`, and `get_system_manifest(<system>)` when the fleet was born from a manifest | informational; `get_system_manifest` is lossy — never a source |
| `edges` | *(no tool)* | `null` |
| `grants` | *(no tool)* — only `known` outcomes from this and previous runs | `known: {permission: true|false}` with the date of the outcome |

Sanity check before trusting a fleet-wide pattern: an empty `get_agent_skills` for most agents, or an empty `list_agents`, is spot-checked (one `get_agent_info`) before it is reported as fact — MCP-layer under-reporting is a known failure mode on this platform.

Hygiene checks ride along, on this agent's own repository only (the tick does not clone the fleet's repos):

```bash
python3 tandem-blueprint/tools/hygiene_checks.py . --json
```

Failing check ids go into the digest beside the gaps — ids only, never a total.

### Step 3: Diff

```bash
python3 tandem-blueprint/tools/diff_view.py "$VIEW" state/reconcile/<fleet>.observed.json --json > state/reconcile/<fleet>.diff.json
```

Rows are `{section, key, target, observed, status, action, note}`; `status ∈ in sync | drift | unobserved | schema-gap`, `action ∈ apply | ask | escalate | propose | none | platform-issue`. Then update the gap ledger `state/reconcile/<fleet>.json`:

```json
{"fleet": "...", "view_sha": "...", "last_run": "<iso>", "last_proposal_at": "<iso or null>",
 "gaps": {"<section>:<key>": {"first_seen": "<iso>", "last_seen": "<iso>", "status": "...", "action": "...", "ask_request_id": null}},
 "grants_known": {"<agent>": {"<permission>": {"value": true, "observed_at": "<iso>"}}},
 "asks": {"<request_id>": {"raised_at": "<iso>", "disposition": null}}}
```

A row that is not `in sync` is a gap: new ones get `first_seen` now; persisting ones keep theirs; a gap that disappeared this run is removed and ledgered as `resolved`. **`--check` stops after this step** and goes to Step 5.

### Step 4: Act — per row, in this order: apply, ask, escalate, propose

Before any write, re-read the row's fact once more only if the observation is older than this run (it is not — skip). Each act writes one ledger line `{ts, fleet, view_sha, section, key, action, call, args, result, request_id?}` to `state/reconcile/<fleet>.ledger.jsonl`. **A call whose read-back does not match is `applied-unverified`, never `done`.**

**4a — apply** (rows with `action: apply`), under the Architect's own grants:

| row | call | read-back |
|---|---|---|
| `approval_map` gate missing or wrong approver, executor ≠ Architect | `set_skill_gate(agent_name=<executor>, skill_name=<skill>, approver="role:<id>")` — if the executor's `list_skill_gates.approvers[]` lacks that role (`unknown_role`), the row becomes **escalate** (a person assigns the role on that agent) | `list_skill_gates` shows the gate with that approver; `warnings: approver_unassigned` / `approver_not_shared` are escalated rows, not success |
| `approval_map` gate the view no longer names, origin `set`, executor ≠ Architect | `clear_skill_gate(agent_name, skill_name)` | `changed: true` (or already clear) |
| gated skill in `approval_map` not held by its executor (`skills` section) | `assign_skill_to_agent(agent_name, skill_name)` — additive, one skill; `delivery.status` `injected` / `pending_start` / `in_progress` are fine, `conflict` and `not_delivered` are reported, never forced | `get_agent_skills` lists it |
| `architect.reconcile` tick disabled | `toggle_agent_schedule(agent_name=<self>, schedule_id=<id>, enabled=true)` | `list_agent_schedules` shows `enabled: true` |
| `agents` row absent live (established only within the Architect's reach — see Rules) | `/compile-view <fleet>` (Skill), then `deploy_system(manifest=<build/<fleet>.system.yaml restricted to the missing agents>, dry_run=true)`; only on `status: deployed` preview with no `failed[]` → `deploy_system(dry_run=false)`. The platform names agents `<system>-<short>` — if the compiled sidecar warns `name_prefix_mismatch` for the agent, do **not** deploy: the created name would never match the view; the row becomes **propose** | `list_agents` shows it |

A `403 skill_management_not_permitted` / `schedule_management_not_permitted` / `agent_management_not_permitted` records `grants_known[<self>][<permission>] = false`, turns every remaining apply of that class into an **escalate** row for this run, and is never retried.

**4b — ask** (rows with `action: ask`), one decision per ask:

1. Resolve the addressee. The view names a role (`approver: role:<id>`); `ask_operator` addresses a **kind** — `primary` | `approver` | `viewer` | `operator` — not a role id. Map through the Architect's own roster (Step 2 `assignments`): the person who fills `role:<id>` is this agent's `primary` → `to: primary`; `approver` → `to: approver`; nobody on the roster fills it → `to: primary` and name the role in the title, and add the row `assignments:<role>` as escalate if it is not already one.
2. Dedupe: `request_id = "reconcile:<fleet>:<section>:<key>"`. `get_my_ask(request_id)` first: `pending` → skip (nothing twice); `answered` → act on the answer (the approved option's proposal is what runs; `(something else)` → carry out none, read `response_text`); `dismissed` → do not re-raise for 7 days (ledger it); `expired` → re-raise only with new information, with `supersedes_expired: <request_id>` and a new id suffix `:2`.
3. Raise: `ask_operator(request_id, type="approval", title ≤120 chars naming the move, question with the row's target/observed/note, options ≤5 × ≤60 chars naming the choice only (e.g. "Set the gate", "Leave as is"), proposal keyed by option with the exact call, to=<kind>, priority="medium")`. Fire and park: never wait in the turn. Record `request_id` on the gap.

**4c — escalate** (rows with `action: escalate`): same dedupe and addressing, `type: question`, **no options**, title "Needs a person: <section> <key>", question = what only a person can do (grant in Settings → Guardrails, assign the role in Agent › Access, add the credential value, re-merge an expiry). One per row, never repeated while pending.

**4d — propose** (rows with `action: propose`, and any `schema-gap` row): at most **one proposal per fleet per day** (`last_proposal_at`). Write the current view with the proposed rows changed and a header comment listing each change with its diff row, to `canon/<x-canon.folder>/proposals/target-view.next.yaml`; validate it with `tools/validate.py --view`; a proposal that does not validate is not written (report why). Never add an agent the view can only half-express — leave the schema-gap in the comment for the schema's owner. Publishing the proposal is `/canon-publish` (own folder, gated); this skill writes the file and names it in the digest. **Never** write to `fleet-targets/`.

### Step 5: Digest, report, metrics

Print the digest — one line per open gap, oldest first:

```
reconcile-fleet <fleet> @ <view_sha> — <n> rows: <i> in sync · <d> drift · <u> unobserved · <s> schema-gap
  <age>d  <section> <key>  <status> → <action>  <note / request_id / call>
  ...
  hygiene: <failing ids or "clean"> · proposal: <path or none> · applied: <n> · asked: <n> · escalated: <n>
```

Then, **only when `mcp__trinity__report` is available** (skip silently when absent or when it refuses for want of an agent identity): `list_reports(report_type="architect.reconcile")` to see the last one, then publish

- `report_type`: `architect.reconcile` · `title`: `Reconcile <fleet> <date>: <d> drift, <u> unobserved` · `display_hint`: `table`
- `payload`: `{"columns": ["age_days","section","key","status","action","target","observed","note"], "rows": [...], "summary": {counts, view_sha, applied, asked, escalated, proposal, hygiene_failing}}`

Record the three declared metrics with `record_metrics` (`execution_id` from the Execution Context so a re-delivered turn replays):

| metric | value |
|---|---|
| `open_gap_age_days` | age in days of the oldest open gap (0 when none) |
| `proposal_queue_age_days` | days since `last_proposal_at` while the view sha has not moved since (0 when no proposal waits) |
| `asks_per_day` | asks and escalations raised this run (one tick per day → per day) |

They must be declared in the Architect's `template.yaml metrics:` first; on `metric_undeclared` skip the metric and say so — never invent a declaration at run time. Declaration to add once:

```yaml
metrics:
  - {name: open_gap_age_days, type: gauge, label: "Oldest open gap (days)", cadence: 1d, direction: down_good, aggregation: last}
  - {name: proposal_queue_age_days, type: gauge, label: "Oldest waiting proposal (days)", cadence: 1d, direction: down_good, aggregation: last}
  - {name: asks_per_day, type: counter, label: "Asks raised per day", cadence: 1d, direction: down_good, aggregation: sum}
```

## Completion checklist

- [ ] View fetched at a recorded sha and validated before anything was observed.
- [ ] Every section in `observed.json` came from a call made this run; every failure is an `error`, not an omission.
- [ ] No row reads `in sync` without a matching fact; edges and grants read `unobserved` unless an outcome proved a grant.
- [ ] No `set_skill_gate` / `clear_skill_gate` on the Architect itself; no `set_agent_skills`; no delete of any agent; no credential value read or written; no write to `fleet-targets/`.
- [ ] Every ask carried a stable `request_id` and was checked with `get_my_ask` first; the broad `list_operator_queue` was never used for dedupe.
- [ ] At most one proposal written today, and only one that validates.
- [ ] Digest printed with ages; report published when the tool exists; metrics recorded only where declared.

## Error recovery

| Situation | Action |
|---|---|
| `GITHUB_TOKEN` unset or a clone refused | Stop before observing; digest = the single line `view unreachable`; report it. |
| View fails validation | Stop; report `view invalid at <sha>` with the errors; no act, no proposal. |
| Trinity MCP unavailable | Validate the view, print it, say the diff cannot run without observation; no row is `in sync`. |
| A tool errors for one agent | That section's entry gets the error; rows read `unobserved`; continue. |
| `403 *_management_not_permitted` | Record the grant as refused; the class becomes escalate for this run; never retry. |
| `set_skill_gate` → `unknown_role` / `approver_unavailable` | The row becomes escalate (a person assigns the role on that agent); never fall back to `primary`. |
| `assign_skill_to_agent` → `conflict` / `not_delivered` | Report as a decision (unassign-or-rename / manual sync by a person); never force. |
| `ask_operator` → `409 already_pending` | Read the named ask with `get_my_ask`; attach its id to the gap; raise nothing. |
| `ask_operator` → `429 rate_limited` / `queue_full` | Stop raising for this run; the remaining ask rows are listed in the digest as `not raised: queue full`. |
| `deploy_system` dry run `invalid` / `partial` | Do not deploy; row stays drift with the dry-run reason; propose if the cause is the view. |
| `record_metrics` → `metric_undeclared` | Skip that metric; say so in the digest. |

## Self-improvement

After a run, consider tactical improvements only — a new drift shape, a tool quirk, a clearer digest line. Never widen the verbs (no new apply class without a PRD §2 change), never infer a status. Edit this SKILL.md in its authoring source (`tandem-blueprint/skills/reconcile-fleet/`), bump `metadata.version`, prepend a changelog entry; the library mirror follows.
