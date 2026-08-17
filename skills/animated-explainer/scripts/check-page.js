#!/usr/bin/env node
/**
 * check-page — assert the things a screenshot cannot tell you.
 *
 * Renders light / dark / narrow and reports JS errors, horizontal overflow, and the
 * *computed* geometry of the canvas. Layout bugs hide in the gap between source and output:
 * a hero that silently collapses to 300px, or a grid computing as `display:block` because
 * its CSS was dropped in an earlier rewrite, both look like "the palette is too subtle".
 *
 *   node check-page.js film.html
 *   node check-page.js http://localhost:3000/about --canvas "#cvF"
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

const [, , target, ...rest] = process.argv;
if (!target) {
  console.error('usage: check-page.js <film.html|url> [--canvas SEL] [--out DIR]');
  process.exit(1);
}
const arg = (flag, dflt) => { const i = rest.indexOf(flag); return i >= 0 ? rest[i + 1] : dflt; };
const CANVAS = arg("--canvas", "canvas");
const OUT = arg("--out", "pagecheck");

(async () => {
  fs.rmSync(OUT, { recursive: true, force: true });
  fs.mkdirSync(OUT, { recursive: true });

  let url = target;
  if (!/^https?:/.test(target)) {
    const body = fs.readFileSync(target, "utf8");
    const html = /<html|<!doctype/i.test(body)
      ? body
      : `<!doctype html><html><head><meta charset="utf-8"><style>*{margin:0;padding:0;box-sizing:border-box}</style></head><body>${body}</body></html>`;
    const tmp = path.resolve(path.dirname(target), ".check-preview.html");
    fs.writeFileSync(tmp, html);
    url = "file://" + tmp;
  }

  const browser = await chromium.launch();
  let bad = 0;

  // NOTE: browser.newPage() takes `viewport`, NOT `viewportSize`. Getting this wrong
  // silently renders every case at the default width — the narrow check passes because
  // it never actually ran narrow.
  for (const [theme, width, tag] of [["light", 1400, "light"], ["dark", 1400, "dark"], ["light", 420, "narrow"]]) {
    const pg = await browser.newPage({ viewport: { width, height: 1000 }, colorScheme: theme });
    const errs = [];
    pg.on("pageerror", (e) => errs.push("PAGEERROR: " + e.message));
    pg.on("console", (m) => { if (m.type() === "error") errs.push("CONSOLE: " + m.text()); });

    await pg.goto(url, { waitUntil: "networkidle" });
    await pg.waitForTimeout(1200);

    const m = await pg.evaluate((sel) => {
      const doc = document.documentElement;
      const cv = document.querySelector(sel);
      const r = cv && cv.getBoundingClientRect();
      return {
        overflow: doc.scrollWidth > doc.clientWidth + 1,
        scrollW: doc.scrollWidth,
        clientW: doc.clientWidth,
        canvas: cv ? { w: Math.round(r.width), h: Math.round(r.height) } : null,
      };
    }, CANVAS);

    const problems = [];
    if (m.overflow) problems.push(`HORIZONTAL OVERFLOW ${m.scrollW} > ${m.clientW}`);
    if (!m.canvas) problems.push(`canvas "${CANVAS}" NOT FOUND / not mounted`);
    // a canvas far narrower than its column is the classic silent flex-stretch failure
    if (m.canvas && m.canvas.w < m.clientW * 0.4) problems.push(`canvas suspiciously narrow: ${m.canvas.w}px in a ${m.clientW}px viewport`);
    problems.push(...errs);

    const label = `${tag.padEnd(7)} ${String(width).padStart(4)}px`;
    console.log(problems.length ? `✗ ${label}  ${problems.join(" | ")}` : `✓ ${label}  canvas ${m.canvas.w}×${m.canvas.h}, no errors, no overflow`);
    bad += problems.length;

    await pg.screenshot({ path: path.join(OUT, `page_${tag}.png`), fullPage: true });
    await pg.close();
  }

  await browser.close();
  console.log(bad ? `\n${bad} problem(s) — see ${OUT}/` : `\nall clear — screenshots in ${OUT}/`);
  process.exit(bad ? 1 : 0);
})();
