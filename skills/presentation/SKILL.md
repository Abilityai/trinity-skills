---
name: presentation
description: Generate a brand-locked multi-slide presentation deck (16:9, 1920x1080) and assemble into a PDF. Mirrors the social-carousel pattern - each slide is an HTML+Playwright PNG render with its own textless soft-futurism hero image. Final step combines all slide PNGs into a single PDF for distribution. Six slide types - cover, section, content, statement, closing on the shared dark canvas brand system, plus a dense type composed via /one-pager for information-dense slides (dashboards, fact sheets, at-a-glance briefings). Use when building a workshop deck, conference talk, internal presentation, or any 16:9 slide set that needs to look brand-coherent and ship as a PDF.
category: visual-communication
automation: gated
argument-hint: "<source with one block per slide> [--aspect 16:9] [--autonomous] [--output-dir PATH]"
allowed-tools: Bash, Read, Write, Edit, Glob, Skill, AskUserQuestion
user-invocable: true
requires:
  env: [GEMINI_API_KEY, GOOGLE_API_KEY]
  binaries: [python3]
  packages: [playwright, pillow]
metadata:
  version: "1.2"
  created: 2026-06-04
  updated: 2026-07-23
  author: Ability.ai
  locked_design: true
  changelog:
    - "1.2: Promoted to the public trinity-skills library — external dependencies vendored (brand_defaults.md replaces the private design-system doc as a swappable DEFAULT, and it is now the only palette source since slide_templates.md carried none inline; image_concepts.md replaces the cross-skill object library; render_html_to_png.py copied into scripts/), --autonomous headless mode added so the skill is callable as one line, Drive delivery removed, imagery invoked via /nano-banana-image-generator by name, speaker/org details in the slide templates replaced with placeholders, 9.2 MB examples/ folder dropped"
    - "1.1: Add dense slide type - composes /one-pager (16:9) for information-dense slides (dashboards, fact sheets, at-a-glance summaries); density guidance (don't overload content slides); Composes section; deck footer carried via the one-pager footer block"
    - "1.0: Initial version"
---

# Presentation

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change - the top entry of `metadata.changelog` above - e.g. `presentation vX.Y — recent: <summary>`. Then proceed.

## Purpose

Generate **brand-locked 16:9 presentation decks** as a set of slide PNGs + a single assembled PDF. Mirrors a social-carousel build (multi-slide, HTML+Playwright rendered, picture-card aesthetic) but targets the **presentation distribution format**: 1920x1080 slides, more spacious typography, PDF as the deliverable.

A deck is a sequence of slides; each slide picks one of **6 slide types** - 5 native (`cover`, `section`, `content`, `statement`, `closing`) defined in `slide_templates.md`, plus **`dense`**, composed by invoking `/one-pager` (16:9) for a slide that must carry an entire briefing's worth of information (status dashboard, fact sheet, KPI/comparison/timeline at-a-glance). Convention: open with a `cover`, close with a `closing`, fill the body with any mix of `section` / `content` / `statement` / `dense`. **Number of slides is driven entirely by the source content** - the skill counts the slide blocks in the source, never asks for a count.

**Density guidance:** the deck default is spacious - one idea per slide, projection-scale type. But presentations should be more information-dense and compact at times: when a slide genuinely needs many facts at once (KPIs, comparisons, timelines, a status snapshot), do NOT overload a `content` slide (max 4 bullets) or split one briefing across five thin slides - declare that slide `dense` and let `/one-pager` compose it at read-up-close density with its mechanical one-page fit guarantee.

Every slide is its own rendered PNG. After all slides render, a final PDF assembly step combines them into `{slug}.pdf` (one page per slide).

## When to use

**Right tool when:**
- You're building a deck for a **workshop, webinar, conference talk, or internal presentation**
- The output needs to be **shareable as a PDF** (most presentation distribution channels prefer PDF over PPTX)
- You want the deck to feel like the same brand as your social posts (a diagram or social-carousel skill)
- You have structured content that naturally splits into slides (number is driven by the content, not pre-decided)

**Wrong tool when:**
- The whole deliverable is ONE dense page (fact sheet, one-sheet, briefing doc) → use `/one-pager` directly (it is composed here only for individual `dense` slides inside a deck)
- The asset is a single image for social → use a single-image social skill or a diagram skill
- The asset is a vertical carousel for LinkedIn / IG → use a social-carousel skill (4:5 not 16:9)
- The asset is a YouTube thumbnail → use `/thumbnails-branded`
- You need live interactive slides with builds/transitions → presentations skill produces a static PDF; for live builds use Keynote/Google Slides directly

## What makes this distinct

| Approach | Trade-off |
|----------|-----------|
| Manual deck in Keynote / Google Slides | Maximum flexibility (builds, transitions) but slow, brand-drift risk, no automatic hero-image generation |
| a social-carousel skill (4:5) | Same engine, wrong aspect for projection / screen-share |
| `/presentation` (this skill) | 16:9 native, brand-locked, hero per slide, ships as PDF. ~$0.07 × N for hero generation; trades live builds for speed + brand coherence |

## State Dependencies

| Source | Location | Purpose |
|--------|----------|---------|
| Brand defaults | `brand_defaults.md` (this skill) | Palette, fonts, weight rule, prose-colour rule, imagery placement - read every time. **§0 first**: swappable defaults; the workspace's own design doc wins |
| Slide templates | `slide_templates.md` | Cover / Section / Content / Statement / Closing HTML + CSS skeletons - read every time |
| Image concepts | `image_concepts.md` (this skill) | Topic → image concept mappings + prompt template |
| Render script | `scripts/render_html_to_png.py` | HTML → PNG via Playwright (called once per slide) |
| Image generation | the `/nano-banana-image-generator` skill, invoked **by name** | Hero generation (once per slide that needs a hero) |
| PDF builder | `scripts/build_pdf.py` | Combines slide PNGs into a single PDF (called once at the end) |

The presentation skill **reuses** the brand design system rather than maintaining its own. A diagram and a slide in a `/presentation` should look like they came from the same brand. The only presentation-specific spec is `slide_templates.md`, which defines the 16:9 slide-level structure + the presentation-scale type tier.

**Type-scale exception (LOCKED):** the design system typography is tuned for 1080-wide mobile-feed assets. Presentations are designed for projection / screen-share at 1920-wide and read at greater viewer distance, so they use a larger scale defined in `slide_templates.md` (160px cover hook, 80-92px content title, 38-44px body, 26-30px chrome). Everything else from the design system applies verbatim - palette, fonts, weight rule (no bold except `.accent`), imagery system (Universe A picture-card or full-bleed), no-emoji rule.

## Prerequisites & cold start

Script paths in this file are relative to **this skill's directory** — run them from there,
or prefix with the directory the skill was injected into.

| Requirement | Needed for | Missing → |
|---|---|---|
| `python3` + Playwright/Chromium | rendering every slide (Step 8) | Report the install command (`pip install playwright && playwright install chromium`); **do not claim slides that were never rendered**. |
| PIL/Pillow (`pip install pillow`) | PDF assembly | Report the install command; the slide PNGs are still a valid deliverable. |
| `GEMINI_API_KEY` (fallback `GOOGLE_API_KEY`) | hero imagery | Not fatal — render the deck hero-free (the layouts degrade gracefully) and say so in the delivery report. Held by the `/nano-banana-image-generator` child skill, which fails naming the key. |

Generation cost: ~$0.067 per hero image × N slides with heroes (a 10-slide deck with 8
heroes runs ~$0.54 + ~3 min). Hero-free = $0.

## Headless mode (`--autonomous`)

This skill is **callable as one line** by a schedule, an orchestrator, or another agent
(the fleet's playbook-call convention). Invoked that way there is nobody to answer a gate,
so `--autonomous` must be passed and both gates are skipped. In that mode:

- The source-format rule hardens rather than relaxes: the skill **assembles and styles only
  what the source provides**. It never invents or paraphrases slide content, and a source
  missing slide text is a **failed run** — report it and produce nothing.
- Any `[NEEDS:]` gap is dropped from the slide and listed in the final report, never guessed.
- Everything else — hero imagery, render, PDF assembly — runs unchanged.

## Inputs

```
/presentation [source] [--aspect 16:9] [--autonomous] [--output-dir PATH]
```

| Flag | Default | Description |
|------|---------|-------------|
| `source` | (required) | **Must contain the complete text for every slide.** Inline text in quotes OR file path to .md/.txt. See "Source format" below - this skill does NOT invent slide content. If the source is vague or incomplete, the skill halts and asks the user to provide the missing slide text BEFORE doing anything else. |
| `--aspect` | `16:9` (1920x1080) | Standard projection aspect. **16:9 is the only supported aspect** in v1.0 - this is a presentation skill, not a social skill. |
| `--output-dir` | `{output-dir}/` | Directory where slide PNGs, hero sources, and final PDF land. |
| `--autonomous` | (off) | Headless mode for scheduled/unattended runs: skip both approval gates. See Headless mode above. |

**Number of slides is NEVER specified as a flag.** The skill counts the `## Slide NN` blocks in the source - whatever's there is what gets rendered. A deck might be 3 slides or 30; that's a content decision, not a parameter. The 5 slide **types** (cover, section, content, statement, closing) are fixed by the design system, but the **count** is whatever the content requires.

### Source format (LOCKED)

The source MUST contain the full text for every slide, slide-by-slide. The skill does NOT invent or paraphrase content - it only assembles, styles, and renders what the user provides. This is the single most important rule: **minimize re-generation by getting the content right BEFORE any image work starts**.

Acceptable source format (markdown blocks, one per slide):

```
## Slide 01 — cover
Eyebrow: Agent Architecture · Workshop Demo
Title: Decomposition isn't the |win|.
Deck: Why most "AI agents" plateau at planning - and what the architecture of one that actually ships looks like.
Speaker: {Speaker} · {date} · {org}
Hero idea: Cathedral interior with glowing atomic loop

## Slide 02 — section
Number: Part 01
Title: Delegation.
Hero idea: Deep concrete vault with a single light column

## Slide 03 — content
Eyebrow: Module 03 · The four things
Title: Agents that ship have |four| things.
Bullet 1 label: Planning
Bullet 1 body: Splitting a task into steps. Table stakes - every framework does it.
Bullet 2 label: Memory
Bullet 2 body: Persisting state across runs. Most "agents" skip this entirely.
Bullet 3 label: Delegation
Bullet 3 body: Spawning sub-agents with bounded scope. Where compound agents emerge.
Bullet 4 label: Recovery
Bullet 4 body: Detecting + revising your own bad output. The actual moat.
Hero idea: Cathedral with glowing atom (reuse incubation_loop)

## Slide 04 — statement
Quote: If your agent can't revise itself mid-run, it's a chatbot in a |wrapper|.
Source: {Speaker} · {module}
Hero idea: Single concrete arch dissolving into amber-rose haze

## Slide 05 — closing
Eyebrow: Closing · Contact
Title: Build something |real|.
Deck: Trinity is open source. Start with the docs, run an agent in 10 minutes.
Contact 1: trinity.ability.ai
Contact 2: github.com/Abilityai/trinity
Contact 3: x.com/evyborov
Speaker: {Speaker} · {date} · {org}
```

Conventions inside the source:
- `|word|` marks the **single `.accent` red word** inside a title (per the no-bold rule)
- `Hero idea:` is a short verbal description - the skill turns this into a Nano Banana prompt at generation time
- The fields needed per slide type are listed in the "Required fields per slide type" table below
- `# heading` blocks separate slides; the skill counts these to verify the deck size

**Required fields per slide type:**

| Slide type | Required fields | Optional |
|---|---|---|
| `cover` | Title, Deck, Speaker, Hero idea | Eyebrow |
| `section` | Number, Title, Hero idea | (none) |
| `content` | Eyebrow, Title, Bullet 1 label + body (at least 2 bullets, max 4), Hero idea | (none) |
| `statement` | Quote, Source, Hero idea | (none) |
| `closing` | Eyebrow, Title, Deck, Contact 1 (at least 1, max 4), Speaker | Hero idea (text-only by default) |
| `dense` | Brief (the raw material or structured block content for the page - facts, KPIs, comparisons, timeline; handed to `/one-pager`) | (no Hero idea - `/one-pager` generates its own accent band, or runs `--no-image`) |

A `dense` slide block looks like:

```
## Slide 06 — dense
Brief: Q3 status at a glance. ARR $412K (+14% QoQ). 9 active clients, 2 in onboarding.
  Pipeline: 6 qualified opps, $180K weighted. Trinity OSS: 1.2K stars, 40 deployments.
  Risks: Xero re-auth pending; 2 renewals in Aug. Roadmap: Agent Hub beta Sep, SOC2 Nov.
```

The Brief must contain the actual facts (numbers, names, claims) - `/one-pager` distills but never invents; missing facts surface as `[NEEDS: …]` markers at the gate.

If ANY required field is missing on ANY slide, the skill halts at Step 1.5 below and asks the user to fill in the gaps. No hero generation, no rendering, no PDF until the source is complete.

## Process (transactional)

### Step 1: Read state

1. Read `brand_defaults.md` — **§0 brand override first**, then palette, typography, imagery system, prose-colour rule. If the workspace has its own design/brand document, port its tokens in and let it override every default.
2. Read `slide_templates.md` (cover/section/content/statement/closing HTML skeletons + CSS)
3. Read `image_concepts.md` (hero concepts + prompt grammar)

### Step 1.5: Source completeness check (LOCKED) — halt if anything is missing

**Before anything else, parse the source and validate that EVERY slide has EVERY required field for its slide type** (see the "Required fields per slide type" table in the Inputs section above). The skill does NOT invent slide content - if the source is a one-liner like "5 slides on deep agents", that is INSUFFICIENT, and the skill must halt here.

If anything is missing or vague:

1. Identify the gaps slide-by-slide. Example:
   ```
   Slide 02 — section: missing "Number" field
   Slide 04 — statement: "Quote" field is too vague ("something about wrappers")
   Slide 05 — closing: missing all contacts
   ```
2. Use `AskUserQuestion` to ask the user to fill in the missing fields. Do NOT proceed to Step 2 until every required field is filled.
3. Once the user provides the missing text, write the completed source to `{output-dir}/source.md` so it can be referenced in later steps and reproduced.

**Why this gate matters:** the most expensive failure mode in this skill is generating heroes + rendering slides (each hero is ~$0.07 and ~10 sec), only to discover the user wanted different wording. By forcing complete text upfront, we make iteration on copy free and ensure the visual generation step runs on locked content. This matters more as the deck grows - a 20-slide deck with 16 heroes is $1.12 of cost behind a single typo.

### Step 2: Parse the source + plan the deck

Count the `## Slide NN` blocks in the source - that's the slide count. Read the type declared on each slide's header line (`## Slide 01 — cover`, `## Slide 02 — section`, etc.).

The deck doesn't follow a fixed length. The only structural conventions:

| Position | Convention | Notes |
|----------|------------|-------|
| **First slide** | Usually `cover` | The user can override; some decks (e.g. an internal status update) might open with a `statement` |
| **Body slides** | Any mix of `section`, `content`, `statement`, `dense` | Driven by content - the source declares each type |
| **Last slide** | Usually `closing` | The user can override |

The 6 slide **types** are fixed (5 defined in `slide_templates.md`, `dense` composed via `/one-pager`). The **count** and the **mix** come entirely from the source content. A 3-slide deck and a 30-slide deck both use the same templates - they just have different numbers of `## Slide NN` blocks in the source.

Each type, recap:

| Type | When to use | Hero placement |
|------|-------------|----------------|
| `cover` | Opens the deck. Title + deck (subtitle) + speaker strip over a hero. | Full-bleed hero with text overlay |
| `section` | Divider between major parts of the talk - "PART 2: DELEGATION". Big hero, minimal text. | Full-bleed hero with title overlay |
| `content` | The workhorse. Title + picture-card on one side + 2-4 bullet points on the other. | Picture-card (left or right) |
| `statement` | One big quote or insight that needs emphasis. Sparingly - 1-2 per deck max. | Full-bleed hero with centered statement |
| `closing` | Closes the deck. CTA + contacts + speaker strip. Often heroless. | Text-focused, optional small hero |
| `dense` | A slide that must carry a whole briefing at read-up-close density (status dashboard, fact sheet, at-a-glance summary). Sparingly - most slides stay one-idea. Composed via `/one-pager`, not `slide_templates.md`. | Thin accent band from `/one-pager` (or none); no deck hero |

### Step 3: Pick hero concepts (one per slide that has a hero)

For each slide that displays a hero image:
- Match the slide's content to a concept in `image_concepts.md` (cover should match the overall topic; content slides should match their specific point)
- Vary concepts across consecutive slides - repeat hero concepts make the deck feel like a stuck loop

The `closing` slide can be heroless (text-only) if the cover already used a hero strong enough to bookend the talk.

`dense` slides are **skipped** in this step - they take no deck hero; `/one-pager` picks its own accent-band concept (or none) in Step 6.5.

### Step 4: [APPROVAL GATE 1 - TEXT] Confirm the assembled text reads as intended *(skipped with `--autonomous`)*

**This is the LOCKED first gate. No hero generation, no rendering, no PDF assembly happens until the assembled text content of EVERY slide is approved.** This gate is the user's final read of their OWN text (collected in Step 1.5) before any spending starts - it's not a place where the skill invents content.

Present the full deck text content (not just headings) inline as plain markdown so the user can read everything in one scroll. The text comes verbatim from `source.md` written in Step 1.5; this gate confirms the rendered-on-screen wording is what the user actually wants. Use this format for each slide:

```
─────────────────────────────────────
SLIDE 01 / N — COVER
  Eyebrow:  Agent Architecture · Workshop Series
  Title:    Decomposition isn't the win.
  Deck:     Why most "AI agents" plateau at planning - and what the
            architecture of an agent that actually ships looks like.
  Hero idea: Cathedral interior with glowing atom-orbit (Universe A,
             matches the diagram’s scene)

SLIDE 02 / N — SECTION
  Number:   Part 01
  Title:    Delegation.
  Hero idea: Deep concrete vault with a single light source

SLIDE 03 / N — CONTENT
  Eyebrow:  Module 03
  Title:    Agents that ship have four things.
  Bullets:
    → PLANNING — Splitting a task into steps. Table stakes.
    → MEMORY — Persisting state across runs. Most skip this.
    → DELEGATION — Spawning sub-agents with bounded scope.
    → RECOVERY — Detecting + revising your own bad output.
  Hero idea: Server-cathedral nave with four light columns

SLIDE 04 / N — STATEMENT
  Quote:    If your agent can't revise itself mid-run, it's a chatbot
            in a wrapper.
  Source:   {Speaker} · {module}
  Hero idea: Single concrete arch dissolving into amber haze

SLIDE 05 / N — CLOSING
  Eyebrow:  Closing · Contact
  Title:    Build something real.
  Deck:     Trinity is open source. Start with the docs, run an
            agent in 10 minutes.
  Contacts:
    → trinity.ability.ai
    → github.com/Abilityai/trinity
    → x.com/evyborov
─────────────────────────────────────
```

Then use `AskUserQuestion` to gate progress:

> "Do you approve all the text content above for the {slug} deck? Any slide you want to edit before I generate the hero images?"

Options:
- **Approve all - generate heroes** → proceed to Step 5
- **Edit slide N** → loop back to revise that slide's text, then re-show this gate
- **Cancel** → stop, don't spend on heroes

DO NOT call the nano-banana generator, render any HTML, or build any PDF until this gate returns "Approve all".

### Step 5: Generate N textless hero images

For each slide that needs a hero, call the nano-banana generator with the slide's hero concept. Use the prompt grammar from `image_concepts.md` - soft futurism, brutalist concrete cathedral, OBJECT glows amber-rose as the brand signal.

```bash
Invoke `/nano-banana-image-generator` **by name** with the built prompt, the output path
`{output-dir}/slide_{NN}_hero_source.png`, and a 16:9 aspect. Never call a sibling skill's
internal scripts — the child owns its own interface and credential handling.
```

Use **`--aspect-ratio 16:9`** for full-bleed and section heroes. Use **`--aspect-ratio 1:1`** for picture-card heroes on content slides (matches the design system's contained-card pattern).

Run sequentially. **Verify each is textless** before authoring HTML.

**Prompt sanitization (LOCKED):** NEVER use internal double quotes inside the prompt string. Use single quotes, parentheses, dashes, or paraphrase instead.

### Step 6: Author N HTML files

For each slide, fork the appropriate template from `slide_templates.md`:
- Slide 01 → **Cover template** (full-bleed hero + title overlay)
- `section` slides → **Section template** (full-bleed hero + section number + title overlay)
- `content` slides → **Content template** (picture-card left or right + title + bullets)
- `statement` slides → **Statement template** (full-bleed hero + centered manifesto)
- Slide N → **Closing template** (text-focused, optional small hero, contact + CTA)

Each HTML file embeds:
- The slide's hero image (if applicable) via `file://{output-dir}/slide_{NN}_hero_source.png`
- The slide's text content
- The slide-progress footer (`01 / 12`, `02 / 12`, etc.)

Save each HTML to `{output-dir}/slide_{NN}.html`.

`dense` slides get **no HTML here** - they are produced whole in Step 6.5.

### Step 6.5: Dense slides — compose /one-pager

For each `dense` slide, **invoke `/one-pager` by name** (Skill tool) - never fork its templates or call its `scripts/` directly; go through the entry point so its fixes propagate:

- **Source**: the slide's `Brief` from `source.md` (already approved at Gate 1 - so the child's content gate is a fast verbatim confirm, not a rewrite)
- **Flags**: `--format 16:9 --theme dark` (matches the deck canvas exactly - 1920x1080, same brand system), `--output-dir {output-dir}/dense_{NN}/`. Add `--no-image` if the slide should be pure typographic density ($0)
- **Footer**: pass the deck footer as the one-pager's footer block content - `{SPEAKER} · {ORG}` left, `{NN} / {N}` progress right - so the LOCKED slide-progress anchor is preserved on dense slides too
- **Consume the PNG**: after the child's fit-guard passes and its visual gate approves, copy `dense_{NN}/{child-slug}.png` to `{output-dir}/{slug}_slide_{NN}.png`. The child's 1-page PDF is an ignored byproduct - the deck PDF (Step 10) is THE deliverable
- **Fit**: the child's fit-guard + tightening ladder mechanically guarantee the slide never clips - do not re-litigate density here

Cost: ~$0.07 per dense slide for the accent band, $0 with `--no-image`.

### Step 7: Render N PNGs

For each slide HTML, run the render script at **1x device scale** (the 1920x1080 native resolution is already projection-ready - 2x doubles file size for no visual benefit on a projector / screen-share):

```bash
python3 scripts/render_html_to_png.py {output-dir}/slide_{NN}.html {output-dir}/{slug}_slide_{NN}.png --width 1920 --height 1080 --device-scale 1
```

`dense` slides are already rendered (by `/one-pager` at device-scale 2, appropriate for their small type) and their PNGs already sit in the slides dir from Step 6.5 - skip them here.

### Step 8: Show rendered PNGs

Use the `Read` tool on each slide PNG in order so the user sees the full deck sequence inline. Report:
- Per-slide PNG paths
- A note that the PDF has NOT been built yet - awaiting visual approval

### Step 9: [APPROVAL GATE 2 - VISUAL] Confirm the rendered slides look right *(skipped with `--autonomous`)*

**This is the LOCKED second gate. PDF assembly does NOT happen until the user has seen the rendered PNGs and approves them.** Text-content approval (Gate 1) does not imply visual approval - a typo-free slide can still render with a hero that misses the brief, a text overflow, or a layout that doesn't sit well.

Use `AskUserQuestion`:

> "All N slides rendered. Do they look right? Any slide you want me to regenerate (text, hero, or layout) before I assemble the PDF?"

Options:
- **All good - assemble the PDF** → proceed to Step 10
- **Regenerate hero on slide K** → re-run Step 5 for slide K, re-render slide K (Step 7), re-show only that slide, then re-ask Gate 2
- **Edit text on slide K** → loop back to Step 4 for that one slide's text, then re-render and re-ask Gate 2
- **Cancel** → stop, don't build the PDF

DO NOT call `build_pdf.py` until this gate returns "All good".

### Step 10: Assemble PDF

After visual approval, combine the slide PNGs into a single PDF (one page per slide, in order):

```bash
python3 scripts/build_pdf.py \
  --slides-dir {output-dir}/ \
  --pattern "{slug}_slide_*.png" \
  --output {output-dir}/{slug}.pdf
```

The script reads all matching PNGs in numerical order and writes a single PDF via PIL. Each PNG becomes one PDF page sized to match the slide (1920x1080 native).

### Step 11: Report final deliverable

Report:
- The PDF path (this is THE deliverable)
- Per-slide PNG paths (for individual reuse if needed)
- Total deck size on disk

### Step 12: Iterate

Per-slide iteration model (mirrors a social-carousel build):

| Change request type | How to handle |
|---------------------|---------------|
| Edit text on slide K | `Edit` slide_{K}.html, re-render only that slide, re-assemble PDF |
| Wrong hero on slide K | Re-run Step 5 for slide K, re-render slide, re-assemble PDF |
| Change a `dense` slide | Re-invoke `/one-pager` (its own iteration step handles block edits / accent regen / density), re-copy the PNG, re-assemble PDF |
| Reorder slides | Renumber files + update slide-progress footers, re-assemble PDF |
| Add / remove a slide | Reauthor + regenerate; re-assemble PDF |

### Step 13: Persist if approved

Copy the entire `{output-dir}/` directory to a permanent location. By default Drive: `Content/Presentations/` (folder ID `1bDej1OZMKA2WOB33AxeDisA4w-LbJi9d`).

### Step 14: Optional Drive upload

Upload the PDF + all slide PNGs:

Delivery beyond the local output directory (upload, send, publish) is the calling agent's
job, not this skill's.

## Slide-progress footer (LOCKED)

Every slide carries a progress indicator + brand footer in the same position:

```
[ {SPEAKER} · {ORG} ]                                  [ 03 / 12 ]
```

The progress number updates per slide; the current page number is in red, the total is in gray.

CSS lives in `slide_templates.md`. This is the locked anchor that ties the deck together visually.

## Output

Return:
- Output directory (containing all N HTML, PNG, hero source files, and the assembled PDF)
- Final PDF path - this is the deliverable
- List of slide PNGs in order
- Inline previews of each slide
- Per-slide hero concept used

## Common issues

| Symptom | Diagnosis | Fix |
|---------|-----------|-----|
| Text feels small at projection distance | Used the wrong scale | Verify against `slide_templates.md` type tier (160px cover, 80-92px content title, 38-44px body) - do NOT use the design system's 1080-canvas sizes |
| PDF file is huge (>20 MB) | Rendered at 2x device scale | Re-render at 1x - 1920x1080 is already projection-native |
| Slide looks empty / sparse | Forced `content` layout on a slide that has only one statement | Switch to `statement` layout - one big idea + full-bleed hero reads better than 1 bullet on an oversized content layout |
| Hero overlaps important text | Full-bleed hero with text in the center | Use the directional gradient (per design_system.md "Text-over-image gradient principle") and ensure title sits in the darker band |
| Slide feels cramped / needs more than 4 bullets | Briefing-density content forced into a `content` slide | Declare it `dense` - `/one-pager` composes it at read-up-close density with a mechanical fit guarantee; don't shrink the projection type tier |

## Composes

| Child skill | Called at | Purpose |
|---|---|---|
| `/one-pager` | Step 6.5 (`dense` slides) | Renders information-dense slides (KPI strips, fact-rails, comparisons, timelines) as a fit-guaranteed 16:9 page; the deck consumes the PNG. Called **unversioned** so the child's fixes propagate; go through the entry point, never its scripts/templates directly. |

## Related skills

- `/one-pager` - the density inverse of this skill (single dense page → PDF). Composed here for `dense` slides; use it **directly** when the whole deliverable is one page, not a deck
- **A social-carousel skill** (if installed) - the social / 4:5 sibling, same engine
- **A diagram skill** (if installed) - if a single slide needs a structured diagram (architecture, flow, comparison), build the diagram with a diagram skill and embed the resulting PNG as the slide's hero
- `/workshop-covers` - for the announcement asset that precedes a presentation (event cover, social tease)

## See also

- `brand_defaults.md` - palette, fonts, imagery system (swappable defaults, §0)
- `slide_templates.md` - the 16:9 slide templates + presentation type scale
- `image_concepts.md` - hero concept library
