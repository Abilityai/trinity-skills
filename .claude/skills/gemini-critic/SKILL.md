---
name: gemini-critic
description: Ask Gemini's most powerful model for an independent second opinion - critique code with fresh eyes, evaluate an article, challenge a plan. The calling agent controls the exact question and material; this skill just executes the call and returns Gemini's answer verbatim.
allowed-tools: Read, Glob, Bash, Write, mcp__aistudio__generate_content
user-invocable: true
argument-hint: "<question or critique instruction> [file paths...] [model=<gemini-model>]"
requires:
  env: [GEMINI_API_KEY]
  binaries: [python3]
metadata:
  version: "1.3"
  created: 2026-07-27
  updated: 2026-08-04
  author: Ability.ai
  changelog:
    - "1.3: Library port — env-only credentials (key-file fallback removed), requires: contract declared"
    - "1.2: Default model -> gemini-pro-latest (alias auto-tracking Google's newest flagship pro; resolved to gemini-3.1-pro-preview as of 2026-07-27 - 2.5-pro was two generations stale); verified thinkingBudget -1 works on 3.1-pro"
    - "1.1: Self-contained - bundled scripts/ask_gemini.py calls the Gemini REST API directly using the local gemini_api_key file (chmod 600, sourced from Corbin's aistudio MCP config); script is now the primary transport, MCP the fallback; smoke-tested end-to-end"
    - "1.0: Initial version - thin executor: caller-framed question + material -> Gemini flagship (default gemini-2.5-pro, unlimited thinking) -> verbatim reply, no editorializing"
category: research-and-analysis
---

# Gemini Critic

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change - the top entry of `metadata.changelog` above - e.g. `gemini-critic vX.Y — recent: <summary>`. Then proceed.

## Purpose

Get a genuinely independent second opinion from a different frontier model. The caller (Eugene or another agent/skill) decides what to ask and what material to send - review this diff, tear apart this article, find holes in this plan. This skill is a **pure executor**: assemble the payload, call Gemini, return the answer verbatim. It never answers the question itself, never softens or summarizes the critique, and never acts on the critique's suggestions.

## State Dependencies

| Source | Location | Read | Write |
|--------|----------|------|-------|
| Gemini API (primary) | bundled `scripts/ask_gemini.py` (direct REST call) | - | sends prompt + material |
| API key | `GEMINI_API_KEY` env var | yes | never |
| Gemini API (fallback) | `mcp__aistudio__generate_content` MCP tool, if connected | - | sends prompt + material |
| Input material | file paths supplied by the caller | yes | never |

The skill is **self-contained**: the bundled script + key file work in any project on this machine, with no MCP server configured. Only transient prompt files are written (to the session scratchpad). No state persists between invocations.

## The Executor Contract

These rules are what make the second opinion worth having - breaking them defeats the skill's purpose:

1. **The caller's framing wins.** Send the caller's question/instruction as given. Do not rephrase it, add your own concerns to it, or narrow its scope.
2. **Return the answer verbatim.** No summarizing, no filtering, no "Gemini mostly agrees with me". The calling agent judges the critique, not you.
3. **Do not act on the critique.** No edits, no fixes, no follow-up calls. Deliver the answer; your job ends there.
4. **Fail loud, never degrade silently.** If the MCP tool is unavailable, a file is missing, or the material is too large - stop and say exactly what's wrong. Never send a partial payload without flagging it.

## Process

### Step 1: Parse the request

From the arguments (or the calling context), extract:
- **The question/instruction** - required. If genuinely absent, stop and ask what to send.
- **Material** - file paths, globs, or inline text. Optional (pure questions are fine).
- **Model override** - a `model=...` token. Default: `gemini-pro-latest` (an alias that always resolves to Google's newest flagship pro model - never pin a versioned model as default; if the caller names a specific model, trust them and pass it through).
- **Optional flags the caller may request in plain words:** grounding via Google Search ("check against current sources"), a temperature, or a custom system prompt.

### Step 2: Assemble the material

- **Text and source code** (any code file, .md, .txt, config, diffs): Read each file and inline it into the `user_prompt` inside fenced blocks, each labeled with its path. This is MIME-independent and most reliable for code. Preserve content exactly.
- **Binary/media** (PDF, images, video, audio): pass as attachments in Step 3 (script `--file`, or MCP `files` on the fallback path); MIME auto-detected from extension.
- **Globs**: expand with Glob, then treat as above.
- **Missing paths**: stop and list them - do not send a payload the caller didn't intend.
- **Size guard**: if inlined text exceeds ~500K characters, stop and report the total with a per-file breakdown so the caller can narrow the selection. Never truncate silently.

### Step 3: Call Gemini (bundled script - primary transport)

Write the assembled prompt (question + inlined material) to a temp file in the session scratchpad, then run:

```bash
python3 ~/.claude/skills/gemini-critic/scripts/ask_gemini.py \
  --prompt-file <scratchpad>/gemini_prompt.md \
  [--system-file <scratchpad>/gemini_system.md] \
  [--model <override>] [--search] [--temperature T] \
  [--file <binary/media path>]...
```

- **Model**: script defaults to `gemini-pro-latest` (auto-tracks the newest flagship pro); pass `--model` only on caller override. Never pass `--thinking-budget 0` - pro-tier models require thinking mode, and the default `-1` = unlimited/dynamic thinking is the point of this skill.
- **System prompt**: if the caller supplied framing (persona, rubric, role), write theirs exactly to the system file. Only if they gave a bare ask like "look at this with fresh eyes" use the default critic prompt:
  > You are an independent expert reviewer seeing this material for the first time. Be candid and specific. Lead with the most serious problems, ranked by severity. Point to exact locations. Say what is genuinely good only where it's load-bearing. No flattery, no hedging.
- `--search`: only if the caller asked for grounding/fact-checking.
- `--temperature`: only if the caller specified one.
- **Binary/media** (PDF, images, audio, video): pass each via `--file` (inline limit ~20MB total).

The script resolves the key itself from the `GEMINI_API_KEY` env var - never inline the key in the command.

If the call fails transiently (timeout, 5xx), retry once. If it fails again, report the exact error. **Fallback**: if `python3` or the script is unavailable but the `aistudio` MCP is connected, call `mcp__aistudio__generate_content` with the same prompt/system/model and `thinking_budget: -1`.

### Step 4: Return the answer

Output exactly:
1. One header line: model used, what was sent (file count/names or "question only"), and whether search grounding was on.
2. Gemini's response, verbatim and clearly delimited.

Nothing else - no commentary, no agreement/disagreement, no action items. If the calling agent wants your view afterward, that's its next question, outside this skill.

## Outputs

- Gemini's verbatim response with a one-line provenance header, returned inline to the caller.
- Nothing persistent written to disk (prompt temp files go to the session scratchpad).

## Error Recovery

| Failure | Action |
|---------|--------|
| Key missing (script exits) | Stop. Report: `GEMINI_API_KEY` not set — add it to this agent's credentials. Do not hunt for keys elsewhere. |
| Script fails AND `aistudio` MCP not connected | Stop. Report both failures (user can check `/mcp`). Do not invent alternate access paths. |
| File path missing / unreadable | Stop. List the exact paths that failed. |
| Payload too large | Stop. Report total size + per-file breakdown; let the caller narrow. |
| API error after one retry | Stop. Report the exact error message and the model requested. |
