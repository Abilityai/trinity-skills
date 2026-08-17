#!/usr/bin/env python3
"""Export a /microsite page to its PDF companion via the page's @media print stylesheet.
Forces all reveals complete first so canvases/counters land at their final state."""
import argparse
import pathlib

from playwright.sync_api import sync_playwright


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html", help="path to the microsite HTML file")
    ap.add_argument("--output", default=None, help="PDF path (default: <html>.pdf)")
    ap.add_argument("--format", default="A4", help="paper format (A4, Letter)")
    ap.add_argument("--landscape", action="store_true")
    args = ap.parse_args()

    src = pathlib.Path(args.html).resolve()
    out = pathlib.Path(args.output) if args.output else src.with_suffix(".pdf")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1240, "height": 900})
        page.goto(src.as_uri())
        page.wait_for_timeout(1800)  # fonts, images, canvas boot
        page.evaluate(
            "document.querySelectorAll('.reveal').forEach(e=>e.classList.add('in'))")
        page.wait_for_timeout(400)
        page.emulate_media(media="print")
        page.pdf(path=str(out), format=args.format, landscape=args.landscape,
                 print_background=True,
                 margin={"top": "12mm", "bottom": "14mm",
                         "left": "12mm", "right": "12mm"})
        browser.close()
    print(out)


if __name__ == "__main__":
    main()
