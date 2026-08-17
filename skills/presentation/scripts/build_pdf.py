#!/usr/bin/env python3
"""
Combine a set of slide PNGs into a single multi-page PDF.

Used as the final step of /presentation. Each PNG becomes one PDF page sized to
match the slide's native dimensions (1920x1080 for 16:9 presentations).

Usage:
    python3 build_pdf.py \
        --slides-dir /tmp/presentation_my_deck/ \
        --pattern "my_deck_slide_*.png" \
        --output /tmp/presentation_my_deck/my_deck.pdf

The script reads all PNGs matching the pattern, sorts them by filename (so
slide_01.png, slide_02.png ... order correctly), converts each to RGB, and
writes them as pages of a single PDF via PIL.
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow is not installed. Run: pip install pillow", file=sys.stderr)
    sys.exit(1)


def build_pdf(slides_dir: Path, pattern: str, output: Path) -> int:
    """Assemble matching PNGs in slides_dir into a single PDF at output. Returns page count."""
    pngs = sorted(slides_dir.glob(pattern))
    if not pngs:
        print(f"ERROR: no files matched {pattern!r} in {slides_dir}", file=sys.stderr)
        sys.exit(2)

    print(f"Found {len(pngs)} slides:")
    for p in pngs:
        print(f"  {p.name}")

    # Open all images as RGB (PDF doesn't support RGBA)
    images = []
    for p in pngs:
        im = Image.open(p)
        if im.mode != "RGB":
            im = im.convert("RGB")
        images.append(im)

    output.parent.mkdir(parents=True, exist_ok=True)
    # The first image is the "host" - additional pages get appended.
    images[0].save(
        output,
        "PDF",
        save_all=True,
        append_images=images[1:],
        resolution=72.0,  # 72 DPI - 1920x1080 PNG -> ~26.67 x 15.0 inch page
    )

    size_kb = output.stat().st_size / 1024
    print(f"\nPDF assembled: {output} ({size_kb:.0f} KB, {len(images)} pages)")
    return len(images)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--slides-dir", type=Path, required=True, help="Directory containing slide PNGs")
    p.add_argument("--pattern", type=str, default="*_slide_*.png",
                   help="Glob pattern for slide PNGs (default: *_slide_*.png)")
    p.add_argument("--output", type=Path, required=True, help="Output PDF path")
    args = p.parse_args()

    if not args.slides_dir.is_dir():
        print(f"ERROR: slides-dir not found or not a directory: {args.slides_dir}", file=sys.stderr)
        sys.exit(2)

    build_pdf(args.slides_dir, args.pattern, args.output)


if __name__ == "__main__":
    main()
