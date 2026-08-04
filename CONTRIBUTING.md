# Contributing to trinity-skills

This is the **public community skills library** for [Trinity](https://github.com/Abilityai/trinity) agents. Trinity instances sync it as their bundled default skills-library source; operators browse it in the Skills tab and assign skills to agents, and the platform injects them. Every skill also works in a plain Claude Code session — copy its directory into an agent's `.claude/skills/`.

This document is the human-readable contract. **`tools/validate.py` is the executable one** — CI runs it on every push and PR, plus a parity check with the Trinity platform's own frontmatter parser (pinned). A validator FAIL is a blocker, never an advisory.

## Trust model — merged ≠ shipped

Instances pin this repo **to a release tag**, never a branch head:

- A merged PR reaches **no instance** until a maintainer cuts the next `v*` tag. If your merged change isn't live for a few days, that is the design, not a bug.
- Trinity **hard-fails a tag that moved** — republishing different bytes under an existing tag breaks every instance's sync. Tags are immutable here.
- Revocation of a bad or compromised skill = cut a new tag without it. That new tag is the fleet-wide fix.

## Layout & naming

- **Flat, always**: `.claude/skills/<name>/SKILL.md`. The platform's sync walks exactly one level — nested directories are invisible. Not configurable.
- Names: lowercase kebab-case, `^[a-z0-9][a-z0-9-]{0,63}$`, named the way they're invoked (`/one-pager`).
- **No version suffixes** (`-v2`) — the name is the invocation surface and the platform's assignment key. Versioning lives in frontmatter and tags (below). A rewrite that changes what a skill fundamentally *is* earns a new descriptive name, and the old skill retires via `deprecated:`.
- Family prefixes only for real families (e.g. `add-*` = agent-capability installers). No artificial taxonomy prefixes.

## Categories

Every skill declares `category:` from this enum (CI-enforced):

| Category | Meaning |
|---|---|
| `agent-development` | Skills that build or extend agents and fleets |
| `visual-communication` | Documents, decks, pages, diagrams, images |
| `documents-and-data` | Extraction, indexing, transformation of files and data |
| `research-and-analysis` | Gathering and judging external information |
| `workspace` | Git, hygiene, self-diagnostics, skill authoring |

Extending the enum is a PR to this file **and** `tools/validate.py` together.

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
- Unknown keys are tolerated by the platform parser, but don't invent fields — propose them here first.

## Credentials

1. **Env vars are the only credential interface.** Skills read named env keys — never credential files, never interactive auth (`gcloud auth login`, browser OAuth); the consuming agent may be headless. If a tool demands a credential *file*, materialize it from the env var at runtime.
2. **One canonical key name per provider**, library-wide:

   | Provider | Canonical key |
   |---|---|
   | GitHub | `GITHUB_TOKEN` |
   | Google Gemini | `GEMINI_API_KEY` (skills may fall back to `GOOGLE_API_KEY`, but declare the canonical) |
   | Replicate | `REPLICATE_API_TOKEN` |

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
