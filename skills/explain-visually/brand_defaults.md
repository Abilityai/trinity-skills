# Brand Defaults

**This file ships a DEFAULT visual system, not a mandate.** The skill is the *discipline* —
one accent, a fixed type pairing, a hard readability floor, textless imagery, forbidden
off-palette decoration. The hex values are a starting point.

Sibling skills in this library (`one-pager`, `presentation`, `explain-visually`,
`microsite`) carry an identical copy of this file, which is why their outputs read as one
system. The library layout is deliberately flat — every skill is injected on its own, so a
shared file is vendored into each rather than referenced across directories. Change one,
change the others.

## 0. Brand override (READ FIRST)

Replace five tokens and everything downstream follows:

| Token | Default | Replace with |
|---|---|---|
| `--bg` | `#000000` pure black | your canvas |
| `--white` | `#FFFFFF` | your primary text color |
| `--red` | `#B85050` muted brick red | **your one accent** |
| `--sans` | DM Sans | your display/body face (update the font `<link>`) |
| `--mono` | JetBrains Mono | your mono face |

**Where the consuming workspace has its own brand or design-system document, that document
wins over every value here** — read it before authoring and port its tokens in. Where it has
none, the defaults below are a coherent, tested system; ship them.

What must NOT be swapped — these are the skill, not the branding:
the single-accent rule, the prose-color rule, emphasis-by-weight, the readability floor,
the textless-imagery rule, and the forbidden-patterns list.

## 1. Palette

Paste into the `:root` of every generated HTML file.

```css
:root {
  --bg: #000000;            /* canvas */
  --bg-card: #0F0F12;       /* lifted card background */
  --bg-card-alt: #0A0A0C;   /* secondary card variant (muted/"foil" column) */
  --white: #FFFFFF;         /* primary text */
  --gray-2: #9DA2BC;        /* secondary — NON-PROSE roles only (see §3) */
  --gray-3: #555766;        /* tertiary (axis labels, footer, arrow strokes) */
  --gray-4: #333333;        /* dashed border for the muted column */
  --red: #B85050;           /* THE accent — swap for your brand */
  --red-dim: #4A2A2A;       /* deep accent for borders */
  --red-soft: rgba(184, 80, 80, 0.10);   /* warm tint for chip backgrounds */
  --border: #2A2A30;        /* default card border */
  --subctx-border: #3A2228; /* dashed sub-region border, accent cast */
  --subctx-bg: rgba(184, 80, 80, 0.04);  /* faint accent tint for sub-context */
}
```

**Rules (LOCKED):**
- **One accent.** `--red` appears sparingly — eyebrow, numbers in cards, sub-context label,
  one key word, single highlights. Never on large surfaces. A second decorative color is
  always a mistake.
- The default accent is a *muted* brick red, deliberately not an alarm red (`#FF4444`).
  Alarm reds win a one-second glance; muted reads as considered at read-up-close scale.
  If you swap it, keep that distinction in mind for the medium you're designing for.
- **Off-palette decoration is FORBIDDEN** — cyan, lime, blue, amber, green as decoration.
  Semantic status colors are a separate, deliberate exception: they mean status, and only
  when the page actually carries status.
- The canvas is flat. No radial glows, no gradients on the background; generated imagery
  supplies the atmosphere, the body sits on flat canvas so it reads as a designed asset.

## 2. Typography

Two faces, fixed roles.

| Face | Role | CSS |
|---|---|---|
| **DM Sans** (400, 500, 600, 700, 800) | Display titles, body, all primary type | `font-family: 'DM Sans', system-ui, sans-serif` |
| **JetBrains Mono** (400, 500) | Eyebrows, footers, chips, axis labels | `font-family: 'JetBrains Mono', ui-monospace, monospace` |

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

### Readability floor (LOCKED — fixed-canvas image assets)

Calibrated so a 1080-wide canvas stays readable rendered at ~400px (≈37%).

| Text role | Tier | Size |
|---|---|---|
| Chrome (eyebrow, footer, tier label, boundary text) | FLOOR | **≥ 26px** |
| Body (row values, card descriptions, column names — text meant to be *absorbed*) | BODY | **28–30px** |
| Display titles | — | 88–104px; well above the floor |

The floor is not a target — titles still dominate. Mono-uppercase at 26px reads visually
smaller than DM Sans at 26px, which is what the 28–30px body tier compensates for.

**This floor applies to fixed-canvas assets rendered to an image.** A skill whose output is
a browser page at 1:1 (a scrolling microsite) applies normal web type rules instead, with a
13px mono-chrome floor — the calibration follows the medium, and a skill that bends this
rule says so explicitly and why.

## 3. Prose color rule (LOCKED)

**Every paragraph of prose is `var(--white)`. Never `var(--gray-2)`.**

`--gray-2` is reserved for non-prose roles only: the muted/"foil" column in a comparison
(so the answer in white reads stronger by contrast), a setup line redirecting attention to
a punch, and secondary chrome labels above body content.

**Emphasis comes from font-weight (500 vs 400) and from a single accent-colored word —
NEVER from a color downshift.** A gray paragraph reads as deprioritized; on a dark canvas
it also loses contrast, telling the reader "this matters less" — wrong for body copy that
exists to be read.

## 4. Imagery

- **Textless, always.** Generated imagery carries NO text, letters, numbers, or glyphs that
  resolve as writing. Text in a generated image is the single most common tell, and it
  cannot be corrected after the fact — regenerate.
- **No humans** in the default universe. Architecture and luminous form are the subject.
- One coherent photographic lineage across a run — pick it once (the default is a
  soft-futurism scene: medium-format film look, warm amber glow, brutalist concrete
  interior) and hold it for every image in the deliverable.
- Imagery is dimmed and desaturated under text (`filter: saturate(.92) brightness(.84)` or
  a directional gradient scrim) so type keeps its contrast. Text legibility outranks the
  picture, every time.
- No emoji as design elements. No stock icon fonts — author inline SVG.

## 5. Forbidden patterns

- Off-palette decorative color · a second accent · gradients on the canvas
- Gray body prose · emphasis by color downshift
- Text baked into generated imagery · humans in the default imagery universe
- Emoji as design elements · stock icon fonts
- Any text below the readability floor for the medium
