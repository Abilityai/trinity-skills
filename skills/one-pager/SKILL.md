---
name: one-pager
description: Generate a brand-locked, information-dense single-page PDF that lets a reader understand an entire topic - a company, a product, a project, a status update, any subject - in one page. Distills a raw brief into a composed grid of reusable blocks (hero-stat, KPI strip, two-column prose, comparison table, timeline, callout, icon-grid, fact-rail, mini-chart), renders one HTML via Playwright to a single PNG, mechanically guarantees it fits on ONE page via a fit-guard + tightening ladder, then wraps it as a 1-page PDF. Default 16:9 landscape; A4/Letter portrait via flag. Dark brand canvas default; light print-friendly theme via flag. Use when someone needs a dense one-pager / one-sheet / fact sheet / briefing doc that ships as a PDF.
category: visual-communication
automation: gated
argument-hint: "<brief, file path, or topic> [--format 16:9|a4|letter|a4-landscape] [--theme dark|light] [--no-image] [--autonomous] [--output-dir PATH]"
allowed-tools: Bash, Read, Write, Edit, Glob, AskUserQuestion, Skill
user-invocable: true
effort: high
requires:
  env: [GEMINI_API_KEY, GOOGLE_API_KEY]
  binaries: [python3]
  packages: [playwright]
metadata:
  version: "1.2"
  created: 2026-06-05
  author: Ability.ai
  locked_design: true
  changelog:
    - "1.2: Promoted to the public trinity-skills library — external dependencies vendored (brand_defaults.md replaces the private design-system doc as a swappable DEFAULT; image_concepts.md replaces the cross-skill object library; render_html_to_png.py copied into scripts/), --autonomous headless mode added so the skill is callable as one line, Drive delivery removed, imagery now invoked via /nano-banana-image-generator by name instead of reaching into its scripts, personal contact details removed from the worked example"
    - "1.0 - initial: distill -> content gate -> image -> render -> fit-guard -> visual gate -> 1-page PDF; 16:9 default, dual theme, thin accent + optional inline imagery"
    - "1.1 - Tier-3 conformance pass: added Completion Checklist + Error Recovery, effort:high, ultrathink marker; fixed the flex no-shrink layout invariant + 3-signal fit-guard found during validation"
---

# One-Pager

## Purpose

Generate a **brand-locked, information-dense one-pager** as a single PNG + a single-page PDF. It is the **density inverse of `/presentation`**: where a slide carries one idea at projection scale, a one-pager carries an entire briefing at read-up-close scale. The promise is literal - **the reader understands the whole topic from one page**, and the output is **never more than one page**.

The page is composed from a library of reusable **blocks** (see `block_templates.md`) laid on a flat row/flex grid. The skill **distills** a raw brief into telegraphic block content, gates that content for approval, generates a thin brand accent image, renders, mechanically verifies the page fits, and assembles the PDF.

Works for **any topic** - company overview, product sheet, project brief, investor one-pager, status dashboard, a topic explainer. The block library is generic; the layout preset adapts to the source's intent.

## When to use

**Right tool when:**
- Someone needs to understand a whole thing - a company, product, project, topic - from **one page**
- The output should ship as a **PDF** (one-pagers / one-sheets / fact sheets / leave-behinds are distributed as PDF)
- You want it to feel like the same system as its siblings (`/presentation`, `/explain-visually`, `/microsite`) — they share `brand_defaults.md`
- The content is dense and structured (stats, comparisons, timelines, key points) rather than one big idea

**Wrong tool when:**
- The content genuinely needs **multiple pages / slides** → use `/presentation` (multi-slide 16:9 deck → PDF)
- It's a single social image (one hero + a title/quote) → a single-image social skill
- It's a vertical social carousel → a social-carousel skill (4:5, multi-slide)
- It's a single structured diagram (one mechanism/flow/comparison) → a diagram skill
- The "one page" is really a website / interactive doc → that's a web build, not this skill

## What makes this distinct

| Approach | Trade-off |
|----------|-----------|
| Manual one-pager in Canva / Figma / InDesign | Max flexibility, but slow, brand-drift risk, no auto-distillation, no mechanical one-page guarantee |
| `/presentation` (multi-slide deck) | Spacious, one-idea-per-slide, many pages - the opposite density profile |
| `/one-pager` (this skill) | Single page, dense, brand-locked, distills a brief, **mechanically guaranteed to fit on one page**. ~$0.07 for the accent image (or $0 with `--no-image`) + ~1-2 min |

## State Dependencies

| Source | Location | Purpose |
|--------|----------|---------|
| Brand defaults | `brand_defaults.md` (this skill) | Palette, fonts, weight rule, prose-colour rule, imagery lineage - read every time. **§0 first**: the values are swappable defaults, and the consuming workspace's own design doc wins over them |
| Block templates | `block_templates.md` | Canvas, dual theme, dense type tier, block library, layout presets, density budget + fit rules - read every time |
| Image concepts | `image_concepts.md` (this skill) | Topic → image concept + prompt grammar (for the accent band) |
| Render script | `scripts/render_html_to_png.py` | HTML → PNG via Playwright (one call) |
| Fit-guard | `scripts/check_fit.py` | Measures whether the page overflows; drives the tightening loop (LOCKED single-page guarantee) |
| Image generation | the `/nano-banana-image-generator` skill, invoked **by name** | Thin accent band + any optional inline image |
| PDF builder | `scripts/build_pdf.py` | Single PNG → correctly-sized 1-page PDF |

The one-pager **reuses** the brand design system rather than maintaining its own. The only one-pager-specific specs are in `block_templates.md`: the single-page canvas, the light theme, the dense type tier, and the block library.

**Type-scale exception (LOCKED):** the design system's 26px floor is calibrated for mobile-feed glanceability. A one-pager is read up close (laptop full-screen / printed in hand), so it uses a **denser tier** (60px title, 24px body, 17px source floor) defined in `block_templates.md`. This mirrors how `/presentation` took the opposite exception (bigger, for projection distance). Everything else from the design system applies verbatim - fonts, weight rule, accent discipline, no-emoji, prose-colour rule.

## Prerequisites & cold start

Script paths in this file are relative to **this skill's directory** — run them from there,
or prefix with the directory the skill was injected into.

| Requirement | Needed for | Missing → |
|---|---|---|
| `python3` + Playwright/Chromium | rendering (Step 7) and the fit-guard (Step 8) | Report the install command (`pip install playwright && playwright install chromium`); the single-page guarantee cannot be claimed without the fit-guard, so **do not claim it**. |
| PIL/Pillow (`pip install pillow`) | PDF assembly (Step 11) | Report the install command; the PNG is still a valid deliverable. |
| `GEMINI_API_KEY` (fallback `GOOGLE_API_KEY`) | the accent band + any inline imagery | Not fatal — proceed as if `--no-image` was passed, and say so in the delivery report. Held by the `/nano-banana-image-generator` child skill, which fails naming the key. |

Generation cost: ~$0.067 for the accent band, +~$0.067 per optional inline image.
`--no-image` (or no key) = $0.

## Inputs

```
/one-pager [source] [--format 16:9|a4|letter|a4-landscape] [--theme dark|light] [--intent auto|company|dashboard|briefing] [--no-image] [--autonomous] [--output-dir PATH]
```

| Flag | Default | Description |
|------|---------|-------------|
| `source` | (required) | A brief, a file path (.md/.txt), pasted notes, or a structured block list. **Can be messy** - this skill distills it (see Content model). If the source is a one-line topic with no substance ("a one-pager about us"), the skill asks for the raw material BEFORE distilling - it does not fabricate facts. |
| `--format` | `16:9` (1920×1080) | `16:9` screen/dashboard (default), `a4` portrait print, `letter` US portrait print, `a4-landscape` print dashboard. See the formats table in `block_templates.md`. |
| `--theme` | `dark` | `dark` = the black canvas of the default palette. `light` = warm-paper print-friendly variant. Both are swappable per `brand_defaults.md` §0. |
| `--intent` | `auto` | Picks the layout preset. `auto` infers from the source; override with `company` (Preset A), `dashboard` (Preset B), or `briefing` (Preset C). |
| `--no-image` | (off) | Skip ALL image generation (no accent band, no inline). Pure typographic + data density. $0, faster. |
| `--autonomous` | (off) | Headless mode for scheduled/unattended runs: skip both approval gates. `[NEEDS:]` facts are **omitted, never guessed**, and listed in the final report. A bare-topic source is a failed run — report it and produce nothing. |
| `--output-dir` | `one_pager_{slug}/` | Where the HTML, PNG, image sources, and PDF land. Relative to the working directory unless given absolutely. |

### Content model (LOCKED): distill, then gate

The skill accepts a **raw brief** and **distills** it into the dense one-pager format. Distillation = selecting blocks, writing telegraphic content within the density budget, and assigning each block to a row. **Distillation condenses and structures the user's material; it never invents facts.** Numbers, names, claims must come from the source - if a block needs a fact the source doesn't provide, the skill leaves a `[NEEDS: …]` marker and surfaces it at the content gate rather than guessing.

If the source is already structured as explicit block content (the user did the condensing), the skill detects this and styles it verbatim - it only distills when handed raw material.

**Why distill-then-gate:** the most expensive failure is generating the accent image + rendering + fit-looping, only to find the wording was wrong or a number was invented. The content gate (Step 4) makes copy iteration free and ensures the visual pipeline runs on locked, fact-checked content.

## Headless mode (`--autonomous`)

This skill is **callable as one line** by a schedule, an orchestrator, or another agent
(the fleet's playbook-call convention). Invoked that way there is nobody to answer a gate,
so `--autonomous` must be passed and both gates are skipped. In that mode:

- `[NEEDS:]` gaps are **dropped from the page and listed in the final report** — never
  filled by guessing. Invented facts are the one failure this skill must never produce.
- A bare-topic source with no substance is a **failed run**: report the failure, produce
  nothing. It is not an invitation to write the content yourself.
- Everything else — distillation, imagery, render, fit-guard, PDF — runs unchanged. The
  fit-guard in particular is never skipped; it is the single-page guarantee.

## Process (transactional)

ultrathink - this playbook carries non-trivial reasoning: distilling a brief within a fixed density budget (Steps 3-4) and converging the fit-guard tightening ladder (Step 8). Reason carefully at each gate and before each re-render rather than tightening blindly.

### Step 1: Read state

1. Read `brand_defaults.md` — **§0 brand override first**, then palette, fonts, weight rule, prose-colour rule. If the workspace has its own design/brand document, port its tokens in and let it override every default.
2. Read `block_templates.md` (canvas, dual theme, dense type tier, block library, presets, density budget + fit rules)
3. Read `image_concepts.md` (accent-band concept + prompt grammar)

### Step 1.5: Resolve flags + classify the source

- Resolve `--format`, `--theme`, `--intent`, `--no-image` (defaults: `16:9`, `dark`, `auto`, image on).
- Derive a `{slug}` from the topic. Set `--output-dir` to `/tmp/one_pager_{slug}/`.
- Classify the source: **raw brief** (distill) vs **structured block list** (style verbatim).
- If the source is a bare topic with no substance, **halt** and ask the user for the raw material (facts, numbers, key points). Do not fabricate.

### Step 2: Pick the layout preset + plan the blocks

From the source's intent, pick a preset from `block_templates.md`:
- `company` → Preset A (hero-stat + KPI strip, problem/solution prose + fact-rail, capabilities icon-grid, roadmap timeline)
- `dashboard` → Preset B (KPI strip, mini-charts + callout, comparison + fact-rail)
- `briefing` → Preset C (thesis callout, two-col prose + bullets, comparison, how-it-works timeline)

Plan the page as an ordered list of rows of blocks. Assign each block a **priority** (must-keep / trimmable / nice-to-have) - this drives the tightening ladder later. Presets are starting points; swap or drop blocks to fit the actual source.

### Step 3: Distill content into the blocks (respect the density budget)

Write the telegraphic content for each block. Hold to the **density budget** in `block_templates.md`: ~450 words total, 1 hero-stat, ≤6 KPI cards, ≤2 prose blocks (≤70 words each), ≤6 bullets/list, ≤2 callouts, ≤5 timeline steps, ≤6 body rows (16:9).

If the source has more than fits, KEEP the highest-signal facts (the ones that serve "understand it in one page") and cut the rest - don't plan to shrink the font. Mark any fact the source doesn't supply as `[NEEDS: …]`.

### Step 3.5: Density lint

Count words and blocks against the budget. If over, tighten the content now (telegraphic rewrites, drop the weakest block) before showing the user. The page should be plausibly one-page BEFORE the gate.

### Step 4: [APPROVAL GATE 1 — CONTENT] Confirm the distilled text + flag any gaps *(skipped with `--autonomous`)*

**LOCKED first gate. No image generation, no rendering, no PDF until the content is approved.** This is where invention-drift and missing facts get caught.

Present the full distilled content as plain markdown, block by block, in reading order, so the user can read the whole page in one scroll. Surface any `[NEEDS: …]` markers prominently. Example shape:

```
ONE-PAGER · {slug}  ·  format 16:9  ·  theme dark  ·  preset: company

HEADER
  Eyebrow:     Company One-Pager · 2026
  Title:       Ability|.ai|
  Value-prop:  Deploy an entire autonomous department in the cloud - not just an agent on your laptop.
  Wordmark:    trinity.ability.ai

HERO-STAT
  72K · YouTube subscribers · +18K in 90 days

KPI STRIP
  3.2× ARR growth (YoY) · 94% net retention · 40+ enterprise pilots

TWO-COL PROSE — "The problem / the solution"
  ... (70 words) ...

FACT-RAIL — "At a glance"
  Founded 2024 · HQ Remote · Stage [NEEDS: funding stage] · License Open source

ICON-GRID — "Capabilities"
  → Persistent memory · Multi-agent orchestration · Full governance

TIMELINE — "Roadmap"
  Q1 Open source · Q2 Agent Hub · Q3 Enterprise (SOC2 + SSO)

FOOTER + CTA
  {Author} · {org} · {year}   →   {call to action}
```

Then use `AskUserQuestion`:
> "Approve this content for the {slug} one-pager? Anything to fix - including the [NEEDS] gaps - before I generate the image and render?"

Options:
- **Approve - render it** → proceed to Step 5
- **Edit a block** → revise that block's text (and fill any `[NEEDS]`), re-show this gate
- **Cancel** → stop, spend nothing

Once approved, write the locked content to `{output-dir}/source.md`. DO NOT generate images, render HTML, or build a PDF until this gate returns "Approve".

### Step 5: Generate imagery (skip if `--no-image`)

Generate the **thin accent band** (the brand signature). Match the topic to a concept in `image_concepts.md` and use its prompt grammar. The band is a wide strip, so request a wide aspect.

Invoke `/nano-banana-image-generator` **by name**, passing the built prompt, the output path `{output-dir}/accent_band.png`, and a 16:9 aspect. Never call a sibling skill's internal scripts — the child owns its own interface, and its credential handling comes with it.

For any approved **inline media** block, generate or place that image too (a 1:1 aspect for a contained card, or embed an existing PNG you were given). Verify each image is **textless**. **Prompt sanitization (LOCKED): never use internal double quotes in the prompt string** - use single quotes, parentheses, or paraphrase.

### Step 6: Author the single HTML

Fork the canvas + theme + block CSS from `block_templates.md`:
- Set the canvas dims for `--format` and `data-theme` for `--theme` on `<html>`.
- Compose the approved blocks into rows per the preset.
- Embed images via `file://{output-dir}/accent_band.png` (and any inline media).
- Use the dense type tier for the chosen format. Apply the prose-colour rule and weight rule.

Save to `{output-dir}/{slug}.html`.

### Step 7: Render the PNG

Render at **device-scale 2** (dense small type must stay crisp):

```bash
python3 scripts/render_html_to_png.py {output-dir}/{slug}.html {output-dir}/{slug}.png \
  --width {CANVAS_W} --height {CANVAS_H} --device-scale 2
```
(`16:9` → 1920×1080, `a4` → 1240×1754, `letter` → 1275×1650, `a4-landscape` → 1754×1240.)

### Step 8: [LOCKED] Fit-guard loop — guarantee one page

Run the fit-guard against the HTML at the canvas size:

```bash
python3 scripts/check_fit.py {output-dir}/{slug}.html \
  --width {CANVAS_W} --height {CANVAS_H}
```

- Exit `0` (`"fits": true`) → proceed to Step 9.
- Exit `3` (overflow) → apply the **tightening ladder** from `block_templates.md` in order, then re-author + re-render + re-check. Repeat until it fits:
  1. Telegraphic rewrites of the longest prose/bullets
  2. Reduce row gap (28→22→18) + card padding (22/26→16/20)
  3. Drop the lowest-priority block
  4. Last resort: step the type tier down one notch (never below the 17px source floor)

**The page is not allowed to clip or spill.** A render only advances past this step when `check_fit.py` returns `fits: true`. Note in the final report what (if anything) was tightened.

### Step 9: Show the rendered PNG

Use the `Read` tool on `{output-dir}/{slug}.png` so the user sees the full page inline. Report that the PDF has NOT been built yet - awaiting visual approval.

### Step 10: [APPROVAL GATE 2 — VISUAL] Confirm it looks right *(skipped with `--autonomous`)*

**LOCKED second gate. No PDF until the rendered page is approved.** Content approval (Gate 1) does not imply visual approval - a typo-free page can still render with an off accent image, an awkward block balance, or a layout that reads poorly.

Use `AskUserQuestion`:
> "Here's the rendered one-pager. Approve it for PDF, or is there a block / the accent image / the layout to fix first?"

Options:
- **Approve - build the PDF** → proceed to Step 11
- **Regenerate the accent image** → re-run Step 5 for the band, re-render, re-show, re-ask
- **Edit a block** → loop back to Step 6 for that block, re-render (+ re-run fit-guard), re-ask
- **Switch theme / format** → re-author for the new theme/format, re-render, re-ask
- **Cancel** → stop, don't build the PDF

DO NOT call `build_pdf.py` until this gate returns "Approve".

### Step 11: Assemble the 1-page PDF

```bash
python3 scripts/build_pdf.py {output-dir}/{slug}.png \
  --output {output-dir}/{slug}.pdf --dpi {DPI}
```
DPI per format: `16:9` → 192, `a4`/`letter`/`a4-landscape` → 300 (see `build_pdf.py` header).

### Step 12: Report the deliverable

Report:
- The **PDF path** (THE deliverable) + its physical page size
- The PNG path (for reuse / direct posting)
- The output directory
- Format, theme, preset, accent concept used
- Anything the fit-guard tightened to keep it on one page
- Any `[NEEDS]` gaps that were filled at the gate

### Step 13: Iterate

| Change request | How to handle |
|---|---|
| Edit a block's text | `Edit` the HTML block, re-render, re-run fit-guard, re-assemble PDF |
| Wrong accent image | Re-run Step 5, re-render, re-assemble |
| Different theme/format | Re-author canvas/theme, re-render, re-run fit-guard, re-assemble |
| Add/remove a block | Re-author the row, re-run fit-guard (it may trigger the ladder), re-assemble |
| Make it denser / sparser | Adjust the density budget for this page, re-distill, re-gate |

### Step 14: Persist

- Keep the full `{output-dir}` (HTML, PNG, image sources, PDF, source.md) as the reproducible record.
- Delivery beyond the local directory (upload, send, publish) is the calling agent's job, not this skill's.

## Completion Checklist

Verify before declaring the one-pager done (the transactional close):

- [ ] Source classified; if it was a bare topic, raw material was gathered - no fabricated facts
- [ ] Content distilled within the density budget; every `[NEEDS: …]` gap filled at Gate 1
- [ ] **Gate 1 (content)** returned Approve; `source.md` written to the output dir
- [ ] Imagery generated and verified textless - or `--no-image` honored
- [ ] HTML authored with the correct format dims, `data-theme`, and dense type tier
- [ ] PNG rendered at device-scale 2
- [ ] **Fit-guard passed** (`check_fit.py` → `fits: true`, exit 0) - the page is mechanically confirmed to be ONE page
- [ ] **Gate 2 (visual)** returned Approve
- [ ] PDF assembled at the correct DPI (16:9 → 192, a4/letter → 300)
- [ ] Output dir retained (HTML, PNG, image sources, source.md, PDF); Drive upload done if requested
- [ ] Final report delivered: PDF path + page size, PNG path, format/theme/preset, fit-guard notes

## Error Recovery

| Failure | Recovery |
|---|---|
| Source is a bare topic with no facts | Halt at Step 1.5 and ask for raw material. NEVER fabricate facts to fill the page. |
| Nano Banana image generation fails | Retry once. If it still fails, fall back to `--no-image` (render text-only), note the missing accent band, and offer to add it later. Never block the deliverable on imagery. |
| Playwright / Chromium render fails | Confirm Playwright + Chromium are installed, then retry the render. If it persists, report the exact error - do NOT assemble a PDF from a stale or partial PNG. |
| Fit-guard won't converge after the full tightening ladder | The content genuinely exceeds one page. Drop the lowest-priority block(s) and return to Gate 1 to re-confirm the trimmed content. NEVER ship a clipped or overlapping page - the single-page guarantee is non-negotiable. |
| Pillow missing at the PDF step | `pip install pillow`, then retry `build_pdf.py` - the PNG already exists, so no re-render is needed. |
| Drive upload fails | The local PDF/PNG are the deliverable and are safe. Report the upload error and retry the upload step alone - do not regenerate the one-pager. |

## Output

Return:
- The single-page **PDF** path - the deliverable - with its physical page size
- The PNG path
- Output directory (HTML, PNG, image sources, source.md, PDF)
- Format / theme / preset / accent concept
- Inline preview of the rendered page
- Fit-guard notes (what was tightened, if anything)

## Common issues

| Symptom | Diagnosis | Fix |
|---------|-----------|-----|
| `check_fit.py` keeps reporting overflow | Content over budget | Walk the tightening ladder (Step 8) - cut content first, type-tier last; never clip |
| Page reads as a "wall of text" | Too much prose, not enough blocks | Convert prose → KPI cards / bullets / fact-rail / comparison; hold ~450 words |
| Looks sparse / empty | Too few blocks for the canvas | Add a KPI strip, fact-rail, or timeline; or switch to a portrait format which fills differently |
| Light theme looks washed out | Used `--ink-2` for body prose | Prose is ALWAYS `--ink` (near-black on light); gray is chrome only |
| Accent band overpowers the page | Band too tall or image too bright | Keep band ≤120px (16:9) / ≤90px (portrait); the `--img-filter` + `.ab-overlay` mute it |
| Two colors creeping in (green/red deltas) | Off-palette second hue | Use `--red` for the ONE notable delta, `--ink-2` neutral for the rest |
| PDF prints at the wrong physical size | Wrong `--dpi` | `16:9` → 192, `a4`/`letter` → 300 |

## Related skills

- `/presentation` - the multi-slide sibling (16:9 deck → PDF). Use it when the content needs more than one page.
- **A diagram skill** (if installed) - if one block needs a real structured diagram, build it at the matching aspect and embed the PNG as an inline-media block (B11).
- **A single-image social skill** (if installed) - single social images, not dense documents.

## See also

- `brand_defaults.md` - palette, fonts, weight + prose-colour rules (swappable defaults, §0)
- `block_templates.md` - canvas, dual theme, dense type tier, block library, presets, density budget + fit rules
- `image_concepts.md` - accent-band concept library
