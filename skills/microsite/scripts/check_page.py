#!/usr/bin/env python3
"""Verify a /microsite page: console errors, horizontal overflow, broken images,
per-section screenshots. Exit 0 = clean, 3 = issues (see JSON report on stdout)."""
import argparse
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html", help="path to the microsite HTML file")
    ap.add_argument("--out-dir", default=None,
                    help="screenshot dir (default: <html dir>/checks)")
    ap.add_argument("--width", type=int, default=1440)
    ap.add_argument("--height", type=int, default=900)
    ap.add_argument("--no-shots", action="store_true",
                    help="skip screenshots (fast re-check, e.g. mobile width pass)")
    args = ap.parse_args()

    src = pathlib.Path(args.html).resolve()
    if not src.exists():
        print(json.dumps({"ok": False, "errors": [f"file not found: {src}"]}))
        sys.exit(3)
    out = pathlib.Path(args.out_dir) if args.out_dir else src.parent / "checks"
    out.mkdir(parents=True, exist_ok=True)

    report = {"file": str(src), "viewport": f"{args.width}x{args.height}",
              "errors": [], "overflow": False, "broken_images": [], "sections": []}

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": args.width, "height": args.height})
        page.on("console",
                lambda m: report["errors"].append(f"console.{m.type}: {m.text}")
                if m.type == "error" else None)
        page.on("pageerror", lambda e: report["errors"].append(f"pageerror: {e}"))
        page.goto(src.as_uri())
        page.wait_for_timeout(1500)  # fonts, images, first paint, canvas boot

        # force reveals so screenshots show final content, then measure
        page.evaluate(
            "document.querySelectorAll('.reveal').forEach(e=>e.classList.add('in'))")
        page.wait_for_timeout(300)
        report["overflow"] = page.evaluate(
            "document.documentElement.scrollWidth > document.documentElement.clientWidth + 1")
        report["broken_images"] = page.evaluate(
            "[...document.images].filter(i=>!i.complete||i.naturalWidth===0)"
            ".map(i=>i.getAttribute('src'))")

        for sec in page.query_selector_all("section[id], header[id]"):
            sid = sec.get_attribute("id") or "anon"
            entry = {"id": sid}
            if not args.no_shots:
                try:
                    sec.scroll_into_view_if_needed()
                    page.wait_for_timeout(250)
                    shot = out / f"section_{sid}.png"
                    sec.screenshot(path=str(shot))
                    entry["shot"] = str(shot)
                except Exception as exc:  # a section that can't shoot is itself a finding
                    entry["shot_error"] = str(exc)
                    report["errors"].append(f"screenshot #{sid}: {exc}")
            report["sections"].append(entry)
        browser.close()

    report["ok"] = (not report["errors"] and not report["overflow"]
                    and not report["broken_images"])
    print(json.dumps(report, indent=2))
    sys.exit(0 if report["ok"] else 3)


if __name__ == "__main__":
    main()
