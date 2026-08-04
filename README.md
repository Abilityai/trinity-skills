# trinity-skills

The **public community skills library** for [Trinity](https://github.com/Abilityai/trinity) agents — the default skills-library source a Trinity instance syncs out of the box.

Each skill is a directory under `.claude/skills/<name>/` with a `SKILL.md` carrying the library's frontmatter contract. Trinity instances sync this repo pinned to a release tag, surface it in the Skills tab, and inject assigned skills into agents. Every skill also works in a plain Claude Code session — copy its directory into your agent's `.claude/skills/`.

**Status: seeding.** The v1 catalog (22 skills across 5 categories) is being promoted in from its authoring sources. The first release tag (`v0.1.0`) will be cut when the seed lands — until a `v*` tag exists, instances cannot pin this repo as a source.

## Skills

<!-- INDEX:BEGIN -->
_No skills yet — seeding in progress._
<!-- INDEX:END -->

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) — the conventions (layout, naming, categories, versioning, credentials), the trust model (merged ≠ shipped: releases are tags), and the review bar. `tools/validate.py` is the executable form of the contract; CI runs it on every push and PR.

## License

[Apache-2.0](LICENSE)
