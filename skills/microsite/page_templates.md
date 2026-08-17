# Microsite Page Templates

The shared UI of every `/microsite` page. This file is the reason two microsites built
months apart look like siblings: same shell, same tokens, same section grammar, same
animation vocabulary. Fork from here; do not invent a new shell per page.

Provenance: shell structure + interaction rig proven on a workshop explainer page; the
section grammar mirrors a dense one-page block library, so a page and its printed
companion read as one system.

---

## 0. Brand override (READ FIRST)

**This file ships a DEFAULT palette, not a mandate.** The skill is the *discipline* — one
accent, semantic colors only when they're bound to named concepts, a locked motion
vocabulary, a print stylesheet that always works. The hex values are a starting point.

To brand a page, replace five tokens in §2 and everything downstream follows:

| Token | Default | Replace with |
|---|---|---|
| `--bg` | `#0B0B0E` near-black | your canvas (dark or light) |
| `--ink` | `#FFFFFF` | your primary text color |
| `--accent` | `#B85050` muted brick red | **your one brand accent** |
| `--sans` | DM Sans | your display/body face (update the font `<link>` in §2) |
| `--mono` | JetBrains Mono | your mono face |

Where the consuming workspace has its own brand or design-system document, **that document
wins** over every value here — read it before authoring and port its tokens into §2. Where
it has none, the defaults below are a coherent, tested system; ship them.

What must NOT be swapped: the color *discipline* rules (§2), the motion vocabulary (§6),
the print stylesheet (§7), and the asset policy (§8). Those are the skill.

---

## 1. Web-tier calibration (documented, deliberate)

A brand system calibrated for **static image assets** (fixed canvas, mobile-feed
glanceability) does not transfer wholesale to a **scrolling page read in a browser**. Three
rules bend on the web tier — apply the same reasoning when porting your own system:

| Image-asset rule | Web tier | Why |
|---|---|---|
| Pure black `#000000` canvas | Near-black `#0B0B0E` | Long-form scroll reading on pure black is harsh; near-black keeps the brand mood with less eye fatigue. Cards still lift off it. |
| No bold except `.accent` | Display headings 700-800 | At scroll scale, heading weight IS the hierarchy. Prose stays 400; emphasis inside prose stays restrained (`.k` at 600, accent color). |
| 26px text floor | Fluid web scale, 17px base | The floor exists for 400px-wide feed rendering. A browser page renders 1:1; standard web type rules apply. Floor here: **13px** for mono chrome, never smaller. |

Everything else holds verbatim: one type pairing (default DM Sans + JetBrains Mono), a
single accent (default `#B85050`), no emoji as design elements, no stock icon fonts (author
inline SVG), no off-palette decoration, telegraphic microcopy, textless generated imagery.

## 2. Tokens (dual theme)

Paste into `:root`. Dark is the default; `data-theme="light"` on `<html>` flips to the warm
print-friendly variant (the print stylesheet forces it regardless — see §7).

```css
:root{
  color-scheme: dark;
  --bg:#0B0B0E; --bg-1:#131318; --bg-2:#1A1A21;
  --line:#26262C; --line-2:#34343C;
  --ink:#FFFFFF; --ink-dim:#9DA2BC; --ink-mute:#6B6E80;
  --accent:#B85050;                   /* THE accent - swap for your brand (§0) */
  --accent-dim:#4A2A2A; --accent-soft:rgba(184,80,80,.10);
  --ok:#5FE0A0; --risk:#FF8FAB; --warn:#F0C14B;        /* status colors - semantic only */
  --sem-a:#6FB2FF; --sem-b:#45D6BF; --sem-c:#A394FF;   /* concept colors - semantic only */
  --sans:'DM Sans',system-ui,sans-serif;
  --mono:'JetBrains Mono',ui-monospace,monospace;
  --wrap:1200px;
  --shadow:6px 6px 0 0 rgba(0,0,0,.5); --shadow-sm:4px 4px 0 0 rgba(0,0,0,.45);
}
html[data-theme="light"]{
  color-scheme: light;
  --bg:#FAF8F5; --bg-1:#FFFFFF; --bg-2:#F1EEE9;
  --line:#E4E0D9; --line-2:#D4CFC6;
  --ink:#1A1A1E; --ink-dim:#4A4C58; --ink-mute:#8A8C99;
  --accent-soft:rgba(184,80,80,.07);
  --shadow:none; --shadow-sm:none;
}
```

### Color discipline (LOCKED)

- **`--accent` is the only decorative accent** - whatever color you set it to. Eyebrows,
  key numbers, nav brand mark, callout borders, the one emphasized phrase. One page, one
  accent; a second decorative color is always a mistake.
- **Semantic colors (`--sem-*`, `--ok/--risk/--warn`) appear ONLY when ≥3 concepts need a
  stable color identity across sections** (e.g. a knowledge page binding decisions=blue / facts=teal /
  judgment=purple). Rules: each color binds to ONE named concept for the whole page, the
  binding is introduced visibly (hero chips or a legend) before first use, and the colors
  never decorate anything conceptless. A page about one thing uses red + grayscale only.
- Status colors mean status (live/good = `--ok`, problem = `--risk`, gate/attention =
  `--warn`) - never "I wanted green here."

### Fonts

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
```

## 3. Type tier (web)

```css
html{scroll-behavior:smooth; font-size:106.25%}            /* 17px base */
body{margin:0; background:var(--bg); color:var(--ink); font-family:var(--sans);
     line-height:1.62; -webkit-font-smoothing:antialiased}
h1{font-size:clamp(2.4rem,5.4vw,4.1rem); line-height:1.03; font-weight:800;
   letter-spacing:-.03em; text-wrap:balance; margin:0}
h2{font-size:clamp(1.9rem,3.6vw,2.8rem); line-height:1.08; font-weight:800;
   letter-spacing:-.025em; text-wrap:balance; margin:0}
h3{font-size:1.25rem; font-weight:700; letter-spacing:-.01em}
.lede{color:var(--ink-dim); font-size:clamp(1.15rem,1.6vw,1.4rem); line-height:1.55;
      max-width:64ch; margin:22px 0 0}
.eyebrow{font-family:var(--mono); font-size:14px; letter-spacing:.16em;
         text-transform:uppercase; color:var(--ink-mute); margin:0 0 20px}
.eyebrow b{color:var(--accent); font-weight:700}
.k{color:var(--ink); font-weight:600}                       /* in-prose emphasis */
em.hl{font-style:normal; color:var(--accent); font-weight:600}
```

Rules: prose is `--ink` on dark cards / `--ink-dim` only for ledes and card descriptions
(secondary voice, matching the KB page). Body copy the reader must absorb never drops to
`--ink-mute` - that's chrome only (eyebrows, captions, footers). Mono chrome floor: 13px.
Line length: prose capped at `64-75ch`. Telegraphic microcopy everywhere labels appear.

## 4. Shell skeleton

Every page is ONE self-contained HTML file with this spine:

```html
<!doctype html>
<html lang="en"><!-- data-theme="light" for the light variant -->
<head>
  <meta charset="utf-8">
  <title>{Topic} — {Brand/Context}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <!-- fonts (§2), then one <style> block: tokens, type tier, shell css, section css, print css -->
</head>
<body>
<div id="bar"></div>                          <!-- scroll progress -->
<nav>
  <div class="wrap">
    <span class="brand">{brand} <b>{mark}</b></span>
    <div class="nlinks"><!-- <a href="#id">Label</a> per section --></div>
  </div>
</nav>

<header id="hero"><!-- §5 · S1 --></header>
<section id="..."><!-- §5 sections, one per id, each with .eyebrow + h2 + .lede --></section>
<!-- ... -->
<footer>
  <div class="wrap">
    <span class="fmono">{author} · {org}</span>
    <span class="fmono">{date or canon stamp} · built with /microsite</span>
  </div>
</footer>

<script>/* §6 interaction rig */</script>
</body></html>
```

```css
*{box-sizing:border-box}
.wrap{max-width:var(--wrap); margin:0 auto; padding:0 30px; position:relative; z-index:1}
#bar{position:fixed; top:0; left:0; height:3px; width:0; background:var(--accent);
     z-index:50; transition:width .12s linear}
nav{position:sticky; top:0; z-index:40; backdrop-filter:blur(10px);
    background:color-mix(in srgb, var(--bg) 76%, transparent); border-bottom:1px solid var(--line)}
nav .wrap{display:flex; align-items:center; gap:18px; height:56px}
.brand{font-family:var(--mono); font-size:13px; letter-spacing:.14em;
       text-transform:uppercase; white-space:nowrap}
.brand b{color:var(--accent); font-weight:700}
.nlinks{display:flex; gap:2px; margin-left:auto; overflow-x:auto; scrollbar-width:none}
.nlinks a{font-family:var(--mono); font-size:13px; color:var(--ink-mute);
          text-decoration:none; padding:6px 9px; border-radius:6px;
          transition:color .15s, background .15s; white-space:nowrap}
.nlinks a:hover{color:var(--ink)}
.nlinks a.active{color:var(--ink); background:var(--bg-2)}
@media(max-width:900px){ .nlinks{display:none} }
section{padding:110px 0; border-bottom:1px solid var(--line);
        scroll-margin-top:66px; position:relative}
footer{padding:48px 0; color:var(--ink-mute)}
footer .wrap{display:flex; flex-wrap:wrap; gap:14px; align-items:center;
             justify-content:space-between}
.fmono{font-family:var(--mono); font-size:13.5px; letter-spacing:.04em}
a:focus-visible{outline:2px solid var(--accent); outline-offset:3px; border-radius:6px}
@media (prefers-reduced-motion:reduce){
  *{animation:none !important; transition:none !important} html{scroll-behavior:auto} }
```

## 5. Section grammar

Names align with `/one-pager` blocks (B1-B12) so content plans translate across media.
Each section = `<section id>` + `.eyebrow` (numbered: `01 · <b>Label</b>`) + `h2` + `.lede`,
then ONE dominant element from this grammar. One idea per section; 6-10 sections per page.

| # | Section | One-pager kin | Use for | Core recipe |
|---|---|---|---|---|
| S1 | **Hero** | header | Title + promise; optional canvas backdrop | `min-height:88-92vh`, flex-centered `.wrap`; optional `<canvas>` at `inset:0 z-0` + gradient scrim div + content at z-2; status `.tag` pill; `h1` with ONE `.accent`-colored key phrase; `.heroflow` chips previewing the page's concepts (where semantic colors get introduced) |
| S2 | **Agenda / TOC** | — | Orient the reader; workshop agendas; report contents | `.agenda` list: numbered rounded squares (mono, accent), `h3` + one-line `p` per item, hairline separators |
| S3 | **KPI strip** | B1/B2 | The numbers that carry the story | `.stats` grid (2-4 across, joined card): big `.n` (tabular-nums, count-up on reveal), mono uppercase `.l` label, optional `.d` detail. ONE notable delta may take `--risk`/`--ok`; rest stay ink |
| S4 | **Prose + pull** | B3/B7 | Narrative, problem statement | Max `64ch` prose; `.pull` blockquote (4px accent left border, large 600 text) for the one sentence that must land |
| S5 | **Card grid** | B8 | Capabilities, principles, steps, kinds | `.steps` auto-fit grid of `.step` cards: CSS-counter mono number (accent), `h3`, short `p`, optional mono `.cmd` chip. Full-width `.recap` variant (accent-tinted gradient card) for the row's takeaway |
| S6 | **Comparison** | B5 | Us-vs-them, before/after, tiers | Two-column grid: foil column dashed `--line-2` border + `--ink-dim` values; winner column `--accent-dim` border + faint red gradient + `--ink` values. Never two hues |
| S7 | **Timeline** | B6 | Sequence, roadmap, history | Horizontal rail (vertical on mobile): mono date/version labels, dots on a hairline, name + one-liner per stop; future stops dashed + hollow (**the unfinished part stays visibly unfinished**) |
| S8 | **Callout banner** | B7 | THE finding, warning, decision, CTA-to-act | Full-width tinted card: mono uppercase badge + one bold-free sentence with `.k`/colored emphasis. Tint = semantic (accent default, `--risk` finding, `--warn` gate) |
| S9 | **Diagram** | B11 | Architecture, flows, mechanisms | Inline `<svg>` hand-authored (KB `flowsvg` style: `--bg-1` boxes, colored 2px edges, mono labels with `paint-order:stroke` halo) — or pre-rendered themed Mermaid SVG inlined. Wrap in `.archscroll{overflow-x:auto}` with `min-width` so mobile scrolls INSIDE the block. Hover-focus: sibling lanes dim to 0.34 |
| S10 | **Chart** | B10 | Real data series | Inline SVG per the `dataviz` skill method (load it when charting). Axis labels mono 13px `--ink-mute`; ONE series may take accent; annotate the takeaway ON the chart |
| S11 | **Media frame** | B11 | Screenshots, product UI, generated imagery | `.frame`: browser-chrome bar (3 dots + mono URL) + `<img>`. Generated imagery = textless, style-consistent with the page, `filter:saturate(.92) brightness(.84)` |
| S12 | **Tree / code** | — | File layouts, configs, commands | Mono `.treecard` rows: `white-space:pre` tree text + muted inline comment per row; horizontal scroll inside the card |
| S13 | **CTA paths** | footer/CTA | End of page: what to do next | 2-up `.path` cards: mono label, `h3`, one-liner, `.btn.pri` (ink bg) / `.btn.sec` (outline). Last section before footer |

**Composition defaults by preset** (starting points, not straitjackets):
- `report` (daily/status): S1 compact hero → S3 KPIs → S8 finding → S10/S7 per topic → S12 details → S13 actions
- `explainer` (topic/workshop): S1 full hero → S2 agenda → S4 problem → S3 stakes → S9 mechanism → S5 rules/steps → S6 comparison → S8 takeaway → S13
- `showcase` (product/project): S1 full hero → S4 narrative → S11 frames → S3 proof → S6 vs alternatives → S7 roadmap → S13

## 6. Animation vocabulary (LOCKED rig)

Motion explains structure; it never performs. Four moves, all IntersectionObserver-driven,
all disabled by `prefers-reduced-motion` and forced-complete by print/verification.

```css
.reveal{opacity:0; transform:translateY(18px);
        transition:opacity .55s ease, transform .55s ease}
.reveal.in{opacity:1; transform:none}
.reveal.d1{transition-delay:.08s} .reveal.d2{transition-delay:.16s} .reveal.d3{transition-delay:.24s}
```

```js
// 1. scroll progress bar
var bar=document.getElementById('bar');
function prog(){var h=document.documentElement,sc=h.scrollTop||document.body.scrollTop,
  max=(h.scrollHeight-h.clientHeight)||1;bar.style.width=(sc/max*100)+'%';}
document.addEventListener('scroll',prog,{passive:true}); prog();

// 2. nav scrollspy
var links=[].slice.call(document.querySelectorAll('.nlinks a')), map={};
links.forEach(function(a){map[a.getAttribute('href').slice(1)]=a;});
var spy=new IntersectionObserver(function(es){es.forEach(function(e){
  if(e.isIntersecting){links.forEach(function(l){l.classList.remove('active');});
    var m=map[e.target.id]; if(m)m.classList.add('active');}});},
  {rootMargin:'-45% 0px -50% 0px'});
document.querySelectorAll('section[id], header#hero').forEach(function(s){spy.observe(s);});

// 3. reveal on scroll (once, no re-hide)
var rio=new IntersectionObserver(function(es){es.forEach(function(e){
  if(e.isIntersecting){e.target.classList.add('in'); rio.unobserve(e.target);}});},
  {threshold:.12});
document.querySelectorAll('.reveal').forEach(function(el){rio.observe(el);});

// 4. count-up numbers: <span class="count" data-to="741" data-suffix="+">0</span>
function countup(el){var to=parseFloat(el.dataset.to), suf=el.dataset.suffix||'',
  dec=(el.dataset.to.split('.')[1]||'').length, t0=null;
  function step(ts){if(!t0)t0=ts; var p=Math.min((ts-t0)/900,1), e=1-Math.pow(1-p,3);
    el.textContent=(to*e).toFixed(dec)+suf; if(p<1)requestAnimationFrame(step);}
  requestAnimationFrame(step);}
var cio=new IntersectionObserver(function(es){es.forEach(function(e){
  if(e.isIntersecting){countup(e.target); cio.unobserve(e.target);}});},{threshold:.6});
document.querySelectorAll('.count').forEach(function(el){cio.observe(el);});
```

**Canvas inserts** (hero orb, particle fields, small mechanism loops): follow the KB-page
rig - self-invoking function, `DPR = min(devicePixelRatio, 2)`, resize-debounced re-init,
**explicit `width:100%; height:100%` on the canvas CSS** (a canvas is a replaced element:
`position:absolute; inset:0` alone leaves it at its intrinsic 300x150 - the drawing then
huddles in the top-left corner),
`prefers-reduced-motion` check that draws ONE static frame and skips the rAF loop, and
pause when off-viewport (`IntersectionObserver` gating `requestAnimationFrame`). A canvas
must render something meaningful as a still: the reduced-motion/print frame is a
composition, not a blank. A canvas that needs a story arc (beats, camera, narration) is a
film - invoke `/animated-explainer` instead and embed or link its output.

**Hard rules:** reveal once, never re-hide on scroll-up · transitions ≤ 600ms · stagger
≤ 3 steps · no parallax on text · nothing teleports (a number counts, a bar grows, a
diagram's edges draw in - motion shows where things come from) · every animated element
reads correctly with animation OFF.

## 7. Print / PDF stylesheet (required in every page)

The PDF is a static companion, not the deliverable. Chromium print rendering via
`scripts/export_pdf.py` uses these rules:

```css
@media print{
  :root{ --bg:#FFFFFF; --bg-1:#FFFFFF; --bg-2:#F4F2EE;
    --line:#D8D4CD; --line-2:#C4BFB6;
    --ink:#1A1A1E; --ink-dim:#444652; --ink-mute:#7A7C88;
    --accent-soft:rgba(184,80,80,.06); --shadow:none; --shadow-sm:none }
  #bar, nav, .no-print{display:none !important}
  section{padding:34px 0; border-bottom:1px solid var(--line); break-inside:auto}
  #hero{min-height:0; padding:30px 0}
  .reveal{opacity:1 !important; transform:none !important; transition:none !important}
  .card,.step,.stat,.path,.frame,.ex{break-inside:avoid}
  h2{break-after:avoid}
  .archscroll{overflow:visible}
  canvas{max-height:340px}
  a[href^="http"]::after{content:" (" attr(href) ")"; font-family:var(--mono);
    font-size:10px; color:var(--ink-mute)}
}
```

The export script force-adds `.in` to all `.reveal` elements before printing, so canvases
and counters land at their final state. **Count-up trap:** a `.count` span's markup value
is `0` and its animation is IntersectionObserver-gated — observers cannot be trusted to
fire in the print pass, so KPIs print as `$0`. Every `.count` span needs a print-only
twin carrying the formatted final value (`.pn{display:none}` on screen;
`@media print{.count{display:none!important}.pn{display:inline!important}}`). Semantic colors survive print (they carry meaning);
check them against the light background - `--sem-b` teal and `--warn` amber may need the
darker print variants `#0E8A76` / `#9A7415` via a print override if used on text.

## 8. Asset policy (LOCKED)

The KB page shipped at 3.2MB because every screenshot was base64-embedded. Default is now:

- **Default: sibling `assets/` folder** next to the HTML, relative `src="assets/x.png"`.
  The deliverable is the folder, not the file.
- **`--inline` flag: single-file build** for pages that must travel as one file
  (email attachment, chat upload). Budget: **≤ 1.5MB total**; images to WebP/JPEG ≤ 200KB
  each before embedding; refuse to inline past budget - switch to the folder layout and
  say so.
- **SVG is always inline** (diagrams, charts, icons) - it's text, it themes with the
  tokens, and it prints sharp.
- Generated imagery: textless, soft-futurism grammar, via `/create-explanatory-image` or
  `/nano-banana-image-generator`; film-matte crop (`transform:scale(1.07)` in an
  `overflow:hidden` frame).

## 9. Quality bar (checked by scripts/check_page.py + eyes)

- No console errors, no broken images, no horizontal page scroll at 1440/1024/390 widths
  (wide content scrolls INSIDE its `.archscroll`/`.treecard` container, never the body)
- Every section earns its scroll: has a job, states it in the eyebrow+h2, one dominant element
- Numbers are real, sourced, and dated - a microsite with invented stats is a lie with
  a progress bar; `[NEEDS: ...]` gaps resolve before ship
- The page reads top-to-bottom as a story WITHOUT any animation, imagery, or color
- Footer stamps the data/canon date it was built from
