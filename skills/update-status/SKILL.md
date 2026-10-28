---
name: update-status
description: Keep the agent's STATUS.md current — its own judgment of what it is in the middle of (now, open loops, next), rewritten in place under a size cap and imported into CLAUDE.md so every new session starts in context. Run at the end of any run that changed something the next run should know; `init` sets it up once.
category: workspace
user-invocable: true
argument-hint: "[init]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
requires:
  binaries: [git]
metadata:
  version: "1.0"
  changelog:
    - "1.0: Authored in trinity-skills (2026-10-08) — STATUS.md as the agent's carried-forward judgment; run history deliberately left to the platform"
---

# Update Status

`STATUS.md` is the agent's note to its next self: **what I am in the middle of**. It is short, it is rewritten in place, and CLAUDE.md imports it, so every session (chat, scheduled run, or a call from another agent) starts already knowing it.

## What belongs in it, and what doesn't

The file carries **judgment only the agent can write**: what it is working on, which loops are open and what each one waits on, and what should happen next.

It does **not** carry:

| Not here | Why | Where it lives instead |
|---|---|---|
| Run history: when it ran, outcomes, failures | The platform records every run, and on Trinity the agent can read its runs back; a copy here only goes stale | The platform's execution record |
| Logs, transcripts, tool output | Noise. It crowds out the judgment | Nowhere, or a dated file under the agent's own working folders |
| Anything already recorded elsewhere (an issue, a commit, a report) | Two copies drift | Link to it: one line and the reference |
| Facts about specific people | Status is read on every session, including ones other people start | The platform's per-user memory, where it exists |
| Secrets, tokens, credentials | Never | Credentials |

## When to run it

- **At the end of a run that changed something the next run should know:** work started or finished, a loop opened or closed, a decision made, a plan changed.
- **Not** after a pure question-and-answer turn, a read-only lookup, or a run that found nothing to do. An untouched status is a correct status.
- On a schedule it is cheap enough to end every working run with it. Put the call in the playbook that does the work (its last step reads "run `/update-status`"), not in the schedule message.

## Modes

| Invocation | Does |
|---|---|
| `/update-status` | Rewrite `STATUS.md` from this session (the default) |
| `/update-status init` | One-time setup: create `STATUS.md` and add the import and the run rule to `CLAUDE.md`. Idempotent |

Neither mode asks questions. Both are safe to call as one line from a schedule or another agent.

---

## Mode: default (update)

### Step 1: Only the main workspace writes

Parallel jobs of one agent each run in their own git worktree. If every job rewrote `STATUS.md`, they would overwrite each other. So only the main workspace writes the file:

```bash
GIT_DIR=$(git rev-parse --git-dir 2>/dev/null)
COMMON_DIR=$(git rev-parse --git-common-dir 2>/dev/null)
if [ -n "$GIT_DIR" ] && [ "$GIT_DIR" != "$COMMON_DIR" ]; then
  echo "LINKED_WORKTREE"   # a job worktree: do not write
fi
```

In a linked worktree, **stop**: say in the run's result that status was not updated because this job ran in a worktree, and name the one or two lines the main workspace should pick up. Outside git, carry on.

### Step 2: Read the current file

Read `STATUS.md` at the workspace root. If it is missing, start from the template below (and suggest `/update-status init` once in the result, so the file gets imported).

### Step 3: Reconcile, don't append

Go through what this session did and fold it into the file. Each line ends up in exactly one of three states:

- **Open loop, closed this session:** move it to *Recently settled* with today's date and one clause on how it ended.
- **Open loop, still open:** keep it and refresh what it waits on. Keep its `since` date; that date is how a stuck loop becomes visible.
- **New loop:** add it with today's date and what it waits on (a person, an agent, an event, a date, or "me").

Then rewrite *Now* and *Next* from scratch for where things actually stand. They are a snapshot, not a log.

Every open loop names **what it waits on**. A loop that waits on nothing is either done or is a *Next* item.

### Step 4: Enforce the caps

| Section | Cap |
|---|---|
| Now | 5 bullets |
| Open loops | 10 bullets |
| Next | 5 bullets |
| Recently settled | 5 bullets, none older than 7 days |
| Whole file | 60 lines |

Over a cap: drop settled items first (oldest first), then merge related loops into one. A loop older than 30 days gets one decision: keep it with a reason, or close it as dropped. Never truncate silently mid-list.

### Step 5: Write it

Rewrite the whole file in this shape:

```markdown
# Status

updated: 2026-10-08T14:20Z

## Now
- <what the agent is working on, one line each>

## Open loops
- <loop> — waits on <who/what> — since 2026-10-02

## Next
- <the next thing to do, in order>

## Recently settled
- 2026-10-07 <loop> — <how it ended>
```

Use the current UTC time for `updated:`. Use plain words: the reader is the agent's next session, possibly on a different model, with none of this session's context.

### Step 6: Leave committing to the agent's normal flow

Don't commit just for this file. If the agent commits its work at the end of the run, `STATUS.md` goes in with it. If the run commits nothing else, commit `STATUS.md` alone with the message `status: <one-line gist>`, provided the agent's workspace is a repo it commits to.

### Step 7: Report

One line in the run's result: `Status updated — N open loops (M new, K closed).` If nothing changed, say `Status unchanged.` and don't touch the file.

---

## Mode: init

1. If `STATUS.md` is missing, create it from the template with every section present and the bullets empty. Write `- (none yet)` rather than leaving headings bare.
2. If `CLAUDE.md` has no `@STATUS.md` line, append:

   ```markdown
   ## Status

   @STATUS.md

   At the end of any run that changed something the next run should know, run `/update-status`.
   ```

   If the line is already there, change nothing.
3. Report what was created or added, or `Already set up.`

`init` is the only mode that touches `CLAUDE.md`, and only to add those lines once.

---

## Why a file, and why this shape

- **Imported, not fetched.** `@STATUS.md` in CLAUDE.md puts the file in context at the start of every session with no tool call. A status the agent has to remember to read is a status it skips.
- **Rewritten, not appended.** An appended log grows until it is skimmed and then ignored. A capped snapshot stays readable on every session.
- **Judgment here, history on the platform.** What happened can be recorded mechanically, so the platform records it. What it means and what comes next can't, so the agent writes it.
