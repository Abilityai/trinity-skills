---
name: daily-brief
description: "Write the seat's daily brief for its primary human — objective status with freshness, gaps as deltas, today's three, one stop-doing, what is waiting on them, what the companion did and will do — plus the standing could-not-see line and the seat's coverage figure. Runs from a one-line schedule addressed to the person; the reply is the brief, delivered to their Main chat."
category: role-companions
allowed-tools: Read, Bash, Glob, Grep, mcp__trinity__get_objectives, mcp__trinity__get_metrics, mcp__trinity__record_metrics, mcp__trinity__list_operator_queue, mcp__trinity__list_reminders, mcp__trinity__list_agent_schedules, mcp__trinity__list_seat_decisions, mcp__trinity__list_available_credentials
user-invocable: true
argument-hint: "[--preview] [--weekly | --monthly | --quarterly]"
requires:
  binaries: [git]
canon: [org-context]
metadata:
  version: "1.0"
  created: 2026-09-28
  author: Ability.ai
  changelog:
    - "1.0: Initial version (ent#510, Tandem framework) — the six-section brief built from role-context + get_objectives (never a re-derived gap) + operator-queue items and reminders + own schedules; standing could-not-see line and coverage (readable ÷ declared systems) from the role file's systems: block; one brief per person per day; blameless, no named cross-team comparisons; refuses to run as a scheduled brief while x-role.status is calibrating (--preview for the reviewer); the reply is the brief (deliver_to_workspace_email lands it in the person's Main chat)"
---

# Daily Brief

> ℹ️ **First, set expectations:** print one line with this skill's version and its most recent change (the top entry of `metadata.changelog`). Then proceed.

The companion's proactive surface: **one brief per person per day**, objective-driven, landed in the primary human's Main chat. Schedule it as a one-line playbook call — `/daily-brief` — on a schedule addressed to that person (`deliver_to_workspace_email`); the run's reply **is** the brief, so this skill never sends a message itself.

## Guards (before anything else)

1. **Readiness.** Read `x-role.status` from `template.yaml`. `calibrating` and this is a scheduled run → stop with one line: `brief held — seat is calibrating (the owner flips it to ready after the walkthrough)`. The platform also holds a calibrating seat's brief schedule; this guard keeps a hand-made schedule from leaking one. `--preview` runs the full brief for the reviewer during calibration and says `PREVIEW — not delivered as a brief` on its first line.
2. **One per person per day.** State file `.trinity/daily-brief/last.json`, keyed by period (`{"daily": "YYYY-MM-DD", "weekly": "YYYY-MM-DD", …}`) so a `--weekly` run never clears the daily guard. This period's key already holds today's date → stop: `already briefed today`. A legacy single-slot file (`{"date", "period"}`) is read as `{<period>: <date>}`. Other companions of the same person feed this one rather than sending their own (Tandem framework) — if a peer companion's note arrived for inclusion, it goes into section 6.
3. **Addressed.** A scheduled run with no person in its Execution Context (no seat it serves) → stop: `brief schedule is not addressed to a person — set deliver_to_workspace_email`.

## Process

### Step 1: Load the seat

Run `/role-context`. Keep its output — role, responsibilities, primary human, objectives with gaps, domains with freshness, systems declared, calibration notes, lessons in force, and its **Could not read** list (it seeds the could-not-see line).

### Step 2: Reach — what could not be seen, and coverage

For every entry in the role's `systems:` block decide **readable** or **not readable this period**:

- its `identity` credential is not available to this agent (`list_available_credentials` / the agent's env) → not readable (`no credential <NAME>`);
- a metric in its `metrics` is `stale: true` in `get_objectives` (or `freshness: no_points`) → not readable (`<metric> stale since <last point>`);
- a domain in its `domains` is stale per role-context → not readable (`<domain> stale since <date>`);
- the companion's own read of it failed during the period (its run notes say so) → not readable, with the error class.

Coverage = readable ÷ declared, as a percentage, with both counts. No `systems:` block → coverage `n/a — reach undeclared`. If `template.yaml` `metrics:` declares `seat_coverage`, record the number with `record_metrics` (percentage, 0–100) so it charts like any other measure (Tandem framework).

The **could-not-see line is standing**: it is printed every day, and says `could not see: nothing` when everything was readable. A revoked credential must produce a named line, never a silent gap.

### Step 3: Build the six sections

1. **Objective status** — every objective the role owns or supports: metric, actual vs target, `gap.status`, freshness. Stale numbers are said to be stale and not interpreted.
2. **Gaps** — where the numbers are off, as deltas (`12 below target 65`), attributed to process and conditions, never to a person.
3. **Today's three** — the three actions with the biggest lift on the gaps. Each is tied to a responsibility id, and each says what the companion will do alongside. Respect `decision_rights`: where the role `recommends`, propose; where it `decides`, say so. When a standing seat decision applies (`list_seat_decisions`), apply its criterion and cite it.
4. **Stop doing** — at most one, framed as a process the companion can take over or eliminate. Omit rather than invent.
5. **Waiting on you** — open operator-queue items this agent raised for the person (`list_operator_queue`), approvals, and due reminders (`list_reminders`). Each says what happens when they answer ("acted on at the next wake-up" until re-triggering ships).
6. **What I did / will do** — this agent's work since the last brief and what is scheduled next (`list_agent_schedules`), so the person never wonders whether it is alive.

Then the reach lines:

```
Could not see: <system — reason>; … | nothing
Coverage: <readable>/<declared> systems (<pct>%) | n/a — reach undeclared
```

### Step 4: Rules

- **Blameless.** Never compare named individuals or teams. Cross-team wins arrive only as adopted lessons, with their conditions, as options.
- **Objective-driven.** No gap and nothing waiting → a short brief that says so; never pad.
- **Weekly / monthly / quarterly** aggregate the same sections over the period (`--weekly` etc.); the period is part of the one-per-day key.
- Close with one line inviting a rating: a negative rating opens `/capture-feedback`.

### Step 5: Record and reply

Set this period's key in `.trinity/daily-brief/last.json` to today (keep the other periods' keys), then reply with the brief. Nothing else goes in the reply.

## Error handling

| Situation | Action |
|---|---|
| `calibrating` + scheduled | Stop (one line) — never deliver |
| Already briefed today | Stop (one line) |
| `get_objectives` unavailable | Brief anyway; section 1 says `objectives unavailable`, and it joins the could-not-see line |
| No `systems:` block | Coverage `n/a — reach undeclared`; the could-not-see line still lists platform reads that failed |
| `record_metrics` fails / `seat_coverage` undeclared | Skip the record; the number stays in the brief |
