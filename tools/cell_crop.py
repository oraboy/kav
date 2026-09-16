#!/usr/bin/env python3
"""Crop a generated image to a page-cell shape: 1, 2 or 3 cells of 4:5 (4:5, 8:5, 12:5).

Crops are centred; --dx/--dy nudge the window in pixels (positive = right/down). Writes
to the given output path, or <image-stem>.cells<N>.png beside the input when none is
given (--in-place overwrites the input). Also prints the centre 4:5 phone safe zone of
the result, for placing balloons: on a wide panel the phone keeps only that crop.
"""
import argparse
import sys
from pathlib import Path

RATIOS = {1: 4 / 5, 2: 8 / 5, 3: 12 / 5}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", help="input image")
    ap.add_argument("dst", nargs="?", help="output image (default <stem>.cells<N>.png beside the input)")
    ap.add_argument("--cells", type=int, default=1, choices=[1, 2, 3])
    ap.add_argument("--dx", type=int, default=0)
    ap.add_argument("--dy", type=int, default=0)
    ap.add_argument("--in-place", action="store_true", help="overwrite the input")
    a = ap.parse_args()
    from PIL import Image
    src = Path(a.src)
    if not src.exists():
        sys.exit(f"No such image: {src}")
    dst = src if a.in_place else Path(a.dst) if a.dst else src.with_name(f"{src.stem}.cells{a.cells}.png")
    im = Image.open(src)
    W, H = im.size
    r = RATIOS[a.cells]
    if W / H > r:          # too wide: cut the sides
        w, h = round(H * r), H
    else:                  # too tall: cut top/bottom
        w, h = W, round(W / r)
    x0 = min(max(0, (W - w) // 2 + a.dx), W - w)
    y0 = min(max(0, (H - h) // 2 + a.dy), H - h)
    out = im.crop((x0, y0, x0 + w, y0 + h))
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(dst)
    # the phone crop is the centre 4:5 of the cell-shaped result: for 8:5 the middle half
    # of the width, for 12:5 the middle third
    safe_w = round(h * 4 / 5)
    sx = (w - safe_w) // 2
    print(f"{dst}: {W}x{H} -> {w}x{h} (crop at {x0},{y0}); "
          f"phone safe zone x {sx}..{sx + safe_w} (full height)")


if __name__ == "__main__":
    main()
