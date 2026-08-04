# trinity-skills

The **public community skills library** for [Trinity](https://github.com/Abilityai/trinity) agents — the default skills-library source a Trinity instance syncs out of the box.

Each skill is a directory under `.claude/skills/<name>/` with a `SKILL.md` carrying the library's frontmatter contract. Trinity instances sync this repo pinned to a release tag, surface it in the Skills tab, and inject assigned skills into agents. Every skill also works in a plain Claude Code session — copy its directory into your agent's `.claude/skills/`.

**Status: seeding.** The v1 catalog (22 skills across 5 categories) is being promoted in from its authoring sources. The first release tag (`v0.1.0`) will be cut when the seed lands — until a `v*` tag exists, instances cannot pin this repo as a source.

## Skills

<!-- INDEX:BEGIN -->
### agent-development

| Skill | Version | Origin | Description |
|---|---|---|---|
| `add-backlog` | 2.0 | mirrored · abilities | Add GitHub Issues backlog workflow to any agent — creates the full development cycle (backlog, claim, close, groom, roadmap, autoplan, commi |
| `add-canon` | 1.4 | mirrored · abilities | Give any agent a shared canonical-data layer — installs /canon-publish (commit this agent's own folder in the fleet's shared canon repo), /c |
| `add-git-sync` | 1.0 | mirrored · abilities | Add git-as-state hooks to an agent — auto-commits on Stop, rebases on SessionStart, snapshots on PreCompact |
| `add-memory` | 1.1 | mirrored · abilities | Add a memory system to an agent — file awareness, knowledge graph, structured state, or multi-session tracking |
| `add-orchestrator` | 1.15 | mirrored · abilities | Make any agent a system-aware orchestrator — installs /discover-agents (discover the fleet from live Trinity and/or a repo list into a descr |
| `add-pipeline` | 1.5 | mirrored · abilities | Scaffold a Trinity-compatible long-running pipeline inside any agent — creates projects/&lt;slug&gt;/{project.md, pipeline.yaml, instances/} |
| `add-project-management` | 1.1 | mirrored · abilities | Install cross-actor project management into this agent — GitHub Issues as single source of truth, uniform task anatomy with approval-ready c |
| `adjust-playbook` | 1.9 | mirrored · abilities | Modify an existing playbook based on conversation context or explicit instructions |
| `agent-fleet-analysis` | 2.3 | mirrored · abilities | Scan one or more directories of agents in ANY paradigm — Claude Code, n8n workflow exports, framework apps (LangChain/CrewAI/AutoGen), or fr |
| `agent-fleet-migrate` | 1.0 | mirrored · abilities | Build a verified Claude Code fleet from an agent-fleet-analysis work order — non-destructive migration of mixed fleets (Claude Code, n8n exp |
| `create-playbook` | 2.13 | mirrored · abilities | Create a new skill or playbook |
| `validate-pipeline` | 1.2 | mirrored · abilities | Lint a pipeline.yaml — schema check, DAG acyclicity, referenced-skill existence, precondition kind registration |

### documents-and-data

| Skill | Version | Origin | Description |
|---|---|---|---|
| `document-extractor` | 1.0 | library | Extracts key information from documents (PDFs, images, text files) in a folder and creates structured markdown summaries with the same filen |
| `epub-chapter-extractor` | 1.0 | library | Extract all chapters from an EPUB file into separate markdown files |
| `file-indexer` | 1.0 | library | Generate a comprehensive file system index with directory tree, file sizes, and modification dates |

### research-and-analysis

| Skill | Version | Origin | Description |
|---|---|---|---|
| `gemini-critic` | 1.3 | library | Ask Gemini's most powerful model for an independent second opinion - critique code with fresh eyes, evaluate an article, challenge a plan |
| `repo-velocity` | 1.5 | library | Measure the development speed / velocity / activity of any GitHub repository using objective metrics from the GitHub API — commits, lines ad |

### visual-communication

| Skill | Version | Origin | Description |
|---|---|---|---|
| `create-explanatory-image` | 1.1 | library | Generate explanatory diagrams and infographics that visually communicate concepts |
| `nano-banana-image-generator` | 1.0 | library | Generate images using Google's Nano Banana 2 (Gemini 3.1 Flash Image Preview) |

### workspace

| Skill | Version | Origin | Description |
|---|---|---|---|
| `commit` | 1.0 | library | Create a meaningful git commit to checkpoint current agent state |
| `self-diagnostic` | 1.0 | library | Run self-diagnostics on the agent to verify skills, commands, agents, and dependencies are working |
| `skill-builder` | 1.0 | library | Expert guide for creating Claude Code skills |
| `workspace-discipline` | 1.0 | library | Enforce workspace organization rules when creating files, writing documents, or generating assets |
<!-- INDEX:END -->

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) — the conventions (layout, naming, categories, versioning, credentials), the trust model (merged ≠ shipped: releases are tags), and the review bar. `tools/validate.py` is the executable form of the contract; CI runs it on every push and PR.

## License

[Apache-2.0](LICENSE)
