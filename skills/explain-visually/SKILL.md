---
name: explain-visually
description: "Explain a complex topic back to you with visuals - the right diagram for each facet (flowchart, timeline, sequence, schema/ER, state machine, chart, comparison, mind map) plus optional conceptual illustrations - rendered in a style you control, then bundled onto a single page. SELF-CONTAINED: it explains what was already discussed or provided; it does NOT research. Decomposes the topic into the facets that most need to be SEEN, picks a visual modality per facet, renders structural diagrams via themed Mermaid (HTML->PNG, $0) and conceptual facets via /create-explanatory-image, then composes /one-pager to assemble everything into one dense page + PDF. Pick the visual style with --style (brand-dark default, clean-light, blueprint, whiteboard, custom). Use when someone says \"explain this to me visually\", \"show me how this works\", \"diagram what we just discussed\", \"make this make sense\", or wants a visual brief of a topic."
category: visual-communication
automation: gated
argument-hint: "<topic or material to explain> [--style brand-dark|clean-light|blueprint|whiteboard|custom] [--format 16:9|a4|letter] [--max-visuals N] [--no-illustrations] [--autonomous] [--output-dir PATH]"
requires:
  env: [GEMINI_API_KEY, GOOGLE_API_KEY]
  binaries: [python3]
  packages: [playwright]
allowed-tools: Bash, Read, Write, Edit, Glob, AskUserQuestion, Skill
user-invocable: true
effort: high
metadata:
  version: "1.1"
  created: 2026-06-22
  author: Ability.ai
  changelog:
    - "1.1: Promoted to the public trinity-skills library — brand-dark preset now cites the vendored brand_defaults.md (swappable DEFAULT palette; the workspace's own design doc wins) instead of a private design-system path, render_html_to_png.py vendored into scripts/, --autonomous headless mode added so the skill is callable as one line, declared requires:/argument-hint + cold-start behavior"
    - "1.0 - initial: decompose topic -> pick modality per facet -> [GATE plan+style] -> render themed Mermaid + /create-explanatory-image -> [GATE visuals] -> compose /one-pager into a single page+PDF. Self-contained (no research). 4 styles + custom; brand-dark default."
---

# Explain Visually

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change - the top entry of `metadata.changelog` above - e.g. `explain-visually vX.Y - recent: <summary>`. Then proceed.

## Purpose

Explain a topic back to the reader **with the right picture for each part of it**. Where `/one-pager` distills text into a dense page and a diagram skill builds ONE brand-locked diagram for posting, this skill is a **comprehension tool**: it breaks a topic into the facets that most need to be *seen*, chooses the best **visual modality** per facet (flowchart, timeline, sequence, schema/ER, state machine, chart, comparison, mind map, or a conceptual illustration), renders each one in a **style you control**, and bundles the set onto a single page so you grasp the whole thing at once.

Two properties define it:

1. **Self-contained, no research.** It explains **what was already discussed or provided** - the current conversation, a paste, or a file. It does NOT browse, query knowledge bases, or pull external facts. If the discussion didn't establish a fact a visual needs, it marks `[NEEDS: ...]` and asks - it never invents.
2. **Style is a dial.** The locked brand is the *default* (`brand-dark`), but you can switch the whole visual language (`clean-light`, `blueprint`, `whiteboard`, or a `custom` brief). Every diagram in a run shares the chosen style.

The deliverable is a **single bundled page (+ PDF)** assembled by `/one-pager`, plus the individual visual PNGs kept for reuse.

## When to use

**Right tool when:**
- "Explain this to me visually" / "show me how this works" / "diagram what we just discussed" / "make this make sense"
- The topic has **internal structure worth seeing** - a process, a sequence, a system, an evolution, a set of trade-offs
- You want **several complementary visuals** (not one), each picked for what it shows best
- You want to **control the look** rather than accept the locked brand

**Wrong tool when:**
- You need ONE brand-locked diagram to **post** -> a diagram skill
- You need a multi-slide **deck** -> `/presentation`
- You need a dense **text** brief (mostly prose/stats, few diagrams) -> `/one-pager` directly
- A single generative infographic is enough -> `/create-explanatory-image`
- You need it to **research** a topic it doesn't already have material on -> this skill refuses; gather the material first (it is self-contained by design)

## What makes this distinct

| Approach | Trade-off |
|----------|-----------|
| a diagram skill | ONE human-composed diagram, brand-locked, for posting. No modality selection, no style control, single artifact. |
| `/create-explanatory-image` | ONE generative image, iterates to correctness. Great for a metaphor; not multi-modal, not assembled. |
| `/one-pager` | Dense single page from a brief - text-first. This skill is its **visual front-end**: it produces the *pictures*, then hands them to `/one-pager`. |
| **`/explain-visually` (this skill)** | Decomposes a topic into facets, picks the **right visual per facet**, renders in a **style you control**, bundles to one page. Mostly $0 (Mermaid); only conceptual-illustration facets cost ~$0.067 each. ~1-3 min. |

## State Dependencies

| Source | Location | Purpose |
|--------|----------|---------|
| Modality guide | `modality_guide.md` | Facet -> visual modality -> engine; per-modality Mermaid templates; node budget - read every time |
| Style library | `style_library.md` | The 4 styles + custom: Mermaid theme vars, render-wrapper HTML, illustration prompt fragment, `/one-pager` theme mapping - read every time |
| Brand defaults | `brand_defaults.md` (this skill) | Read **only when `--style brand-dark`** - **§0 first** (swappable defaults; the workspace's own design doc wins). Exact palette/fonts the brand-dark preset cites |
| Render script | `scripts/render_html_to_png.py` | Themed Mermaid HTML -> PNG via Playwright |

## Prerequisites & cold start

Script paths in this file are relative to **this skill's directory** — run them from there,
or prefix with the directory the skill was injected into.

| Requirement | Needed for | Missing → |
|---|---|---|
| `python3` + Playwright/Chromium | rendering every Mermaid visual | Report the install command (`pip install playwright && playwright install chromium`); **do not claim visuals that were never rendered**. |
| Network access at render time | Mermaid + Google Fonts load via CDN | See `style_library.md` for offline vendoring; without either, the render fails visibly rather than silently producing an unstyled diagram. |
| `GEMINI_API_KEY` (fallback `GOOGLE_API_KEY`) | conceptual-illustration facets only | Not fatal — proceed as if `--no-illustrations` was passed and say so in the delivery report. Held by the `/create-explanatory-image` child skill, which fails naming the key. Pure-Mermaid runs cost $0. |

## Headless mode (`--autonomous`)

This skill is **callable as one line** by a schedule, an orchestrator, or another agent
(the fleet's playbook-call convention). Invoked that way there is nobody to answer a gate,
so `--autonomous` must be passed and both gates are skipped. In that mode:

- The self-contained rule hardens: with no operator to ask, a bare topic with no material
  behind it is a **failed run** — report it and produce nothing. It is never a licence to
  research or to fill the topic from general knowledge.
- `[NEEDS:]` gaps are dropped from the visual and listed in the final report, never guessed.
- The style preset must be passed explicitly or the default applies; nothing else changes.

## Inputs

```
/explain-visually [source] [--style brand-dark|clean-light|blueprint|whiteboard|custom] [--format 16:9|a4|letter] [--max-visuals N] [--no-illustrations] [--autonomous] [--output-dir PATH]
```

| Flag | Default | Description |
|------|---------|-------------|
| `source` | (the conversation) | **What to explain.** If omitted, it explains **what was just discussed** (the current conversation + any material already in context). Can also be a topic we covered, a paste, or a file path. NEVER triggers research - if there's no substance to explain, it halts and asks. |
| `--style` | `brand-dark` | Visual language for ALL diagrams this run. See `style_library.md`. `custom` -> you describe the look and it maps to theme vars. |
| `--format` | `16:9` | Final bundled-page format (passed to `/one-pager`): `16:9` screen, `a4`/`letter` print. |
| `--max-visuals` | `5` | Cap on visuals (facets). The decomposition keeps the highest-signal facets up to this cap. |
| `--no-illustrations` | (off) | Mermaid/structural diagrams only - skip all `/create-explanatory-image` facets. $0, faster, fully deterministic. |
| `--autonomous` | (off) | Headless mode for scheduled/unattended runs: skip both approval gates. See Headless mode above. |
| `--output-dir` | `explain_{slug}/` | Where `visuals/`, the HTML sources, and the final PDF land. Relative to the working directory unless given absolutely. |

### Content model (LOCKED): explain, don't research; structure, don't fabricate

- The skill's job is to **re-present material that already exists** in the discussion/source as visuals. The *structure* and *teaching framing* are the skill's synthesis - that's expected and good.
- **Facts, numbers, names, and claims must come from the source/discussion.** If a visual needs a specific fact the discussion never established, leave a `[NEEDS: ...]` marker and surface it at Gate 1. Do not guess, and do not reach for outside knowledge to fill it.
- If the source is a bare topic with no substance behind it ("explain quantum gravity") and nothing was discussed, **halt** and ask what material to explain. This skill does not research.

## Composes

- `/one-pager` - bundles the rendered visuals into the single page + PDF (the deliverable). Always invoked.
- `/create-explanatory-image` - renders any **conceptual-illustration** facet (a metaphor / rich visual that no structural diagram captures). Invoked per such facet unless `--no-illustrations`.

Called by their **unversioned** names so child fixes propagate. Structural diagrams are rendered in-skill (themed Mermaid -> `render_html_to_png.py`); Mermaid is a tool, not a skill, so it is used directly.

## Process (transactional)

ultrathink - the load-bearing reasoning here is **decomposition + modality matching** (Step 2): choosing *which* facets of the topic to show and the *right* visual type for each is what makes the explanation land. Reason carefully about what the reader actually needs to see before picking diagrams, and confirm at Gate 1 before spending any render time.

### Step 1: Read state

1. Read `modality_guide.md` (facet -> modality -> engine; Mermaid templates; node budget).
2. Read `style_library.md` (the styles, render wrapper, theme mapping).
3. If `--style brand-dark`, also read `brand_defaults.md` (§0 override first) for the exact palette/fonts the preset cites.

### Step 1.5: Resolve flags + identify the source

- Resolve `--style` (default `brand-dark`), `--format`, `--max-visuals`, `--no-illustrations`. Derive a `{slug}`; set `--output-dir` to `{output-dir}/`.
- Identify the source: by default it is **what was discussed before** (the current conversation + material already in context). If a paste/topic/file is given, use that instead.
- If `--style custom`, ask the user for a one-paragraph style brief (background, line/text color, accent, font feel, mood) before proceeding.
- If there is no real substance to explain, **halt** and ask for the material. Do not research.

### Step 2: Decompose the topic into visual facets

Identify the **3-6 facets** (capped by `--max-visuals`) that most need to be *seen* to understand the topic. For each facet, pick a **modality + engine** using `modality_guide.md`'s decision table, e.g.:

- a process / decision logic -> **flowchart** (Mermaid)
- ordering / evolution / roadmap -> **timeline** (Mermaid)
- who-does-what over time / a protocol -> **sequence diagram** (Mermaid)
- system structure / components -> **architecture / block** (Mermaid) or an illustration
- entities & relations / a data model -> **ER / class** (Mermaid)
- lifecycle / modes -> **state machine** (Mermaid)
- quantities / proportions / trend -> **chart** (Mermaid `pie` / `xychart`)
- X vs Y trade-offs -> **comparison** (Mermaid `quadrant` or an HTML table)
- how it all hangs together / taxonomy -> **mind map** (Mermaid)
- a metaphor no structural diagram captures -> **conceptual illustration** (`/create-explanatory-image`)

Assign each facet a **priority** (must-keep / trimmable / nice-to-have). Order the facets into the reading sequence that best teaches the topic (usually: orient -> mechanism -> detail -> synthesis).

### Step 3: Draft each visual's content

- **Mermaid facets:** pick the Mermaid diagram type and write the node/edge labels - **telegraphic** (2-5 words). Hold the **node budget** (<= ~10-12 nodes per diagram; if a facet needs more, split it into two or simplify). Draft from the templates in `modality_guide.md`.
- **Illustration facets:** write the concept brief you'll hand to `/create-explanatory-image`, plus the style's image-prompt fragment from `style_library.md`.
- Mark any missing fact as `[NEEDS: ...]`.

### Step 4: [APPROVAL GATE 1 - PLAN + STYLE] Confirm the visual plan *(skipped with `--autonomous`)*

**LOCKED first gate. No rendering, no image generation, no PDF until approved.** This is where modality choices, the teaching order, the style, and any `[NEEDS]` gaps get settled - all free to change here.

Present the plan compactly - the topic, the style, and the ordered facet list with each facet's modality + a one-line content sketch. Example shape:

```
EXPLAIN-VISUALLY · {slug}   ·   style: brand-dark   ·   format 16:9   ·   bundle: /one-pager

1. FLOWCHART   "How a request flows through the system"
     Ingest -> Plan -> Delegate -> Verify -> Respond   (5 nodes)
2. SEQUENCE    "Orchestrator <-> worker handoff"
     User -> Orchestrator -> Worker -> Orchestrator -> User
3. COMPARISON  "Shallow vs deep agents"
     axes: memory, planning, delegation, autonomy
4. TIMELINE    "How we got here"
     2023 prompts · 2024 tools · 2025 agents · 2026 departments
5. MIND MAP    "The four pillars, at a glance"   [nice-to-have]

[NEEDS]  facet 4 has no dates for the 2025 milestone - confirm or drop
```

Then use `AskUserQuestion`:
> "Approve this visual plan for {slug}? Want to change a modality, the order, the style, which facets, or fill the [NEEDS] gaps before I render?"

Options:
- **Approve - render it** -> Step 5
- **Edit the plan** -> change modality / order / facets / fill `[NEEDS]`, re-show this gate
- **Change style** -> switch `--style` (re-read `style_library.md` for it), re-show
- **Cancel** -> stop, spend nothing

Once approved, write the locked plan to `{output-dir}/plan.md`. DO NOT render until this gate returns "Approve".

### Step 5: Render the visuals in the chosen style

For each **Mermaid facet** (in order):
1. Author a themed HTML file from the **render wrapper** in `style_library.md`, injecting the style's Mermaid `themeVariables` + page CSS + the diagram definition. Save to `{output-dir}/visuals/NN_{slug}.html`.
2. Render at device-scale 2, using the per-modality canvas defaults from `modality_guide.md`:
   ```bash
   python3 scripts/render_html_to_png.py {output-dir}/visuals/NN_{slug}.html {output-dir}/visuals/NN_{slug}.png \
     --width {W} --height {H} --device-scale 2
   ```

For each **illustration facet** (skip if `--no-illustrations`):
```
Invoke `/create-explanatory-image` with the facet's concept brief + the style's image-prompt fragment, --output-dir {output-dir}/visuals/, matching aspect.
```

Verify each PNG is non-blank and nothing is clipped (see Error Recovery for the blank-Mermaid fix).

### Step 6: [APPROVAL GATE 2 - VISUALS] Confirm the rendered set *(skipped with `--autonomous`)*

**LOCKED second gate. No bundling until the visuals are approved.** A correct plan can still render with a clipped diagram, a wrong label, or an off illustration.

`Read` each PNG in `{output-dir}/visuals/` inline so the user sees the full set. Then use `AskUserQuestion`:
> "Here are the {N} visuals in {style}. Approve them for the bundled page, or fix a diagram / re-style / re-order first?"

Options:
- **Approve - bundle the page** -> Step 7
- **Fix a visual** -> edit that diagram's labels/type (or re-run the illustration), re-render, re-show
- **Re-style** -> switch `--style`, re-author the wrapper(s), re-render, re-show
- **Cancel** -> stop, don't bundle

DO NOT compose `/one-pager` until this gate returns "Approve".

### Step 7: Bundle into a single page - compose /one-pager

Hand the approved visuals to `/one-pager` as a **structured block list** (it styles a structured list verbatim rather than re-distilling): a header (topic title + one-line framing), then each visual as an **inline-media block** pointing at its rendered PNG path with a telegraphic caption, in the approved order.

```
Invoke `/one-pager` with that structured source, plus:
  --theme {dark for brand-dark|blueprint, light for clean-light|whiteboard}
  --format {--format}
  --output-dir {output-dir}
```

`/one-pager` owns the single-page fit-guard + PDF assembly and runs its own content/visual confirmation on the final page - tell the user that final page approval happens inside `/one-pager`. Note: the bundled-page **chrome** follows `/one-pager`'s brand; the **visuals** carry the chosen `--style`. `brand-dark` is the most coherent pairing (which is why it's the default); for other styles the diagrams keep their look while the page frame stays branded.

### Step 8: Report the deliverable

Report:
- The **single-page PDF path** (the deliverable) + its page size, from `/one-pager`
- The `visuals/` folder (each diagram PNG, reusable on its own)
- The output directory
- Style used, and the modality of each visual (e.g. "flowchart, sequence, comparison, timeline")
- Any `[NEEDS]` gaps filled at Gate 1
- Anything `/one-pager` tightened to keep it on one page

### Step 9: Iterate

| Change request | How to handle |
|---|---|
| Fix a diagram's label/type | Edit that visual's HTML/definition, re-render, re-bundle via `/one-pager` |
| Different style | Switch `--style`, re-author wrappers, re-render all, re-bundle |
| Add / drop a facet | Re-plan that facet (Gate 1 if adding), render it, re-bundle |
| Wrong illustration | Re-run `/create-explanatory-image` for that facet, re-bundle |
| Make it a deck instead of a page | Re-bundle with `/presentation` instead of `/one-pager` |

### Step 10: Persist

- Keep the full `{output-dir}` (plan.md, `visuals/`, HTML sources, PDF) as the reproducible record.
- Delivery beyond the local output directory (upload, send, publish) is the calling agent's job, not this skill's.

## Completion Checklist

- [ ] Source identified (conversation / paste / file); if bare, material was gathered - **nothing researched, nothing fabricated**
- [ ] Topic decomposed into <= `--max-visuals` facets, each with a justified modality and a teaching order
- [ ] Every `[NEEDS: ...]` gap filled or resolved at Gate 1
- [ ] **Gate 1 (plan + style)** returned Approve; `plan.md` written
- [ ] Each Mermaid visual rendered in the chosen style at device-scale 2; each illustration rendered (or `--no-illustrations` honored)
- [ ] No visual is blank or clipped (node budget held)
- [ ] **Gate 2 (visuals)** returned Approve
- [ ] `/one-pager` composed with the visuals as inline-media + matching `--theme`; single-page PDF produced
- [ ] Output dir retained; Drive upload done if requested
- [ ] Final report delivered: PDF path + page size, visuals folder, style, per-visual modality

## Error Recovery

| Failure | Recovery |
|---|---|
| Source is a bare topic with no material | Halt at Step 1.5 and ask what to explain. NEVER research or fabricate to fill it - self-contained is the contract. |
| Mermaid PNG renders blank/partial | The CDN/ESM render hadn't finished at screenshot. Re-run the render (CDN now warm); if it persists, vendor `mermaid@11` locally and reference it via `file://` (see `style_library.md`). |
| A diagram is clipped / overflows the canvas | Too many nodes. Reduce to the node budget, split the facet into two visuals, or raise that visual's canvas height; re-render. Never ship a clipped diagram. |
| Mermaid syntax error (empty/garbled SVG) | Validate the diagram definition against the template in `modality_guide.md`; fix the syntax (often a reserved char in a label - quote it), re-render. |
| `/create-explanatory-image` fails | Retry once. If it still fails, drop that facet to a structural diagram or omit it (note the omission). Never block the deliverable on one illustration. |
| Playwright / Chromium render fails | Confirm Playwright + Chromium installed, retry. Report the exact error; do not bundle from stale/partial PNGs. |
| `/one-pager` can't fit everything on one page | Drop the lowest-priority visual(s) and re-bundle, or switch `--format a4` for more room. The single-page guarantee is `/one-pager`'s; respect it. |

## Output

Return:
- The single-page **PDF** path (the deliverable) + page size
- The `visuals/` folder (individual diagram PNGs)
- Output directory (plan.md, visuals, HTML sources, PDF)
- Style + per-visual modality
- Inline preview of the visuals and/or the final page
- Any `[NEEDS]` filled and anything `/one-pager` tightened

## Common issues

| Symptom | Diagnosis | Fix |
|---------|-----------|-----|
| Diagrams all look the same flavor | Defaulted every facet to flowchart | Re-read `modality_guide.md`; match the modality to what each facet actually *shows* (timeline for evolution, sequence for handoffs, etc.) |
| Visual reads as a "wall of nodes" | Over the node budget | Split into two diagrams or simplify; <= ~10-12 nodes each |
| Style looks off-brand for `brand-dark` | Didn't read `design_system.md` | brand-dark cites the locked palette/fonts - read it and use the exact values |
| Page chrome clashes with a non-brand style | `/one-pager` chrome is brand-locked | Expected; the visuals carry the style. Use `brand-dark` for full coherence, or accept frame/visual divergence |
| It tried to look something up | Ignored the self-contained rule | Stop. Explain only the discussed/provided material; mark gaps `[NEEDS]` |

## Related skills

- `/one-pager` - the bundler this composes; use it directly when the content is text-first with few diagrams.
- **A diagram skill** (if installed) - one brand-locked diagram for posting (not multi-modal, not style-switchable).
- `/create-explanatory-image` - one generative infographic; composed here for conceptual facets.
- `/presentation` - swap in for `/one-pager` when you want a deck instead of a single page.

## See also

- `modality_guide.md` - facet -> modality -> engine; Mermaid templates; node budget
- `style_library.md` - the styles, the themed render wrapper, the `/one-pager` theme mapping
- `brand_defaults.md` - the default brand spec that `brand-dark` cites (swappable, §0)
