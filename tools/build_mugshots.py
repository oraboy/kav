#!/usr/bin/env python3
"""Build a character's mug shots: the reference sheet every later generation draws on.

A cast member starts as one or two loose images (a portrait, an inspiration photo) or
only a description. That is not enough to render them from any angle: a three-quarter
portrait carries no frontal information, so a selfie invents the face. This turns what
exists into a consistent set of views (front, three-quarter, smile, full-body) written
to stories/<slug>/cast/<name>/<shot>.png, or cast/<name>/<pack>/<shot>.png with
--style-pack. Seed images are cast/<name>/source*.{png,jpg,jpeg,webp} plus --from.
The seedream lane is a cheap draft pass saved under .../draft/, which the pipeline never
binds. Needs FAL_KEY.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kav_env import REPO  # noqa: E402
from kav_refs import (cast_dir, current_story, load_spec, root, set_story,  # noqa: E402
                      style_medium, style_pack_images)
import lanes  # noqa: E402
import ledger  # noqa: E402

SEEDREAM_SIZES = {"1:1": (2048, 2048), "9:16": (1152, 2048)}

# Frontal comes first: it is the view most often missing and the one selfies and close
# two-shots depend on.
SHOTS = {
    "front": ("head-and-shoulders, facing the camera straight on, looking directly into the lens, "
              "neutral relaxed expression, mouth closed", "1:1"),
    "three-quarter": ("head-and-shoulders turned about 30 degrees from camera, eyes still on the lens, "
                      "neutral relaxed expression", "1:1"),
    "smile": ("head-and-shoulders, facing the camera, smiling — the smile reaching the eyes, "
              "warm and self-possessed rather than a broad cheerful grin", "1:1"),
    "full-body": ("full body with the entire figure inside the frame — clear empty space above the "
                  "head and below the feet, nothing cropped. A person stands squarely facing the "
                  "camera, arms relaxed at the sides, everyday clothes; an animal stays an animal, "
                  "standing naturally on all fours, whole body and head visible", "9:16"),
}

FRAME = ("A plain reference photograph of this exact character for a character sheet — the very "
         "same subject as in the reference image{plural}, whether a person or an animal: {spec}. "
         "Even soft studio lighting with no coloured cast, plain light-grey seamless background, "
         "sharp focus, no props, no motion, nothing stylised. "
         "Keep the subject's exact identity — face or muzzle structure, eye shape and spacing, "
         "nose, mouth, jawline or head shape, hair or fur colour, markings and texture, skin or "
         "coat tone, and apparent age. Never substitute a different species or individual. "
         "Only the camera angle and expression change.")

IMG_EXT = {".png", ".jpg", ".jpeg", ".webp"}


def seed_images(name, extra=None):
    folder = cast_dir() / name
    out = []
    if folder.is_dir():
        out += sorted(p for p in folder.glob("source*") if p.suffix.lower() in IMG_EXT)
    legacy = cast_dir() / f"{name}.png"
    if legacy.exists():
        out.append(legacy)
    if extra:
        out.append(Path(extra).expanduser())
    return out


def build(name, provider=None, describe=None, extra=None, force=False, style_pack=None, lane="nanobanana",
          shots=None, seed=7):
    seeds = seed_images(name, extra)
    if not seeds and not describe:
        sys.exit(f"{name}: nothing to work from. Put a photo at cast/{name}/source.jpg, "
                 f"or pass --from <image> or --describe '<text>'")

    folder = cast_dir() / name / style_pack if style_pack else cast_dir() / name
    if lane == "seedream":
        folder = folder / "draft"        # drafts only: the pipeline never binds draft/
    folder.mkdir(parents=True, exist_ok=True)
    legacy = cast_dir() / f"{name}.png"
    if not style_pack and legacy.exists() and not (folder / "source.png").exists():
        legacy.replace(folder / "source.png")      # keep the original as the source
        seeds = seed_images(name, extra)

    spec = load_spec()
    who = describe or spec["characters"].get(name, "")
    print(f"[{name}] {len(seeds)} seed image(s) · {who}")

    wanted = {s.strip() for s in shots.split(",")} if shots else set(SHOTS)
    failed = 0
    for shot, (posture, ratio) in SHOTS.items():
        if shot not in wanted:
            continue
        out = folder / f"{shot}.png"
        if out.exists() and not force:
            print(f"  {shot} exists, skipping (--force to rebuild)")
            continue
        prompt = FRAME.format(spec=posture, plural="s" if len(seeds) > 1 else "")
        if who:
            prompt += f" For reference, {name.capitalize()} is {who}."
        direction = spec.get("mugshot_direction", {}).get(name, "")
        if direction and shot == "smile":
            prompt += " " + direction
        images = list(seeds)
        if style_pack:
            # A full-body frame ("entire figure, empty space above and below") is a wide
            # composition, the same shape as the style stills, which invites the model to
            # pull in their whole scene. Headshots keep 2 style refs; full-body goes
            # text-only, the medium line alone carrying the look.
            images += style_pack_images(style_pack, limit=0 if shot == "full-body" else 2)
            medium = style_medium(style_pack) or "illustration in the style of the style images"
            prompt = (f"Redraw this exact character — the very same subject as in the reference "
                      f"photographs, whether a person or an animal — as a {medium}. Keep the face "
                      f"or muzzle structure, eye shape and spacing, nose, mouth, jawline or head "
                      f"shape, hair or fur colour, markings and apparent age exactly; never "
                      f"substitute a different species or individual — only the rendering changes. "
                      f"{posture}. Plain flat background, nothing else in frame — exactly one "
                      f"subject, {name.capitalize()} alone. The style images are references for "
                      f"rendering technique only (line, shading, palette): ignore any people, "
                      f"animals, props or settings they show — none of that content belongs in "
                      f"this image.")
        size = SEEDREAM_SIZES[ratio] if lane == "seedream" else None
        stage = f"mugshots:{name}" + (f":{style_pack}" if style_pack else "")
        try:
            img, via = lanes.generate(prompt, images, lane=lane, ar=ratio, size=size, seed=seed,
                                      provider=provider)
            out.write_bytes(img)
            ledger.record(current_story(), stage=stage, tool="build_mugshots.py", provider=via,
                          lane=lane, ar=ratio, seed=seed, file=out, line=shot)
            print(f"  {shot} -> {out}  ({lane} via {via})")
        except Exception as e:
            failed += 1
            ledger.record(current_story(), stage=stage, tool="build_mugshots.py",
                          provider=provider, lane=lane, ar=ratio, seed=seed,
                          outcome="error", error=e, line=shot)
            print(f"  {shot} FAILED: {str(e)[:300]}")
    return failed


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*", metavar="name", help="cast member(s), same as --char")
    ap.add_argument("--story", required=True, help="story slug (stories/<slug>/)")
    ap.add_argument("--char", action="append", default=[], help="cast member to build (repeatable)")
    ap.add_argument("--from", dest="extra", help="an extra seed image (a photo, an inspiration)")
    ap.add_argument("--describe", help="who they are, if briefs.json does not say")
    ap.add_argument("--force", action="store_true", help="rebuild shots that already exist")
    ap.add_argument("--style-pack", help="render the set in a style pack, into cast/<name>/<pack>/")
    ap.add_argument("--lane", default="nanobanana", choices=["nanobanana", "seedream"],
                    help="seedream = cheap draft pass saved under .../draft/; nanobanana = production set")
    ap.add_argument("--provider", choices=list(lanes.PROVIDERS),
                    help="who runs the lane (default: $KAV_PROVIDER, else the first configured)")
    ap.add_argument("--shots", help="comma list of shots (front,three-quarter,smile,full-body); default all")
    ap.add_argument("--seed", type=int, default=7,
                    help="generation seed (default 7). Change it to reroll a shot that drifted")
    a = ap.parse_args()
    set_story(a.story)
    names = a.char + a.names
    if not names:
        sys.exit("Name a character: --char <name>")
    print(f"[root] {root().relative_to(REPO)}")
    provider = lanes.resolve(a.lane, a.provider)
    failed = sum(build(n, provider, a.describe, a.extra, a.force, a.style_pack, a.lane, a.shots, a.seed)
                 for n in names)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
