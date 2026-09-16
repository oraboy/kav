#!/usr/bin/env python3
"""Assemble lettered panels into (a) classic pages and (b) a phone carousel.

Page format: a cell is 4:5; a panel spans 1, 2 or 3 cells; a page is 3 columns of cells,
as many rows as the layout lists. Wide panels are centre-cropped to their exact slot. For
the carousel every panel becomes one 1080x1350 JPEG, wide panels cropped to their centre
4:5 (the safe zone the lettering was placed in); <panel>.phone.png is used instead of
<panel>.png when present. Rows run right to left by default (layout "dir": "ltr" flips).

Reads stories/<story>/chapters/<chapter>/panels/<panel-id>.png and writes
.../pages/<page-id>.png plus .../pages/carousel/<seq>-<panel-id>.jpg (the carousel folder
is wiped first). See tools/examples/layout.example.json.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kav_env import REPO, resolve  # noqa: E402


def fit(im, w, h):
    """Resize + centre-crop to exactly w x h."""
    from PIL import Image
    r = w / h
    W, H = im.size
    if W / H > r:
        nw, nh = round(H * r), H
    else:
        nw, nh = W, round(W / r)
    x0, y0 = (W - nw) // 2, (H - nh) // 2
    return im.crop((x0, y0, x0 + nw, y0 + nh)).resize((w, h), Image.Resampling.LANCZOS)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("layout", help="layout JSON (usually stories/<slug>/chapters/chNN/pages/layout.json)")
    a = ap.parse_args()
    from PIL import Image
    spec = json.loads(resolve(a.layout).read_text(encoding="utf-8"))
    ch = REPO / "stories" / spec["story"] / "chapters" / spec["chapter"]
    panels = ch / "panels"
    out = ch / "pages"
    # Wipe the carousel folder: files are named <seq>-<panel>.jpg, so a layout change
    # leaves the previous numbering behind and the reader would show a panel twice.
    if (out / "carousel").is_dir():
        for stale in (out / "carousel").glob("*.jpg"):
            stale.unlink()
    (out / "carousel").mkdir(parents=True, exist_ok=True)
    PW, G = spec.get("page_width", 2400), spec.get("gutter", 36)
    cw = (PW - 4 * G) // 3
    chh = round(cw * 5 / 4)
    bg = tuple(spec.get("background", (17, 21, 28)))
    rtl = spec.get("dir", "rtl") != "ltr"

    missing = [pid for page in spec["pages"] for row in page["rows"] for pid, _ in row
               if not (panels / f"{pid}.png").exists()]
    if missing:
        sys.exit(f"Missing lettered panels in {panels}: {', '.join(missing)}")

    seq = 0
    for page in spec["pages"]:
        rows = page["rows"]
        PH = G + len(rows) * (chh + G)
        im = Image.new("RGB", (PW, PH), bg)
        y = G
        for row in rows:
            # Right-to-left books: the first panel of a row sits at the right edge. Rows in
            # the layout are always listed in reading order.
            x = PW - G if rtl else G
            for pid, cells in row:
                w = cells * cw + (cells - 1) * G
                if rtl:
                    x -= w
                src = Image.open(panels / f"{pid}.png").convert("RGB")
                im.paste(fit(src, w, chh), (x, y))
                x = x - G if rtl else x + w + G
                seq += 1
                # A wide panel can carry a second lettering pass for the phone: balloons that
                # hug the frame edge must hug the centre-crop edge there, not the page edge.
                phone = panels / f"{pid}.phone.png"
                psrc = Image.open(phone).convert("RGB") if phone.exists() else src
                fit(psrc, 1080, 1350).save(out / "carousel" / f"{seq:02d}-{pid}.jpg", quality=92)
            y += chh + G
        im.save(out / f"{page['id']}.png")
        print(f"{page['id']}: {im.size}, {sum(len(r) for r in rows)} panels")
    print(f"carousel: {seq} images in {out / 'carousel'}")


if __name__ == "__main__":
    main()
