#!/usr/bin/env node
/**
 * shoot-beats — scrub a canvas film to specific timestamps and screenshot each beat.
 *
 * A canvas film is unreviewable without this: you cannot see beat 0:47 by reading the code,
 * and almost every layout defect (collisions, clipped labels, things drawn through other
 * things) is invisible in source and obvious in a frame.
 *
 *   node shoot-beats.js film.html 154 "5,20,45,70,100,140"
 *   node shoot-beats.js http://localhost:3000/about 154 "68,100,146" --canvas "#cvF"
 *
 * Expects the page to expose a scrub bar. Default selector matches both the standalone
 * film skeleton and the shipped React component.
 *
 * Requires: npm i playwright
 */
// Resolve playwright from the CALLER's cwd, not this script's location. Node resolves
// requires relative to the script file — and this script lives inside a skill directory, which
// will never have node_modules. Without this, `npm i playwright` where you actually run it
// has no effect and you get MODULE_NOT_FOUND.
function loadPlaywright() {
  for (const base of [process.cwd(), __dirname]) {
    try { return require(require.resolve("playwright", { paths: [base] })); } catch {}
  }
  console.error("playwright not found. Run `npm i playwright` in this directory, then retry.");
  process.exit(1);
}
const { chromium } = loadPlaywright();
const fs = require("fs");
const path = require("path");

const [, , target, endRaw, timesRaw, ...rest] = process.argv;
if (!target || !endRaw || !timesRaw) {
  console.error("usage: shoot-beats.js <film.html|url> <END_SECONDS> \"t1,t2,t3\" [--canvas SEL] [--scrub SEL] [--out DIR]");
  process.exit(1);
}
const arg = (flag, dflt) => { const i = rest.indexOf(flag); return i >= 0 ? rest[i + 1] : dflt; };

const END = Number(endRaw);
const TIMES = timesRaw.split(",").map((s) => Number(s.trim())).filter((n) => !Number.isNaN(n));
const CANVAS = arg("--canvas", "canvas");
const SCRUB = arg("--scrub", '[data-scrub], div.cursor-pointer.touch-none');
const OUT = arg("--out", "beats");

(async () => {
  // Stale frames from a previous run WILL end up in your contact sheet and read as bugs.
  // This happened three times on one build, twice producing a phantom "regression".
  fs.rmSync(OUT, { recursive: true, force: true });
  fs.mkdirSync(OUT, { recursive: true });

  let url = target;
  if (!/^https?:/.test(target)) {
    // wrap a bare film body in a skeleton if needed, so the same rig works pre- and post-port
    const body = fs.readFileSync(target, "utf8");
    const html = /<html|<!doctype/i.test(body)
      ? body
      : `<!doctype html><html><head><meta charset="utf-8"><style>*{margin:0;padding:0;box-sizing:border-box}</style></head><body>${body}</body></html>`;
    const tmp = path.resolve(path.dirname(target), ".shoot-preview.html");
    fs.writeFileSync(tmp, html);
    url = "file://" + tmp;
  }

  const browser = await chromium.launch();
  const pg = await browser.newPage({ viewport: { width: 1400, height: 1000 }, deviceScaleFactor: 2 });

  const errs = [];
  pg.on("pageerror", (e) => errs.push("PAGEERROR: " + e.message));
  pg.on("console", (m) => { if (m.type() === "error") errs.push("CONSOLE: " + m.text()); });

  await pg.goto(url, { waitUntil: "networkidle" });
  await pg.waitForTimeout(800);

  const cv = pg.locator(CANVAS).first();
  const bar = pg.locator(SCRUB).first();

  // Scroll the SCRUB into view, not the canvas: the transport sits below the canvas and a
  // tall film pushes it under the fold — clicks then land on nothing and every frame comes
  // back identical (looks like "seeking is broken", is actually "you clicked the void").
  await bar.scrollIntoViewIfNeeded();
  await pg.waitForTimeout(300);

  for (const t of TIMES) {
    const box = await bar.boundingBox();
    if (!box) { console.error("scrub bar not visible — check --scrub selector"); process.exit(1); }
    await pg.mouse.click(box.x + box.width * (t / END), box.y + box.height / 2);
    await pg.waitForTimeout(160);
    const file = path.join(OUT, `beat_${String(Math.round(t)).padStart(4, "0")}.png`);
    await cv.screenshot({ path: file });
    console.log(`  ${String(t).padStart(6)}s  ->  ${file}`);
  }

  console.log(errs.length ? "\n" + errs.join("\n") : "\nno js errors");
  console.log(`\ncontact sheet:\n  ffmpeg -pattern_type glob -i "${OUT}/beat_*.png" -vf "scale=460:-1,tile=3x3:padding=5:color=0x444444" -frames:v 1 ${OUT}/sheet.png -y`);
  await browser.close();
})();
