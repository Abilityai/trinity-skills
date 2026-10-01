---
name: role-context
description: "Load the seat this companion serves into working context — the role file, the objectives it owns or supports with target vs actual, the canon domains it reads (with freshness), the systems it declares, who fills the seat today (primary human, approver, stakeholders), open calibration notes and adopted lessons. Read-only; every other role-pack skill starts here."
category: role-companions
allowed-tools: Read, Bash, Glob, Grep, mcp__trinity__get_agent_assignments, mcp__trinity__get_objectives
user-invocable: true
argument-hint: "[--quiet]"
requires:
  binaries: [git]
canon: [org-context]
metadata:
  version: "1.0"
  created: 2026-09-28
  author: Ability.ai
  changelog:
    - "1.0: Initial version (ent#510, Tandem framework) — resolves x-role → roles/<id>.yaml (vacant → defaults_to), who fills the seat via get_agent_assignments (with role-drift flag), objectives via get_objectives (never re-derives a gap), the role's inputs + declared canon: domains through domains.yaml with freshness, the role's systems: block (the canon role-schema shape: id, direction, identity, authority, metrics, domains — ent#639), open calibration notes (capture-feedback) and adopted lessons (adopt-lesson); prints one Role context block and names every source it could not read"
---

# Role Context

> ℹ️ **First, set expectations:** print one line with this skill's version and its most recent change (the top entry of `metadata.changelog`), e.g. `role-context v1.0 — recent: <summary>`. Then proceed.

Load **the seat** into working context before acting on it. A role companion serves a role, not a person: the role file says what the seat is for, the objectives say what it is measured on, the assignment says who fills it today. Every role-pack skill (`/daily-brief`, `/capture-feedback`, `/record-decision`, `/report-observation`, `/adopt-lesson`) calls this first.

**Read-only.** This skill never writes to the canon, the agent repo, or the platform. It says what it could not read instead of guessing (framework principle: absence must not present as success).

## Inputs

| Source | Where | Required |
|---|---|---|
| Seat declaration | `template.yaml` → `x-role:` (`role`, `status`, `brain`) — written by the role-companion wizard | yes |
| Canon clone | `template.yaml` → `x-canon:` (`clone_path`, default `canon/`) | yes |
| Role file | `<canon>/roles/<role>.yaml` | yes |
| Domain map | `<canon>/domains.yaml` | no (reported when missing) |
| Who fills the seat | `get_agent_assignments(<self>)` | no (reported when unavailable) |
| Objectives, target vs actual | `get_objectives()` | no (reported when unavailable) |
| Calibration notes | `<canon>/agents/<self>/feedback/*.yaml` with `action: calibration-note`, `status: open` | no |
| Adopted lessons | `<canon>/agents/<self>/adoptions.yaml` + the brain's `lessons/` | no |

## Process

### Step 1: Seat and canon

```bash
ROLE=$(awk '/^x-role:/{f=1;next} f&&/^[^ ]/{f=0} f&&/^ *role:/{print $2}' template.yaml)
STATUS=$(awk '/^x-role:/{f=1;next} f&&/^[^ ]/{f=0} f&&/^ *status:/{print $2}' template.yaml)
BRAIN=$(awk '/^x-role:/{f=1;next} f&&/^[^ ]/{f=0} f&&/^ *brain:/{print $2}' template.yaml)
CANON=$(awk '/^x-canon:/{f=1;next} f&&/^[^ ]/{f=0} f&&/clone_path:/{print $2}' template.yaml); CANON=${CANON:-canon}
SELF=$(awk '/^x-canon:/{f=1;next} f&&/^[^ ]/{f=0} f&&/folder:/{print $2}' template.yaml | sed 's#^agents/##; s#/$##')
git -C "$CANON" pull --ff-only 2>/dev/null || echo "CANON_STALE"
```

- No `x-role:` block → stop: "this agent does not serve a seat — run the role-companion wizard (`create-agent:role-companion`) or add `x-role: {role: <id>, status: calibrating}`."
- No canon clone → stop and point at `/canon-doctor` (it self-heals the clone). A failed pull is not a stop: continue on the local copy and put `canon: local copy, pull failed` on the could-not-read list.
- `STATUS` is `calibrating` or `ready`. Anything else → report it as-is; never change it (the owner flips it).

### Step 2: The role file

Read `$CANON/roles/$ROLE.yaml` (grammar: the Tandem framework — `id`, `title`, `mission`, `status`, `defaults_to`, `responsibilities[]`, `inputs`, `outputs`, `capabilities`, `credentials`, `systems`, `review_by`, `notes`).

- Missing file → stop: the seat is undeclared; name the path.
- `status: vacant` → load the role in `defaults_to` as well and say "covering for vacant <role>".
- `review_by` in the past → flag `role file stale since <date>` (never treat a stale role as current fact; still load it).
- Keep `responsibilities` with their `decision_rights` (`decides | recommends | executes | informed`) — they decide what the companion may do alone vs recommend.

### Step 3: Who fills the seat

Call `get_agent_assignments` with this agent's own name. Keep: the **primary** human (the person the companion coaches and briefs), the approver(s), other stakeholders by kind, and the drift flag. Drift (the role file changed since the assignment was made, or the role went vacant) → carry it forward as `assignment drift — ask the admin to confirm`; never "fix" an assignment (only admins write them). Tool missing or erroring → `assignments: unavailable` on the could-not-read list.

### Step 4: Objectives — target vs actual

Call `get_objectives()` and use its rows as-is. **Never re-derive a gap from `get_metrics` plus an objective file** — `get_objectives` is the one place target and actual are joined. Keep per metric: target, actual, `gap.status`, `stale`, and the `findings`. A `stale: true` metric is carried as stale — its number is not acted on. `unavailable` → put `objectives` on the could-not-read list.

### Step 5: Domains this seat reads

The domains to load are the role's `inputs:` plus the `canon:` list of the calling skill. For each id, resolve it in `$CANON/domains.yaml` → `path`, `owner`, `freshness_days`. Freshness: the file's own `updated:`/`review_by:` front matter when it has one, else its last commit date (`git -C "$CANON" log -1 --format=%cs -- <path>`); older than `freshness_days` → stale. An id absent from the map, or a path that does not resolve → could-not-read (`domain <id>: not in the map` / `path missing`). Read stale domains, but label them.

### Step 6: Systems (the seat's declared reach)

Read the role file's `systems:` block when present — one entry per system the seat depends on:

```yaml
systems:
  - id: hubspot
    direction: read                # read | write
    identity: HUBSPOT_TOKEN        # the vault credential NAME it reads with (also in `credentials`)
    authority: paradigm-it-admin   # whose administrator granted that scope
    metrics: [mql_count]           # metrics this system feeds
    domains: [hubspot-pipeline]    # canon domains it feeds
```

The shape is the canon role schema (`CONVENTIONS.md` → `roles/<role-id>.yaml` → `systems`, ent#639): one level of structure, so `metrics` and `domains` sit on the entry itself. Freshness and the unavailable state are never declared — `/daily-brief` reports them each period.

Carry the list forward; `/daily-brief` decides which were readable this period. No `systems:` block → say so (`reach undeclared — coverage cannot be computed`); never infer systems from credentials.

### Step 7: Calibration notes and adopted lessons

- Open calibration notes: `$CANON/agents/$SELF/feedback/*.yaml` whose `action: calibration-note` and `status: open`. These are the reviewer's corrections from the calibration loop — **read them before acting**, and apply them.
- Adopted lessons: `$CANON/agents/$SELF/adoptions.yaml` entries with `decision: adopt | adapt`, joined to the lesson file in `$CANON/agents/$BRAIN/lessons/`. Keep each lesson's `conditions` — a lesson without its context is invalid (Tandem framework). An `adapt` carries its own `why`, which scopes it.
- New lessons for this role that have no adoption entry yet → count them (`<n> new lesson(s) — /adopt-lesson`).

### Step 8: Print the Role context block

```
## Role context — <title> (<role>) · <calibrating|ready> · canon@<short-sha>
Serving: <primary human> · approver: <…> · stakeholders: <…>        [assignment drift: …]
Mission: <mission>
Responsibilities: <id> (<decision_rights>) · …
Objectives:
  - <objective id> — <metric>: <actual> vs <target> (<gap.status>) [stale]
Domains read: <id> (fresh | stale since <date>) · …
Systems declared: <id> (<direction>) · … | reach undeclared
Calibration notes (open): <n> — <one line each>
Lessons in force: <id> (<adopt|adapt>: <conditions>) · <n> new — /adopt-lesson
Could not read: <source — reason> · … | nothing
```

`--quiet` prints only the `Could not read` line when it is non-empty (for callers that already hold the rest).

## Error handling

| Situation | Action |
|---|---|
| No `x-role:` | Stop — the agent serves no seat; point at the wizard |
| Role file missing | Stop — name `roles/<id>.yaml` |
| Canon pull fails | Continue on the local copy; list it under Could not read |
| A platform read fails | Continue; list it under Could not read — never invent a value |
| Role or domain past `review_by` | Load it, label it stale |
