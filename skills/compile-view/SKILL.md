---
name: compile-view
description: "Compile a fleet's target view into a Trinity SystemManifest build artifact (build/<fleet>.system.yaml — Trinity's native format only, no invented fields) plus an apply sidecar (build/<fleet>.apply.json) listing what the view binds but a manifest cannot carry: grants, approval map, assignments, credential names, the Architect's tick. Validates the view first, warns where deploy_system's naming (<system>-<short>) cannot reproduce the view's agent names, and dry-runs the manifest against Trinity when MCP is available. Never deploys."
category: agent-development
user-invocable: true
argument-hint: "[<fleet>] [--view <path-or-url>] [--system-name <name>] [--dry-run]"
when_to_use: Before a first deploy of a fleet from its view ("compile the view", "what manifest does this view produce"), inside /reconcile-fleet when an agent the view names is missing live, or to check what a view change would mean for the manifest. Not a deploy — /reconcile-fleet deploys missing agents within the view, a person deploys a whole new fleet (/compose-system or deploy_system by hand).
allowed-tools: Read, Write, Bash, Glob, Grep, mcp__trinity__deploy_system
requires:
  binaries: [git, python3]
metadata:
  mirror: "tandem-blueprint@41b9f4a skills/compile-view"
  version: "1.0"
  created: 2026-10-28
  author: architect
  changelog:
    - "1.0: Initial version — tools/compile_view.py: agents[] → agents{short: {template (with @ref inside), kind}}, edges[] → permissions.explicit (every agent a source key; preset none when no edges), everything else → the apply sidecar; name_prefix_mismatch / edges_outside_manifest / architect_not_in_agents warnings; optional deploy_system dry run; abilityai/trinity-enterprise#992"
---

# Compile View

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `compile-view vX.Y — recent: <summary>`. Then proceed.

## Purpose

The `SystemManifest` is a **build artifact**: compiled from the target view every time it is needed, never edited, never a second source (PRD §1). This skill is the compiler. It reads a validated view and writes exactly what `deploy_system` parses — nothing the platform would warn about or drop — and puts everything else the view binds into a sidecar for `/reconcile-fleet`, which applies, asks or escalates it (PRD §2).

## What maps where (read from the platform code, Trinity dev f754dfb0)

| view | manifest (`SystemManifest`, `src/backend/models.py`) | note |
|---|---|---|
| `fleet` | `name` (or `--system-name`) | `deploy_system` names every agent `<name>-<short>` (`resolve_agent_names`) |
| `agents[].name` | the agent's short key — `name` minus the `<system>-` prefix | a name without that prefix cannot be reproduced → `name_prefix_mismatch` warning |
| `agents[].repo` | `template: github:owner/repo[@ref]` | the `@ref` stays inside the template string; there is no branch field |
| `agents[].kind` | `kind: agent \| deployment` | ent#704; omitted means the platform default |
| `edges[]` | `permissions.explicit: {from_short: [to_short, …]}` | every agent appears as a source key (an empty list clears its outgoing edges; `{}` would be falsy and apply nothing); no edges → `preset: none` |
| `architect` | a member only if it is also in `agents[]`; otherwise `architect_not_in_agents` warning | the manifest never creates the Architect by implication |
| `grants`, `approval_map`, `assignments`, `credentials` (names), `seats`, `architect.reconcile`, edges with an endpoint outside `agents[]` | **sidecar** `build/<fleet>.apply.json` | not manifest fields — `credentials:` / `skills:` on a manifest agent are dropped with a warning (#2373) |
| `clients`, `engagements`, `budgets` | nothing | boundary parties are not platform objects |

Not emitted, on purpose: `prompt`, `default_tags`, `system_view`, `folders`, `schedules`, `resources` — the view does not bind them (schedules are the agent's own layer), and a person adds them to a deploy by hand if a fleet wants them.

## Process

### Step 1: Resolve the view

- `<fleet>`: first bare argument; default as in `/reconcile-fleet` (the only `<fleet>/` in `fleet-targets/`, else the only `views/<fleet>/`).
- `--view <path-or-url>`: compile this file instead (fetched once when a URL).
- Self-heal the tools clone: `[ -d tandem-blueprint/.git ] || git clone --quiet https://github.com/Abilityai/tandem-blueprint tandem-blueprint; git -C tandem-blueprint pull --quiet --ff-only`.
- View sha: `git -C fleet-targets rev-parse --short HEAD` when from the clone, else the file's sha256 (first 12).

### Step 2: Compile

```bash
mkdir -p build
python3 tandem-blueprint/tools/compile_view.py <view> --out-dir build --view-sha <sha> [--system-name <name>]
```

The compiler validates the view first (`tools/validate.py --view`) and refuses one that fails — a view that does not validate is not a source. On success it prints the two paths and every warning:

| warning | meaning | what to do |
|---|---|---|
| `name_prefix_mismatch` | `deploy_system` would create `<system>-<name>`, never `<name>` | a fleet not born from a manifest (instance zero) cannot be re-created under its names; `/reconcile-fleet` must not deploy that agent — the gap is a platform question (no-prefix deploy, or a view convention `<fleet>-<short>`) |
| `edges_outside_manifest` | an edge names a principal the manifest does not create (the Architect outside `agents[]`, a boundary agent) | the sidecar lists them; they are `unobserved` rows until trinity-enterprise#991 |
| `architect_not_in_agents` | the view's supervisor is not a member | expected when the Architect governs a fleet it is not part of; nothing to fix |
| `template_shape` | a repo is not `github:owner/repo[@ref]` | fix the view (a person) — the validator should already have caught it |

`build/` is gitignored in the authoring repo and should be in the Architect's repo too: the artifact is regenerated, never committed.

### Step 3: Dry run (when Trinity MCP is available, or `--dry-run` asked for it)

```
deploy_system(manifest=<contents of build/<fleet>.system.yaml>, dry_run=true)
```

Read `status` and `failed[]`: `invalid` with a populated `failed[]` means the manifest would not deploy cleanly — print each reason verbatim. A dry run resolves templates and names (it reports `Agent '<x>' already exists, will create '<x>-2'` per collision — on an existing fleet that is every agent, and it is the `name_prefix_mismatch` story told by the platform). **This skill never calls `deploy_system` without `dry_run: true`.** With an agent key the dry run needs `agents.manage`; a `403 agent_management_not_permitted` is reported as such and the compile is still complete.

### Step 4: Report

Print:

```
compile-view <fleet> @ <sha> → build/<fleet>.system.yaml (<n> agents, permissions: explicit|none) + build/<fleet>.apply.json
  sidecar: <g> grants · <m> gates · <a> assignments · <c> credential names · <e> edges outside manifest
  warnings: <list or none>
  dry run: deployed|partial|invalid|skipped (<reason>)
```

No Trinity report — this is a build step; `/reconcile-fleet` reports.

## Completion checklist

- [ ] View validated by the compiler before writing anything.
- [ ] Manifest carries only `name`, `description`, `agents{template, kind}`, `permissions` — no invented or dropped-by-the-platform keys.
- [ ] `@ref` left inside `template`; every agent a source key under `permissions.explicit`, or `preset: none`.
- [ ] Every warning printed, `name_prefix_mismatch` especially.
- [ ] `deploy_system` called only with `dry_run: true`, and only when MCP is available.
- [ ] Nothing committed: `build/` is a gitignored artifact.

## Error recovery

| Situation | Action |
|---|---|
| View missing / fails validation | Stop; print the validator's lines; nothing written. |
| `tandem-blueprint` clone refused | Stop; the compiler lives there — say so and name the repo. |
| Trinity MCP unavailable | Compile completes; dry run `skipped (no MCP)`. |
| `deploy_system` dry run → `403 agent_management_not_permitted` | Report; compile complete; the grant is a person's to give. |
| Dry run `invalid` | Print `failed[]` verbatim; the artifact stays for inspection; fix is in the view (a person) or the platform. |

## Self-improvement

Tactical only, and only in step with the platform: when `SystemManifest` gains a field the view binds, the mapping table and `tools/compile_view.py` change together, with the platform file and sha cited. Edit the authoring source (`tandem-blueprint/skills/compile-view/`), bump `metadata.version`, prepend a changelog entry.
