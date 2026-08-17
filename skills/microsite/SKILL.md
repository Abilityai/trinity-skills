---
name: microsite
description: Build a brand-locked, animated single-page microsite (locked to YOUR palette - the shipped tokens are a swappable default) - a self-contained scrolling HTML page that presents any topic or dataset as a visual story with text, diagrams, charts, KPI strips, and canvas animation, plus optional print-stylesheet PDF export. The web-native sibling of /one-pager (dense PDF page) and /presentation (slide deck) - the mother skill for "make me a nice web page about X". Use for daily/status reports as web pages, topic explainers, workshop pages, project/product showcases, briefing sites. Composes /explain-visually thinking, /create-explanatory-image, /animated-explainer, and the dataviz method behind one consistent UI. Use when someone wants an animated report, a scrolling explainer page, a workshop microsite, or "present this beautifully in the browser".
category: visual-communication
automation: gated
argument-hint: "<source material or path> [--preset report|explainer|showcase] [--theme dark|light] [--autonomous] [--pdf] [--inline] [--share] [--output-dir PATH]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Skill, AskUserQuestion
user-invocable: true
effort: high
requires:
  env: [GEMINI_API_KEY, GOOGLE_API_KEY, VERCEL_TOKEN]
  binaries: [python3]
  packages: [playwright]
metadata:
  version: "1.5"
  created: 2026-07-29
  author: Ability.ai
  changelog:
    - "1.5: Promoted to the public trinity-skills library — brand-neutralized (page_templates.md §0 makes the palette a swappable DEFAULT and defers to the consuming workspace's own design doc; the discipline rules stay locked), --share made headless-capable via VERCEL_TOKEN, Drive delivery removed, skill-relative script paths, sibling-skill references made optional, declared requires:/argument-hint + cold-start behavior"
    - "1.4: Print trap - .count spans print as $0 (observer-gated); every count-up needs a print-only .pn twin with the final value (recipe in page_templates.md §7)"
    - "1.3: Canvas trap documented in page_templates.md §6 - absolutely-positioned canvas needs explicit width/height:100% (replaced element stays at intrinsic 300x150 under inset:0 alone; symptom: drawing huddles top-left)"
    - "1.2: --share hardened to PRIVATE-share semantics (operator directive) - unguessable URLs (96-bit secrets token in the project name, wildcard cert so the hostname stays out of CT logs) + non-indexable (X-Robots-Tag noindex/nofollow/noarchive via staged vercel.json AND meta robots injected into the staged copy; local file untouched); scope auto-resolution for non-interactive CLI; robust URL parse"
    - "1.1: --share flag - post-approval publish to Vercel as a unique shareable URL (scripts/share_vercel.py; project-per-share microsite-{slug}-{id}; production deploy so no Vercel preview-auth wall; page stays up until removed - removal one-liner reported; requires authenticated Vercel CLI)"
    - "1.0: Initial version - shell + section grammar + animation rig distilled from a workshop explainer page, tokens reconciled with a locked design system (3 documented web-tier deviations), two-gate flow mirroring the one-page sibling, --autonomous mode for scheduled report runs, check_page.py verification rig + export_pdf.py print-stylesheet PDF"
---

# Microsite

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change - the top entry of `metadata.changelog` above - e.g. `microsite vX.Y - recent: <summary>`. Then proceed.

ultrathink

## Purpose

Turn any topic or dataset into a **brand-locked, animated, self-contained web page** - a
scrolling visual story with a hero, KPI strips, diagrams, charts, timelines, and canvas
animation, all on one consistent UI defined in `page_templates.md`. The deliverable is an
HTML file (plus `assets/`) that opens in a browser; a print-stylesheet **PDF is an
optional companion**, never the point.

This is the **web-native tier of the family**:

| Skill | Medium | Density | Deliverable |
|---|---|---|---|
| `/one-pager` † | one fixed page | maximal | 1-page PDF |
| `/presentation` † | slides | one idea/slide | multi-page PDF |
| `/explain-visually` † | one bundled page | diagram-heavy | 1-page PDF |
| `/animated-explainer` | canvas film | one mechanism | live film / MP4 |
| **`/microsite`** | **scrolling page** | **one section/idea** | **HTML in the browser (+ PDF)** |

† separate skills that may not be installed in your workspace. This skill **never requires
them** — it degrades to authoring the section itself. Only `/animated-explainer` and the
imagery skills below are true optional collaborators.

## When to use

**Right tool when:**
- "Make me a nice web page about X" / "present this beautifully" / an animated report
- A daily/status **report** that should be *read*, not just filed (KPIs, findings, actions)
- A **topic explainer or workshop page** (the canonical exemplar this shell was distilled from)
- A **project/product showcase** with narrative + screenshots + proof
- The content has 5+ distinct facets that deserve their own scroll sections

**Wrong tool when:**
- The deliverable must be a **PDF/print artifact** → a one-page or deck skill (this one's `--pdf` is a companion, not the point)
- One mechanism needs a **time-based film** with narration → `/animated-explainer` (this skill embeds or links its output for a single animated section)
- One diagram or image → `/create-explanatory-image` or a diagram skill
- A real multi-page **website** with routing/deploy → a site-scaffolding skill or the site's own agent
- Research is needed first - this skill presents material it's given; it does NOT research

## State Dependencies

| Source | Location | Read | Write |
|---|---|---|---|
| Page shell, tokens, section grammar, animation rig | `page_templates.md` (this skill) | ✅ every run | ❌ |
| Brand tokens + override rules | `page_templates.md` §0 (defaults) and the workspace's own design doc if it has one — **that doc wins** | ✅ | ❌ |
| Chart method | a `dataviz`-style chart skill, if installed | ✅ when a section charts data | ❌ |
| Verification rig | `scripts/check_page.py` | run | ❌ |
| PDF export | `scripts/export_pdf.py` | run | ❌ |
| Vercel share deploy | `scripts/share_vercel.py` (needs `VERCEL_TOKEN`) | run when `--share` | ❌ |
| The page + assets | `{output-dir}/{slug}.html` + `assets/` | ✅ | ✅ |
| Locked content record | `{output-dir}/source.md` | ✅ | ✅ |

## Composes

| Skill | When |
|---|---|
| `/create-explanatory-image` | A section needs a conceptual illustration (iterates to correctness) |
| `/nano-banana-image-generator` | A section needs a plain soft-futurism hero/media image |
| `/animated-explainer` | A section deserves a full data-driven film (embed or link its output) |

Invoke children by name (unversioned); never inline their steps or call their internal
scripts directly.

## Prerequisites & cold start

Script paths below are relative to **this skill's directory** - run them from there, or
prefix with the directory the skill was injected into.

| Requirement | Needed for | Missing → |
|---|---|---|
| `python3` + Playwright/Chromium | Step 7 verification, Step 9 PDF | Report the install command (`pip install playwright && playwright install chromium`); **never claim verification that didn't run**. |
| `GEMINI_API_KEY` (fallback `GOOGLE_API_KEY`) | generated imagery only | Not fatal - build the page imagery-free (the grammar degrades gracefully) and say so in the delivery report. Imagery-free runs cost $0. |
| `VERCEL_TOKEN` | `--share` only | Fail that step naming the key (`VERCEL_TOKEN not set - add it to this agent's credentials`); the local page is still THE deliverable. An interactively-logged-in Vercel CLI also works for a human at a terminal, but a headless agent needs the token. |

## Inputs

```
/microsite [source] [--preset report|explainer|showcase] [--theme dark|light]
           [--autonomous] [--pdf] [--inline] [--share] [--output-dir PATH]
```

| Flag | Default | Description |
|---|---|---|
| `source` | (required) | The material: a brief, file path(s), session data, pasted notes, or "what we just discussed". **This skill distills; it never invents facts.** A bare topic with no substance halts with a request for raw material. |
| `--preset` | auto-inferred | Section composition starting point (see `page_templates.md` §5): `report` (KPIs + findings + actions), `explainer` (agenda + mechanism + rules), `showcase` (narrative + frames + proof). |
| `--theme` | `dark` | `dark` = the near-black canvas of the default palette. `light` = warm-paper variant (`data-theme="light"`). Print always renders light. Both palettes are swappable per `page_templates.md` §0. |
| `--autonomous` | (off) | Skip both approval gates for scheduled/headless runs (e.g. a daily report). `[NEEDS:]` facts are **omitted** (never guessed) and listed in the final report. |
| `--pdf` | (off) | Also export the print-stylesheet PDF companion. |
| `--inline` | (off) | Single-file build: base64-embed images within the 1.5MB budget (`page_templates.md` §8). Default is a sibling `assets/` folder. |
| `--share` | (off) | After Gate 2 approval, publish the page to Vercel as a **private share link** via `scripts/share_vercel.py`: a throwaway project per share named `ms-{24 hex chars}` - **hard to guess** (96 random bits, no content hint in the hostname; kept short because Vercel truncates long names in the URL, which would cut the entropy; wildcard `*.vercel.app` cert keeps the hostname out of certificate-transparency logs) and **non-indexable** (`X-Robots-Tag: noindex, nofollow, noarchive` header + injected `meta robots`, local file untouched). Reachable only by people given the link. Production deploy (Vercel's preview URLs sit behind an auth wall that would block recipients). The page does NOT auto-expire; "temporary" = removable with the reported one-liner (`echo y \| vercel project rm <project>`). Requires the Vercel CLI plus `VERCEL_TOKEN` (or an interactively logged-in CLI). Can also be requested at Gate 2 without the flag. |
| `--output-dir` | see below | Where the page lands. Default: `session-files/{YYYY-MM-DD}_{slug}_microsite/` if the workspace has a `session-files/` convention, else `./microsite_{slug}/`. Never a scratchpad - the page is a durable deliverable. |

## Process (transactional)

ultrathink - the reasoning-heavy steps are the content architecture (Step 3: what earns a
section, what carries each one) and reconciling real data with the story (no invented
numbers, unfinished parts shown unfinished).

### Step 1: Read state

1. Read `page_templates.md` fully - **§0 brand override first**, then tokens, section
   grammar, animation vocabulary, print rules, asset policy. The shell is forked, never
   re-invented.
2. Resolve the brand: if the workspace has its own design/brand document, port its tokens
   into §2 and let it override every default. Otherwise ship the defaults.
3. If any section will chart real data, load a `dataviz`-style chart skill if one is
   installed before writing chart code; otherwise follow §5 S10.
4. If imagery will be generated, follow the imagery rules in §5 S11 and §8.

### Step 2: Classify the source + resolve flags

- Derive `{slug}`; resolve `--preset` (infer from intent: recurring data snapshot →
  `report`; teaching a topic → `explainer`; selling/presenting a thing → `showcase`),
  `--theme`, `--output-dir`.
- Classify the source: substantive material (proceed) vs bare topic (**halt and ask for
  the raw material** - facts, numbers, structure. Never fabricate. In `--autonomous`
  mode, a bare-topic source is a failed run: report it, produce nothing).
- **Interrogate any data before designing the story** (inherited from
  `/animated-explainer`): check what the numbers actually support; a trend that's noise
  or a sampling artifact doesn't get a section.

### Step 3: Content architecture

Plan the page as an ordered list of sections from the grammar (`page_templates.md` §5):
for each - `id`, section type (S1-S13), the one idea it carries, the content
(telegraphic), the visual (inline SVG diagram / chart / media / canvas), and the
animation notes (what reveals, what counts, what draws in). Decide whether the page
needs semantic concept colors (≥3 recurring concepts) or stays red+grayscale.

Mark every fact the source doesn't supply as `[NEEDS: ...]`. Keep 6-10 sections; if the
plan exceeds that, cut the weakest - a microsite that scrolls forever is a document that
should have been a `/one-pager`.

### Step 4: [APPROVAL GATE 1 - PLAN + CONTENT] *(skipped with `--autonomous`)*

Present the full section plan as markdown - reading order, each section's type, content,
visual, and animation - with `[NEEDS:]` gaps surfaced prominently. Ask via
`AskUserQuestion`: approve / edit sections / cancel. Nothing renders and no imagery
spends until approved. Write the locked plan to `{output-dir}/source.md`.

In `--autonomous` mode: drop `[NEEDS:]` items from the page, log them for the final
report, and proceed.

### Step 5: Build the visuals

Per the plan, in this order (cheap before costly):
- **Inline SVG diagrams** - hand-authored per the §5 S9 recipe (or pre-rendered themed
  Mermaid SVG, inlined).
- **Charts** - inline SVG per the chart method (§5 S10); real data only.
- **Canvas inserts** - per the §6 canvas rig (DPR cap, reduced-motion static frame,
  visibility-gated rAF). A section needing a narrated film → invoke `/animated-explainer`.
- **Generated imagery** - invoke `/create-explanatory-image` (conceptual) or
  `/nano-banana-image-generator` (scene); textless, film-matte-cropped; save to `assets/`.

### Step 6: Author the page

Fork the shell skeleton from `page_templates.md` §4 into `{output-dir}/{slug}.html`:
tokens + type tier + shell CSS + only the section CSS the plan uses + the §6 interaction
rig + the §7 print stylesheet (required even without `--pdf`). Nav links for every
section. Footer stamps the data/canon date. Honor the asset policy (§8).

### Step 7: Verify

```bash
python3 scripts/check_page.py {output-dir}/{slug}.html
```

Exit 0 = clean; exit 3 = issues in the JSON report (console errors, horizontal overflow,
broken images). Fix and re-run until clean. Then **look at every section screenshot**
(the rig saves them to `{output-dir}/checks/`) with the Read tool - the script catches
mechanical breakage; only eyes catch a cramped grid, an unreadable chart, a hero scrim
that kills the canvas. Also re-check at mobile width:
`check_page.py {slug}.html --width 390 --no-shots`.

### Step 8: [APPROVAL GATE 2 - VISUAL] *(skipped with `--autonomous`)*

Open the page for the operator (`open {output-dir}/{slug}.html`) and ask via `AskUserQuestion`:
approve / fix a section / regenerate an image / switch theme / share a link / cancel. Loop
through Steps 5-7 for fixes. No PDF export, Drive upload, Vercel share, or "done" claim
until approved.

### Step 9: Optional PDF companion

If `--pdf` (or asked at the gate):

```bash
python3 scripts/export_pdf.py {output-dir}/{slug}.html
```

Print stylesheet renders the light theme, reveals everything, freezes canvases at their
final frame. Skim the PDF - it's a companion, but a broken companion still ships your name.

### Step 10: Deliver + persist

- Report the page path (THE deliverable), the `checks/` screenshots, the PDF if built.
- Open the output dir in the OS file browser if the workspace has that convention; open the
  page in the browser if not already done at Gate 2.
- Keep the full output dir (HTML, assets/, source.md, checks/) as the reproducible record.
- If `--share` (or asked at Gate 2): AFTER approval, run
  `python3 scripts/share_vercel.py {output-dir}/{slug}.html`
  - it stages `index.html` + `assets/`, injects the noindex meta + `vercel.json`
  X-Robots-Tag header, and deploys a throwaway Vercel project with an **unguessable
  96-bit name** (`ms-{24 hex}` - private share: only people given the link can find
  it; no search indexing; no content hint in the hostname). Verify the header landed
  (`curl -sI <url> | grep -i x-robots-tag`). Report the share URL **and the removal
  one-liner** from the script's JSON (`echo y | vercel project rm <project>`) - the
  page stays up until removed. Never share an unapproved page; in `--autonomous` mode
  share only when the flag was explicitly passed, and include the URL in the final
  report.
- If the run produced a surfaceable result on a schedule (autonomous report mode) and
  `mcp__trinity__report` is available, publish a short report
  (`report_type: microsite.build`, markdown display hint: page path + sections +
  omitted `[NEEDS:]` list). Skip silently when the tool is absent.

## Completion Checklist

- [ ] Source was substantive; zero invented facts; `[NEEDS:]` gaps resolved (gated) or omitted + reported (autonomous)
- [ ] Data interrogated - no section animates a number the data doesn't support
- [ ] Section plan fits the grammar; 6-10 sections; semantic colors only if ≥3 bound concepts
- [ ] Gate 1 approved (or `--autonomous`); `source.md` written
- [ ] Page authored from the shared shell - not a bespoke shell; brand resolved per §0
      (workspace design doc if present, defaults otherwise)
- [ ] `check_page.py` exit 0 at 1440 AND 390 widths; every section screenshot eyeballed
- [ ] Reduced-motion + print stylesheet present; page reads correctly with animation off
- [ ] Asset policy honored (folder default / ≤1.5MB inline)
- [ ] Gate 2 approved (or `--autonomous`)
- [ ] Delivered: page opened, folder opened, paths reported; PDF built if requested; footer stamps the data date
- [ ] If shared: deploy ran only after approval; share URL AND removal command reported

## Error Recovery

| Failure | Recovery |
|---|---|
| Bare topic, no substance | Halt and ask (gated) / fail the run with a clear report (autonomous). NEVER pad with invented content. |
| Image generation fails | Retry once; then ship the section imagery-free (the grammar degrades gracefully) and note it. Never block the page on a picture. |
| Playwright/Chromium missing | Report install command; do not claim verification that didn't run. |
| check_page.py won't go clean | Fix the page, not the checker. Horizontal overflow = wide content escaping its scroll container (§9); console errors usually = the interaction rig referencing a section id that doesn't exist. |
| Canvas insert misbehaves | Its reduced-motion static frame is the fallback: gate the rAF loop off and ship the still. A canvas is never allowed to break the page. |
| PDF looks wrong | Fix the print stylesheet (§7), re-export. Don't hand-edit the PDF; don't let PDF needs distort the web page - the page is primary. |
| `--inline` exceeds budget | Switch to `assets/` folder layout and say so. |
| Vercel share deploy fails | Check `VERCEL_TOKEN` (or `vercel whoami`) and the CLI install; retry once. The local page is still THE deliverable - report it delivered and the share as failed with the fix. Never block delivery on the share. |

## Related skills

- `/animated-explainer` - the film tier; this skill embeds its output for animated sections
- `/create-explanatory-image`, `/nano-banana-image-generator` - the imagery collaborators
- Optional, if installed: one-page/deck/diagram siblings for print-native deliverables, and
  a `dataviz`-style chart skill for S10 sections

## Self-Improvement

After completing this skill's primary task, consider tactical improvements:

- [ ] **Review execution**: friction points, unclear steps, inefficiencies?
- [ ] **New trap or recipe found?** A layout/animation/print bug that cost real time goes
      into `page_templates.md` (recipe) or this file's Error Recovery (trap), symptom-first
- [ ] **Scope check**: tactical/execution changes only - NOT core purpose
- [ ] **Apply improvement**: edit SKILL.md / page_templates.md; bump `metadata.version`
      and prepend a `changelog` entry
- [ ] **Version control** (if in a git repository): `git add` the skill dir, commit as
      `refactor(microsite): <brief improvement>`
