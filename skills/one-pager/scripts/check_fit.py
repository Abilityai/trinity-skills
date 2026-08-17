#!/usr/bin/env python3
"""
Single-page fit-guard for /one-pager.

Loads a one-pager HTML in headless Chromium at the target canvas size and measures
whether the content actually fits the fixed page, or overflows it. This is the
mechanical half of the "literally one page" guarantee: the skill renders, runs this
check, and if it reports overflow it applies the tightening ladder and re-renders.

The page container (.page) is `height: <canvas>; overflow: hidden`, so its
`scrollHeight` reports the TRUE content extent even though overflow is clipped in the
screenshot. We compare scrollHeight/scrollWidth against the fixed client box.

Usage:
    python3 check_fit.py <html_path> --width 1920 --height 1080 [--selector .page] [--tolerance 4]

Exit codes:
    0  -> fits          (content within tolerance of the page box)
    3  -> overflow      (content exceeds the page box; see JSON for px)
    1  -> error         (file missing / measurement failed)

Always prints a one-line JSON report to stdout, e.g.
    {"fits": false, "overflow_y": 137, "overflow_x": 0, "content_h": 1217, "page_h": 1080, ...}
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

from playwright.async_api import async_playwright


async def measure(html_path: Path, width: int, height: int, selector: str, tolerance: int) -> dict:
    file_url = html_path.resolve().as_uri()
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=1,  # geometry only; pixels don't matter for the measurement
        )
        page = await context.new_page()
        await page.goto(file_url, wait_until="networkidle")
        await page.wait_for_timeout(400)  # let web fonts settle (font swap changes height)

        metrics = await page.evaluate(
            """(sel) => {
                const el = document.querySelector(sel);
                if (!el) return { found: false };
                const body = document.querySelector('.page-body');
                const footer = document.querySelector('.page-footer');
                // scrollHeight reports the full content extent even under overflow:hidden, but a
                // shrinking flex child can hide overflow as internal overlap - so we measure THREE
                // signals and take the worst: page overflow, body overflow, and content/footer overlap.
                const r = {
                    found: true,
                    content_h: el.scrollHeight,
                    content_w: el.scrollWidth,
                    page_h: el.clientHeight,
                    page_w: el.clientWidth,
                    body_scroll_h: body ? body.scrollHeight : 0,
                    body_client_h: body ? body.clientHeight : 0,
                };
                // bottom of the lowest body row vs the top of the footer (catches overlap directly)
                let lastBottom = 0, worst = null;
                el.querySelectorAll('.page-body > .row, .page-body > .block').forEach((row) => {
                    const b = row.getBoundingClientRect().bottom;
                    if (b > lastBottom) { lastBottom = b; worst = row.className; }
                });
                r.last_content_bottom = lastBottom;
                r.footer_top = footer ? footer.getBoundingClientRect().top : el.getBoundingClientRect().bottom;
                r.last_row_class = worst;
                return r;
            }""",
            selector,
        )
        await browser.close()

    if not metrics.get("found"):
        return {"error": f"selector {selector!r} not found", "fits": False}

    page_over = metrics["content_h"] - metrics["page_h"]
    body_over = metrics["body_scroll_h"] - metrics["body_client_h"]
    overlap = metrics["last_content_bottom"] - metrics["footer_top"]
    overflow_y = max(0, page_over, body_over, overlap)
    overflow_x = max(0, metrics["content_w"] - metrics["page_w"])
    fits = overflow_y <= tolerance and overflow_x <= tolerance
    return {
        "fits": fits,
        "overflow_y": overflow_y,
        "overflow_x": overflow_x,
        "page_over": page_over,
        "body_over": body_over,
        "footer_overlap": overlap,
        "content_h": metrics["content_h"],
        "page_h": metrics["page_h"],
        "tolerance": tolerance,
        "last_row_class": metrics.get("last_row_class"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html_path", type=Path)
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--selector", type=str, default=".page")
    ap.add_argument("--tolerance", type=int, default=4, help="px of slack before declaring overflow")
    args = ap.parse_args()

    if not args.html_path.exists():
        print(json.dumps({"error": f"file not found: {args.html_path}", "fits": False}))
        return 1

    result = asyncio.run(measure(args.html_path, args.width, args.height, args.selector, args.tolerance))
    print(json.dumps(result))
    if result.get("error"):
        return 1
    if result["fits"]:
        return 0
    return 3


if __name__ == "__main__":
    sys.exit(main())
