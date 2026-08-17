#!/usr/bin/env python3
"""
Wrap a one-pager PNG as a single-page PDF, sized to the correct physical page.

/one-pager renders ONE PNG (one page, never two). This stamps it into a PDF at the
right DPI so the page comes out physically correct when printed:

    16:9    -> --dpi 192   (3840x2160 PNG -> 20.0 x 11.25 in screen page)
    a4      -> --dpi 300   (2480x3508 PNG -> 8.27 x 11.69 in = exact A4)
    letter  -> --dpi 300   (2550x3300 PNG -> 8.5  x 11.0  in = exact US Letter)

Usage:
    python3 build_pdf.py <png> --output out.pdf --dpi 300
    python3 build_pdf.py <png1> [<png2> ...] --output out.pdf --dpi 300   # multi-page also works

Accepts one or more PNGs (sorted by name). The typical one-pager call passes exactly one.
"""
import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow is not installed. Run: pip install pillow", file=sys.stderr)
    sys.exit(1)


def build(pngs: list[Path], output: Path, dpi: float) -> int:
    pngs = sorted(pngs)
    images = []
    for p in pngs:
        if not p.exists():
            print(f"ERROR: PNG not found: {p}", file=sys.stderr)
            sys.exit(2)
        im = Image.open(p)
        if im.mode != "RGB":
            im = im.convert("RGB")
        images.append(im)

    output.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(
        output,
        "PDF",
        save_all=True,
        append_images=images[1:],
        resolution=float(dpi),
    )

    w, h = images[0].size
    size_kb = output.stat().st_size / 1024
    page_in = f"{w / dpi:.2f} x {h / dpi:.2f} in"
    print(f"PDF written: {output} ({size_kb:.0f} KB, {len(images)} page(s), {w}x{h}px @ {dpi:.0f}dpi = {page_in})")
    return len(images)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pngs", type=Path, nargs="+", help="one-pager PNG(s)")
    ap.add_argument("--output", type=Path, required=True, help="output PDF path")
    ap.add_argument("--dpi", type=float, default=300.0, help="page DPI (16:9 -> 192, a4/letter -> 300)")
    args = ap.parse_args()
    build(args.pngs, args.output, args.dpi)


if __name__ == "__main__":
    main()
