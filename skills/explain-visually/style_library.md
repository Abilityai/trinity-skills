# Style Library - /explain-visually

The **style** is a dial. Every visual in a run shares one style. Each preset below defines four things:

1. **Mermaid `themeVariables`** - injected into `mermaid.initialize(...)` so structural diagrams take the look.
2. **Page CSS** (`background`, `padding`, font) - the canvas the diagram is rendered on.
3. **Fonts link** - the Google Fonts `<link>` to load.
4. **Illustration fragment** - appended to the concept brief when a facet is rendered via `/create-explanatory-image`.
5. **`/one-pager` theme** - which theme to pass when bundling (`dark` or `light`).

Default is **`brand-dark`**. `custom` is authored on the fly from a one-paragraph brief.

---

## Render wrapper (themed Mermaid -> PNG)

Author one HTML file per Mermaid visual from this template, substituting the `{...}` placeholders from the chosen preset, then render with this skill's `scripts/render_html_to_png.py`.

```html
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  {FONTS_LINK}
  <style>
    html, body { margin: 0; padding: 0; }
    body {
      background: {BG};
      box-sizing: border-box;
      padding: {PAD};
      min-height: 100vh;
      display: flex; align-items: center; justify-content: center;
      font-family: {FONT_CSS};
    }
    .mermaid { width: 100%; }
    .mermaid svg { width: 100%; height: auto; max-height: 100%; }
  </style>
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
    mermaid.initialize({
      startOnLoad: true,
      theme: 'base',
      {LOOK}
      securityLevel: 'loose',
      flowchart: { curve: 'basis', useMaxWidth: true },
      themeVariables: {THEME_VARS}
    });
  </script>
</head>
<body>
  <pre class="mermaid">
{DIAGRAM_DEFINITION}
  </pre>
</body>
</html>
```

**Accent a node** (the ONE emphasized box per diagram) - append to any flowchart/graph definition:

```
classDef accent fill:{ACCENT},stroke:{ACCENT},color:#fff;
class NodeId accent;
```

### Per-modality canvas defaults (`--width` x `--height`, before device-scale 2)

| Modality | Canvas | Notes |
|----------|--------|-------|
| flowchart / sequence / timeline | 1600 x 900 | 16:9; the common case |
| state machine | 1400 x 1000 | |
| ER / class / architecture | 1600 x 1100 | denser, ~4:3 |
| mind map | 1400 x 1400 | radial, square |
| chart (pie / xychart) | 1200 x 900 | |
| comparison (quadrant) | 1200 x 1200 | square reads best |

If a diagram is clipped, raise the height (Mermaid auto-sizes the SVG; `useMaxWidth:true` fits the width). Never shrink below readability - cut nodes instead.

### Render readiness

`render_html_to_png.py` waits for `networkidle` + 400ms, which normally covers the ESM import + draw. If a PNG comes back **blank**, the render hadn't finished:
- Re-run the render once (CDN now cached) - usually fixes it.
- Or **vendor offline**: download `mermaid@11` `dist/mermaid.esm.min.mjs` into `vendor/`, and change the import to a `file://` path. Removes the CDN dependency entirely.

---

## Preset: `brand-dark` (DEFAULT)

Cites the palette in `brand_defaults.md` (this skill) - read its §0 override first, then use the exact hex values. Black canvas, white text, muted brick-red accent (`#B85050`), DM Sans + JetBrains Mono. Most coherent with the `/one-pager` bundle chrome.

- **FONTS_LINK:** `<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">`
- **BG:** `#000000`
- **PAD:** `64px`
- **FONT_CSS:** `'DM Sans', system-ui, sans-serif`
- **LOOK:** *(omit - default look)*
- **ACCENT:** `#B85050`
- **THEME_VARS:**
  ```js
  {
    background: '#000000',
    primaryColor: '#0F0F12',
    primaryTextColor: '#FFFFFF',
    primaryBorderColor: '#2A2A30',
    lineColor: '#555766',
    textColor: '#FFFFFF',
    secondaryColor: '#0A0A0C',
    tertiaryColor: '#0F0F12',
    fontFamily: "'DM Sans', sans-serif",
    fontSize: '20px'
  }
  ```
- **Illustration fragment:** `Soft-futurism, Pentax 67 / Kodak Portra 400 aesthetic, brutalist concrete + warm amber glow, textless, black background. (See broll-soft-futurism style guide.)`
- **/one-pager theme:** `dark`

## Preset: `clean-light`

Paper-white, near-black ink, one muted-red accent. Calm and legible for studying on screen or printing.

- **FONTS_LINK:** `<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">`
- **BG:** `#FFFFFF`
- **PAD:** `64px`
- **FONT_CSS:** `'DM Sans', system-ui, sans-serif`
- **LOOK:** *(omit)*
- **ACCENT:** `#B85050`
- **THEME_VARS:**
  ```js
  {
    background: '#FFFFFF',
    primaryColor: '#F4F2EC',
    primaryTextColor: '#1A1A1A',
    primaryBorderColor: '#D8D4CA',
    lineColor: '#5A5A5A',
    textColor: '#1A1A1A',
    secondaryColor: '#FBFAF6',
    tertiaryColor: '#F0EDE5',
    fontFamily: "'DM Sans', sans-serif",
    fontSize: '20px'
  }
  ```
- **Illustration fragment:** `Clean editorial infographic, white background, dark line work, one muted-red accent, generous whitespace, no clutter.`
- **/one-pager theme:** `light`

## Preset: `blueprint`

Deep-navy canvas, cyan/white strokes, amber accent, mono-forward type. Reads as engineering / schematic / CAD.

- **FONTS_LINK:** `<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet">`
- **BG:** `#0B1F3A`
- **PAD:** `56px`
- **FONT_CSS:** `'JetBrains Mono', monospace`
- **LOOK:** *(omit)*
- **ACCENT:** `#FFB454`
- **THEME_VARS:**
  ```js
  {
    background: '#0B1F3A',
    primaryColor: '#10294A',
    primaryTextColor: '#E6F4FF',
    primaryBorderColor: '#7FD3FF',
    lineColor: '#7FD3FF',
    textColor: '#E6F4FF',
    secondaryColor: '#0E2440',
    tertiaryColor: '#10294A',
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: '19px'
  }
  ```
- **Illustration fragment:** `Technical blueprint illustration, deep navy background, cyan line drawing, white annotations, schematic / exploded-view feel.`
- **/one-pager theme:** `dark`

## Preset: `whiteboard`

Off-white board, marker-black strokes, red-marker accent, hand-drawn look (Mermaid `look: 'handDrawn'`) + a handwritten font. Informal, like a teaching sketch.

- **FONTS_LINK:** `<link href="https://fonts.googleapis.com/css2?family=Architects+Daughter&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet">`
- **BG:** `#FAF7F0`
- **PAD:** `60px`
- **FONT_CSS:** `'Architects Daughter', 'Segoe Print', cursive`
- **LOOK:** `look: 'handDrawn',`
- **ACCENT:** `#C0392B`
- **THEME_VARS:**
  ```js
  {
    background: '#FAF7F0',
    primaryColor: '#FFFFFF',
    primaryTextColor: '#2B2B2B',
    primaryBorderColor: '#2B2B2B',
    lineColor: '#2B2B2B',
    textColor: '#2B2B2B',
    secondaryColor: '#F2EEE4',
    tertiaryColor: '#FFFFFF',
    fontFamily: "'Architects Daughter', cursive",
    fontSize: '22px'
  }
  ```
- **Illustration fragment:** `Hand-drawn whiteboard sketch, off-white background, black marker line art, one red-marker accent, casual lecture-diagram feel.`
- **/one-pager theme:** `light`

## Preset: `custom`

Ask the user for a one-paragraph brief: **background color, line/text color, one accent color, font feel (sans / mono / handwritten), and overall mood.** Map it onto the same fields as the presets above:
- Pick `BG`, `primaryColor` (a slightly lifted card tone), `primaryTextColor`/`textColor`, `primaryBorderColor`, `lineColor`, and `ACCENT` from the brief.
- Choose `FONT_CSS` + `FONTS_LINK` for the requested font feel (sans -> DM Sans; mono -> JetBrains Mono; handwritten -> Architects Daughter + `look: 'handDrawn'`).
- Choose the `/one-pager theme` by background luminance (dark bg -> `dark`, light bg -> `light`).
- Echo the resolved values back at Gate 1 so the user can confirm the mapping.

---

## /one-pager theme mapping (quick reference)

| `--style` | `/one-pager --theme` |
|-----------|----------------------|
| brand-dark | dark |
| clean-light | light |
| blueprint | dark |
| whiteboard | light |
| custom | by background luminance |

The bundle's **chrome** (header, surround, accent band) follows `/one-pager`'s brand; the **visuals** carry the chosen style. `brand-dark` pairs most coherently.
