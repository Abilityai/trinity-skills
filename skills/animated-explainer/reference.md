# Animated Explainer — code reference

Recipes and traps. Every trap here cost real time on a real build; each is listed
**symptom-first**, because that's how you'll search for it at 2am.

---

## Palette sampling — never eyeball a hex

```bash
ffmpeg -ss 6 -i ref.mp4 -frames:v 1 f.png
python3 -c "
from PIL import Image; import colorsys; from collections import Counter
im = Image.open('f.png').convert('RGB'); c = Counter()
for rgb in im.getdata():
    r,g,b = [v/255 for v in rgb]; h,s,v = colorsys.rgb_to_hsv(r,g,b)
    if s > .25 and v > .2: c[rgb] += 1        # ignore the near-neutral ground
for rgb,n in c.most_common(6):
    h,_,_ = colorsys.rgb_to_hsv(*[x/255 for x in rgb])
    print(f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}  hue={h*360:5.1f}  x{n}')
"
```
Sample a frame that actually *contains* the accent — a title card is mostly background and
will report `#fdfdfd` six times.

**Then prefer the product's own tokens.** Copying a reference's invented colour language is
weaker than using the one your brand already owns semantically (e.g. `--color-success` for
"correct", `--color-danger` for "wrong").

---

## Film skeleton

One self-contained HTML. Time-driven and **stateless** — `draw(t)` must be a pure function of
`t` so it can be scrubbed to any point.

```js
const clamp = (v, a = 0, b = 1) => v < a ? a : v > b ? b : v;
const seg   = (t, a, b) => clamp((t - a) / (b - a));      // 0→1 across a beat
const easeInOut = x => x < .5 ? 4*x*x*x : 1 - Math.pow(-2*x + 2, 3) / 2;
const lerp  = (a, b, t) => a + (b - a) * t;
const hash  = i => { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };

// a beat that fades in and out
const o = Math.min(seg(t, 4.0, 4.4), 1 - seg(t, 9.6, 10.0));
```

**Deterministic jitter only.** `hash(i)`, never `Math.random()` — random breaks scrubbing and
makes every frame irreproducible.

**Global pace is one line, not a re-authoring.** When the note is "make it ~20% faster/
shorter", do NOT touch hundreds of beat constants. Keep the storyboard on its authored clock
and compress only the wall-clock:

```js
const F_STORY = 198;                 // the storyboard's internal clock — never edited for pace
const SHORTEN = 0.8;                 // 20% faster
const F_END   = F_STORY * SHORTEN;   // what mount()/export see
function draw(g, W, H, t) {
  t = t / SHORTEN;                   // play-time -> storyboard-time, ONCE, first line
  ...                                // every seg()/beat constant below stays untouched
}
```

Everything downstream converts by the same factor: narration.json times = storyboard × SHORTEN,
review-rig beat lists are play-time (storyboard × SHORTEN), and the storyboard can still be
EXTENDED (raise `F_STORY`) while playing compressed. Proven on the knowledge-agent re-cut
(198 → 213 storyboard, played at 0.8×) with zero beat-constant edits.

---

## Camera — keyframes, interpolation, and clamping

```js
const SHOTS = [
  { t: 0,  cx: .33, cy: .33, z: 1.6 },   // world coords, z = zoom
  { t: 11, cx: .50, cy: .50, z: 1   },
  { t: 54, cx: .67, cy: .30, z: 1.7 },
];
function camAt(t) {
  let c = SHOTS[SHOTS.length - 1];
  if (t <= SHOTS[0].t) c = SHOTS[0];
  else for (let i = 1; i < SHOTS.length; i++) {
    if (t <= SHOTS[i].t) {
      const a = SHOTS[i-1], b = SHOTS[i], u = easeInOut(clamp((t - a.t) / (b.t - a.t)));
      c = { cx: lerp(a.cx,b.cx,u), cy: lerp(a.cy,b.cy,u), z: lerp(a.z,b.z,u) };
      break;
    }
  }
  // TRAP: never show off-world black. Clamp the centre to the visible half-span.
  const h = 1 / (2 * c.z);
  return { cx: clamp(c.cx, h, 1 - h), cy: clamp(c.cy, h, 1 - h), z: c.z };
}

g.save();
g.translate(W/2, H/2); g.scale(cam.z, cam.z); g.translate(-cam.cx*W, -cam.cy*H);
/* draw the world here */
g.restore();
/* draw captions AFTER restore — screen space, unaffected by the camera */
```

**Two camera rules you will otherwise learn the hard way:**

1. **You cannot centre on an edge element.** At `z`, `cx` is confined to `[1/(2z), 1−1/(2z)]`.
   Clamping keeps it visible (just not centred); not clamping shows black gutters.
2. **The caption band eats the bottom of every zoom.** Content below
   `cy + (0.79 − 0.5)/z` (world units) lands under the letterbox. Check this *before* laying
   out a zoomed panel — it's why a four-panel column can't fit one push and needs a two-stop
   tour instead.

---

## Travellers must follow the drawn path

**Symptom:** dots cut corners the line doesn't; they drift off the rail.
**Cause:** the stroke is a bezier, the particle is hand-written straight segments.
**Fix:** one path definition, read by both.

```js
const bez = (a,b,c,d,u) => { const m = 1-u; return m*m*m*a + 3*m*m*u*b + 3*m*u*u*c + u*u*u*d; };
const RAIL_U = [0, .16, .84, 1];                 // split by rough arc length

function railAt(u, P) {                          // P = the SAME control points you stroke
  if (u < RAIL_U[1]) { const k = (u - RAIL_U[0]) / (RAIL_U[1] - RAIL_U[0]);
    return { x: bez(P.a[0],P.b[0],P.c[0],P.d[0],k), y: bez(P.a[1],P.b[1],P.c[1],P.d[1],k) }; }
  if (u < RAIL_U[2]) { const k = (u - RAIL_U[1]) / (RAIL_U[2] - RAIL_U[1]);
    return { x: lerp(P.d[0],P.e[0],k), y: lerp(P.d[1],P.e[1],k) }; }
  const k = (u - RAIL_U[2]) / (RAIL_U[3] - RAIL_U[2]);
  return { x: bez(P.e[0],P.f[0],P.g[0],P.h[0],k), y: bez(P.e[1],P.f[1],P.g[1],P.h[1],k) };
}
```

---

## ⚠️ The aliasing trap — dots run BACKWARDS

**Symptom:** during a speed-up, travellers run the wrong way for a while, then correct.
**Cause:** multiplying a *ramping* rate by *absolute* `t`:

```js
const u = ((t * (0.16 + many * 0.22)) + i/nP) % 1;   // ✗ WRONG
```
`d/dt(t·rate) = rate + t·rate′`. With `t ≈ 137`, that second term dominates → **~8 laps/sec**
→ at 30fps that's 0.26 laps/frame against a 0.05 spacing → wagon-wheel effect → apparent
reverse. Changing `nP` mid-ramp shifts the spacing too, so the direction *flips around*.

**Fix:** phase is the **integral** of the rate, in closed form.

```js
const R0 = .16, DR = .22, MA = 136, MB = 140;      // rate = R0 + DR·many(t)
function railPhase(t) {
  let area;                                         // ∫ many dt
  if (t <= MA) area = 0;
  else if (t >= MB) area = (MB - MA)/2 + (t - MB);
  else area = (t - MA)*(t - MA) / (2*(MB - MA));
  return R0 * t + DR * area;
}
const nP = 20;                                      // FIXED — inserting particles reshuffles
for (let i = 0; i < nP; i++) {                      //   every other one's phase
  const on = clamp((live - i) / 1.5);               // fade extras in instead
  if (on <= .01) continue;
  const q = railAt(((railPhase(t) + i/nP) % 1 + 1) % 1, RP);
  dot(g, q.x, q.y, r, col, { alpha: on });
}
```

**Verify numerically, not visually** — aliasing is invisible in a still:

```js
// phase must be monotonic AND travel < half the particle spacing per frame
for (let t = 134; t <= 146; t += 1/30) { /* assert railPhase(t) >= prev */ }
```

---

## Growth — a circle that grows with its contents

**Rule:** radius ∝ √count, so **density stays constant**. A circle twice the area holds twice
as much — the growth is honest.

```js
const NMAX = 420, RMAX = H*.075, RMIN = H*.038;
const K = RMAX * .86 / Math.sqrt(NMAX);     // cloud radius = K·√n
const n = Math.floor(fill * NMAX);
const R = Math.max(RMIN, K * Math.sqrt(n) / .86);      // ring tracks the cloud, with a floor

for (let j = 0; j < n; j++) {
  const arr = clamp((n - j) / 7);                       // 0 = just landed, 1 = settled
  const ang = j * 2.39996, rr = K * Math.sqrt(j);       // golden angle = even packing
  const e = easeOut(arr);
  const px = lerp(entryX, cx + Math.cos(ang)*rr, e);    // fly in from the feed, then settle
  const py = lerp(entryY, cy + Math.sin(ang)*rr, e);
  dot(g, px, py, dotR * (1 + (1-arr)*1.4), col, { alpha: .55 + .45*arr });  // newest is loudest
}
```
Check packing before committing: `n·πr² / π(0.86R)²` ≈ 65–70% reads as dense-but-distinct.
Pin labels to `RMAX`, not the live `R`, or they drift while the circle breathes.

---

## React port

Lift the proven `draw` block **by script**; hoist constants to module scope; data comes in as
props from a server component.

```tsx
// app/<page>/page.tsx  — server: read the repo's own data, so the film self-updates
const resolved = await getPredictionsResolved();
const points = resolved.filter(p => p.outcome !== null)
                       .map(p => ({ p: p.probability, o: p.outcome as number }));
<Explainer points={points} tiers={tiers} />
```

### ⚠️ The effect-structure trap — scrubbing silently does nothing

**Symptom:** scrub the transport, nothing happens; the film restarts on pause/play.
**Cause:** the `IntersectionObserver` sits in an effect that depends on `playing`. Every
pause/play re-runs the effect → re-creates the observer → `observe()` **refires immediately**
→ it resets `t = 0` and starts playing. Your scrub is undone within a frame.

```tsx
// ✓ observers: MOUNT-ONLY. `seen` must be a ref, or it resets with the effect.
useEffect(() => {
  /* size + ResizeObserver + IntersectionObserver here */
  return () => { ro.disconnect(); io.disconnect(); };
}, [draw]);                        // NOT [draw, playing]

// ✓ the clock: its own effect, so it can start/stop without touching observers
useEffect(() => {
  if (!playing) return;
  const loop = (ts: number) => { /* advance t, render */ raf.current = requestAnimationFrame(loop); };
  raf.current = requestAnimationFrame(loop);
  return () => cancelAnimationFrame(raf.current);
}, [playing]);

// ✓ a paused scrub must render itself — nothing else will
const scrub = (e) => { t.current = ...; setPlaying(false); renderRef.current(); };
```

### Poster frames
`t = 0` is an empty black frame. If autoplay is blocked or the viewer prefers reduced motion,
that black box is your whole first impression. Rest the canvas on a **representative frame**
until first play (`started` ref → reset to 0 on play).

---

## Layout traps

| Symptom | Cause | Fix |
|---|---|---|
| Hero canvas collapses to ~300px in a wide page | flex column inherits `align-items:start` from a base class | set `align-items:stretch` on the wide variant |
| List text renders **one word per line** | `display:grid` on the `<li>` — the bare text node after `</strong>` becomes its own grid item and lands in the 14px marker column | `position:relative; padding-left` + absolutely-positioned `::before` |
| Cards render unstyled / stacked | the CSS block was dropped in an earlier rewrite; markup reintroduced without it | measure `getComputedStyle(el).display` — don't blame the palette |
| 2px scrub bar unclickable (for users *and* tests) | the hit target is the visual track | wrap in a ~14px hit area; keep the 2px track as a `::before` |
| "Dimmed" canvas text renders at full brightness — every fade on labels silently ignored | a draw helper (e.g. `dot()`) that ends with `globalAlpha = 1` runs **between** your `fade()` and the `fillText` | order per element: helper-with-own-alpha first, `fade()` immediately before `txt()`; audit every `fade → dot → txt` sequence |
| Canvas text shows mojibake (`·` → `Ä·`, `→` → `â†'`) only in the render | standalone film file starts with `<title>` — no `<meta charset="utf-8">`, so the browser guesses the encoding | make `<meta charset="utf-8">` the first line of the film file |
| Labels on the left/bottom of a feature clip or fall into the caption band **only in zoomed shots** | camera-centre clamping shifts the actual frame away from the composed one; captions live in screen space but labels in world space | fan labels toward the frame's open side; compute the caption-safe world-y for each shot's zoom before placing anything |
| Items on a radial arc bunch into collisions near 90°, or wrap off-frame | `sin` flattens near the pole; evenly-spaced angles ≠ evenly-spaced positions | for ≥5 labelled items use a vertical list + a pointing spoke instead of an arc |
| Labels rendered from real data overflow their fixed-size boxes (grid of entity cards: some names 6 chars, some 19) | one hand-picked font size can't fit data-driven strings | `measureText` each label and clamp: `size = min(base, base*(boxW-pad)/measured)` with a floor |
| ~3s of near-black "dead air" during a stage→overview transition — one element gliding through an empty frame | fade-out window of act N ends before fade-in window of act N+1 begins; each looked fine alone | overlap the windows: the reveal must start fading in while the old act is still fading out; screenshot the MIDDLE of every transition, not just beat centres |
| Full-page screenshot shows the dark theme only in one viewport-sized band — white everywhere else (also flashes white on iOS Safari) | the page ground is a `background-attachment:fixed` gradient on `body`; fixed backgrounds paint the viewport, not the document, so stitched captures and some mobile engines get nothing outside it | keep the fixed gradient but put a solid base color on `html` underneath (`html{background:var(--void)}`) |
| The PREVIOUS scene flashes for ~a second between a scrim-backed finale and the closing title card | the scrim fades out with the scene's own stage variable, but the world render underneath outlives it and the title card fades in later — three fade windows, and the middle one exposes the layer below | fade the scene's CONTENTS only; keep the scrim at full opacity through the end and let the next full-screen card paint over it. Any time a scene sits on a scrim over live content, the scrim's life must span until whatever replaces it is fully opaque |
| A world-space label pinned to one region of the graph clips off the frame edge — but only during certain shots | its visibility is gated on TIME windows while the camera pans; a left pan pushes right-side world labels out of frame regardless of the time gate | gate the label's alpha on the CAMERA too: `alpha *= clamp((cam.cx - x0) / span)` so it only shows while the camera is where the composition assumed; don't try to find one world position that survives every shot |
| "Zoom the whole picture out into a box" reads as a cut — a new miniature just appears | the miniature is an independent drawing, not the graph the viewer was watching | draw the miniature from the REAL node array at each node's REAL screen position, then `lerp` every point into the box interior while an opaque scrim covers the world render — the copy starts pixel-identical to the live graph, so the handoff is invisible and the collapse reads as one motion (principle 6 at scene scale) |
| Captions print straight across bottom-row world structures (a foundations slab, a ledger) in every MILDLY zoomed shot (z≈1.2–1.4) — while the overview frames are fine | the caption-safe world-y rule (`cy + (0.79−0.5)/z`) ignores the film's world-scale inset (`WSC`); with the world drawn at 0.875 scale, more world fits above the caption band than the formula predicts, so bottom-row content you "cropped out" is actually on screen under the captions | either include WSC in the safe-y check (`screen_v = WSC·(0.5+(y−cy)·z)`), or — usually better — focus-dim the bottom-row structures during the zoomed chapters where they are not the subject (multiply their alpha by a per-chapter window). They are furniture there, and the dim doubles as focus direction |

---

## Review traps

| Symptom | Cause | Fix |
|---|---|---|
| A hairline dark stroke (`#2a2a30`) reads as **bright/white** in a contact sheet → phantom "wrong color" bug | 50%-downscaled thumbnails brighten 1px strokes over black (resampling), and eyes calibrate to the thumb | Measure the actual pixel with `getImageData` at the stroke's screen coords before "fixing" any color |
| A scripted time-shift breaks later anchored replaces with "MISSING: …" | the shift regex *reformatted* sub-threshold literals (`45.0` → `45`) while "leaving them alone" | when shifting only times ≥ N, return the **original matched string** below the threshold — byte-identical, never re-formatted; and `assert` every subsequent anchor so a drifted file fails before it writes |
| Playwright MCP refuses the film (`file:` protocol blocked), and there's no local `npm i playwright` | MCP browser servers commonly block `file://` | Serve the folder (`python3 -m http.server <port>` — check the port isn't already serving something else), expose `window.__films[id] = { seek(t) }` in the mount engine, then build **in-page contact sheets**: one `evaluate` call seeks each beat and `drawImage(cv, …)` into a composite canvas appended to the body; screenshot that element. A whole act ships in one screenshot, zero installs |
| A frame shows elements that the source's timing math says CANNOT be on screen yet (e.g. three strike marks at a t where only one has fired) — you "fix" phantom timing bugs | `shoot-beats.js` seeks by **clicking the scrub bar** — pixel-quantized (~0.2s/px on a long film) and drift-prone, so the captured t isn't the requested t | For any timing-sensitive frame, bypass the scrub: drive `window.__films[id].seek(t)` from `evaluate` (exact), and settle disputes with a `getImageData` probe at the element's screen coords across a t-sweep. On the builders-film build the "bug" was 100% rig drift; the draw code was correct |
| You review a transition frame and it looks fine — but it's actually a DIFFERENT beat's frame | `shoot-beats.js` names outputs by rounded integer seconds (`beat_0168.png`); two requested beats < 1s apart round to the same name and the second silently overwrites the first (bit one ending review: 167.6 and 168.4 both wrote beat_0168) | keep requested beats ≥ 1s apart, or shoot sub-second-spaced frames in separate invocations — and when a reviewed frame contradicts the timeline math, suspect the filename before the draw code |

---

## Measuring — what to check, and how

Screenshots catch layout. **Only measurement catches these:**

```js
// in-browser: is it actually laid out how you think?
await pg.evaluate(() => {
  const el = document.querySelector('.film.wide');
  return { display: getComputedStyle(el).display,          // "block" when you expected grid?
           w: el.getBoundingClientRect().width,            // 300 when you expected 1130?
           overflow: document.documentElement.scrollWidth >
                     document.documentElement.clientWidth + 1 };
});
```

```bash
# data payloads: verify the embedded copy against the source, byte for byte
node -e "const a=require('fs').readFileSync('pack.txt','utf8').trim();
         const b=require('fs').readFileSync('film.html','utf8').match(/PACK = \"([0-9]+)\"/)[1];
         console.log(a.length, b.length, a===b ? 'IDENTICAL' : 'DIFFER');"
```
A hand-copied payload once dropped 3 characters = one whole record = a headline number that
read 0.195 instead of 0.194. **Inject data with a script; diff it; never retype it.**

Also verify: a sampled field's scale is disclosed on screen; the tier/bin filter (`n ≥ 10`)
is applied so tiny buckets don't swing the curve on noise.

---

## Voiced export — stamping the film into a video

The film is the artifact; the MP4 is a **dated stamp** of it for channels that only take
video. Both scripts live in this skill's `scripts/`. Full pipeline, proven on the Trinity
film (195s · 29 narration lines · 1080p30):

```bash
cp path/to/film.html work/film.html && md5 -q work/film.html      # FREEZE the source first
node scripts/export-film.js work/film.html --out film_silent.mp4
python3 scripts/voice-film.py narration.json --film film_silent.mp4 --report-only   # iterate here
python3 scripts/voice-film.py narration.json --film film_silent.mp4 -o film_voiced.mp4
# optional background music: any audio file — loops/trims to the film, 3s fades,
# sidechain-ducks ~10dB under the voice (--no-duck / --music-volume to taste)
python3 scripts/voice-film.py narration.json --film film_silent.mp4 \
    --music bg.mp3 -o film_voiced.mp4
```

**How the frame render works** — it drives the same `window.__films[id].seek(t)` hook the
review rigs use. `seek()` renders synchronously, so `seek(t); canvas.toDataURL()` inside one
`evaluate` is exact — no realtime capture, no dropped frames. Captures are batched (~12 per
round-trip; the IPC, not the draw, is the cost) → ~140fps capture, a 195s film in ~45s. The
canvas is forced to the target store size by inline style + `deviceScaleFactor: 2` (a film
capping dpr at 2 yields exactly `--width` device pixels), and `reducedMotion: "reduce"` keeps
the film's own IntersectionObserver from autoplaying under the render.

**narration.json** — the voice reads the **caption spine, compressed**; never a claim that
isn't on screen:

```json
{ "voice_id": "…",
  "speed": 1.0,
  "lines": [ { "t": 1.0, "end": 5.8, "text": "…" } ] }
```

`t` = when the line speaks (film clock). `end` = its caption's fade (optional). `speed` =
ElevenLabs pacing 0.7–1.2 (also `--speed`) — the first knob to turn when a voice reads slow.
The fit report distinguishes: **collision** = speech still going at the *next line's* `t`
(hard error, refused); **spill** = speech past its own caption's fade (fine — VO bridging a
transition is normal). Durations in the report are **effective**: each clip's dead tail
(~0.5s of TTS silence) is measured, excluded, and trimmed identically in the render. Clips
cache by `(voice, model, speed, text)` hash, so a trim pass re-bills only the lines you
edited.

### Traps

| Symptom | Cause | Fix |
|---|---|---|
| EVERY exported MP4 has its content squished into the top-left (~77% of frame) with ghost/stale panels in the right and bottom margins — while the browser, check-page, and shoot-beats all render perfectly centered. Reads exactly like a composition bug and invites a pointless re-layout of every film | export-film.js shrinks the canvas CSS width (inline style) and waits for the film to re-mount its backing store — but a style change fires NO window resize event, so films whose engine uses `addEventListener('resize',fit)` (instead of a ResizeObserver) never re-mount. `seek()` then paints the new smaller CSS size into the stale, larger load-time store: top-left content, and whatever the first paint left in the margins never gets cleared | exporter ≥ skill v1.23 dispatches `new Event('resize')` after the style change and HARD-FAILS if `cv.width != --width` after the wait. If you see this geometry in an export, check the exporter's printed store size FIRST — do not touch film layouts |
| Exported MP4 plays at a slideshow-like effective ~2.5fps — fades and eases are jumpy — while the SAME film is perfectly smooth in the browser, and check-page + shoot-beats both passed | the film's engine was authored with an **async seek** (`seek(t){t=…;pause();}` — paint deferred to the next rAF). In-browser the free-running rAF loop hides it completely, and both verification rigs allow a rAF between capture steps — but export-film.js calls `seek()` + `toDataURL()` in a synchronous batch of 12 per `evaluate()`, so no rAF ever fires inside a batch and every batch captures 12 copies of a stale canvas. Measured: 3 exact-unique frames per 120 (vs 117/120 on a compliant film) | `seek()` MUST render synchronously (the exporter's stated contract): `seek(t){…;pause();draw(g,W,H,t);}`. Decisive audit for any film before export: render an 8s segment and count exact-unique frames (`ffmpeg … f_%03d.png` + md5 uniq) across an animating window — expect near-framecount uniques minus static holds; a per-12 duplication pattern is this bug. Note `mpdecimate` UNDER-counts (its similarity threshold merges adjacent quantized alpha steps on dark fades) — hash exactly, don't decimate |
| Half your narration lines collide on the first fit report | a cloned ElevenLabs voice reads **~2.0–2.2 words/sec** on clause-heavy lines (commas, dashes and enumerations cost real seconds; product names read slowest) — not the ~2.7 you'd estimate | author main-caption-plus-sub, generate ONCE, then trim only the reported collisions; per-line rate varies ±25%, so measuring beats any pre-estimate |
| Nearly EVERY line collides after switching voices — same texts that fit fine before | voices differ far more than intuition allows: a "steady broadcaster" premade reads ~0.6-0.7 s/word, ~40% slower than a conversational clone | don't gut the narration — set `speed` (ElevenLabs voice_settings, e.g. 1.15) and regenerate; pauses compress too so the clips shorten ~28%, and prosody survives far better than post-hoc `atempo`. On the Trinity v2 export this cleared 21 of 25 collisions with zero words cut |
| Fit report shows collisions the mix doesn't actually have (0.2–0.5s, many lines) | every TTS clip ends in ~0.5s of dead silence; counted as speech it fabricates sub-second collisions across the whole script | voice-film.py ≥1.8 handles it: trailing silence is measured per clip (areverse+silencedetect), excluded from the report, and the render cuts at that exact duration |
| A line's measured duration is SHORTER than its audible content — the exact-duration cut clips the last word's tail ("…articles" loses 0.2s) — while other clips measure fine | `trailing_silence` matched `"silence_start: 0"` as a SUBSTRING, which also hits `silence_start: 0.523` — so a mid-clip pause got returned as the trailing tail. Bonus discovery: v3 clips end HOT (zero trailing silence), so on v3 most cuts should equal the full clip length | parse silencedetect output numerically and accept only the interval whose reversed start ≈ 0 (voice-film.py ≥1.21). Decisive per-clip audit when in doubt: for every cached clip assert `cut ≥ audible_end` (tail at −40dB) — margin +0.00 with cut=raw is fine (hot end), a NEGATIVE margin is the truncation |
| A line ends MID-WORD in the mix (the closing word clipped to its first syllable) right after the exact-duration-cut fix | the tail gate (−45dB) counted the final word's quiet decay as silence, so the measured effective duration landed inside the word — and v1.19 cuts exactly at the measurement | tail gate is −60dB from v1.20: only provable silence (true dead tail ≈ −90dB) counts as tail. Rule of thumb: the trim threshold must sit BETWEEN speech decay (−45..−60dB) and the clip's real noise floor — verify per voice by measuring both. Longer durations → the fit report absorbs them (atempo/trims), which is the correct place for the cost |
| The enforced min-gap "exists" in the fit report but the real mix has almost no air between lines (measured 0.15s where 0.3s was guaranteed) | the render trimmed tails by RE-DETECTING silence (`silenceremove`, windowed-RMS) while the fit measured with `silencedetect` (absolute level) — different detectors, and on breathy v3 tails they disagree ~0.3s, so the mix kept tail the math thought was cut. Same threshold is NOT enough | voice-film.py ≥1.19: never re-detect at render — `atrim` each clip at the measured effective duration (the measurement IS the trim), declick fade ending at the cut. Verify gaps in the OUTPUT: silencedetect the mux across a line boundary and read the actual silence between speech end and next onset |
| Exported video shows the film crushed into the top-left quadrant (or otherwise garbled) at the right resolution | the export snapshotted the film **mid-edit** — another session/author was writing the HTML while the render read it | freeze first: copy the film to a working path, `md5` it, render the copy, `md5` again; never render a file someone may be editing |
| `Executable doesn't exist at …chromium_headless_shell-NNNN` with browsers visibly present in `~/Library/Caches/ms-playwright` | the cached browser builds belong to *other* playwright installs; each playwright version pins its own revision | `npx playwright install chromium-headless-shell` from the repo whose playwright you resolve (or set `$PLAYWRIGHT_DIR` to a repo whose pinned revision is already cached) |
| Onset check reports a line ~6s off, and another ~0.6s early — but playback sounds perfect | back-to-back lines leave no silence gap, so silence-detection sees ONE onset for two lines; and clips that open with a breath trip the detector early | treat both as benign: verify `abs(onset−t) < 0.5s` for the *bulk* of lines and explain the outliers before touching anything |
| Onset check says the FIRST line is missing entirely — nearest onset is the next line's | a soft-spoken opening line can sit just under the silencedetect threshold (measured: −40.2dB mean vs a −38dB gate), so the detector never fires for it | don't lower the gate globally (it starts fabricating onsets from breaths): `volumedetect` the line's window vs an adjacent gap — speech-level mean in the window with a −90dB gap beside it proves placement |
| Music "ducking" audibly does nothing — speech span measures voice + full-level music | `sidechaincompress` at default gain staging: conversational VO RMS (~-41dB) never clears the threshold, so the compressor idles and the graph runs "successfully" | boost the sidechain into the detector (`level_sc=4` ≈ +12dB, `threshold=0.01`); then **measure**: `volumedetect` on a speech span vs a VO gap — speech ≈ voice-only level (+≤3dB), gap = music at full background level |
| Onset check collapses to noise on a MUSIC mix (dozens of spurious onsets, most lines "off") | silence-detection cannot see speech starts through a bed that fills every gap - and gating between music and voice levels still fires on the music's own swells | verify placement on a no-music mux of the SAME clips (pure ffmpeg, no re-billing), prove stragglers with volumedetect windows, and prove ducking separately (voice-only vs mix at one speech span) |
| Two previously-fitting lines COLLIDE after you merely INSERT a new narration line elsewhere | the clip cache filename embeds the line INDEX, so an insert invalidates every later line's cache; the re-generated clips re-roll their TTS durations (ElevenLabs is nondeterministic, ±20%) | after any insert/delete/reorder, re-read the WHOLE fit report, not just the new line - and budget for the re-billing; trim the re-rolled collisions by text, not by re-rolling the dice |
| Onset check reads EVERY line a uniform ~0.9–1.0s early (consistent bias, all lines) — looks like a placement bug in the mixer | voice-film.py's AAC output carries `audio start_time≈0.976` (edit-list offset; both shipped Trinity exports have it). Flattening to WAV — or any tool that ignores edit lists — drops the offset and shifts all content early by exactly that amount | a CONSTANT bias across all lines is a container-offset symptom, never a placement bug (placement errors vary per line). Verify on the muxed MP4 directly (ffmpeg honors PTS): `silencedetect` gated ABOVE the music floor (e.g. `-25dB:d=0.8` over a 0.06 music bed), and prove individual lines with windowed `volumedetect`. Check `ffprobe … stream=start_time` before touching the mixer |
| Ducking measurement reads "music adds 0.0dB" in BOTH the speech span AND your chosen "gap" — proves nothing either way | the "gap" was picked by eyeballing caption times and actually contains speech; also two ffmpeg CLI gotchas silently break the rig: `volumedetect`/`silencedetect` log at INFO level so `-v error` swallows all output (a measurement that prints nothing), and `-ss A -to B` placed AFTER `-i` mis-scopes the window | find TRUE silence first — `silencedetect` on the no-music mux, take the longest interval's middle — then `volumedetect` that window vs a speech span on the music mix (`-hide_banner`, and `-ss A -t DUR` before `-i`). Expected result: gap = music floor (≈−35dB at 0.06 volume), speech ≈ voice-only level |
| After switching to `eleven_v3` every line reads slower and `"speed"` does nothing — no error anywhere; and the first fresh generation dies with `400 unsupported_model: previous_text` | v3 accepts `voice_settings.speed` (HTTP 200) but IGNORES it (a 1.15 request measured LONGER than a 1.0 roll of the same text), and it rejects `previous_text`/`next_text` outright — both are v2-family features | voice-film.py ≥1.16 auto-skips prosody context on v3; pace v3 with `--max-speedup 1.1` (compresses only colliding clips; ~10% atempo is transparent) and trim leftover collisions by text; pin `model_id: eleven_multilingual_v2` in narration.json for projects built around the speed knob. Never trust a 200 on a tuning param — measure two rolls |
| A sharp click/chirp "spike" right at the END of a spoken line — usually on the last word, recurring across exports | ElevenLabs clips sometimes end in a terminal artifact at speech end. The render's tail-trim removes only SILENCE (`silenceremove` at −45dB), so a loud click at the effective end survives it — and the hard trim edge also gives the music sidechain a cliff to jump back against | voice-film.py ≥1.15 declicks every clip: a 0.12s `afade=t=in` BETWEEN the `areverse` pair = a fade-out at the true trim point, riding mostly on the kept TAIL_KEEP silence (never audibly shortens speech). For a clip that already carries the spike: evict it from `vo_clips/` and re-roll (nondeterministic ⇒ usually clean). Verify by measurement, not ear: 100ms `max_volume` slices across the line's end must ramp monotonically to −91dB — any bump is the spike |

---

## Honesty checklist (this is the product, not paperwork)

- [ ] Every statement/metric traces to real data — **nothing invented**, ever
- [ ] Verbatim vs composed is stated on the page
- [ ] Sampled marks disclose their scale (`1 dot ≈ N`); no silent mixed scales
- [ ] Rare-but-important things drawn 1:1 and labelled, not scaled into invisibility
- [ ] Snapshots aren't mixed across dates in one frame
- [ ] The misses are as visible as the hits
- [ ] The unfinished loop looks unfinished
- [ ] If the data didn't support the beat, the beat is gone — and you said why
