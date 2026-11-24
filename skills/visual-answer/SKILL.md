---
name: visual-answer
description: "The everyday habit of showing instead of telling. When an answer explains how something works or describes data, pick the visual form that fits the content (steps, a line over time, sorted bars, a table, boxes and links, states), build it on the surface the reader is on (plain text, a page, a canvas), and check it against five rules before sending. No gate, no image cost, no keys. Use it inside any reply or report; for a finished deliverable hand over to /explain-visually, /one-pager, /microsite or /presentation."
category: visual-communication
automation: autonomous
user-invocable: true
argument-hint: "<what to explain, or the data to describe>"
allowed-tools: Read, Write, Edit, Glob, Grep
metadata:
  version: "1.0"
  changelog:
    - "1.0: Authored in trinity-skills (2026-11-24) - form selection by what the content is about, surface selection, build rules, a five-check review. Built and scored by a skill-up run: ten fixed requests answered with and without it, judged blind by a second model. It takes effect only when the agent's own instructions name it (loaded in 8 of 10 runs) or it is called by name; installed alone it loaded in 1 of 10"
---

# Visual Answer

Most answers that explain something or describe numbers are easier to take in when part of
them is shown. This skill is the habit of doing that well in ordinary work: a reply in a chat,
a status report, a note to a person. It needs no keys and asks no questions.

**Usage:** `/visual-answer <what to explain, or the data>`, or simply follow it whenever a
reply you are writing explains a mechanism or describes data.

**Make it a habit, not an option.** An agent that merely has this skill installed rarely
reaches for it. Put one line in the agent's own instructions: "When an answer explains how
something works or describes data, load and follow the visual-answer skill before writing
it."

It is not a deliverable builder. When the person asked for a finished artefact (a brief, a
deck, a page to share), use the skill made for that: `/explain-visually`, `/one-pager`,
`/presentation`, `/microsite`. Where one of those is not installed, follow this skill and say
which one would have done more.

## Step 1 - Decide whether to show anything

Show when the content has **shape**: an order, a branch, a comparison, a change over time,
parts and links, proportions, a spread.

Say it in a sentence when it has none: one fact, a yes or no, two numbers, three items or
fewer. A chart of two numbers is worse than the sentence "A is twice B".

## Step 2 - Write the one message first

Before choosing a form, write the single sentence the reader should leave with: "Sign-ups rose
by half during the campaign and fell back to a slightly higher base." It decides everything else: what to show, what to highlight, what to leave out.

**That sentence is the first line of the answer, alone, before any heading or visual.** One
sentence, not two or three joined together. A reader who stops there has the answer.

If you cannot write it, you are not ready to draw. If there are two messages, make two small
visuals, each with its own.

## Step 3 - Pick the form from what the content is about

| The content is about | Show it as | Notes |
|---|---|---|
| Steps in order, with decisions or loops | flowchart | one path highlighted if there is a normal case |
| Who does what, in turn, between actors | sequence (actors across, time down) | not a flowchart: the actors matter |
| Events over dates or eras | timeline | |
| Parts of a system and how they connect | boxes and links | group by layer; arrows mean one thing only |
| States and what moves between them | state diagram | name every transition |
| Kinds and sub-kinds, or an idea's parts | tree or outline | |
| How one thing changed over time | line; in plain text, one bar per period in time order | time left to right or top to bottom; mark the event that explains the change |
| Sizes across categories | horizontal bars, sorted largest first | not sorted only when the order itself means something |
| Parts of one whole | one stacked bar, or sorted bars with shares | a pie only for two or three parts |
| How values are spread | histogram or dot strip | mark the target or the typical value; name the outliers |
| Two measures for each item | scatter, each point labelled | draw the threshold as a line when there is one |
| One number against a goal | the number, large, with the goal beside it | |
| Options against several criteria | table, options as rows | mark the cells that decide the choice |
| Exact values someone will look up | table | |
| An idea with no structure or numbers | a plain analogy, then a two-column contrast | no diagram for its own sake |

Two tie-breakers. If people will read exact values, use a table; if they will read a pattern,
use a chart. If the content has both structure and numbers, show the structure and write the
numbers on it.

## Step 4 - Pick the surface the reader is on

- **Plain text (a chat reply, a terminal, a message).** Use what plain text does well: a
  short table, a numbered list for steps, a small box-and-arrow diagram in a code block, bars
  drawn with block characters next to their values. Keep any line under about 70 characters.
  Use a Mermaid block only where you know the surface renders it.
- **A page or a file the reader opens.** Write one self-contained HTML file with inline SVG:
  no external scripts, text as real text, colours as CSS variables so light and dark both
  work, readable at phone width.
- **A canvas or artifact surface your platform gives you.** Use it, in its own block
  vocabulary, in place of a file.

Always give the message and the key numbers in text as well. A reader who cannot open the
visual should still get the point, and so should another agent that reads your answer: a
model reading a chart is misled by it more easily than by the numbers themselves.

**Do not dump rows.** A table over about eight rows or four columns does not go into a reply.
Show the rows that carry the message, say how many more there are, and put the full table in a
file.

## Step 5 - Build it

- **Every visual and every table has a title, and the title is its point as a full
  sentence**, not its topic: "Two requests in thirty missed the target", not "Response times";
  "Tests and one review stand between a change and the main branch", not "The path at a
  glance". If you cannot title it that way, it has no point yet.
- **About twelve elements or fewer** (boxes, bars, points, rows). More than that: group, split
  into two visuals, or cut to what the message needs.
- **Label the marks themselves.** Put the name and value on or beside the bar, line end or
  point. A legend is a last resort; with four series or fewer it is never needed.
- **One accent colour, the rest grey.** The accent goes on what the message is about. Never
  use colour alone to carry meaning.
- **Bars start at zero.** A line may start elsewhere when the axis says so.
- **Units on every number**, rounded to what the reader needs: 1,450 ms, 35%, USD 70k.
- **Labels are plain words, two to five of them.** No internal codes, no abbreviations the
  reader has not seen.
- **Show only what you were given.** Every number, name and link in the visual comes from the
  source. Compute what follows from it (a total, a share, a median) and say that you did.
  Never estimate a missing value to complete a chart; leave the gap and name it.
- **Do not say it twice.** Text beside a visual adds what the visual cannot show (the cause,
  the caveat, what to do). It does not walk through the same values again.
- **Never:** 3D, two different vertical axes, decoration, a chart with no message.

## Step 6 - Check before sending

1. **Right form:** does the form match the row in Step 3, and would a sentence have done?
2. **One message:** is the first line one sentence that carries the answer, and is every
   visual's and table's title a sentence stating its point?
3. **Ten-second read:** can someone get the point in about ten seconds without a legend?
4. **Faithful:** read every number, count and link in the visual back against the source,
   one by one. A visual that looks right is not evidence that it is right: a clean chart hides
   a wrong value better than a sentence does. Recount anything you counted.
5. **Fits the surface:** does it read correctly where it will actually be seen?

Fix what fails. If the visual still does not beat the sentence, send the sentence.

## Outputs

The answer itself, in the reply or the file the caller named. No other files, no state, no
commits.
