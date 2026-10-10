# Contributing to trinity-skills

This is the **public community skills library** for [Trinity](https://github.com/Abilityai/trinity) agents. Trinity instances sync it as their bundled default skills-library source; operators browse it in the Skills tab and assign skills to agents, and the platform injects them. Every skill also works in a plain Claude Code session — copy its directory into an agent's `.claude/skills/`.

This document is the human-readable contract. **`tools/validate.py` is the executable one** — CI runs it on every push and PR, plus a parity check with the Trinity platform's own frontmatter parser (pinned). A validator FAIL is a blocker, never an advisory.

## Trust model — merged ≠ shipped

Instances pin this repo **to a release tag**, never a branch head:

- A merged PR reaches **no instance** until a maintainer cuts the next `v*` tag. If your merged change isn't live for a few days, that is the design, not a bug.
- Trinity **hard-fails a tag that moved** — republishing different bytes under an existing tag breaks every instance's sync. Tags are immutable here.
- Revocation of a bad or compromised skill = cut a new tag without it. That new tag is the fleet-wide fix.

## Layout & naming

- **Flat, always**: `skills/<name>/SKILL.md`. The platform's sync walks exactly one level — nested directories are invisible. The root is declared in `catalog.yaml` (`skills_root:`); Trinity resolves it per source (probe order `catalog.yaml` → `skills/` → `.claude/skills/`, trinity-enterprise#332).
- Names: lowercase kebab-case, `^[a-z0-9][a-z0-9-]{0,63}$`, named the way they're invoked (`/one-pager`).
- **No version suffixes** (`-v2`) — the name is the invocation surface and the platform's assignment key. Versioning lives in frontmatter and tags (below). A rewrite that changes what a skill fundamentally *is* earns a new descriptive name, and the old skill retires via `deprecated:`.
- Family prefixes only for real families (e.g. `project-*` = the project-management set). No artificial taxonomy prefixes.
- **Runtime skills, not installers.** A library entry is something an agent is *assigned* and *runs*; the platform re-injects it whenever the library updates, so the agent never holds a stale copy. Installers that write copies of skills into an agent's repo (`add-*` wizards) are marketplace tooling — they retire from here via `deprecated:`, and the skills they used to embed are promoted individually. Per-agent configuration a skill needs (e.g. `PROJECT_STANDARD.md`) belongs in the agent's repo; the skill ships its template and self-heals a missing file on first run.

## Library or agent skill? — the rubric

Before proposing a skill here, ask one question:

> **Would you want this skill, unchanged, in another company tomorrow?**

- **Yes → it belongs in this library.** It is a procedure: how to build a deck, reconcile a backlog, brief a person. It holds no company's facts, names no company's systems beyond the credential keys it declares, and is equally correct for any fleet that assigns it.
- **No → it is an agent skill.** It encodes one organisation's facts, thresholds, pipeline, tone or people. It lives in that agent's own `.claude/skills/`, and the facts it leans on belong in that fleet's canon (see `canon:` below), not in a SKILL.md.
- **Mixed → split it.** The generic procedure comes here; the company-specific configuration stays in the agent's repo and is read at run time (the per-agent configuration rule under *Layout & naming*). A skill that needs a company's facts to be correct reads them; it never embeds them.

When a skill improves, the rubric decides where the change lands. A fix that would be the same in every company is a PR here, so it reaches every agent that carries the skill. A fix that only holds for one company's conditions stays in that agent.

## Categories

Every skill declares `category:` from this enum (CI-enforced):

| Category | Meaning |
|---|---|
| `agent-development` | Skills that build or extend agents and fleets |
| `visual-communication` | Documents, decks, pages, diagrams, images |
| `documents-and-data` | Extraction, indexing, transformation of files and data |
| `research-and-analysis` | Gathering and judging external information |
| `workspace` | Git, hygiene, self-diagnostics, skill authoring |
| `project-management` | Backlogs, task registries and the project lifecycle — GitHub Issues as the shared ledger |

The enum lives in `catalog.yaml` (`categories:`) — the validator reads it from there. Extending it is a PR to `catalog.yaml` and this file together.

## Frontmatter contract

```yaml
---
name: repo-velocity                     # must equal the directory name
description: Measure the development velocity of any GitHub repository using objective metrics — commits, merged-PR throughput, contributors, time-to-merge, release cadence.
category: research-and-analysis
user-invocable: true
requires:                               # EXHAUSTIVE — everything the skill reads
  env: [GITHUB_TOKEN]
  binaries: [git]
metadata:
  version: "1.0"                        # per-skill semver, bump on every change
  changelog:                            # newest-first
    - "1.0: Promoted from user-level skill"
---
```

Rules:

- `description` ≥ 40 chars — it is the browse surface and the model's selection signal.
- `requires:` is **exhaustive and honest**. CI cross-checks every env name referenced in the skill's body and scripts against `requires.env` — both directions: an undeclared reference fails, and a declared-but-unused key fails. The platform probes these keys at injection and warns the agent when one is missing, so an undeclared key is a silent runtime failure.
- Optional lifecycle keys: `deprecated: true` and `superseded-by: <name>` — how a skill retires. Deprecated skills are removed at the next major tag.
- Mirrored skills carry `metadata.mirror: "abilities@<sha> <path>"` (see below).
- **`canon:` — the shared truth a skill reads.** A skill that reads a fleet's canon (the shared canonical-data repo: roles, objectives, the domain map and the facts each agent publishes) declares exactly which domains it needs, by their ids in the canon's `domains.yaml`:

  ```yaml
  canon: [org-context, icp-model]
  ```

  It is a declaration of need, not a permission — the canon is readable by every agent in the fleet — so context loading is explicit and reviewable instead of discovered at run time. Omit the key when the skill reads no canon. The validator checks the shape only (a non-empty list of lowercase kebab-case ids, no duplicates); whether a domain exists is the consuming fleet's canon, which this repo cannot see.

  **Parser note:** `canon:` is not part of the Trinity platform's skill contract. The platform's frontmatter parser (`skill_packaging.extract_contract`) is tolerant and ignores keys it does not know, which is what makes this field free today. If that parser is ever made strict, it would reject every skill carrying `canon:` — so a strict parser must allowlist `canon` first. CI's platform-parity step (below) is where that break would surface.
- Unknown keys are tolerated by the platform parser, but don't invent fields — propose them here first.
- **Callable as one line.** A library skill may be invoked by a schedule, an orchestrator, or another agent as a single `/name [args]` message (the fleet's playbook-call convention). It must therefore run correctly from that one line: declare its inputs in `argument-hint`, and if it has approval gates, declare and implement a headless mode (`--autonomous`) — a gated skill invoked unattended blocks on a prompt nobody sees. The SKILL.md is the contract; no input/output schema is required.

### No bare dollar-digit in a skill body

The runtime fills `$0`, `$1`, `$2` … anywhere in a `SKILL.md` body — code blocks included — with the words the skill was invoked with. A skill called with arguments therefore runs with `awk '{print $2}'` or a shell function's `"$1"` silently rewritten. The validator fails any bare dollar-digit in the body (rule `arg-substitution`). Write shell positionals as `${1}`, awk fields as `$(2)`, the intended argument placeholder as `$ARGUMENTS` / `$ARGUMENTS[0]`, and prices as `USD 0.07`. Frontmatter is not substituted and is not checked.

## Credentials

1. **Env vars are the only credential interface.** Skills read named env keys — never credential files, never interactive auth (`gcloud auth login`, browser OAuth); the consuming agent may be headless. If a tool demands a credential *file*, materialize it from the env var at runtime.
2. **One canonical key name per provider**, library-wide:

   | Provider | Canonical key |
   |---|---|
   | GitHub | `GITHUB_TOKEN` |
   | Google Gemini | `GEMINI_API_KEY` (skills may fall back to `GOOGLE_API_KEY`, but declare the canonical) |
   | Replicate | `REPLICATE_API_TOKEN` |
   | ElevenLabs | `ELEVENLABS_API_KEY` |
   | Vercel | `VERCEL_TOKEN` |

   A PR introducing a new provider adds its canonical key to this table in the same PR.
3. **Secrets only in env; config in files.** Non-secret configuration (account IDs, defaults) may ship as a config file inside the skill.
4. **Declared cold-start behavior.** A missing key is an injection *warning*, not a block — so every skill with `requires.env` must state in its SKILL.md what happens without the key: fail fast naming the exact key ("`GITHUB_TOKEN` not set — add it to this agent's credentials"), or degrade gracefully.

## Versioning & releases

- **Per skill**: `metadata.version` (semver) + newest-first `metadata.changelog`, bumped on every change. The platform's machine-level version is the git tree SHA; this is the human layer.
- **Per catalog**: `v<major>.<minor>.<patch>` tags. Breaking changes — a removed or renamed skill, a new required env key, a changed output contract — require at least a minor bump and a release-notes line. Patch tags are for fixes that change no skill's contract.
- Tags are cut deliberately by a maintainer, never by automation.

## Mirrored skills

Some skills are **authored in the [abilities](https://github.com/Abilityai/abilities) plugin marketplace** and mirrored here (they carry `metadata.mirror`). For those:

- **Do not PR changes to the mirrored copy here** — it is generated. PR the change to `abilities` instead; the mirror is refreshed from there (currently via the trinity-pm agent's promote/refresh pipeline), and a hand-edit would be overwritten by the next refresh.
- Skills without `metadata.mirror` are authored here — PR them directly.

## Review bar

- CI green (`tools/validate.py --all` + platform-parser parity + README index freshness) — a FAIL blocks merge.
- Review required via CODEOWNERS.
- Public-repo hygiene: no credentials, no internal URLs, no customer data. GitHub secret scanning is enabled; the validator additionally greps for secret-shaped literals.
- Byte caps (platform injection limits): ≤ 10 MiB per skill, ≤ 50 MiB library total, frontmatter ≤ 64 KiB.

## Regenerating the index

```bash
python3 tools/validate.py --write-readme
```

Run it in the same commit as any skill change — CI fails a stale index.
