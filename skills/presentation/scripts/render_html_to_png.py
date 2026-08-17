"""
Render an HTML file to a PNG using headless Chromium (Playwright).

Usage:
    python3 render_html_to_png.py <html_path> <output_png> [--width 1080] [--height 1080] [--device-scale 2]

Width/height in CSS pixels. device-scale controls retina output (default 2 = sharp).
"""
import argparse
import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright


async def render(html_path: Path, output_path: Path, width: int, height: int, scale: int) -> None:
    file_url = html_path.resolve().as_uri()
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=scale,
        )
        page = await context.new_page()
        await page.goto(file_url, wait_until="networkidle")
        # extra beat so web fonts settle
        await page.wait_for_timeout(400)
        await page.screenshot(path=str(output_path), full_page=False, omit_background=False)
        await browser.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("html_path", type=Path)
    parser.add_argument("output_png", type=Path)
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--device-scale", type=int, default=2)
    args = parser.parse_args()

    if not args.html_path.exists():
        print(f"HTML file not found: {args.html_path}", file=sys.stderr)
        return 1

    args.output_png.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(render(args.html_path, args.output_png, args.width, args.height, args.device_scale))
    print(f"Rendered {args.output_png} ({args.width}x{args.height} @ {args.device_scale}x)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
