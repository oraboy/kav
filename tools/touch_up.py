#!/usr/bin/env python3
"""Touch up a finished mug shot with one Seedream edit pass: one image in, one image out.

Use when a set is approved except for one attribute the identity lock keeps copying from
the photos (eye colour, a stray accessory, a background tint). Regenerating from the seeds
re-rolls the whole face; an edit pass on the finished shot changes only what you name.
Reads stories/<slug>/cast/<name>/[<pack>/]<shot>.png and writes the result beside it as
.../touch/<shot>.png. Review it, then copy it over the production file yourself: the
pipeline never binds touch/. Needs FAL_KEY.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kav_refs import cast_dir, set_story  # noqa: E402
import lanes  # noqa: E402
import ledger  # noqa: E402

FRAME = ("Edit this single illustration. {instruction}. Keep the drawing style, linework, "
         "colours, framing, pose, expression, clothing, hair and background exactly as they are — "
         "this is a minimal retouch of one detail, not a new image.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--story", required=True, help="story slug")
    ap.add_argument("--char", required=True, help="cast member")
    ap.add_argument("--instruction", required=True,
                    help="the one detail to change, e.g. 'change only the iris colour to light green'")
    ap.add_argument("--shot", "--shots", dest="shots", default="front",
                    help="shot(s) to touch up, comma list (front,three-quarter,smile,full-body); default front")
    ap.add_argument("--pack", help="style-pack subfolder of the set (cast/<name>/<pack>/); default the plain set")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--provider", choices=list(lanes.PROVIDERS),
                    help="who runs the Seedream edit (default: $KAV_PROVIDER, else the first configured)")
    a = ap.parse_args()
    set_story(a.story)
    from PIL import Image
    provider = lanes.resolve("seedream", a.provider)

    folder = cast_dir() / a.char / a.pack if a.pack else cast_dir() / a.char
    out_dir = folder / "touch"
    out_dir.mkdir(parents=True, exist_ok=True)
    done = 0
    for shot in [s.strip() for s in a.shots.split(",") if s.strip()]:
        src = folder / f"{shot}.png"
        if not src.exists():
            print(f"  {shot}: no file at {src}, skipping")
            continue
        w, h = Image.open(src).size
        img, via = lanes.generate(FRAME.format(instruction=a.instruction.rstrip(".")), [src],
                                  lane="seedream", size=(w, h), seed=a.seed, provider=provider)
        (out_dir / f"{shot}.png").write_bytes(img)
        ledger.record(a.story, stage=f"touch-up:{a.char}", tool="touch_up.py", provider=via,
                      lane="seedream", seed=a.seed, file=out_dir / f"{shot}.png",
                      line=a.instruction)
        print(f"  {shot} -> {out_dir / (shot + '.png')}")
        done += 1
    sys.exit(0 if done else 1)


if __name__ == "__main__":
    main()
