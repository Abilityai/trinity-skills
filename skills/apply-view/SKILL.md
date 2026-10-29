---
name: apply-view
description: The Trinity-native merge of a target-view proposal for installs without a git review flow (ruling 7) — validate the proposal against the target-view schema, show the diff against the current view, raise ONE approval ask to the fleet owner, and on approval write the proposal over the Trinity-held view in the Architect's own repo and run /reconcile-fleet once. Refuses a proposal that fails validation. Meant to be assigned as a gated skill (approval recommended) so Trinity itself raises the approval.
category: agent-development
user-invocable: true
approval: recommended
argument-hint: "<proposal-path> [--gated]"
when_to_use: When a person wants to accept a proposal the Architect wrote (proposals/target-view.next.yaml) on an install that has no fleet-targets repository to merge in — "apply the proposal", "accept the view change", "merge the Architect's proposal here". Not for installs whose view lives in Abilityai/fleet-targets (a person merges a PR there; this skill refuses). Never used to edit a view by hand — a proposal file is the only input.
allowed-tools: Read, Write, Bash, Glob, Grep, Skill, mcp__trinity__get_agent_assignments, mcp__trinity__ask_operator, mcp__trinity__get_my_ask, mcp__trinity__report
requires:
  binaries: [git, python3]
metadata:
  mirror: "tandem-blueprint@41b9f4a skills/apply-view"
  version: "1.0"
  created: 2026-10-28
  author: architect
  changelog:
    - "1.0: Initial version — validate → diff → one approval ask (request_id keyed by the proposal's sha256) → fire and park → on approval copy into views/<fleet>/target-view.yaml, commit locally, run /reconcile-fleet once; refuses an invalid proposal and a fleet whose view lives in fleet-targets; abilityai/trinity-enterprise#992"
---

# Apply View

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `apply-view vX.Y — recent: <summary>`. Then proceed.

## Purpose

The target view changes only when a person merges the change (PRD §2, level 3). Where the fleet's view lives in `Abilityai/fleet-targets`, that merge is a GitHub PR with human CODEOWNERS and the Architect's token read-only. An install **without** that repository still needs the same act: a person approving one specific proposal, after which the Architect holds the new view. This skill is that act, done with Trinity's own primitives — one approval ask, one write to the Trinity-held view at `views/<fleet>/target-view.yaml` in the Architect's repo, one reconcile tick.

It is designed to be a **gated skill**: `approval: recommended` in the frontmatter means that when the library assigns it, Trinity puts an approval gate on it (`list_skill_gates`, origin `library_default`), the request is frozen, the approver sees the proposal, and an approved run executes once. That gate is the approval; a second ask inside the run would be the same inbox under a second hat.

## Rules this skill encodes

- **A proposal that fails `tools/validate.py --view` is refused.** No diff, no ask, no write. The Architect does not repair proposals; it reports the errors and stops.
- **The authoritative view wins.** If `fleet-targets/<fleet>/target-view.yaml` exists for this fleet (a side clone is present), refuse: the merge belongs in that repository, by PR. This skill only writes the Trinity-held copy.
- **One approval, one decision.** Either the platform gate approved this run (invoked `--gated`, see below) or the skill raises exactly one `ask_operator` approval with two options; never both, never more.
- **The approver is a role, resolved by the platform.** The ask goes `to: primary` (the Architect's owner — the fleet owner on instance zero) or `to: approver` when the fleet owner fills that kind on the Architect's roster (`get_agent_assignments(self)`); `ask_operator` does not accept `role:<id>`, so the role is named in the title.
- **Fire and park.** The ask is raised and the turn ends. The write happens on the wake (`wakes_on_ending`) or on the next invocation with the same proposal path, after `get_my_ask` shows `answered` with the approving option. `(something else)` means none of the options is approved: nothing is written, the person's `response_text` is reported.
- **Idempotent.** `request_id = "apply-view:<fleet>:<sha256 of the proposal file, first 16 hex>"`. The same proposal never raises twice (`status: replayed`); a changed proposal is a new id. An expired ask is re-raised only on an explicit new invocation, with `supersedes_expired`.
- **Local commit only; the platform pushes.** The write is committed in the Architect's repo; the agent's auto-sync carries it. This skill never pushes to another repository and never touches `fleet-targets`.

## Process

### Step 1: Locate and validate

- `<proposal-path>`: required. Default location the Architect writes to: `canon/<x-canon.folder>/proposals/target-view.next.yaml`.
- Self-heal the tools clone: `[ -d tandem-blueprint/.git ] || git clone --quiet https://github.com/Abilityai/tandem-blueprint tandem-blueprint; git -C tandem-blueprint pull --quiet --ff-only`.

```bash
python3 tandem-blueprint/tools/validate.py --view <proposal-path>
```

Any `FAIL` → print them, say `proposal refused — fix the file and re-run`, stop. Read `fleet:` from the proposal. If `fleet-targets/<fleet>/target-view.yaml` exists → stop: `this fleet's view lives in Abilityai/fleet-targets — open a PR there; apply-view writes only the Trinity-held copy`.

### Step 2: Diff

Current view = `views/<fleet>/target-view.yaml` (absent on a first apply — then the diff is against an empty file and the ask says so).

```bash
diff -u views/<fleet>/target-view.yaml <proposal-path> || true
```

Print the diff. Summarize it as plain rows (section, before, after) — the ask's `question` carries this summary, never raw YAML dumps beyond what a person can read at a glance.

### Step 3: The one approval

**If invoked with `--gated`** — the convention for a run Trinity already approved through the skill gate (the gate approver saw the frozen request naming this proposal) — skip to Step 4. There is no platform signal inside the run that says "this execution was gate-approved"; the flag is the caller's statement (PRD §8 X7, a platform question).

Otherwise resolve the addressee from `get_agent_assignments(agent_name=<self>)` (fleet owner on the roster as `primary` → `to: primary`; as `approver` → `to: approver`; else `primary`), then check `get_my_ask(request_id)`:

- `pending` → say it is waiting, stop.
- `answered`, approving option → Step 4.
- `answered`, `(something else)` or the declining option → report `response_text`, stop; nothing written.
- `dismissed` → stop; do not re-raise now.
- `expired` → re-raise only because a person invoked this skill again, with `supersedes_expired: <request_id>`.
- not found → raise:

```
ask_operator(
  request_id = "apply-view:<fleet>:<sha16>",
  type = "approval", to = <kind>, priority = "high",
  title = "Apply target-view proposal for <fleet> (role:fleet-owner)",
  question = "<the diff summary rows, and what the Architect will do after the write: one /reconcile-fleet run>",
  options = ["Apply the proposal", "Keep the current view"],
  proposal = {"Apply the proposal": {"write": "views/<fleet>/target-view.yaml", "sha256": "<full>", "then": "/reconcile-fleet <fleet>"},
              "Keep the current view": {"write": null}},
  context = {"fleet": "<fleet>", "proposal_path": "<path>", "rows_changed": <n>})
```

Record the receipt (`id`, `to_role`, `resolved`) and **end the turn**. `resolved: true` means a Workspace will show it, not that anyone has read it.

### Step 4: Write, commit, reconcile

```bash
mkdir -p views/<fleet>
cp <proposal-path> views/<fleet>/target-view.yaml
python3 tandem-blueprint/tools/validate.py --view views/<fleet>/target-view.yaml
git add views/<fleet>/target-view.yaml
git commit -m "view(<fleet>): apply proposal <sha16> — approved via <request_id or gate>"
```

Then run `/reconcile-fleet <fleet>` once (Skill tool). Report: the commit sha, the ask or gate that approved it, and the reconcile digest. **Only when `mcp__trinity__report` is available:** publish `report_type: architect.apply_view`, `display_hint: markdown`, payload `{markdown: "<fleet> · proposal <sha16> applied · approved by <...> · commit <sha> · reconcile: <one line>"}`.

## Completion checklist

- [ ] Proposal validated before anything else; refused on any FAIL.
- [ ] Refused when the fleet's view lives in `fleet-targets`.
- [ ] Exactly one approval — the platform gate (`--gated`) or one `ask_operator` with a stable `request_id`; `get_my_ask` read before raising.
- [ ] Nothing written before an approval; `(something else)` wrote nothing.
- [ ] Write committed locally in the Architect's own repo; no push, no write to any other repository.
- [ ] `/reconcile-fleet <fleet>` ran once after the write.

## Error recovery

| Situation | Action |
|---|---|
| Proposal path missing or unreadable | Stop; name the path. |
| Validation FAIL | Print the errors; refuse. |
| `fleet-targets/<fleet>/` present | Refuse; point to the PR path. |
| `ask_operator` → `409 already_pending` | Read the named ask; report it is waiting; stop. |
| `ask_operator` → `role_unassigned` on `to: approver` | Re-raise `to: primary` with the role in the title; say why. |
| Approval answered but the proposal file changed since (sha mismatch) | Do not write; say the approved bytes are not the current file; a new invocation raises a new ask. |
| `git commit` fails (nothing to commit) | The held view already equals the proposal; report `already applied` and still run `/reconcile-fleet`. |
| `/reconcile-fleet` fails | The view is written and committed; report the reconcile error — the next tick retries by schedule. |

## Self-improvement

Tactical only: clearer diff summaries, a better refusal message. Never add a second write target, never bypass the single approval. Edit the authoring source (`tandem-blueprint/skills/apply-view/`), bump `metadata.version`, prepend a changelog entry.
