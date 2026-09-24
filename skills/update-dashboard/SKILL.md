---
name: update-dashboard
description: Refresh an agent's business metrics in one pass — compute every metric declared in template.yaml metrics:, refresh dashboard.yaml, and record the same numbers as points via Trinity's record_metrics so they build a real time series. One playbook, both surfaces; safe to run locally.
category: workspace
user-invocable: true
automation: autonomous
disable-model-invocation: false
argument-hint: "[--dry-run]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - mcp__trinity__record_metrics
  - mcp__trinity__refresh_metric_definitions
metadata:
  version: "1.1"
  created: 2026-09-22
  author: Ability.ai
  changelog:
    - "1.1: Declare `automation: autonomous` — the playbook never asks (its `allowed-tools` carry no AskUserQuestion), and a schedule verifier that keys on the declaration flagged it as gated on every fleet it landed on (corbin pilot, trinity-enterprise#681, 2026-09-22). Frontmatter only; no behaviour change."
    - "1.0: Initial version — the generic runtime half of trinity-enterprise#482. Reads the agent's own template.yaml metrics: block, computes one value per declared metric from a declared x-source: recipe (or the agent's evidence), refreshes dashboard.yaml when present, records the batch via record_metrics (identity metric+ts+dims, execution_id replay, metric_undeclared → refresh_metric_definitions once), and degrades to the file write off Trinity. No kpi_snapshot report: the metric store is the history (ent#476 ruling 2026-09-21). Platform contract: ent#477 registry / ent#478 write / ent#479 read, merged 2026-09-22"
---

# Update Dashboard

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `update-dashboard vX.Y — recent: <summary>`. Then proceed.

Compute this agent's declared business metrics once and write them to **both surfaces**: `dashboard.yaml` (the live snapshot the Dashboard tab renders) and Trinity's metric store (the time series that tiles, canvas charts, freshness and objectives read). The Dashboard tab's *Update Dashboard* button calls `/update-dashboard` by this exact name — never introduce a second playbook name for the same job.

**Trinity is the upgrade, never the gate.** Off Trinity (no `mcp__trinity__record_metrics` tool) this skill still refreshes `dashboard.yaml` and reports what it would have recorded.

`--dry-run` computes everything and prints the batch it would record, writes nothing, records nothing.

---

## Where a value comes from

For every metric the agent declares, this skill needs a **recipe** — how to produce the number. Precedence:

1. **`x-source:` on the metric entry** (preferred). Trinity preserves `x-` prefixed keys on `template.yaml metrics:` entries (≤ 20 keys / 1 KB per entry) and never validates them — the documented escape hatch. One line, three forms:
   - `x-source: "bash: <command that prints exactly one value>"` — run it, take stdout.
   - `x-source: "file: <path>#<dotted.key>"` — read a JSON/YAML file, take the key.
   - `x-source: "<plain-language instruction>"` — follow it (e.g. *count the rows in data/leads.csv added since the last run*).
2. **A `dashboard.yaml` widget bound to the metric** (`metric: <name>`): its label and `description` say what it measures; compute it from the same workspace evidence the unbound widgets use.
3. **The agent's own CLAUDE.md and skills** describing the data source for that number.

**No evidence → no number.** A metric with no usable recipe is skipped and named in the confirm step. Never invent a value, never record a placeholder, never coerce (`"42"` is not `42`; a `status` takes one of its declared `values`, not a number).

---

## Process

### Step 1: Read the declarations

Read `template.yaml` → `metrics:`. For each entry note `name`, `type`, `cadence`, `values` (status metrics), `dimensions`, and `x-source`.

- No `metrics:` block → say so in one line, still run Step 3 if `dashboard.yaml` exists, then stop. Suggest declaring metrics only if the agent's CLAUDE.md names KPIs it evidently produces — never propose decorative ones.

### Step 2: Compute one value per metric

Apply the recipe (precedence above). Shape by type:

| `type` | value |
|---|---|
| `counter` · `gauge` · `duration` · `bytes` | a finite number |
| `percentage` | a finite number 0–100 |
| `status` | one of the declared `values[].value` labels |

If the metric declares `dimensions:` and the source yields them (e.g. per region), produce one point per combination with `dims: {<key>: "<label>"}`; otherwise record the point without `dims`. Only declared dimension keys are accepted.

### Step 3: Refresh `dashboard.yaml` (when it exists)

- Set the top-level `updated` timestamp to now (ISO 8601).
- Update **unbound** `metric`/`status`/`progress` widgets' `value` (and `color` against their thresholds) from the values you computed.
- Leave **bound** widgets (`metric: <name>`) alone — Trinity renders them from the recorded series (value, point time, stale flag, sparkline).
- Do **not** create a `dashboard.yaml` that does not exist: declared metrics render as tiles on their own.

Write the file in place. On Trinity the path is `/home/developer/dashboard.yaml`; locally it is the agent root.

### Step 4: Record the points (Trinity)

If `mcp__trinity__record_metrics` is available, record every computed value in **one** call:

```
record_metrics(points=[
  {"metric": "<name>", "value": <number-or-status-label>},
  {"metric": "<name>", "value": <number>, "dims": {"<key>": "<label>"}},
  ...
], execution_id="<from your Execution Context block, when present>")
```

Rules the platform enforces, so follow them rather than discover them:

- **Declared first.** `metric_undeclared` → the registry has not seen the entry. Call `refresh_metric_definitions` **once** (idempotent; the agent must be running), then retry the batch **once**. If it still refuses, report the name — do not loop.
- **Identity is `(metric, ts, dims)`**, not the value: omit `ts` for "now"; stamp an RFC 3339 `ts` with an offset only when the source states the moment it observed. Re-sending the same observation is deduplicated; a correction is a **new `ts`**.
- **All-or-nothing.** A refused batch names every bad point with a reason code and a fix. Fix and retry **once**; then report.
- **One point per metric per run** (per dims combination).

Skip this step **silently** when the tool is absent (local run) or refuses with an agent-scoped-key error. The dashboard write above still succeeded.

### Step 5: Confirm

```
Dashboard refreshed <timestamp>
| metric | value | store |
| <name> | <value> | recorded · deduplicated · skipped (<reason>) |
```

No KPI report is published: the metric store **is** the history (one mechanism for a business number — trinity-enterprise#476). Reports stay for narrative results, never as a second copy of a metric.

---

## Adding or changing a metric

The agent edits its own `template.yaml metrics:`, pushes, and then **calls `refresh_metric_definitions`** — the in-container auto-sync pushes but never pulls, so the backend does not see the edit until a restart or that call. A malformed entry is dropped from the registry and reported as compatibility finding **D-009**; its points then come back `metric_undeclared`. Never write `metrics.json` — the file is retired and reported as **D-010**.

## Scheduling

Declare the cadence once, in `template.yaml`:

```yaml
schedules:
  - name: update-dashboard
    cron: "0 */6 * * *"          # = the metrics' declared cadence:
    message: "/update-dashboard"
    enabled: true
```

A metric is **stale** when no point arrived within 2 × its `cadence:`, so the schedule interval and the declared cadence should agree. Schedules materialize at agent creation and run only while agent autonomy is on.

## Outputs

- `dashboard.yaml` refreshed in place (when present)
- One `record_metrics` batch per run — `<n> recorded, <m> deduplicated, <k> skipped`
- Skipped metrics named with the reason (no recipe · no evidence · refused: `<code>`)
