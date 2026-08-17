# Presentation Slide Templates

This file defines the **slide-level structure** for `/presentation`. Palette, typography roles, weight rule, imagery system - all inherited from `brand_defaults.md` (this skill; read its §0 brand override FIRST - the values are swappable defaults and the consuming workspace's own design doc wins over them). What lives HERE is presentation-specific: the 16:9 canvas, the five slide-type layouts, and the projection type-scale.

## Canvas

All slides: **1920×1080** (16:9 native projection / screen-share aspect). Pure flat black canvas (`var(--bg)`). The picture-card or full-bleed hero carries the warmth/atmosphere; surrounding canvas stays flat black so the deck reads as one designed asset.

```css
html, body {
  margin: 0; padding: 0;
  background: var(--bg);
  color: var(--white);
  font-family: 'DM Sans', system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
  width: 1920px; height: 1080px;
  overflow: hidden;
}
.slide {
  width: 1920px; height: 1080px;
  box-sizing: border-box;
  background: var(--bg);
  position: relative;
}
```

## Type scale - presentation tier (LOCKED)

Presentations read at projection / screen-share distance (3-30 ft), not at mobile-feed distance. Type sizes are **larger than the mobile-feed image tier** to compensate. This is the LOCKED scale - do not invent sizes.

| Text role | Size | Font | Use |
|-----------|------|------|-----|
| **Cover hook** | **160px** DM Sans 700, line-height 0.96 | Display | Slide 01 title - the talk's headline |
| **Cover deck** | **44px** DM Sans 400, line-height 1.3 | Body | Slide 01 subtitle - one short sentence below the hook |
| **Section number** | **120px** JetBrains Mono 500, red | Display chrome | Section dividers - "PART 02" |
| **Section title** | **128px** DM Sans 700, line-height 0.98 | Display | Section dividers - the part name |
| **Content title** | **92px** DM Sans 700, line-height 0.98 | Display | Content slide headings |
| **Content body / bullet** | **40px** DM Sans 400, line-height 1.28 | Body | Bullets on content slides |
| **Content bullet label** | **26px** JetBrains Mono 500 caps, gray-2 | Body chrome | Optional mono label above each bullet for taxonomy |
| **Statement** | **104px** DM Sans 700, line-height 1.05 | Display | Statement slides - the manifesto / quote |
| **Statement attribution** | **32px** JetBrains Mono 500 caps, red | Display chrome | Statement slides - the source / speaker |
| **Closing title** | **120px** DM Sans 700, line-height 0.96 | Display | Final slide - "Thanks." / "Build something real." |
| **Eyebrow** | **28px** JetBrains Mono 500 caps, red, 0.22em tracking | Chrome | Top eyebrow strip on content slides |
| **Footer** | **26px** JetBrains Mono 500 caps, gray-3, 0.14em tracking | Chrome | Brand + page progress |

**MINIMUM SIZE RULE (LOCKED, inherited from design_system.md):** every text element >= 26px in the 1920 canvas. Chrome at 26-30px, body content at 38-44px, display at 80-160px.

**WEIGHT RULE (LOCKED, inherited):** no bold anywhere by default. Bold (700+) appears ONLY on the `.accent` span inside a title - a single emphasized word that gets the muted-red color too.

## Slide-progress footer (LOCKED)

Every slide except `cover` and `closing` carries the same footer band:

```html
<div class="footer">
  <span>{Speaker} · {org}</span>
  <span class="page-num"><span class="current">03</span> / 12</span>
</div>
```

```css
.footer {
  position: absolute;
  left: 80px; right: 80px;
  bottom: 36px;
  display: flex; justify-content: space-between; align-items: center;
  font-family: 'JetBrains Mono', monospace;
  font-size: 26px;
  letter-spacing: 0.14em;
  color: var(--gray-3);
  text-transform: uppercase;
  font-weight: 500;
}
.page-num .current { color: var(--red); }
```

The cover and closing slides drop the footer (the cover has its own speaker/date strip, the closing replaces the footer with contact info).

## Layouts

Five slide types. Each one is a separate HTML template that imports the same fonts and `:root` palette from the design system.

---

### 1. Cover

Slide 01. Sets the talk's headline + speaker + date. **Full-bleed hero with text overlay** (Universe A or B). The cover IS the visual hook - go big on the headline.

**Structure:**
```
+----------------------------------------------------------+
| [full-bleed hero, scale(1.07) film-matte crop]           |
| [linear gradient: dark left bottom -> transparent top]   |
|                                                          |
|  EYEBROW · DECK · SECTION  (mono, red, 28px)             |
|                                                          |
|  THE WORKSHOP TITLE.                                     |
|  ONE LINE OR TWO.                                        |
|  (DM Sans 700, 160px, white, accent word in red)         |
|                                                          |
|  One-sentence deck describing what the talk delivers.    |
|  (DM Sans 400, 44px, gray-2)                             |
|                                                          |
|  {SPEAKER} · {DATE} · {ORG}                 |
|  (mono caps, 28px, gray-3, bottom strip)                 |
+----------------------------------------------------------+
```

**HTML skeleton:**
```html
<div class="slide stage-cover">
  <div class="hero-bg"><img src="file:///.../slide_01_hero_source.png"></div>
  <div class="hero-overlay"></div>
  <div class="content">
    <div class="eyebrow">Agent Architecture · Workshop Series</div>
    <h1 class="cover-title">Decomposition isn't<br>the <span class="accent">win</span>.</h1>
    <p class="cover-deck">Why most "AI agents" plateau at planning - and what the architecture of an agent that actually ships looks like.</p>
  </div>
  <div class="cover-strip">
    <span>{Speaker}</span>
    <span>June 2026</span>
    <span>ability.ai</span>
  </div>
</div>
```

**Cover-specific CSS** (palette + fonts come from the design system; sizes from the tier above):
```css
.stage-cover .hero-bg { position: absolute; inset: 0; overflow: hidden; }
.stage-cover .hero-bg img {
  width: 100%; height: 100%;
  object-fit: cover; object-position: center 45%;
  filter: saturate(0.92) brightness(0.84);
  transform: scale(1.07); transform-origin: center;
}
.stage-cover .hero-overlay {
  position: absolute; inset: 0;
  background:
    linear-gradient(135deg, rgba(0,0,0,0.92) 0%, rgba(0,0,0,0.55) 40%, rgba(0,0,0,0.0) 75%),
    linear-gradient(180deg, rgba(0,0,0,0) 50%, rgba(0,0,0,0.55) 80%, rgba(0,0,0,0.85) 100%);
}
.stage-cover .content {
  position: absolute; inset: 0;
  padding: 96px 96px 200px;
  display: flex; flex-direction: column; justify-content: flex-end;
}
.stage-cover .eyebrow { font-size: 28px; }   /* see chrome tier */
.stage-cover .cover-title {
  font-family: 'DM Sans'; font-weight: 700;
  font-size: 160px; line-height: 0.96; letter-spacing: -0.02em;
  color: var(--white); margin: 28px 0 32px;
}
.stage-cover .cover-title .accent { color: var(--red); }
.stage-cover .cover-deck {
  /* Prose colour rule (design_system.md): cover deck is ALWAYS white, never gray. */
  font-family: 'DM Sans'; font-weight: 400;
  font-size: 44px; line-height: 1.3; color: var(--white);
  margin: 0; max-width: 1400px;
}
.stage-cover .cover-strip {
  position: absolute; left: 96px; right: 96px; bottom: 60px;
  display: flex; gap: 48px;
  font-family: 'JetBrains Mono'; font-weight: 500;
  font-size: 28px; letter-spacing: 0.16em;
  color: var(--gray-3); text-transform: uppercase;
}
```

---

### 2. Section

A divider between major parts of the talk. Massive number + section name. Full-bleed hero. **Minimal text** so the hero gets to breathe and the audience knows "we're shifting gears."

**Structure:**
```
+----------------------------------------------------------+
| [full-bleed hero with subtle dark gradient]              |
|                                                          |
|              PART 02 (mono red, 120px)                   |
|              ──────                                      |
|              DELEGATION. (DM Sans 700, 128px)            |
|                                                          |
|                                            [footer 02/12]|
+----------------------------------------------------------+
```

**HTML skeleton:**
```html
<div class="slide stage-section">
  <div class="hero-bg"><img src="file:///.../slide_05_hero_source.png"></div>
  <div class="hero-overlay"></div>
  <div class="content">
    <div class="section-num">Part 02</div>
    <div class="section-rule"></div>
    <h1 class="section-title">Delegation.</h1>
  </div>
  <div class="footer">
    <span>{Speaker} · {org}</span>
    <span class="page-num"><span class="current">05</span> / 12</span>
  </div>
</div>
```

**Section-specific CSS:**
```css
.stage-section .hero-overlay {
  background:
    linear-gradient(180deg, rgba(0,0,0,0.25) 0%, rgba(0,0,0,0.55) 50%, rgba(0,0,0,0.92) 100%);
}
.stage-section .content {
  position: absolute; inset: 0;
  padding: 0 96px;
  display: flex; flex-direction: column;
  justify-content: center; align-items: center;
  text-align: center;
}
.stage-section .section-num {
  font-family: 'JetBrains Mono'; font-weight: 500;
  font-size: 120px; letter-spacing: 0.08em;
  color: var(--red); text-transform: uppercase;
  line-height: 1.0;
}
.stage-section .section-rule {
  width: 96px; height: 4px; background: var(--red);
  margin: 32px 0 36px;
}
.stage-section .section-title {
  font-family: 'DM Sans'; font-weight: 700;
  font-size: 128px; line-height: 0.98; letter-spacing: -0.02em;
  color: var(--white); margin: 0;
}
```

---

### 3. Content (the workhorse - reuses the design system picture-card)

The most common slide. Picture-card on one side + title + bullets on the other. Uses the **picture-card placement** described in `brand_defaults.md` §4 (textless imagery, dimmed under text) - see the design system. This is the same layout demonstrated in `examples/example_content_slide.html`.

**Structure:**
```
+----------------------------------------------------------+
| EYEBROW · MODULE (mono red, 28px)                        |
|                                                          |
| +-------------+  TITLE                                   |
| | picture-    |  Two lines max at 92px DM Sans 700       |
| | card        |                                          |
| | (1:1 hero,  |  → LABEL                                 |
| |  scale 1.07)|    Bullet body 40px white                |
| |             |  → LABEL                                 |
| |             |    Bullet body 40px white                |
| |             |  → LABEL                                 |
| |             |    Bullet body 40px white                |
| +-------------+                                          |
|                                                          |
| {SPEAKER} · {ORG}                  03 / 12     |
+----------------------------------------------------------+
```

**HTML skeleton:**
```html
<div class="slide stage-content">
  <div class="content-wrap">
    <div class="eyebrow">Agent Architecture · Module 03</div>
    <div class="main">
      <div class="picture-card">
        <img src="file:///.../slide_03_hero_source.png">
      </div>
      <div class="text-stack">
        <h1 class="content-title">Decomposition<br>isn't the <span class="accent">win</span>.</h1>
        <ul class="bullets">
          <li>
            <span class="arrow">→</span>
            <span>
              <span class="bullet-label">Planning</span>
              Splitting a task into steps is table stakes. Every framework does it.
            </span>
          </li>
          <li>
            <span class="arrow">→</span>
            <span>
              <span class="bullet-label">The real moat</span>
              Memory, delegation, recovery from your own bad output.
            </span>
          </li>
          <li>
            <span class="arrow">→</span>
            <span>
              <span class="bullet-label">Test</span>
              If your agent can't revise itself mid-run, it's a chatbot in a wrapper.
            </span>
          </li>
        </ul>
      </div>
    </div>
  </div>
  <div class="footer">
    <span>{Speaker} · {org}</span>
    <span class="page-num"><span class="current">03</span> / 12</span>
  </div>
</div>
```

**Content-specific CSS:**
```css
.stage-content .content-wrap {
  position: absolute; inset: 0;
  padding: 56px 80px 100px;
  display: grid;
  grid-template-rows: auto 1fr;
  row-gap: 36px;
}
.stage-content .eyebrow {
  font-family: 'JetBrains Mono'; font-weight: 500;
  font-size: 28px; letter-spacing: 0.22em;
  color: var(--red); text-transform: uppercase;
  line-height: 1.0;
}
.stage-content .main {
  display: grid;
  grid-template-columns: 840px 1fr;
  column-gap: 72px;
  align-items: start;
}
/* Variant: picture-right - swap grid-template-columns to "1fr 840px" and reverse children order */

.stage-content .picture-card {
  width: 840px; height: 860px;
  border-radius: 18px;
  border: 1px solid var(--border);
  overflow: hidden;
  background: var(--bg-card);
}
.stage-content .picture-card img {
  width: 100%; height: 100%;
  object-fit: cover; object-position: center center;
  filter: saturate(0.92) brightness(0.84);
  transform: scale(1.07); transform-origin: center;
}

.stage-content .text-stack { padding-top: 8px; }
.stage-content .content-title {
  font-family: 'DM Sans'; font-weight: 700;
  font-size: 92px; line-height: 0.98; letter-spacing: -0.02em;
  color: var(--white); margin: 0 0 44px 0;
}
.stage-content .content-title .accent { color: var(--red); }

.stage-content .bullets {
  list-style: none; margin: 0; padding: 0;
  display: flex; flex-direction: column; row-gap: 28px;
}
.stage-content .bullets li {
  display: grid;
  grid-template-columns: 40px 1fr;
  column-gap: 12px;
  font-family: 'DM Sans'; font-weight: 400;
  font-size: 40px; line-height: 1.28;
  color: var(--white);
}
.stage-content .bullets .arrow {
  color: var(--red); font-weight: 500; line-height: 1.28;
}
.stage-content .bullets .bullet-label {
  font-family: 'JetBrains Mono'; font-weight: 500;
  font-size: 26px; letter-spacing: 0.14em;
  color: var(--gray-2); text-transform: uppercase;
  display: block; margin-bottom: 6px;
}
```

**Placement variant rule:** alternate `picture-left` (default) and `picture-right` across consecutive content slides for compositional rhythm. Same logic as a social-carousel skill's TOP / BOTTOM alternation.

---

### 4. Statement

A single big quote / insight. Full-bleed hero with the statement overlaid - centered or anchored. Use sparingly (1-2 per deck). The statement IS the slide; everything else recedes.

**Structure:**
```
+----------------------------------------------------------+
| [full-bleed hero, heavy bottom gradient]                 |
|                                                          |
|                                                          |
|                                                          |
|   "If your agent can't revise itself                     |
|    mid-run, it's a chatbot                               |
|    in a wrapper."                                        |
|    (DM Sans 700, 104px, white)                           |
|                                                          |
|    {SPEAKER} · {MODULE} (mono red 32px)            |
|                                                          |
| {SPEAKER} · {ORG}                  07 / 12     |
+----------------------------------------------------------+
```

**HTML skeleton:**
```html
<div class="slide stage-statement">
  <div class="hero-bg"><img src="file:///.../slide_07_hero_source.png"></div>
  <div class="hero-overlay"></div>
  <div class="content">
    <p class="statement">If your agent can't revise itself mid-run,<br>it's a chatbot in a <span class="accent">wrapper</span>.</p>
    <p class="attribution">{Speaker} · {module}</p>
  </div>
  <div class="footer">
    <span>{Speaker} · {org}</span>
    <span class="page-num"><span class="current">07</span> / 12</span>
  </div>
</div>
```

**Statement-specific CSS:**
```css
.stage-statement .hero-overlay {
  background:
    linear-gradient(180deg, rgba(0,0,0,0.50) 0%, rgba(0,0,0,0.70) 50%, rgba(0,0,0,0.85) 100%);
}
.stage-statement .content {
  position: absolute; inset: 0;
  padding: 0 120px 140px;
  display: flex; flex-direction: column;
  justify-content: center;
}
.stage-statement .statement {
  font-family: 'DM Sans'; font-weight: 700;
  font-size: 104px; line-height: 1.05; letter-spacing: -0.02em;
  color: var(--white); margin: 0 0 40px 0;
  max-width: 1500px;
}
.stage-statement .statement .accent { color: var(--red); }
.stage-statement .attribution {
  font-family: 'JetBrains Mono'; font-weight: 500;
  font-size: 32px; letter-spacing: 0.18em;
  color: var(--red); text-transform: uppercase;
  margin: 0;
}
```

---

### 5. Closing

Slide N. Thanks / CTA / contact. Text-focused. The hero can be a smaller picture-card or omitted entirely. Replaces the footer with full contact info.

**Structure:**
```
+----------------------------------------------------------+
| EYEBROW · CONTACT (mono red, 28px)                       |
|                                                          |
| BUILD SOMETHING REAL.                                    |
| (DM Sans 700, 120px, white, accent word red)             |
|                                                          |
| One short closing line - what to do next.                |
| (DM Sans 400, 40px, gray-2)                              |
|                                                          |
| → Twitter: x.com/evyborov                                |
| → {contact / handle}                |
| → Workshop signup: trinity.ability.ai                    |
|                                                          |
| {SPEAKER} · {DATE} · {ORG}                  |
+----------------------------------------------------------+
```

**HTML skeleton:**
```html
<div class="slide stage-closing">
  <div class="content">
    <div class="eyebrow">Closing · Contact</div>
    <h1 class="closing-title">Build something <span class="accent">real</span>.</h1>
    <p class="closing-deck">Trinity is open source. Start with the docs, run an agent in 10 minutes.</p>
    <ul class="contact-list">
      <li><span class="arrow">→</span> trinity.ability.ai</li>
      <li><span class="arrow">→</span> github.com/Abilityai/trinity</li>
      <li><span class="arrow">→</span> x.com/evyborov</li>
    </ul>
  </div>
  <div class="cover-strip">
    <span>{Speaker}</span>
    <span>June 2026</span>
    <span>ability.ai</span>
  </div>
</div>
```

**Closing-specific CSS:**
```css
.stage-closing .content {
  position: absolute; inset: 0;
  padding: 96px 96px 200px;
  display: flex; flex-direction: column; justify-content: center;
}
.stage-closing .eyebrow {
  font-family: 'JetBrains Mono'; font-weight: 500;
  font-size: 28px; letter-spacing: 0.22em;
  color: var(--red); text-transform: uppercase;
  line-height: 1.0; margin-bottom: 36px;
}
.stage-closing .closing-title {
  font-family: 'DM Sans'; font-weight: 700;
  font-size: 120px; line-height: 0.96; letter-spacing: -0.02em;
  color: var(--white); margin: 0 0 36px 0;
}
.stage-closing .closing-title .accent { color: var(--red); }
.stage-closing .closing-deck {
  /* Prose colour rule (design_system.md): closing deck is ALWAYS white, never gray. */
  font-family: 'DM Sans'; font-weight: 400;
  font-size: 40px; line-height: 1.3; color: var(--white);
  margin: 0 0 56px 0; max-width: 1400px;
}
.stage-closing .contact-list {
  list-style: none; margin: 0; padding: 0;
  display: flex; flex-direction: column; row-gap: 20px;
}
.stage-closing .contact-list li {
  font-family: 'JetBrains Mono'; font-weight: 500;
  font-size: 36px; letter-spacing: 0.10em;
  color: var(--white); text-transform: lowercase;
}
.stage-closing .contact-list .arrow {
  color: var(--red); margin-right: 16px;
}
.stage-closing .cover-strip {
  position: absolute; left: 96px; right: 96px; bottom: 60px;
  display: flex; gap: 48px;
  font-family: 'JetBrains Mono'; font-weight: 500;
  font-size: 28px; letter-spacing: 0.16em;
  color: var(--gray-3); text-transform: uppercase;
}
```

---

## Pacing rules

| Rule | Why |
|------|-----|
| Section divider every 3-5 content slides | Audience attention reset; gives projection rhythm |
| ≤ 2 statement slides per deck | Statement slides are punctuation, not the main course |
| Alternate picture-left and picture-right on content slides | Avoids the "every slide looks the same" trance |
| Vary hero concepts - don't repeat objects across consecutive slides | Decks with the same hero feel like a stuck loop |
| Body bullets: max 4 per content slide | More than 4 forces text shrinkage below the 38px body floor |
| Closing always has the same speaker strip as the cover | Bookends the deck visually |

## Mixing with pre-made diagrams

If a slide needs a structured diagram (architecture, flow, comparison), build the diagram separately with a diagram skill at **16:9 aspect (1920×1080)**, then embed the resulting PNG as the hero of a `statement`-style slide (full-bleed) or as the picture in a `content`-style slide (picture-card). This keeps the deck brand-coherent without duplicating diagram logic in the presentation skill.
