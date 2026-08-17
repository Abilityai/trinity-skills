# One-Pager Block Templates

This file defines the **block-level structure** for `/one-pager`. Palette philosophy, fonts, weight rule, imagery lineage - all inherited from `brand_defaults.md` (this skill; read its §0 brand override FIRST - the values are swappable defaults and the consuming workspace’s own design doc wins over them). What lives HERE is one-pager-specific: the single-page canvas, the dual theme (dark + light), the **dense** type tier, and the reusable block library that composes onto a flat row/flex grid.

A one-pager is the **density inverse of `/presentation`**: where a slide holds one idea at projection scale, a one-pager holds an entire briefing at read-up-close scale. Everything below is tuned for "understand the whole thing in one page."

---

## Canvas + formats

`/one-pager` renders **one** HTML file to **one** PNG, then wraps it as a **single-page PDF**. There is never a page 2.

| Format (flag) | CSS canvas | Render @2x | PDF DPI | When |
|---|---|---|---|---|
| **`16:9` (DEFAULT)** | **1920 × 1080** | 3840 × 2160 | 192 | Screen / dashboard / embed-in-deck. Wide rows fit 3-6 KPI cards side by side. |
| `a4` | 1240 × 1754 | 2480 × 3508 | 300 | Print-ready A4 portrait (international). Narrative-first vertical stacking. |
| `letter` | 1275 × 1650 | 2550 × 3300 | 300 | Print-ready US Letter portrait (US audiences). |
| `a4-landscape` | 1754 × 1240 | 3508 × 2480 | 300 | Print A4 landscape - dashboard density on paper. |

Render ALWAYS at `--device-scale 2` (small dense type must stay crisp). The @2x column is the actual PNG size; the DPI column is what `build_pdf.py` stamps so the PDF page is physically correct.

```css
html, body { margin: 0; padding: 0; }
* { box-sizing: border-box; }
body {
  background: var(--bg);
  color: var(--ink);
  font-family: 'DM Sans', system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
}
.page {
  position: relative;
  width: 1920px; height: 1080px;   /* swap per format table above */
  background: var(--bg);
  display: flex; flex-direction: column;
  overflow: hidden;                /* enforces the single page; fit-guard measures true scrollHeight */
  padding: 56px 72px 0;            /* footer supplies its own bottom padding */
}
```

Load fonts (same as every brand skill):
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

---

## Dual theme (LOCKED palettes)

Dark is the default and is byte-identical to the brand system. Light is a print-friendly variant - the ONLY place in Ruby's asset library where the canvas is not black, justified because printed/shared one-pagers waste ink on a black field. Set the theme with `data-theme` on the `<html>` element (dark = no attribute, light = `data-theme="light"`).

```css
:root {                              /* DARK (default) */
  --bg: #000000;
  --bg-card: #0F0F12;
  --bg-card-alt: #0A0A0C;
  --ink: #FFFFFF;                    /* primary text - ALL prose */
  --ink-2: #9DA2BC;                  /* secondary: chrome labels, fact keys, deltas-neutral */
  --ink-3: #555766;                  /* tertiary: footer, axis, rules */
  --red: #B85050;                    /* muted brick red accent - the brand signal */
  --red-dim: #4A2A2A;
  --red-soft: rgba(184,80,80,0.10);
  --border: #2A2A30;
  --rule: #2A2A30;
  --img-filter: saturate(0.92) brightness(0.84);
}
[data-theme="light"] {               /* LIGHT (print-friendly) */
  --bg: #F4F2ED;                     /* warm paper, not pure white (softer in print) */
  --bg-card: #FFFFFF;
  --bg-card-alt: #FBFAF7;
  --ink: #17171A;                    /* near-black primary text */
  --ink-2: #5A5C68;
  --ink-3: #8A8C98;
  --red: #B14444;                    /* a touch deeper for contrast on white */
  --red-dim: #E2C4C4;
  --red-soft: rgba(177,68,68,0.06);
  --border: #E3E0D8;
  --rule: #E3E0D8;
  --img-filter: saturate(0.98) brightness(0.99);
}
```

**Prose colour rule (inherited, both themes):** every paragraph the reader is meant to *read* is `var(--ink)` (white on dark, near-black on light). `--ink-2` / `--ink-3` are for chrome ONLY (mono labels, fact keys, axis labels, footer, neutral deltas). Never downshift body prose to gray.

**Accent discipline (inherited):** `--red` appears sparingly - eyebrow, the one hero number, the winning comparison cell, the CTA, a single `.accent` word in a callout. No off-palette colors. **No green/red up-down duo** on deltas (that introduces a second hue) - use `--red` for the one notable delta and `--ink-2` for the rest.

---

## Type tier - one-pager DENSE scale (LOCKED)

A one-pager is read **up close** (on a laptop full-screen, or printed in hand), not glanced at in a 400px mobile feed. So it deliberately goes **below the design system's 26px mobile-feed floor**. This is the same kind of medium-specific exception `/presentation` took in the opposite direction (it went *bigger* for projection). The one-pager floor is **17px** (sources/footnotes only); anything carrying meaning stays **>= 22px**.

### Default `16:9` (1920×1080) tier

| Role | Size | Font / weight |
|---|---|---|
| Page title | **60px** | DM Sans 700 |
| Value-prop (header sub) | 28px | DM Sans 400, prose colour |
| Hero-stat number | **92px** | DM Sans 700 |
| Hero-stat unit | 44px | DM Sans 700, `--ink-2` |
| KPI value | **52px** | DM Sans 700 |
| Block / section title | 30px | DM Sans 500 |
| Callout quote | 30px | DM Sans 500 |
| Body prose | **24px** | DM Sans 400, line-height 1.4 |
| Bullet / dense body | 23px | DM Sans 400, line-height 1.32 |
| Table cell / fact value | 22px | DM Sans 400 / 500 |
| Caption / secondary | 20px | DM Sans 400, `--ink-2` |
| Eyebrow / mono label | 20px | JetBrains Mono 500 caps |
| KPI label / fact key / axis | 18-20px | JetBrains Mono 500 caps |
| Footer / chrome | 18px | JetBrains Mono 500 caps |
| Source / footnote (FLOOR) | **17px** | JetBrains Mono 400 |

### Portrait `a4` / `letter` (1240-1275 wide) tier

Narrower canvas → step the display sizes down so titles don't crowd. Body stays at the ~10pt print sweet spot.

| Role | Size | Role | Size |
|---|---|---|---|
| Page title | **52px** | Body prose | **21px** (≈10pt) |
| Hero-stat number | **78px** | Bullet / dense | 20px |
| KPI value | **46px** | Caption | 18px |
| Block title | 27px | Eyebrow / chrome | 17-18px |
| Callout quote | 27px | Source / footnote (FLOOR) | **14px** (≈6.5pt) |

**WEIGHT RULE (inherited, with the `/presentation` display exception):** body is 400, sub-heads/labels are 500, and the big **display tier (page title, hero-stat, KPI value)** may use **700** - this is the same exception `/presentation` made for its display titles. Bold is NEVER used inside running body prose; emphasis there is the single red `.accent` span only.

---

## Grid - flat row / flex model

The body is a vertical stack of **rows**; each row is a flex container of **blocks**. This is deliberately simpler than CSS-grid auto-placement: it makes the layout predictable and lets the fit-guard measure one clean `scrollHeight`.

```css
.page-body {
  flex: 1 0 auto;            /* grow to fill, but NEVER shrink below content (so overflow is honest, not hidden as overlap) */
  display: flex; flex-direction: column;
  gap: 28px;                 /* inter-row breathing room; tighten to 20/16 under fit pressure */
  padding: 28px 0;
}
.row { display: flex; gap: 24px; align-items: stretch; }
.row > .block { flex: 1 1 0; min-width: 0; }   /* equal split by default */
.block.w2 { flex-grow: 2; }                    /* 2:1 widths -> main + sidebar */
.block.w3 { flex-grow: 3; }
.block.w4 { flex-grow: 4; }

.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 22px 26px;
}
```

A full-width block is simply the only child of its row. A `main + fact-rail` split is `<div class="row"><div class="block w2">…</div><div class="block w1">…</div></div>` (the rail at `flex-grow:1`).

---

## Page chrome - header, footer, accent band

### Accent band (thin brand signature - DEFAULT, omit with `--no-image`)

A slim full-bleed soft-futurism strip at the very top. Purely visual (no baked text); it blends into the canvas at its lower edge so the header sits on flat `--bg`. ~120px on 16:9, ~90px on portrait.

```html
<div class="page">
  <div class="accent-band">
    <img src="file:///.../accent_band.png">
    <div class="ab-overlay"></div>
  </div>
  <div class="page-header"> … </div>
  <div class="page-body"> … </div>
  <div class="page-footer"> … </div>
</div>
```

```css
.accent-band {
  position: relative;
  width: calc(100% + 144px);     /* cancel the .page horizontal padding for full bleed */
  margin: -56px -72px 24px;      /* cancel the .page top padding too */
  height: 120px; overflow: hidden;
}
.accent-band img {
  width: 100%; height: 100%;
  object-fit: cover; object-position: center 50%;
  filter: var(--img-filter); transform: scale(1.07); transform-origin: center;
}
.ab-overlay {                    /* fade the band's bottom into the canvas, theme-aware */
  position: absolute; inset: 0;
  background: linear-gradient(180deg, rgba(0,0,0,0) 35%, var(--bg) 100%);
}
```
Portrait: `margin: -40px -56px 18px; height: 90px;` (matches the portrait page padding).

### Header

```html
<div class="page-header">
  <div>
    <div class="eyebrow">Company One-Pager · 2026</div>
    <h1 class="ph-title">Ability<span class="accent">.ai</span></h1>
    <p class="ph-valueprop">Deploy an entire autonomous department in the cloud - not just an agent on your laptop.</p>
  </div>
  <div class="ph-wordmark">trinity.ability.ai</div>
</div>
```

```css
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 32px;
  padding-bottom: 22px; border-bottom: 1px solid var(--rule); }
.eyebrow { font-family: 'JetBrains Mono'; font-weight: 500; font-size: 20px; letter-spacing: 0.2em;
  text-transform: uppercase; color: var(--red); margin: 0 0 12px; }
.ph-title { font-family: 'DM Sans'; font-weight: 700; font-size: 60px; line-height: 1.0;
  letter-spacing: -0.02em; color: var(--ink); margin: 0; }
.ph-title .accent { color: var(--red); }
.ph-valueprop { font-family: 'DM Sans'; font-weight: 400; font-size: 28px; line-height: 1.3;
  color: var(--ink); margin: 12px 0 0; max-width: 1200px; }
.ph-wordmark { font-family: 'JetBrains Mono'; font-weight: 500; font-size: 20px; letter-spacing: 0.16em;
  text-transform: uppercase; color: var(--ink-2); text-align: right; white-space: nowrap; padding-top: 8px; }
```

### Footer + CTA (always last, CTA flush right = Z-pattern endpoint)

```html
<div class="page-footer">
  <span>{Author} · {org} · {year}</span>
  <span class="cta">→ {call to action}</span>
</div>
```

```css
.page-footer { display: flex; justify-content: space-between; align-items: center;
  padding: 18px 0 24px; border-top: 1px solid var(--rule);
  font-family: 'JetBrains Mono'; font-weight: 500; font-size: 18px; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--ink-3); }
.page-footer .cta { color: var(--red); }
```

---

## Block library

Each block is a self-contained component you drop into a row. A one-pager = header + an ordered list of rows of blocks + footer. Use the smallest set of blocks that tells the story; density comes from picking the right block, not from cramming.

### B1 · Hero-stat (the single visual anchor)

One huge number. Use AT MOST ONE per page - it's the thing the eye lands on first.

```html
<div class="block card herostat">
  <div class="hs-value">72<span class="unit">K</span></div>
  <div class="hs-label">YouTube subscribers</div>
  <div class="hs-delta">+18K in 90 days</div>
</div>
```
```css
.herostat { display: flex; flex-direction: column; justify-content: center; }
.hs-value { font-family: 'DM Sans'; font-weight: 700; font-size: 92px; line-height: 0.92;
  letter-spacing: -0.03em; color: var(--ink); }
.hs-value .unit { font-size: 44px; color: var(--ink-2); margin-left: 4px; }
.hs-label { font-family: 'JetBrains Mono'; font-weight: 500; font-size: 22px; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--ink-2); margin-top: 12px; }
.hs-delta { font-family: 'DM Sans'; font-weight: 500; font-size: 22px; color: var(--red); margin-top: 8px; }
```

### B2 · KPI strip (3-6 stat cards in a row)

The density workhorse. Summary numbers up top, right under the header. Cap at 6.

```html
<div class="row">
  <div class="block card kpi"><div class="k-value">3.2×</div><div class="k-label">ARR growth</div><div class="k-delta">YoY</div></div>
  <div class="block card kpi"><div class="k-value">94%</div><div class="k-label">Net retention</div><div class="k-delta neutral">trailing 12mo</div></div>
  <div class="block card kpi"><div class="k-value">40+</div><div class="k-label">Enterprise pilots</div><div class="k-delta neutral">active</div></div>
</div>
```
```css
.kpi { display: flex; flex-direction: column; gap: 8px; justify-content: center; }
.k-value { font-family: 'DM Sans'; font-weight: 700; font-size: 52px; line-height: 0.92;
  letter-spacing: -0.02em; color: var(--ink); }
.k-label { font-family: 'JetBrains Mono'; font-weight: 500; font-size: 20px; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--ink-2); }
.k-delta { font-family: 'DM Sans'; font-weight: 500; font-size: 22px; color: var(--red); }
.k-delta.neutral { color: var(--ink-2); }   /* use red for the ONE notable, neutral for the rest */
```

### B3 · Two-column prose (problem / solution narrative)

CSS columns force a short measure (the readability win at small type). Keep to ~70 words.

```html
<div class="block card">
  <div class="block-title">The problem</div>
  <div class="prose two-col">
    <p>Local AI agents run on one laptop, forget between sessions, and never get governed. Enterprises can't ship them.</p>
    <p>Trinity runs whole departments of agents in the cloud - persistent memory, audit trails, approval gates, self-hosted.</p>
  </div>
</div>
```
```css
.block-title { font-family: 'DM Sans'; font-weight: 500; font-size: 30px; line-height: 1.05;
  letter-spacing: -0.01em; color: var(--ink); margin: 0 0 14px; }
.block-eyebrow { font-family: 'JetBrains Mono'; font-weight: 500; font-size: 18px; letter-spacing: 0.16em;
  text-transform: uppercase; color: var(--red); margin: 0 0 10px; }
.prose { font-family: 'DM Sans'; font-weight: 400; font-size: 24px; line-height: 1.4; color: var(--ink); margin: 0; }
.prose p + p { margin-top: 14px; }
.two-col { column-count: 2; column-gap: 36px; }
.two-col p { break-inside: avoid; }
```

### B4 · Bullet list (front-loaded, red arrow markers)

```html
<div class="block card">
  <div class="block-title">What we ship</div>
  <ul class="bullets">
    <li><span class="arrow">→</span><span><span class="b-label">Orchestration</span>Deploy multi-agent departments, not single agents.</span></li>
    <li><span class="arrow">→</span><span><span class="b-label">Sovereignty</span>Self-hosted. Data never leaves your perimeter.</span></li>
    <li><span class="arrow">→</span><span><span class="b-label">Governance</span>Audit trails, approval gates, role-based access.</span></li>
  </ul>
</div>
```
```css
.bullets { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 14px; }
.bullets li { display: grid; grid-template-columns: 26px 1fr; gap: 12px;
  font-family: 'DM Sans'; font-weight: 400; font-size: 23px; line-height: 1.32; color: var(--ink); }
.bullets .arrow { color: var(--red); }
.bullets .b-label { font-family: 'JetBrains Mono'; font-weight: 500; font-size: 18px; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--ink-2); display: block; margin-bottom: 4px; }
```

### B5 · Comparison table (us vs them / tiers / before-after)

```html
<div class="block card">
  <div class="block-title">Local agents vs Trinity</div>
  <table class="cmp">
    <thead><tr><th></th><th>Local agent</th><th>Trinity</th></tr></thead>
    <tbody>
      <tr><td class="col-axis">Scope</td><td>One agent</td><td class="highlight">A department</td></tr>
      <tr><td class="col-axis">Memory</td><td>Forgets</td><td class="highlight">Persistent</td></tr>
      <tr><td class="col-axis">Governance</td><td>None</td><td class="highlight">Full audit</td></tr>
    </tbody>
  </table>
</div>
```
```css
.cmp { width: 100%; border-collapse: collapse; }
.cmp th, .cmp td { text-align: left; padding: 12px 16px; border-bottom: 1px solid var(--border);
  font-family: 'DM Sans'; font-size: 22px; font-weight: 400; color: var(--ink); }
.cmp thead th { font-family: 'JetBrains Mono'; font-weight: 500; font-size: 19px; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--ink-2); border-bottom: 1px solid var(--rule); }
.cmp tbody tr:last-child td { border-bottom: none; }
.cmp .col-axis { font-family: 'JetBrains Mono'; font-size: 19px; letter-spacing: 0.08em;
  text-transform: uppercase; color: var(--ink-3); }
.cmp .highlight { color: var(--red); font-weight: 500; }   /* the winning column */
```

### B6 · Timeline / process strip (horizontal milestones)

```html
<div class="block card">
  <div class="block-title">Roadmap</div>
  <div class="timeline">
    <div class="tl-step"><span class="dot"></span><div class="tl-when">Q1</div><div class="tl-what">Open source</div><div class="tl-desc">Trinity GA on GitHub.</div></div>
    <div class="tl-step"><span class="dot"></span><div class="tl-when">Q2</div><div class="tl-what">Agent Hub</div><div class="tl-desc">Marketplace launch.</div></div>
    <div class="tl-step"><span class="dot"></span><div class="tl-when">Q3</div><div class="tl-what">Enterprise</div><div class="tl-desc">SOC2 + SSO.</div></div>
  </div>
</div>
```
```css
.timeline { display: flex; gap: 0; align-items: flex-start; }
.tl-step { flex: 1; position: relative; padding: 34px 18px 0 0; }
.tl-step::before { content: ''; position: absolute; top: 11px; left: 0; right: 0; height: 2px; background: var(--border); }
.tl-step .dot { position: absolute; top: 5px; left: 0; width: 14px; height: 14px; border-radius: 50%; background: var(--red); }
.tl-when { font-family: 'JetBrains Mono'; font-weight: 500; font-size: 18px; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--red); }
.tl-what { font-family: 'DM Sans'; font-weight: 500; font-size: 23px; color: var(--ink); margin-top: 6px; line-height: 1.15; }
.tl-desc { font-family: 'DM Sans'; font-weight: 400; font-size: 20px; color: var(--ink-2); margin-top: 4px; line-height: 1.25; }
```

### B7 · Quote / callout (thesis, testimonial, key insight)

```html
<div class="block callout">
  <p class="q">"Don't run an agent on your laptop. Deploy an entire <span class="accent">autonomous department</span> in the cloud."</p>
  <div class="src">{Author} · {role}, {org}</div>
</div>
```
```css
.callout { border-left: 3px solid var(--red); padding: 6px 0 6px 24px; display: flex; flex-direction: column; justify-content: center; }
.callout .q { font-family: 'DM Sans'; font-weight: 500; font-size: 30px; line-height: 1.2;
  letter-spacing: -0.01em; color: var(--ink); margin: 0; }
.callout .q .accent { color: var(--red); }
.callout .src { font-family: 'JetBrains Mono'; font-weight: 500; font-size: 18px; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--ink-2); margin-top: 12px; }
```

### B8 · Icon-grid (capabilities / use cases / values)

Author the SVG inline; `stroke="currentColor"` so it inherits `--red`. No icon-font libraries.

```html
<div class="block card">
  <div class="block-title">Capabilities</div>
  <div class="icon-grid">
    <div class="ig-item">
      <svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>
      <div><div class="ig-label">Persistent memory</div><div class="ig-desc">Context across sessions.</div></div>
    </div>
    <!-- repeat 3-6 items -->
  </div>
</div>
```
```css
.icon-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px 22px; }
.ig-item { display: grid; grid-template-columns: 44px 1fr; gap: 14px; align-items: start; }
.ig-item .ico { width: 40px; height: 40px; color: var(--red); }
.ig-label { font-family: 'DM Sans'; font-weight: 500; font-size: 22px; color: var(--ink); line-height: 1.1; }
.ig-desc { font-family: 'DM Sans'; font-weight: 400; font-size: 19px; color: var(--ink-2); margin-top: 3px; line-height: 1.25; }
```

### B9 · Fact-rail / sidebar (at-a-glance key:value stack)

Lives in the narrow column (`block w1` beside a `w2` main). Quick facts that don't need prose.

```html
<div class="block card fact-rail">
  <div class="block-title">At a glance</div>
  <div class="fr-row"><span class="fr-key">Founded</span><span class="fr-val">2024</span></div>
  <div class="fr-row"><span class="fr-key">HQ</span><span class="fr-val">Remote</span></div>
  <div class="fr-row"><span class="fr-key">Stage</span><span class="fr-val">Seed</span></div>
  <div class="fr-row"><span class="fr-key">License</span><span class="fr-val">Open source</span></div>
</div>
```
```css
.fact-rail { display: flex; flex-direction: column; }
.fr-row { display: flex; justify-content: space-between; gap: 16px; padding: 11px 0; border-bottom: 1px solid var(--border); }
.fr-row:last-child { border-bottom: none; }
.fr-key { font-family: 'JetBrains Mono'; font-weight: 500; font-size: 18px; letter-spacing: 0.08em;
  text-transform: uppercase; color: var(--ink-2); }
.fr-val { font-family: 'DM Sans'; font-weight: 500; font-size: 22px; color: var(--ink); text-align: right; }
```

### B10 · Mini-chart (author-drawn inline SVG)

Simple bar/line drawn by hand from the data (no chart libraries). One highlight bar in `--red`, the rest `--ink-3`. Always pair with a one-line takeaway.

```html
<div class="block card">
  <div class="block-title">ARR by quarter</div>
  <svg class="bars" viewBox="0 0 420 180" preserveAspectRatio="none">
    <rect x="10"  y="120" width="70" height="60"  fill="var(--ink-3)"/>
    <rect x="100" y="90"  width="70" height="90"  fill="var(--ink-3)"/>
    <rect x="190" y="60"  width="70" height="120" fill="var(--ink-3)"/>
    <rect x="280" y="20"  width="70" height="160" fill="var(--red)"/>
  </svg>
  <div class="chart-take">3.2× ARR in 12 months.</div>
</div>
```
```css
.bars { width: 100%; height: 150px; display: block; }
.chart-take { font-family: 'DM Sans'; font-weight: 500; font-size: 22px; color: var(--ink); margin-top: 12px; }
```

### B11 · Inline media (optional contained image - product shot, embedded diagram PNG, soft-futurism)

Use only when a picture genuinely earns its space. Soft-futurism heroes come from `/nano-banana-image-generator`; a PNG from a diagram skill can be embedded here too.

```html
<div class="block media-card"><img src="file:///.../inline_media.png"></div>
```
```css
.media-card { border-radius: 12px; overflow: hidden; border: 1px solid var(--border); background: var(--bg-card); }
.media-card img { width: 100%; height: 100%; object-fit: cover; filter: var(--img-filter); transform: scale(1.06); display: block; }
```

### B12 · Section divider (color-coded region label)

A thin labelled rule to separate major regions when the page has distinct zones.

```html
<div class="block divider"><span class="d-label">Traction</span><span class="d-rule"></span></div>
```
```css
.divider { display: flex; align-items: center; gap: 16px; }
.d-label { font-family: 'JetBrains Mono'; font-weight: 500; font-size: 18px; letter-spacing: 0.2em;
  text-transform: uppercase; color: var(--red); }
.d-rule { flex: 1; height: 1px; background: var(--rule); }
```

---

## Layout presets (starting compositions)

Pick the preset that matches the source's intent, then trim/swap blocks. These are starting points, not cages.

### Preset A · Company / org one-pager (DEFAULT for "understand the company")
```
accent-band
header               (name + value-prop + wordmark)
row: hero-stat  | KPI-strip (3)            (B1 w1 | B2 w2)
row: two-col prose (problem/solution) w2 | fact-rail w1   (B3 | B9)
row: icon-grid (capabilities)              (B8)
row: timeline (roadmap)                    (B6)
footer + CTA
```

### Preset B · Dashboard / status update
```
header
row: KPI-strip (4-6)                       (B2)
row: mini-chart | mini-chart | callout     (B10 | B10 | B7)
row: comparison table w2 | fact-rail w1    (B5 | B9)
footer
```

### Preset C · Topic / briefing explainer (any subject)
```
accent-band
header               (topic title + one-line thesis)
row: callout (the thesis)                  (B7)
row: two-col prose w2 | bullets w1         (B3 | B4)
row: comparison table                      (B5)
row: timeline (how it works / history)     (B6)
footer
```

---

## Density budget + fit rules (LOCKED - the single-page guarantee)

A one-pager that needs a page 2 has failed. Two mechanisms keep it on one page:

### 1. Pre-render density budget (a lint, applied before authoring HTML)

| Limit | Value |
|---|---|
| Total word count | **~450 words** (hard ceiling ~550) |
| Hero-stat blocks | **1** |
| KPI cards | **<= 6** |
| Prose blocks | **<= 2** (each <= ~70 words) |
| Bullets per list | **<= 6**, each 1-2 lines |
| Callouts | **<= 2** |
| Timeline steps | **<= 5** |
| Rows in the body | **<= 6** (16:9) / **<= 8** (portrait) |

If the distilled content exceeds the budget, tighten the CONTENT (telegraphic rewrites, drop the weakest block) before rendering - never plan to "shrink the font to fit."

**Starting-spacing calibration (16:9, by body-row count).** The "comfortable" spacing (gap 28 / card padding 22-26 / band 120) suits a sparse page; a denser page needs tighter starting values or it overflows and forces the ladder on every render. Author with these starting values so the first render lands at/near fit:

| Body rows | Row gap | Card padding | Accent band | Body padding |
|---|---|---|---|---|
| 1-2 (sparse) | 28px | 22px 26px | 120px | 28px 0 |
| 3 | 22px | 20px 24px | 110px | 22px 0 |
| 4 | 16px | 16px 24px | 96px | 16px 0 |
| 5-6 (dense) | 12px | 14px 22px | 88px | 14px 0 |

Portrait (a4/letter) has ~50% more vertical room than 16:9, so it can hold one more row at the same tier. The fit-guard + ladder remain the backstop - these starts just minimize re-renders.

**Layout invariant (LOCKED):** `.page-body` must be `flex: 1 0 auto` (grow, NEVER shrink). A shrinking body hides overflow as content-over-footer overlap that `scrollHeight` won't report - which is exactly the bug the fit-guard's three-signal measurement (page overflow + body overflow + footer overlap) exists to catch.

### 2. Post-render fit-guard (mechanical, every render)

After rendering, run `scripts/check_fit.py` - it measures the `.page` element's true `scrollHeight` against its fixed height. Exit 0 = fits, exit 3 = overflow (with the overflow in px). On overflow, apply the **tightening ladder** in order and re-render until it fits:

1. Rewrite the longest prose/bullets telegraphically (biggest, cheapest win)
2. Reduce row gap (`28px → 22px → 18px`) and card padding (`22px 26px → 16px 20px`)
3. Drop the lowest-priority block (the one that adds least to "understand it in one page")
4. **Last resort:** step the whole type tier down one notch (e.g. body 24→22, title 60→54) - never below the 17px source floor

Each block should carry an implicit **priority** (header/footer/value-prop/hero-stat = must-keep; supporting prose/icon-grid/timeline = trimmable; nice-to-have media/second callout = first to go). The ladder drops from lowest priority up.

---

## Forbidden patterns (inherited + one-pager specific)

- Spilling to a second page (the whole point of the skill is one page)
- Non-`--bg` canvas (the only sanctioned light surface is the `data-theme="light"` palette above; no other colors)
- Pure alarm red `#FF4444` (always the muted `--red`)
- Off-palette accents, or a **second hue** (no green/red delta duo - use red + neutral gray)
- Emoji as design elements
- Bold (700) inside running body prose - display tier only; emphasis in prose is the single `.accent` span
- Body prose in `--ink-2`/gray (prose is always `--ink`)
- Icon-font libraries (Font Awesome, Feather) or chart libraries - author inline SVG
- Text below the 17px floor (sources only at 17px; meaning-carrying text >= 22px on 16:9)
- A hero image that eats the page (the spec is a THIN accent band; the page is information-first)
