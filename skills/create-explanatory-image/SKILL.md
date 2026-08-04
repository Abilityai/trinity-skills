---
name: create-explanatory-image
description: Generate explanatory diagrams and infographics that visually communicate concepts. Iterates autonomously until images are logically correct, text is clean, and the concept explanation is clear. Uses Nano Banana 2 (Gemini 3.1 Flash Image).
automation: gated
allowed-tools: Bash, Read, Write, Glob, AskUserQuestion
user-invocable: true
metadata:
  version: "1.1"
  created: 2026-03-03
  author: Ruby
  changelog:
    - "1.1: Imported explanation principles from /animated-explainer, adapted for static images - truth gate before design, one worked example (prefer a failure), explainer-not-advertisement, mechanism/numbers separation with disclosed scale, locked no-crossing layout, nothing floats, visibly-unfinished parts, labels-first storyboarding; self-critique now checks facts and structure separately from looks"
    - "1.0: Initial version"
category: visual-communication
---

# Create Explanatory Image

## Purpose

Generate explanatory diagrams and infographics that clearly communicate a concept, iterating autonomously until the images are logically correct, text is accurate, and the visual explanation lands.

## Core Principles

Adapted from `/animated-explainer` - what makes an image *explain* rather than decorate.
Apply them at decomposition time (Steps 2-3); the self-critique loop (Step 5) checks them.

1. **The facts are the boss - interrogate before you design.** Decide what's TRUE before
   deciding what's compelling. If the image explains a real system, read its source of
   truth (specs, architecture docs, the actual data) - not marketing copy or published
   summaries. A concept the facts don't support dies at this step; that is the step
   working, not failing. Never soften an unsupported claim into a diagram.

2. **One concrete worked example beats any amount of abstraction.** A diagram that traces
   one real item end to end (this request, this invoice, this forecast) explains more
   than an abstract schema. Prefer a failure case the mechanism catches - it shows the
   machine doing its job and cannot be read as cherry-picking.

3. **Explainer, not advertisement.** Assume the viewer knows nothing. Open on the problem
   the mechanism solves - the title states what's broken or the single insight, not the
   product name. If the image only makes sense to someone who already understands the
   system, it has failed.

4. **Separate the mechanism from the numbers.** Carry the mechanism with symbolic marks;
   put real figures in ONE place (a footer stat, a single callout) or nowhere. If a mark
   is not 1:1 with a thing, say so on the image (`1 dot = ~30 runs`). Never silently mix
   scales. This also serves the 10-label limit.

5. **Lock the layout - nothing crosses anything.** One spine (a left-to-right flow or a
   single loop), elements sitting ON it. Crossing arrows read as *complexity*, not as a
   system. Prompt for it explicitly and reject renders where connections cross or wander.

6. **Nothing floats - every element visibly comes from somewhere.** The static cousin of
   "nothing teleports": causality is carried by explicit arrows and numbered steps
   (input -> transform -> output). An element with no incoming or outgoing connection is
   decoration - cut it or wire it in.

7. **Show the part that doesn't work.** If part of the system is unproven, planned, or
   broken, draw it dashed/hollow/greyed and label it. A diagram where everything works is
   the least trustworthy thing you can draw - the unfinished part is the credibility.

8. **Labels first.** Write every text string before generating anything (Step 2 does
   this) - if the labels alone, read in order, tell the story, the image will work. If
   they don't, no amount of visual polish will save it.

## State Dependencies

| Source | Location | Read | Write | Description |
|--------|----------|------|-------|-------------|
| Best practices | `.claude/skills/nano-banana-image-generator/best_practices.md` | yes | | Prompt engineering constraints and style guide |
| Generate script | `.claude/skills/nano-banana-image-generator/scripts/generate_image.py` | yes | | Image generation API |
| Output folder | User-specified or auto-created | | yes | Final and intermediate images |

## Prerequisites

- `GOOGLE_API_KEY` or `GEMINI_API_KEY` set in `.env`
- Nano Banana image generator scripts available at `.claude/skills/nano-banana-image-generator/scripts/`

## Inputs

- **Concept description**: What the diagram should explain (from user message or arguments)
- **Output folder** (optional): Where to save images. Default: auto-created folder named after the concept in current directory
- **Style** (optional): `dark` (black bg, brand style) or `warm` (charcoal bg, illustrated). Default: `warm`
- **Aspect ratio** (optional): `16:9`, `1:1`, `9:16`. Default: `16:9`
- **Variant count** (optional): How many initial variants. Default: 3

---

## Process

### Step 1: Read Current State

1. Read `.claude/skills/nano-banana-image-generator/best_practices.md`
   - Note complexity limits: **10 boxes max, 10 text labels max, 3 hierarchy levels max**
   - Note known model limitations (misspellings on 4+ syllable words, font inconsistency)

2. Confirm output folder:
   - If user specified a folder, use it
   - Otherwise, create: `[concept_slug]_diagrams/` in current directory
   - `mkdir -p [folder]`

### Step 2: Decompose the Concept

Analyze the user's concept description and break it down:

1. **Truth gate** (Principle 1): If the image describes a real system or carries real
   numbers, verify every claim against the source of truth (specs, docs, actual data) -
   never from memory or marketing copy. Cut anything unsupported and tell the user what
   was cut and why.
2. **Core message**: What single insight should the viewer walk away with? State it as
   the problem or insight, not the product name (Principle 3).
3. **Worked example** (Principle 2): Can the concept be shown as one concrete item traced
   end to end instead of an abstract schema? Prefer it; prefer a failure case the
   mechanism catches.
4. **Visual elements**: List all shapes, icons, nodes, connections needed. Every element
   must be wired into the flow (Principle 6) - an element with no incoming or outgoing
   connection gets cut or connected.
5. **Text labels**: List every text string that will appear in the image - then read them
   in order. If the labels alone tell the story, the image will work; if they don't, fix
   the story before generating anything (Principle 8).
6. **Honest state** (Principle 7): Which parts are live vs planned/unproven/broken? Mark
   the latter to render dashed, hollow, or greyed with a label.
7. **Layout type**: Identify the best diagram type:
   - Framework (central concept + surrounding elements)
   - Before/after comparison
   - Flow/process (horizontal or vertical)
   - Circular loop/cycle
   - Visual metaphor
   - Timeline/evolution
   - Cross-section/exploded view

### Step 3: Simplify for Constraints

**This step is critical.** The concept decomposition will almost always exceed Nano Banana's limits. Simplify ruthlessly:

1. **Count visual elements** - if > 10, merge or remove until <= 10
2. **Count text labels** - if > 10, shorten labels to 1-2 words, replace words with icons, or remove sub-labels
3. **Move numbers out of the mechanism** (Principle 4) - carry the mechanism with symbolic
   marks; keep real figures in ONE place (a footer stat or single callout) or drop them.
   If a mark is not 1:1, spend one label on the scale legend (`1 dot = ~30 runs`).
4. **Check word complexity** - replace any word with 4+ syllables with a simpler alternative:

   | Avoid (misspells) | Use Instead |
   |-------------------|-------------|
   | SOVEREIGNTY | OWN SPACE, ISOLATE |
   | ORCHESTRATION | COORDINATE, TEAMWORK |
   | HIERARCHICAL | TOP-DOWN, LEADER |
   | INFRASTRUCTURE | FOUNDATION, BUILD |
   | OBSERVABILITY | MONITOR, WATCH |
   | GOVERNANCE | CONTROL, AUDIT |
   | PLAYBOOK | (usually OK but occasionally garbles) |

5. **Verify hierarchy** - max 3 levels: title, main content, footer

Present the simplified plan:
```
Concept: [one sentence]
Layout: [type]
Elements: [count] / 10 max
Labels: [count] / 10 max
Complex words replaced: [list]
Cut as unsupported: [list, or none]
Unfinished parts (render dashed): [list, or none]
```

### Step 4: Generate Initial Variants

Generate the specified number of variants (default 3), each taking a slightly different visual approach to the same concept.

**For each variant:**

1. Craft a narrative prompt following best practices:
   - Write descriptive paragraphs, not keyword lists
   - Include style tokens (background color, text color, font)
   - Specify layout positioning explicitly - prescribe element order and position
     ("left to right: A, then B, then C"); the model follows stated order far better
     than inferred structure
   - Lock the layout (Principle 5): one spine (left-to-right flow or a single loop),
     elements sitting on it, and say explicitly that no connection lines cross
   - For unproven/planned parts (Principle 7): request "drawn with a dashed outline,
     unfilled" right next to that element's description, plus its label
   - Request "generous spacing" and "clean minimal design"

2. Generate using the Python script (handles JSON escaping properly):
   ```bash
   python3 .claude/skills/nano-banana-image-generator/scripts/generate_image.py "[prompt]" /tmp/[concept]_v[N].png --aspect-ratio [ratio]
   ```
   **Important**: Use the Python script, not the bash script, to avoid JSON escaping issues with quotes in prompts.

3. Wait 2 seconds between API calls to avoid rate limits:
   ```bash
   sleep 2
   ```

### Step 5: Self-Critique Loop

**For each generated image, run this analysis cycle. This is the core differentiator of this skill.**

1. **View the image**: Use the Read tool on the PNG file to visually inspect it

2. **Check for issues** against this checklist. Looking at the render and checking the
   facts are DIFFERENT jobs - layout bugs are invisible in the plan, factual bugs are
   invisible in the render. Do both.

   *Looks (inspect the render):*
   - [ ] **Title text**: Is it spelled correctly and readable?
   - [ ] **All labels**: Are they spelled correctly? Any garbled/mushy text?
   - [ ] **Element count**: Does the image have roughly the right number of elements?
   - [ ] **Missing elements**: Is anything from the concept missing entirely?
   - [ ] **Duplicate elements**: Are any labels or nodes repeated incorrectly?
   - [ ] **Text placement**: Are labels in the right positions relative to their elements?
   - [ ] **Readability**: Would this be readable on a mobile screen?

   *Structure (check against the Step 2 plan):*
   - [ ] **Logical structure**: Does the layout match the requested concept? Are connections correct?
   - [ ] **No crossings**: Connection lines don't cross or wander (crossing reads as complexity, not system)
   - [ ] **Nothing floats**: Every element is wired into the flow with a visible connection
   - [ ] **Honest state**: Unproven/planned parts actually rendered dashed/hollow with their label

   *Truth (check against the Step 2 sources):*
   - [ ] **Factual accuracy**: Every number and claim in the render matches the verified source; the scale legend is present if marks are not 1:1
   - [ ] **Cold-viewer test**: Would someone with zero context walk away with the core message? (Explainer, not advertisement)

3. **Classify the image**:
   - **Good**: No issues found, or only very minor ones. Keep as candidate.
   - **Fixable**: 1-2 specific issues that can be addressed by prompt adjustment. Iterate.
   - **Redo**: Fundamental layout/structure problems. Needs a different prompt approach.

4. **For Fixable images**, identify the specific fix:
   - Missing element → Add explicit instruction for it
   - Misspelled word → Replace with simpler word or remove
   - Wrong layout → Be more explicit about positioning
   - Duplicate node → Emphasize exact count ("exactly six nodes, not five, not seven")
   - Elements merged → Use completely distinct words for each element
   - Crossing lines → Restate the layout as an explicit ordered sequence with positions ("one horizontal spine, left to right: A, B, C; no lines cross")
   - Unfinished part rendered solid → Repeat the dashed/hollow instruction immediately adjacent to that element's description
   - Floating element → Name its connection explicitly ("an arrow from X to Y") or cut it

5. **Regenerate** with targeted fixes. Maximum 3 iteration rounds per variant.

6. **Track the best version** of each variant approach.

### Step 6: Present Candidates

[APPROVAL GATE] - Present the best candidates to the user

Show each candidate image and describe:
- What it got right
- Any remaining minor imperfections
- Which concept angle it takes

**User options:**
1. **Pick a winner** - Select one or more as final
2. **Iterate on specific one** - Request changes to a candidate
3. **New direction** - Describe a different visual approach
4. **Combine elements** - Mix aspects from multiple candidates

If user requests changes:
- Apply modifications to the prompt
- Regenerate and re-run self-critique (Step 5)
- Return to this gate

### Step 7: Finalize and Cleanup

1. **Copy final images** to the output folder with clean names:
   ```bash
   cp /tmp/[best_version].png [output_folder]/[concept_name].png
   ```

2. **Delete intermediate files** from /tmp:
   ```bash
   rm /tmp/[concept]_v*.png
   ```

3. **Keep only final versions** in the output folder. Delete any intermediate copies.

4. **Open the output folder** for the user:
   ```bash
   open [output_folder]
   ```

### Step 8: Write Completion Summary

Report:
```
## Generated Images

**Concept**: [description]
**Output**: [folder path]
**Files**: [list of final files]
**Iterations**: [total attempts] across [variants] variants
**Cost**: ~$[0.039 * total_attempts] ([total] images generated)
```

---

## Outputs

- Final explanatory images in the output folder
- All intermediate files cleaned up

## Error Recovery

| Error | Recovery | Notify |
|-------|----------|--------|
| API rate limit | Wait 3 seconds and retry | No |
| API quota exceeded | Wait 60 seconds, retry once | Yes - warn user about quota |
| JSON escape error | Switch to Python script (not bash) | No |
| All variants have garbled text | Simplify further - reduce to 6 labels max | No |
| Image generation fails completely | Check API key in `.env` | Yes |

## Completion Checklist

- [ ] Best practices read fresh
- [ ] Truth gate passed: claims verified against the source; unsupported beats cut and reported
- [ ] Labels written first and read in order - they tell the story on their own
- [ ] Concept decomposed and simplified to constraints; no undisclosed scale mixing
- [ ] Unfinished parts marked to render visibly unfinished (dashed/hollow)
- [ ] Initial variants generated
- [ ] Each variant self-critiqued on all three passes: looks, structure, truth
- [ ] Best candidates presented and approved by user
- [ ] Final images saved to output folder with clean names
- [ ] Intermediate files deleted
- [ ] Output folder opened for user

## Style Reference

**Warm style (default):**
```
Warm charcoal background (#2D2926), soft cream text (#FAF8F5),
illustrated flat design with soft shadows, DM Sans font style,
dusty rose (#D4A5A5), coral (#E8B4A0), muted teal (#7BA3A3),
soft gold (#D4C4A0) accent colors.
```

**Dark brand style:**
```
Black background (#000000), white text (#ffffff), DM Sans font,
bold 700 weight for titles, clean minimal design, high contrast.
```

## Self-Improvement

After completing this skill's primary task, consider tactical improvements:

- [ ] **Review execution**: Were there friction points, unclear steps, or inefficiencies?
- [ ] **Common failure patterns**: Did certain types of prompts consistently fail? Add to the word replacement table.
- [ ] **Iteration efficiency**: Did self-critique catch real issues or waste cycles on false positives?
- [ ] **Prompt patterns**: Did any prompt structure produce consistently better results? Document it below.
- [ ] **Apply improvement** (if identified):
  - [ ] Edit this SKILL.md with the specific improvement
  - [ ] Keep changes minimal and focused
- [ ] **Version control** (if in a git repository):
  - [ ] Stage: `git add .claude/skills/create-explanatory-image/SKILL.md`
  - [ ] Commit: `git commit -m "refactor(create-explanatory-image): <brief improvement description>"`

### Learned Patterns

<!-- Add patterns discovered through self-improvement here -->
- "playbook" frequently misspells as "playbaak" or "playbauk" - avoid in taglines, use "it" or "the file" instead
- EDIT and SAVE merge into one label when used as adjacent cycle nodes - use completely distinct words (RUN/CHECK/STORE/REFLECT/REFINE/PUSH)
- Circular diagrams with 6+ nodes tend to duplicate labels - stick to 3-4 nodes max for loops
- The Python generate_image.py script handles JSON escaping; the bash generate.sh does not - always prefer Python for complex prompts
- Explicitly state "exactly N nodes, not more, not fewer" when count precision matters
- Labels OUTSIDE circles/nodes render more reliably than labels inside
- Use numbered lists (1. READ STATE, 2. DO WORK) to force correct vertical stacking
