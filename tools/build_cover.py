#!/usr/bin/env python3
"""Build a story's link-preview cover: the image shown when a trailer URL is pasted into a
chat app or anywhere else that unfurls links.

One half is a character's round cast portrait on the deck's ink ground, the other half a
scene image cover-cropped to fill. Writes stories/<slug>/package/cover.png at 1200x630,
the shape link unfurlers expect. The portrait comes from
stories/<slug>/cast/<char>/[<pack>/]front.png.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kav_env import resolve, story_dir  # noqa: E402
import kav_refs  # noqa: E402

W, H = 1200, 630
INK = (15, 23, 32)
CREAM = (244, 236, 214)


def fill(src, w, h, focus_y=0.32):
    """Cover-crop: fill the box, keep the interesting band (faces sit high in most frames)."""
    from PIL import Image
    im = Image.open(src).convert("RGB")
    scale = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.Resampling.LANCZOS)
    x = (im.width - w) // 2
    y = min(max(0, round(im.height * focus_y - h / 2)), im.height - h)
    return im.crop((x, y, x + w, y + h))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--story", required=True, help="story slug")
    ap.add_argument("--portrait-char", required=True, help="cast member for the round portrait")
    ap.add_argument("--scene-image", required=True, help="scene image for the other half")
    ap.add_argument("--pack", help="style-pack subfolder of the portrait set (cast/<char>/<pack>/front.png)")
    ap.add_argument("--portrait-side", choices=["left", "right"], default="left")
    ap.add_argument("--scene-focus", type=float, default=0.42, help="vertical focus of the scene crop, 0..1")
    ap.add_argument("--out", help="output PNG (default stories/<slug>/package/cover.png)")
    a = ap.parse_args()
    from PIL import Image, ImageDraw

    S = story_dir(a.story)
    kav_refs.set_story(a.story)
    scene = resolve(a.scene_image)
    if not scene.exists() and (S / a.scene_image).exists():
        scene = S / a.scene_image
    if not scene.exists():
        sys.exit(f"Scene image not found: {a.scene_image}")
    portrait = kav_refs.portrait_path(a.portrait_char, a.pack)
    out = Path(a.out) if a.out else S / "package" / "cover.png"
    out.parent.mkdir(parents=True, exist_ok=True)

    cover = Image.new("RGB", (W, H), INK)
    half = W // 2
    left_portrait = a.portrait_side == "left"
    cover.paste(fill(scene, W - half, H, focus_y=a.scene_focus), (half if left_portrait else 0, 0))

    d = ImageDraw.Draw(cover)
    px0 = 0 if left_portrait else half
    d.rectangle([px0, 0, px0 + half, H], fill=INK)
    ring, size = 6, 430
    mug = fill(portrait, size, size, focus_y=0.45)
    mask = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size * 4, size * 4], fill=255)
    mask = mask.resize((size, size), Image.Resampling.LANCZOS)
    cx, cy = px0 + half // 2, H // 2
    d.ellipse([cx - size // 2 - ring, cy - size // 2 - ring,
               cx + size // 2 + ring, cy + size // 2 + ring], fill=CREAM)
    cover.paste(mug, (cx - size // 2, cy - size // 2), mask)

    cover.save(out)
    print(f"wrote {out} ({W}x{H})")


if __name__ == "__main__":
    main()
