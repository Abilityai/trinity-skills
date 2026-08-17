#!/usr/bin/env node
/**
 * export-film — render a canvas film to an MP4, frame by frame, deterministically.
 *
 * The film stays the source of truth (live, data-driven, in the page). This produces the
 * *distribution artifact*: a video file for channels that only take video — YouTube,
 * LinkedIn, X. It is a stamp of the film at a point in time; re-export after data moves.
 *
 * Works on any film built on this skill's skeleton: draw(t) pure in t, and the mount
 * engine exposing window.__films[id] = { end, seek(t) }. Because seek() renders
 * synchronously, every captured frame is exact — no realtime capture, no dropped frames,
 * no rAF jitter.
 *
 *   node export-film.js film.html --out film.mp4
 *   node export-film.js film.html --fps 30 --width 1920 --out film.mp4
 *   node export-film.js film.html --from 47 --to 80 --out actII.mp4      # segment
 *   node export-film.js http://localhost:3000/about --film F --canvas "#cvF" --out f.mp4
 *
 * Requires: playwright resolvable from cwd, $PLAYWRIGHT_DIR, or next to this script;
 *           ffmpeg on PATH.
 */
// Resolve playwright from the CALLER's cwd, not this script's location. Node resolves
// requires relative to the script file — and this script lives inside a skill directory, which
// will never have node_modules. Without this, `npm i playwright` where you actually run it
// has no effect and you get MODULE_NOT_FOUND. $PLAYWRIGHT_DIR lets you point at any repo
// that already has playwright installed without cd-ing into it.
function loadPlaywright() {
  const bases = [process.cwd(), process.env.PLAYWRIGHT_DIR, __dirname].filter(Boolean);
  for (const base of bases) {
    try { return require(require.resolve("playwright", { paths: [base] })); } catch {}
  }
  console.error("playwright not found. `npm i playwright` in your cwd, or set PLAYWRIGHT_DIR=/path/to/repo-with-playwright.");
  process.exit(1);
}
const { chromium } = loadPlaywright();
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const [, , target, ...rest] = process.argv;
if (!target) {
  console.error(`usage: export-film.js <film.html|url> [options]
  --out FILE      output mp4 (default: <film>_export.mp4 next to the source)
  --fps N         frames per second (default 30)
  --width N       target video width in px (default 1920; height follows the canvas aspect)
  --from S        start time in seconds (default 0)
  --to S          end time in seconds (default: the film's own END)
  --film ID       key in window.__films (default: the first one)
  --canvas SEL    canvas selector (default "canvas")
  --format F      frame format: jpeg (default, q=0.92) or png (lossless, ~4x slower/bigger)
  --crf N         x264 quality (default 18; lower = better)
  --frames DIR    keep frames in DIR instead of a temp dir (skips cleanup)`);
  process.exit(1);
}
const arg = (flag, dflt) => { const i = rest.indexOf(flag); return i >= 0 ? rest[i + 1] : dflt; };

const FPS = Number(arg("--fps", 30));
const WIDTH = Number(arg("--width", 1920));
const FROM = Number(arg("--from", 0));
const TO_RAW = arg("--to", null);
const FILM_ID = arg("--film", null);
const CANVAS = arg("--canvas", "canvas");
const FORMAT = arg("--format", "jpeg");
const CRF = Number(arg("--crf", 18));
const FRAMES_DIR = arg("--frames", null);
const OUT = arg("--out", null) ||
  (/^https?:/.test(target) ? "film_export.mp4"
    : path.join(path.dirname(path.resolve(target)), path.basename(target, path.extname(target)) + "_export.mp4"));

const EXT = FORMAT === "png" ? "png" : "jpg";
const MIME = FORMAT === "png" ? "image/png" : "image/jpeg";
const BATCH = 12;   // frames per evaluate() round-trip — the IPC, not the draw, is the overhead

(async () => {
  let url = target;
  if (!/^https?:/.test(target)) {
    const body = fs.readFileSync(target, "utf8");
    const html = /<html|<!doctype/i.test(body)
      ? body
      : `<!doctype html><html><head><meta charset="utf-8"><style>*{margin:0;padding:0;box-sizing:border-box}</style></head><body>${body}</body></html>`;
    const tmp = path.resolve(path.dirname(target), ".export-preview.html");
    fs.writeFileSync(tmp, html);
    url = "file://" + tmp;
  }

  const framesDir = FRAMES_DIR || fs.mkdtempSync(path.join(require("os").tmpdir(), "film-frames-"));
  // Stale frames from a previous run would be silently glued into this video.
  if (FRAMES_DIR) { fs.rmSync(framesDir, { recursive: true, force: true }); fs.mkdirSync(framesDir, { recursive: true }); }

  const browser = await chromium.launch();
  // dpr 2 + halved CSS size = an exact WIDTH-px backing store from a film that caps dpr at 2.
  // reducedMotion keeps the film's own IntersectionObserver from autoplaying under us.
  const pg = await browser.newPage({
    viewport: { width: Math.max(1400, WIDTH / 2 + 200), height: 1000 },
    deviceScaleFactor: 2,
    reducedMotion: "reduce",
  });
  const errs = [];
  pg.on("pageerror", (e) => errs.push("PAGEERROR: " + e.message));
  pg.on("console", (m) => { if (m.type() === "error") errs.push("CONSOLE: " + m.text()); });

  await pg.goto(url, { waitUntil: "networkidle" });
  await pg.waitForFunction(() => window.__films && Object.keys(window.__films).length > 0, null, { timeout: 10000 })
    .catch(() => { console.error("window.__films not found — the film must expose the seek() test hook (see the skill's mount engine)."); process.exit(1); });

  // Force the canvas to the exact output size, wait for the film's ResizeObserver to re-mount
  // the backing store, and read back what we actually got.
  const meta = await pg.evaluate(async ({ sel, filmId, width }) => {
    const cv = document.querySelector(sel);
    if (!cv) return { error: `canvas "${sel}" not found` };
    const id = filmId || Object.keys(window.__films)[0];
    const film = window.__films[id];
    if (!film) return { error: `film "${id}" not in window.__films (have: ${Object.keys(window.__films)})` };
    const dpr = Math.min(devicePixelRatio || 1, 2);
    cv.style.width = (width / dpr) + "px";           // inline style beats the stylesheet's width:100%
    cv.scrollIntoView({ block: "center" });
    // Films re-mount their backing store from EITHER a ResizeObserver or a window resize
    // listener. An inline style change fires only the former — dispatch the event so
    // window-resize films re-mount too. Without this the store keeps its load-time size and
    // seek() paints the new (smaller) CSS size into it: content lands top-left with stale
    // pixels in the margins.
    window.dispatchEvent(new Event("resize"));
    await new Promise((r) => setTimeout(r, 400));    // let the re-mount resize the store
    await document.fonts.ready;
    film.seek(0);
    return { id, end: film.end, w: cv.width, h: cv.height, error: null };
  }, { sel: CANVAS, filmId: FILM_ID, width: WIDTH });
  if (meta.error) { console.error(meta.error); process.exit(1); }
  if (meta.w % 2 || meta.h % 2) console.error(`note: odd canvas store ${meta.w}x${meta.h} — ffmpeg will crop 1px to keep yuv420p happy`);
  if (Math.abs(meta.w - WIDTH) > 2) {
    console.error(`canvas store is ${meta.w}px wide, expected ${WIDTH} — the film did not re-mount after the resize; frames would render top-left with stale margins. Aborting.`);
    await browser.close();
    process.exit(1);
  }

  const TO = TO_RAW !== null ? Number(TO_RAW) : meta.end;
  const nFrames = Math.max(1, Math.round((TO - FROM) * FPS));
  console.log(`film "${meta.id}" · ${meta.w}x${meta.h} @ ${FPS}fps · t=${FROM}s → ${TO}s · ${nFrames} frames · ${FORMAT}`);

  const t0 = Date.now();
  for (let start = 0; start < nFrames; start += BATCH) {
    const count = Math.min(BATCH, nFrames - start);
    // seek + toDataURL inside one evaluate: render() is synchronous, so each dataURL is
    // exactly the frame at its t — deterministic by construction.
    const urls = await pg.evaluate(({ id, from, fps, start, count, mime }) => {
      const film = window.__films[id];
      const cv = document.querySelector("#cv" + id) || document.querySelector("canvas");
      const out = [];
      for (let k = 0; k < count; k++) {
        film.seek(from + (start + k) / fps);
        out.push(cv.toDataURL(mime, 0.92));
      }
      return out;
    }, { id: meta.id, from: FROM, fps: FPS, start, count, mime: MIME });
    urls.forEach((u, k) => {
      fs.writeFileSync(path.join(framesDir, `f_${String(start + k).padStart(6, "0")}.${EXT}`),
        Buffer.from(u.slice(u.indexOf(",") + 1), "base64"));
    });
    if ((start / BATCH) % 20 === 0 || start + count >= nFrames) {
      const done = start + count, rate = done / ((Date.now() - t0) / 1000);
      process.stdout.write(`\r  ${done}/${nFrames} frames  (${rate.toFixed(0)} fps capture, ~${Math.max(0, (nFrames - done) / rate).toFixed(0)}s left)   `);
    }
  }
  console.log();
  await browser.close();
  if (errs.length) console.error("JS errors during render:\n" + errs.join("\n"));

  // Assemble. crop guards odd dimensions; yuv420p is what every player expects.
  const ff = spawnSync("ffmpeg", [
    "-y", "-framerate", String(FPS), "-i", path.join(framesDir, `f_%06d.${EXT}`),
    "-c:v", "libx264", "-preset", "medium", "-crf", String(CRF),
    "-vf", "crop=trunc(iw/2)*2:trunc(ih/2)*2", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
    OUT,
  ], { stdio: ["ignore", "ignore", "pipe"] });
  if (ff.status !== 0) { console.error("ffmpeg failed:\n" + ff.stderr.toString().slice(-2000)); process.exit(1); }

  if (!FRAMES_DIR) fs.rmSync(framesDir, { recursive: true, force: true });
  const probe = spawnSync("ffprobe", ["-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", OUT]);
  const info = JSON.parse(probe.stdout.toString());
  const v = info.streams.find((s) => s.codec_type === "video");
  console.log(`\n${OUT}\n  ${v.width}x${v.height} · ${Number(info.format.duration).toFixed(2)}s · ${(info.format.size / 1e6).toFixed(1)} MB`);
  console.log(`\nnext: voice it —\n  python3 ${path.join(__dirname, "voice-film.py")} narration.json --film ${OUT} -o ${OUT.replace(/\.mp4$/, "_voiced.mp4")}`);
})();
