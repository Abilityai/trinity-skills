---
name: propose-improvements
description: The standard procedure by which an agent researches its market and its own record, then proposes improvements for a human or superior agent to accept or reject — read the research sources and own execution record declared in IMPROVEMENT_PROPOSALS.md §0 since the last anchor, map every delta against what the agent does today and its plan, write classed proposals (BUILD / SELF / COUNTER-POSITION / WATCH / IGNORE) with the bet stated into the declared inbox, raise one ask per proposal to the declared approver role, and record the ruling. The agent proposes; the approver decides; nothing is applied here.
automation: autonomous
schedule: "0 12 * * 1"   # default: weekly, Monday 12:00 UTC — adjust per agent
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, mcp__trinity__ask_operator, mcp__trinity__get_my_ask, mcp__trinity__record_decision, mcp__trinity__report, mcp__trinity__list_reports, mcp__trinity__list_recent_executions
effort: high
user-invocable: true
argument-hint: "[run | review | status] [--since YYYY-MM-DD]"
category: project-management
requires:
  binaries: [git, gh]
metadata:
  version: "1.0"
  created: 2026-10-18
  author: trinity-pm
  changelog:
    - "1.0: Initial version — generalized from trinity-pm's /product-proposals (operator ask 2026-10-18: 'agents can have a special procedure for researching the market and proposing ideas for their own improvement to superior agents or managing humans… this should be the standard procedure'). Config in IMPROVEMENT_PROPOSALS.md §0 (sources, inbox, approver role, budget); proposals are asks to a role, decisions land in the inbox entry and the seat decision record; the agent never applies a change itself"
---

# Propose Improvements

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `propose-improvements vX.Y — recent: <summary>`. Then proceed.

## Purpose

Every agent that runs for a while accumulates two things nobody reads: a market that moved around it, and an execution record that shows where it struggled. This skill turns both into **proposals** — short, evidence-bearing, classed, with the bet stated — and puts each one in front of the person or agent who holds the **approver role**, as one decision. The approver accepts, counters, rejects or defers. The agent **never applies** a change from here: an accepted BUILD goes to whoever owns the product backlog, an accepted SELF change goes through the agent's normal self-change path (its repo, a PR to its library, or an admin grant), and a rejection is recorded with the why so it is never re-litigated.

Two roles this skill assumes exist around the agent, without naming people:

- **The mechanics** (system engineers, the platform's steward tier) keep the agent running — budgets, schedules, health. They are not asked anything here.
- **The approver** (change management — a managing human or a superior agent) rules on proposals. Declared as a **role** in §0 and resolved by the platform (`ask_operator` `to:`), never hard-coded to a person.

Hard rules: a competitor doing something is **never by itself a reason to build it**; at most **`budget_per_run`** BUILD + SELF proposals per run; anything already filed is a link, not a proposal; nothing internal (pricing, packaging, credentials) leaves the workspace; the skill never re-researches what a declared source already covers — a missing fact becomes a *question for that source*, not a web search.

## Configuration — `IMPROVEMENT_PROPOSALS.md` §0

The skill reads `IMPROVEMENT_PROPOSALS.md` at the repo root. **Missing → stop** and print the template below with "create IMPROVEMENT_PROPOSALS.md §0 first". Headless-safe: never ask mid-run.

```markdown
# Improvement proposals

## §0 Configuration
```yaml
sources:                                   # research the agent consumes (never produces here)
  - name: competitor-intel                 # a git repo another agent publishes
    kind: git                              # git | path
    repo: https://github.com/<org>/<repo>
    clone_dir: competitor-intel            # side clone at the repo root; add it to .gitignore
    delta: outputs/changelog.md            # dated "## YYYY-MM-DD" sections — the delta feed
    also: [outputs/repo-signals/, outputs/discovery/]   # dated files read when newer than the anchor
  - name: dev-watch
    kind: path
    path: reports/dev-watch/               # dated files in this repo
own_record: true                           # read own executions since the anchor (Trinity only)
what_we_do: [PLATFORM_STATE.md, CLAUDE.md] # the ONLY sources for "do we already do this"
plan: [ROADMAP.md]                         # where "is it already planned" is answered
inbox: IMPROVEMENT_PROPOSALS.md#Proposals  # file[#section] proposals are appended to
id_prefix: IP                              # IP-1, IP-2 … (stable ids)
approver: approver                         # primary | approver | operator | role:<canon-role-id>
budget_per_run: 3                          # max BUILD + SELF proposals per run
digest_dir: reports/improvement-proposals  # dated digest + anchor.json live here
report_type: <agent>.improvement_proposals # Trinity report type; omit to skip reporting
product_owner: trinity-pm                  # agent whose intake takes accepted BUILD proposals (omit if this agent owns the backlog)
```

## Proposals
<!-- appended by /propose-improvements, newest last -->
```

Resolver (deterministic; `awk` fields are written `$(2)` because the skill runner rewrites bare dollar-digits):

```bash
ROOT="$(git rev-parse --show-toplevel)"; CFG="$ROOT/IMPROVEMENT_PROPOSALS.md"
[ -f "$CFG" ] || { echo "create IMPROVEMENT_PROPOSALS.md §0 first (template in the skill)"; exit 2; }
cfg() { awk -v k="${1}" '/^```yaml/{y=1;next} /^```/{y=0} y && $(1)==k":"{sub(/^[^:]*: */,""); print; exit}' "$CFG"; }
APPROVER="$(cfg approver)"; BUDGET="$(cfg budget_per_run)"; DIGEST="$(cfg digest_dir)"; PREFIX="$(cfg id_prefix)"
```

## Modes

| Invocation | Does |
|---|---|
| `run` (default) | gather deltas since the anchor → map → classify → write → ask → report → advance the anchor. Headless. |
| `review` | interactive: walk `Proposed` entries one at a time, one plain-text question each; or consume answered asks (`get_my_ask`) and record rulings. |
| `status` | read-only: anchor, pending proposals, open asks, last digest. |
| `--since YYYY-MM-DD` | lower bound for one run (anchor still advances to today). |

## Process — `run`

### 1. Anchor
`$DIGEST/anchor.json`: `{ "last_run", "sources": {"<name>": "<sha or latest date>"}, "proposals_filed": [], "pending": [] }`. Missing → first run → lower bound 14 days ago.

### 2. Gather (read-only)
For each `kind: git` source: clone if missing, `fetch` + `reset --hard origin/<default>`; record the sha. Take every dated section of `delta` newer than the anchor, and every file under `also:` newer than the anchor. For `kind: path`: dated files newer than the anchor. With `own_record: true` and Trinity present: `list_recent_executions` for this agent — failures, retries, repeated asks, runs that hit a stop rule — these are **SELF** signals.

```bash
awk -v since="$SINCE" '/^## [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]/{d=substr($(2),1,10); keep=(d>since)} keep' "$ROOT/$CLONE/$DELTA"
```

Working list: `source · subject · what changed · evidence (url/date) · axis or area · confidence`. Never fabricate a delta: if a source has not moved since the anchor, say so.

### 3. Map each delta
Answer four things, from `what_we_do` and `plan` **only**:
1. **Do we have it?** yes (where) · partly (the gap) · no · deliberately not (cite the ruling).
2. **Does it touch something we lead on or depend on?** name it.
3. **Is it planned?** issue/epic/workstream, or nothing.
4. **Does a second signal corroborate it?** another competitor, a user ask, our own failure record — or none.

### 4. Classify

| Class | Meaning | Default recommendation |
|---|---|---|
| **BUILD** | the product/service this agent serves lacks it; ≥1 corroborating signal or ≥2 sources moved | accepted → `product_owner`'s intake (or this agent's backlog if it owns one) |
| **SELF** | a change to **this agent's** instructions, skills, schedules or sources, grounded in its own record or a source it should watch | accepted → the agent's self-change path; never applied from here |
| **COUNTER-POSITION** | we have it or do it differently; the market is claiming the language | note for whoever owns positioning |
| **WATCH** | real, single-source, no corroboration, or sits on a standing ruling | hold; name the trigger that brings it back |
| **IGNORE** | off the bet or a ruled non-goal | record the why once (digest only) |

Stop at `budget_per_run` BUILD + SELF. More means the filter is too loose, not that the market is louder.

### 5. Write
**(a) Inbox entry** (append under the `inbox` section; ids `<PREFIX>-<n>`, next free number):

```
### <PREFIX>-<n> — <what, one line>
- **What:** …
- **Why (market/record):** <source · subject · what · evidence date> — <source name> @ <sha>
- **Why (us):** <corroborating signal, or "none">
- **Where it lives today:** <from what_we_do, or "not built", or the ruling>
- **Planned:** <issue/workstream or "no">
- **Class:** BUILD | SELF | COUNTER-POSITION | WATCH · **Recommendation:** <one sentence + the bet>
- **Effort:** S/M/L · **Source:** /propose-improvements <date>
- **Status:** Proposed <date> — ask <request_id or "review">
```

**(b) Digest** `$DIGEST/YYYY-MM-DD.md` (≤120 lines): what moved → proposals by class (≤3 lines each) → counter-positions → watch → ignored with why → questions for each source → inputs read (shas, dates, what was *not* read).

**(c) Asks** — Trinity present: for each BUILD/SELF proposal raise **one** `ask_operator` to `$APPROVER` — title ≤120 chars = the proposal's one line; body = the four map answers + recommendation + digest path; options (≤5, ≤60 chars each): `Accept — file it` · `Counter — positioning only` · `Reject (say why)` · `Defer to next run`. The platform adds "(something else)". Record the `request_id` in the entry's Status. A refused ask (`approver_cannot_open_agent`, `role_unassigned`, `already_pending`) is recorded verbatim and the entry stays `Proposed — review`; never route around it. No Trinity: entries wait for `review`.

**(d) Report** — `report(report_type=<cfg>, display_hint="markdown", title="Improvement proposals <date> — <n> build · <n> self · <n> counter · <n> watch", payload={markdown: digest})`. Skip silently when the tool is absent or refuses for key identity.

**(e) Anchor** — advance; list `pending`.

### 6. Closing line
Counts by class · digest path · "Rulings: `/propose-improvements review`". If a declared source was not read (budget, clone failure), say which.

## Process — `review`

1. For each `pending` entry: if its ask is answered (`get_my_ask`), take the answer; else ask the operator **one plain-text question** (accept / counter / reject why / defer).
2. Write the ruling into the entry's **Status** with date and, for a rejection, the approver's words. `record_decision` when available (the seat decision record: approved / deferred / killed).
3. Hand-offs, never actions: **Accept + BUILD** → one line to `product_owner`'s intake (its own capture playbook, e.g. `/feature-intake capture <PREFIX>-<n>`), or this agent's backlog skill; **Accept + SELF** → open the change as a PR / `/adjust-playbook` draft for the owner to apply, never a live edit of a running schedule or instruction from inside this run; **Counter** → append to `$DIGEST/counter-positions.md`; **Reject** → the why stays in the entry; **Defer** → back to `pending`.
4. End with the tally and the next run date.

## Guardrails

- Read-only against every source and every external surface; never sign up, never contact anyone.
- `what_we_do` is the only source for "we already have it" — never memory.
- Numbers (scores, counts) are copied from the source files, never typed from recollection.
- One run ≤ 30 minutes; stop gathering at the budget and say what was skipped.
- A proposal is a proposal: this skill holds no `*.manage` grant and needs none.

## Related

- `project-steward`, `project-intake` — the managed-project side an accepted BUILD may land in.
- The approval machinery this relies on is the platform's: asks to a role (resolved through the agent's assignments), the seat decision record, gated skills for anything that *acts*.
