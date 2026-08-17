---
name: animated-explainer
description: Build an animated, data-driven explainer film for a real system — a canvas film that renders live from the product's own data and cannot drift, not an exported video. Can additionally stamp the finished film into a voiced MP4 (deterministic frame render + timed ElevenLabs narration) for channels that only take a video file. Use when someone wants to explain how a system works visually, wants an explainer/hero video, references a motion-graphics explainer to imitate, or asks to show a mechanism rather than describe it. NOT for static diagrams or single illustrations.
category: visual-communication
argument-hint: "<system or topic to explain> [--reference <video-url>] [--data <path>] [--export] [--voice]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill, AskUserQuestion, WebFetch
user-invocable: true
requires:
  env: [ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, PLAYWRIGHT_DIR]
  binaries: [node, python3, ffmpeg]
metadata:
  version: "1.26"
  created: 2026-07-15
  author: Ability.ai
  changelog:
    - "1.26: Promoted to the public trinity-skills library — declared requires:/argument-hint, documented cold-start behavior for the optional ElevenLabs keys (the film itself needs no credentials; only the Step 11 voiced export does), skill-relative script paths, sibling-skill references made optional, and build provenance genericized for a public repo"
    - "1.25: WSC caption-band trap (multi-agent concepts film): the caption-safe world-y rule (cy + (0.79-0.5)/z) ignores the world-scale inset (WSC 0.875), so bottom-row structures thought cropped at z 1.2-1.4 render straight under the captions in every mildly-zoomed shot; fix = include WSC in the safe-y math, or focus-dim the bottom row during chapters where it is furniture (reference.md → Layout traps)"
    - "1.24: Standing-fixture accumulation trap (user-reported on the BE intelligence-layer film): in films that BUILD UP a persistent world (stack/map films), each chapter's vignette furniture (annotation chips, helper persons, shelf labels, dashed marks) silently accumulates into overlap clutter by the late chapters — and every per-beat review passes because each chapter looks fine in ITS OWN frames. Rule: transient annotations fade when their chapter ends (keep only core structures); verify by reviewing LATE-chapter frames for accumulated fixtures and transition midpoints, not just each chapter's own beats. Also: if a closing frame draws a boundary (ownership/sovereignty metaphor), assert every fixture's extents sit INSIDE it — side panels poking through the frame edge break the metaphor"
    - "1.23: Export top-left/ghost-margin trap (user-reported twice, misdiagnosed once as composition): export-film.js shrinks the canvas CSS width and waits for a re-mount, but films whose engine uses addEventListener(resize, fit) never re-mount (inline style change fires no window resize) — seek() then paints the new smaller CSS size into the stale load-time backing store: content top-left at ~77%, stale pixels ghosting in the margins, while browser/check-page/shoot-beats all look perfect. Fix in exporter: dispatch new Event(resize) after the style change AND hard-fail if the store width != --width. The film-side symptom is identical to a composition bug — check meta.w BEFORE re-authoring layouts"
    - "1.22: Async-seek export trap from a 12-film course batch — an engine whose seek() only sets state (paint on next rAF) is invisibly broken for export-film.js, which batches 12 seek+toDataURL calls per evaluate() with no rAF between them: every batch captures 12 stale frames (~2.5fps output) while the browser, check-page, and shoot-beats all look perfect. seek() must draw synchronously (the exporter's contract); audit with exact-frame-hash uniqueness on an animating segment, not mpdecimate (which merges quantized dark-fade steps)"
    - "1.21: trailing_silence substring bug — 'silence_start: 0' in line also matches 0.523, so a MID-CLIP pause could be returned as the tail and the exact-duration cut truncated the line's end by that amount; parse numerically (start ≈ 0 only). Also learned: v3 clips end HOT (zero trailing silence), so most cuts = full clip length"
    - "1.20: Tail gate −45dB → −60dB — a final word's quiet decay counted as silence at −45, so the exact-duration cut (1.19) truncated it mid-word ('…Yo'). Only provable silence (true dead tail ≈ −90dB) may trim; longer effective durations are the fit machinery's problem, never the listener's"
    - "1.19: The render trim now IS the measurement — atrim at each clip's measured effective duration (declick fade at the cut) replaces silenceremove. Trap it fixes: silencedetect (absolute) and silenceremove (windowed RMS) disagree on v3 breathy tails by ~0.3s, so the render kept tail the fit math thought was cut — the min-gap guarantee silently shrank (measured: 0.15s of real air where 0.3s was enforced)"
    - "1.18: voice-film.py --base-speedup — uniform render-time atempo on every clip (the global pace lever for models that ignore the API speed knob, e.g. eleven_v3; 1.05 = 5% faster, zero re-billing); fit report and spill math now use effective (atempo-adjusted) durations"
    - "1.17: Guaranteed inter-line breathing gap — voice-film.py --min-gap (default 0.3s): each line must END that much silence before the NEXT line's start; line starts stay pinned to caption times (the film alignment), the previous line absorbs the gap via auto-atempo or a trim. Matters most on eleven_v3, whose dense expressive read can otherwise butt lines together with ~0.05s of air"
    - "1.16: Default TTS model → eleven_v3 (most expressive tier). Two measured traps: v3 accepts voice_settings.speed (HTTP 200) but ignores it — pace v3 with --max-speedup 1.1 + text trims (pin model_id eleven_multilingual_v2 when the speed knob is required) — and v3 rejects previous/next_text (400 unsupported_model), so voice-film.py now auto-skips prosody context on v3"
    - "1.15: Terminal-spike trap from a course film — ElevenLabs clips can end in a sharp click/chirp on the final word, and the tail-trim removes only silence so it survives the render; voice-film.py now fades the last 0.12s of every clip at its trim point (afade=t=in between the areverse pair — declicks the tail and softens the ducking release). Existing spiked clip: evict from vo_clips/ + re-roll; verify with 100ms max_volume slices (must ramp monotonically to silence)"
    - "1.14: From the knowledge-agent film re-cut — verbatim-subtitle mode is now the default for voiced films (one line, one font, byte-identical to narration.json + scripted parity check; user-confirmed that caption/voice divergence reads as an error); global pace as a single t/SHORTEN divisor (reference: Film skeleton); four new traps — scrim must outlive its scene's contents (previous-scene flash), camera-gated world labels, shoot-beats integer-second filename collisions, and true-silence-first ducking measurement with the -v error / -ss-after-i ffmpeg gotchas"
    - "1.13: Trap from the knowledge-agent lens re-export - inserting a narration line invalidates the index-keyed clip cache for every later line and re-rolls their durations; re-read the whole fit report after any insert"
    - "1.12: Container-offset trap from the builders-film export — voice-film.py MP4s carry audio start_time≈0.976 (edit list); WAV-flattened onset checks read ALL lines a uniform ~1s early. A constant bias = container offset, never a placement bug; verify on the muxed MP4 (PTS honored) with a music-floor-aware gate + windowed volumedetect"
    - "1.11: Trap from the knowledge-agent music export - the onset check is blind on a music mix; verify placement on a no-music mux of the same clips and prove ducking separately"
    - "1.10: Onset-check trap from the knowledge-agent export — a soft-spoken FIRST line can sit under the silencedetect gate and read as missing; prove placement with volumedetect (speech-level window vs −90dB gap), never by lowering the gate"
    - "1.9: Trap from the builders-film build — shoot-beats' scrub-click seeking drifts (pixel-quantized), producing phantom timing bugs; verify timing-sensitive frames via the __films seek hook + a getImageData probe before touching the draw code"
    - "1.8: Voice pacing + honest fit math in voice-film.py — `speed` (ElevenLabs voice_settings, 0.7-1.2) fixes a slow narrator globally BEFORE any words are cut (Daniel at 1.15 cleared 21 of 25 collisions untouched), and every clip's ~0.5s dead tail is now measured, excluded from the fit report, and trimmed identically in the render"
    - "1.7: Background music in the voiced export — voice-film.py --music FILE (loop/trim/fade + sidechain ducking under the voice). Trap: sidechaincompress silently does nothing at default gain staging — the sidechain needs level_sc boost to clear the threshold; verify ducking by measuring a speech span vs a gap, never by ear alone"
    - "1.6: Voiced video export — scripts/export-film.js (seek-hook frame render → MP4) + scripts/voice-film.py (timed ElevenLabs narration with a collision-checked fit report, muxed). Proven on the Trinity film (195s, 29 lines). The film stays the source of truth; the MP4 is a dated stamp"
    - "1.5: Two layout traps from the Trinity business-explainer build — data-driven labels need measureText fit-to-width (one font size can't fit real entity names), and stage→overview transitions need overlapping fade windows (screenshot transition midpoints, not just beat centres)"
    - "1.4: Trap from the Trinity extension: scripted time-shifts must keep sub-threshold literals byte-identical (no reformatting) and assert every later anchor before writing"
    - "1.3: Layout trap from the knowledge-agent orb-restyle — a background-attachment:fixed page gradient paints only the viewport band (white elsewhere in stitched full-page captures and on iOS Safari); fix is a solid base color on html under it"
    - "1.2: Review traps from the Trinity build — hairline strokes read bright in downscaled contact sheets (measure with getImageData, not eyes), and a zero-install Playwright-MCP rig (http.server + window.__films seek hook + in-page composite contact sheets)"
    - "1.1: Four render-only traps added to reference.md from the knowledge-agent build — draw-helper globalAlpha reset silently defeating label fades, missing charset meta producing canvas mojibake, camera-clamp shifting zoomed framings so world-space labels clip or hit the screen-space caption band, and radial arcs bunching/wrapping labelled items (use a list + spoke)"
    - "1.0: Initial version — distilled from building a forecasting platform's hero explainer end to end (reference decode → data interrogation → worked example → canvas film → React port → shipped live)"
---

# Animated Explainer

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `animated-explainer vX.Y — recent: <summary>`. Then proceed.

ultrathink

## Purpose

Build an **animated explainer of how a real system works** — rendered live to a `<canvas>`
from the system's **own data**, so it regenerates on every publish and can never drift from
what the product reports.

**The thesis: a data-driven film, not a video.** An exported MP4 is stale the day the data
moves, and it quietly becomes a lie. A film that reads `data/*.json` at render time changes
when the system changes. (This is testable: on the forecasting build, a data refresh landed
mid-deploy and the calibration curve visibly redrew.)

**Use this when** someone wants to *show a mechanism* — how a system works, why it's
trustworthy, what happens to one item as it moves through.

**Don't use this for** static diagrams or illustrations — a diagram skill (if your
workspace has one) is the right tool there. This skill is specifically **time-based motion
driven by live data**.

## State Dependencies

| Source | Location | Read | Write |
|---|---|---|---|
| The system's real data | product repo `data/*.json` (or equivalent) | ✅ | ❌ never |
| The system's source of truth | `ARCHITECTURE.md`, papers, specs — **not** published artifacts | ✅ | ❌ |
| Brand tokens | the product's `globals.css` / theme file | ✅ | ❌ |
| Working film | `<scratch>/film.html` (standalone, no build) | ✅ | ✅ |
| Shipped component | product repo `components/**/explainer.tsx` | ✅ | ✅ |
| Verification rigs | `scripts/shoot-beats.js`, `scripts/check-page.js` (this skill) | ✅ | ❌ |
| Export rigs | `scripts/export-film.js`, `scripts/voice-film.py` (this skill) | ✅ | ❌ |
| Narration script | `<film dir>/narration.json` (timed lines, next to the film) | ✅ | ✅ |
| Voiced export | `<film dir>/export/` — MP4 stamp + `vo_clips/` TTS cache | ✅ | ✅ |

## Composes

| Skill | When |
|---|---|
| a site-publishing skill | Final step, only if the film ships to a live site and the user has asked for a deploy. Optional — this skill never requires it. |

## Credentials & cold start

Building, verifying, and shipping a film needs **no credentials at all**. Only the optional
voiced export (Step 11) reads any:

| Key | Needed for | Missing → |
|---|---|---|
| `ELEVENLABS_API_KEY` | Step 11 TTS narration | Fail fast with `ELEVENLABS_API_KEY not set — add it to this agent's credentials`; every earlier step still runs, and the silent MP4 export is unaffected. |
| `ELEVENLABS_VOICE_ID` | default voice for Step 11 | Optional — `voice_id` in `narration.json` or `--voice` overrides it. Absent with no override → the tool stops and names the three ways to supply it. |
| `PLAYWRIGHT_DIR` | pointing the render scripts at an existing playwright install | Optional — the scripts resolve playwright from the caller's cwd first, then this variable, then the skill directory. |

Script paths below are relative to **this skill's directory**; run them from there, or
prefix with the directory the skill was injected into.

---

## Core principles

These are load-bearing. Each one was paid for.

### 1. The data is the story's boss — interrogate it before you design the arc

Decide what's **true** before you decide what's **compelling**. Concepts must die here; that
is the step working, not failing.

Two died on the forecasting build, both after the storyboard felt great:
- *"watch it get better over time"* — the metric was **flat** (0.217 → 0.188 → 0.210). Noise,
  not learning. Animating it would have faked the one number the brand rests on.
- *"performance improving"* curve — the sample was **back-loaded** (Q1 spanned 3 months, Q4
  spanned 1 day), so the apparent decline was a **sampling artifact**, not improvement.

Run the numbers yourself. Check the **shape and the sampling**, not just the headline.
Finding this at storyboard costs an hour; finding it after a render costs a week; not finding
it costs your credibility.

### 2. Read the source of truth, not the published artifacts

Published data dirs are a *curated snapshot* of a system, not the system. On that build the whole
first film was built from the website's `data/` and got the architecture **wrong** — the real
mechanism was in `ARCHITECTURE.md` and an unpublished paper. Find the design docs.

### 3. One concrete worked example beats any amount of abstraction

Follow **one real item end to end**. The film only worked once it became a single real
forecast — *said 88%, world said no* — traced from question to consequence.

**Prefer a failure.** A miss shows the machine doing its job, is impossible to read as
cherry-picking, and gives every downstream loop something real to react to.

### 4. Explainer, not advertisement

Assume the viewer knows nothing. It must read **with** a voiceover on top and **without** one.
Open on the **problem**, not the architecture — state what's broken, then reveal the machine
as the answer. A hook is not a flourish; it's the reason to keep watching.

### 5. Separate the mechanism from the numbers

Statistics clutter an explanation. Carry the mechanism with **symbolic marks**, then put real
figures at the very end — or nowhere. If a mark is not 1:1 with a thing, **say so on screen**
(`1 dot ≈ 30 beliefs`). If something is too rare to be field scale (17 of 44,510 = 0.6 of a
dot), draw it 1:1 as an annotated callout and label it — never silently mix scales.

### 6. Nothing teleports

If a thing appears somewhere new, **animate it getting there**. A chart that materialises is a
cut; a chart that dots visibly *fall onto* is an explanation. This was the single biggest
"it doesn't explain it better" complaint on that build, and fixing it changed the film.

### 7. Lock the layout

One circuit. Nothing crosses anything. Spaghetti beziers read as *complexity*, not as a
system. A horizontal spine + a return rail + entities sitting **on** the rail reads instantly.

### 8. Show the part that doesn't work

That system's Loop 0 stays **dashed and hollow** for the whole film because it has commissioned
consequences but zero resolved. A diagram where everything works is the least trustworthy
thing you can draw. **The unfinished part is the credibility.**

### 9. Screenshot every beat. Measure anything computed. They are different jobs.

- **Look** at renders → catches collisions, clipping, off-frame labels, composition.
- **Measure** in the browser/numerically → catches wrong values, wrong layout, aliasing.

Neither substitutes for the other. On that build, *every* numeric bug was invisible to the eye and
*every* layout bug was invisible to the code.

### 10. Lift proven code — never retype it

Port by **script**, not by hand. Hand-copying a data payload once silently dropped a record
and changed a headline number from 0.194 to 0.195.

---

## Process

### Step 1 — Decode the reference (if there is one)

Never design against a *description* of a reference. Get the artifact.

```bash
yt-dlp -o ref.mp4 "<url>"                                   # X/social links often block WebFetch
ffmpeg -i ref.mp4 -vf "fps=1/2,scale=520:520,tile=4x5" sheet.png   # contact sheet of the arc
ffmpeg -ss 12 -i ref.mp4 -frames:v 1 f.png                  # a specific beat, full res
```
Then **sample its actual palette** (don't eyeball hex): see `reference.md` → *Palette sampling*.

Write down **what the reference does**, decision by decision, and explicitly mark which
decisions transfer and which you'll break — and why.

### Step 2 — Interrogate the data (the gate)

Before any storyboard, answer in writing:
- What does the data actually support? What does it **refuse** to support?
- Is any apparent trend an artifact of **sampling** (uneven time buckets, back-loading)?
- What's the most interesting **true** thing here?

If the story you wanted isn't supported: **change the story, say so, and offer the honest
alternative.** Do not soften it into an animation.

### Step 3 — Find the source of truth

Read the architecture docs, papers, specs. Not the published JSON. Reconcile disagreements and
note which snapshot each figure comes from (dates matter — never mix snapshots in one frame).

### Step 4 — Choose the worked example

One real item, ideally a real failure. Pull it verbatim: the claim, the number, the outcome,
the reasoning. Note precisely **what is verbatim and what you compose** — and disclose it.

### Step 5 — Storyboard the beats

Problem → question → commitment → reality → *"but does that prove anything?"* → mechanism →
payoff. Write the captions first: **if the captions alone tell the story, the film will work.**

**Decide the caption mode now, not at export time:**
- **Voiced film planned** (the usual case) → **one caption line, one font, verbatim what the
  voice will say.** Viewers read while they listen; a second font or diverging text reads as
  an error, not as extra detail (user-confirmed on the knowledge-agent film — "having two different
  fonts is confusing; what the voice is saying should exactly match the subtitles"). Fine
  detail (names, edge types, figures) lives in on-canvas diagram labels, not a caption sub-line.
- **Silent-only film** → caption pairs (main + sub) are fine; the sub-line carries the detail.

### Step 6 — Build in a standalone HTML

One self-contained file, no build step, opens in a browser. Fast iteration is everything here.
Use the product's **real brand tokens**. See `reference.md` for the film skeleton, camera,
path-following, and growth recipes.

Author the storyboard on its own internal clock and treat overall pace as a **single divisor**
(`t = t / SHORTEN`, first line of `draw`) — "make it 20% faster" then costs one constant, not
a re-authoring of every beat. Recipe: `reference.md` → *Film skeleton*.

### Step 7 — Verify every beat

```bash
node scripts/shoot-beats.js film.html 154 "5,20,45,70,100,140"   # scrub + shoot each beat
node scripts/check-page.js  film.html                            # themes, overflow, JS errors
```
**Delete old screenshots before every shoot** (`rm -f shot_*.png`) — stale frames polluted
three separate reviews and produced two phantom "bugs".

Look at every frame. Then measure anything numeric (see `reference.md` → *Measuring*).

### Step 8 — Port to a component (by script)

Lift the `draw` block out of the proven HTML with a script. Hoist constants to module scope.
Feed data in as **props from the server component**, computed from the repo's own files — this
is what makes it self-updating. See `reference.md` → *React port* (and its effect-structure
trap, which silently breaks scrubbing).

### Step 9 — Build-gate, then drive the real page

```bash
npm run build        # never ship a broken build
npm run start        # then drive the REAL page, not just the static HTML
```
Kill stale servers first (`kill -9 $(lsof -ti:3000)`) — testing a stale build wastes a cycle.
Assert: canvas mounts at expected size, no JS errors, no horizontal overflow, **scrubbing
lands where you click**.

### Step 10 — Ship (only if asked)

Invoke `/publish-site`. Deploy **source only**; don't bundle a data refresh into a component
deploy — it muddies rollback. Verify the live page by driving it, not by curling for a 200.

### Step 11 — Export a voiced video (only if asked)

The film is the source of truth; some channels (YouTube, LinkedIn, X) only take a video file.
This step **stamps** the film into a voiced MP4. The stamp is dated the moment the film or its
data changes — say so wherever it's posted, and re-export instead of editing the video.

```bash
# 1. Render frames deterministically through the film's own seek() hook → silent MP4
node scripts/export-film.js film.html --out film_silent.mp4          # 1080p30 by default

# 2. Author narration.json — in verbatim mode (the default, Step 5) each line is the caption
#    text byte-for-byte; in compressed mode it's the caption spine, trimmed to fit.
#    Either way: never introduce claims that aren't on screen.

# 3. Generate clips + fit report (no render). Iterate on the text until 0 collisions.
python3 scripts/voice-film.py narration.json --film film_silent.mp4 --report-only

# 4. Render: timed voiceover track, muxed over the silent export
python3 scripts/voice-film.py narration.json --film film_silent.mp4 -o film_voiced.mp4

# Optional: background music under the voice — any audio file; it loops/trims to the film,
# fades in/out, and sidechain-ducks ~10dB while the voice speaks (--no-duck to disable).
# Sourcing the track is upstream of this skill: a music library or a generative
# music service. This skill never sources audio; it only places what you give it.
python3 scripts/voice-film.py narration.json --film film_silent.mp4 \
    --music bg.mp3 --music-volume 0.06 -o film_voiced.mp4
```

Rules that make this work (paid for on the Trinity export — details in `reference.md` →
*Voiced export*):

- **Freeze the source first.** Copy the film to a working path and hash it before/after the
  render. Exporting a file that's mid-edit produced a corrupted render once already.
- **Narration = captions.** In **verbatim mode** the two are the SAME strings — so a trim to
  fix a collision edits the film's caption AND narration.json together, and you re-render the
  silent MP4 after any text change (the words are on screen). Parity-check the two arrays
  (extract the CAPS strings, diff against narration.json, require 0 mismatches) as part of
  verification. A cloned voice runs ~2.0–2.2 words/sec on clause-heavy lines — slower than
  you'd guess. Don't pre-trim by guesswork: generate once, read the fit report, trim only the
  collisions. The clip cache re-bills only edited lines.
- **Fix pace before words.** Voices differ hugely (ElevenLabs' Daniel reads ~40% slower than
  a typical clone). If the first report is a wall of collisions, set `"speed"` in
  narration.json (or `--speed`, 0.7–1.2) and regenerate — speed compresses pauses too, so
  1.15 shortens clips ~28%. Only then trim the survivors by hand.
- **Collisions are errors; spills are style.** Speech overlapping the *next* line's start is
  refused by the tool. Speech running past its own caption's fade is fine.
- **Verify placement objectively**: the fit report proves fit, not placement — after muxing,
  run silence-detection over the output and diff speech onsets against `narration.json` times
  (expect two benign artifacts: back-to-back lines merge, and a breath fires ~0.5s early).
- **Verify ducking by measurement, not by ear**: compare `volumedetect` mean levels of a
  speech span against a voiceover gap. Speech span ≈ voice-only level (music adds ≤3dB);
  gap shows the music at full background level. A "duck" that measures 0dB is the
  sidechain-threshold trap (`reference.md` → *Voiced export* → Traps).
- Requires: `ffmpeg` on PATH, playwright resolvable (cwd / `$PLAYWRIGHT_DIR`),
  `$ELEVENLABS_API_KEY` (or `--env /path/to/.env`), and a voice id (`voice_id` in
  narration.json, `--voice`, or `$ELEVENLABS_VOICE_ID`).
- **Model:** default is `eleven_v3` (most expressive tier). v3 **ignores
  `voice_settings.speed`** — the request returns 200 and the audio is unchanged (measured), so
  the `"speed"` pacing knob only works on `eleven_multilingual_v2` (pin it via `model_id` in
  narration.json when you need it). On v3, pace with `--max-speedup 1.1` (auto-compresses only
  colliding clips, transparently) and trim the survivors by text.
- **Breathing gap:** the fit enforces `--min-gap` (default 0.3 s) of silence between each
  line's speech end and the next line's start. Starts never move — they are the film
  alignment; the *previous* line absorbs the gap via atempo or a trim.

---

## Outputs

- A standalone `film.html` (durable working source — **save it out of any scratchpad**)
- A shipped component reading live data as props
- Beat screenshots proving each beat renders
- A written note of what is verbatim vs composed, surfaced on the page
- (If exported) `narration.json` + the voiced MP4 + `vo_clips/` cache, saved next to the film
  source — the narration script is part of the working source, not a throwaway

## Completion checklist

- [ ] Data interrogated; unsupported story beats cut and reported
- [ ] Palette sampled from the real reference / brand tokens
- [ ] One real worked example, verbatim, with sourcing disclosed
- [ ] No un-disclosed scale mixing; no fabricated statements or metrics
- [ ] The unfinished part is visibly unfinished
- [ ] Every beat screenshotted and reviewed; every computed value measured
- [ ] Component reads live data (change the data → the film changes)
- [ ] Build passes; real page driven; scrubbing verified
- [ ] Working source saved somewhere durable, not a scratchpad
- [ ] (If exporting) narration fits: 0 collisions in the fit report; onsets verified against
      `narration.json` after the mux; the stamp's date disclosed wherever the video is posted
- [ ] (If verbatim mode) captions ⇄ narration parity: 0 mismatches, checked by script — and
      every caption trim re-rendered the silent MP4, not just the audio

## Reference

`reference.md` — code recipes: film skeleton, camera + clamping, path-following travellers,
the integrated-rate trap, growth packing, the React port, palette sampling, measuring, and
the voiced-export pipeline (frame render, narration format, pacing traps).

## Self-Improvement

After completing this skill's primary task, consider tactical improvements:

- [ ] **Review execution**: Were there friction points, unclear steps, or inefficiencies?
- [ ] **New trap found?** If a bug cost real time, add it to `reference.md` → *Traps* with the
      symptom, the cause, and the fix. Symptom-first — that's how it'll be searched for.
- [ ] **Scope check**: Only tactical/execution changes—NOT changes to core purpose or goals
- [ ] **Apply improvement** (if identified):
  - [ ] Edit this SKILL.md (or `reference.md`) with the specific improvement
  - [ ] Bump `metadata.version` and prepend a `changelog` entry
- [ ] **Version control** (if in a git repository):
  - [ ] Stage: `git add <skill-path>`
  - [ ] Commit: `git commit -m "refactor(animated-explainer): <brief improvement description>"`
