#!/usr/bin/env python3
"""The setup test image: one generated panel, lettered with a speech balloon.

Proves the whole chain works before a story exists: an API key, an image lane, Chrome
and the lettering tool. Generates a cartoon panel of an author and a robot working over
a notepad in a workshop (no text in the image), then letters the robot saying
"Welcome to Kav, your AI co-writer for graphic novels". No story and no references.

  python3 tools/welcome_panel.py                   generate + letter (costs one image)
  python3 tools/welcome_panel.py --letter-only     re-letter the existing panel after
                                                   editing setup/welcome.lettering.json
  python3 tools/welcome_panel.py --dry-run         print lane, prompt and paths; no API call

Uses the cheapest configured lane (Seedream via fal.ai, else Nano Banana via Gemini)
unless --lane is given. Writes to setup/ (gitignored): welcome-panel.png (raw),
welcome.lettering.json (the balloon spec) and welcome.png (lettered).
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kav_env import REPO, get_key  # noqa: E402

OUT = REPO / "setup"
RAW, SPEC, FINAL = OUT / "welcome-panel.png", OUT / "welcome.lettering.json", OUT / "welcome.png"
W, H = 2304, 2880  # one 4:5 page cell
SEEDREAM_T2I = "fal-ai/bytedance/seedream/v4.5/text-to-image"
NANOBANANA_T2I = "fal-ai/nano-banana-pro"

PROMPT = (
    "A simple, warm cartoon comic panel, clean bold ink outlines and flat bright colours. "
    "Inside a cosy cluttered workshop, a human author (left of frame) and a friendly boxy "
    "robot (right of frame) lean together over a notepad on a wooden workbench, both "
    "concentrating, the author holding a pencil, the robot pointing at the page. Tools, "
    "sketches and coffee mugs around them, lamp light. Leave the top third of the frame "
    "as calm wall space. No text, no letters, no signs, no speech balloons anywhere."
)

BALLOON = {
    "panel": str(RAW),
    "size": [W, H],
    "overlays": [{
        "type": "balloon", "kind": "speech",
        "cx": 1450, "cy": 520, "rx": 700, "ry": 300, "lang": "en",
        "lines": ["Welcome to Kav,", "your AI co-writer", "for graphic novels"],
        "tail": [1700, 1250],
    }],
}


def pick_lane(forced):
    fal, gem = get_key("FAL_KEY"), get_key("GEMINI_API_KEY")
    if forced == "nanobanana" or (not forced and not fal and gem):
        if fal:
            return "nanobanana", "fal"
        if gem:
            return "nanobanana", "gemini"
    elif fal:
        return "seedream", "fal"
    sys.exit("No image key set. Run: python3 tools/check_setup.py")


def generate(lane, via):
    from lanes import fal, gemini
    seed = int(time.time()) % 100000
    if via == "gemini":
        return gemini.run(PROMPT, [], get_key("GEMINI_API_KEY"), ar="4:5", seed=seed)
    if lane == "seedream":
        payload = {"prompt": PROMPT, "image_size": {"width": W, "height": H}, "seed": seed}
        return fal.run(SEEDREAM_T2I, payload, get_key("FAL_KEY"))
    payload = {"prompt": PROMPT, "aspect_ratio": "4:5", "resolution": "2K", "output_format": "png"}
    return fal.run(NANOBANANA_T2I, payload, get_key("FAL_KEY"))


def letter():
    if not RAW.exists():
        sys.exit(f"No panel at {RAW}; run without --letter-only first.")
    if not SPEC.exists():
        SPEC.write_text(json.dumps(BALLOON, indent=2))
    r = subprocess.run([sys.executable, str(REPO / "tools" / "letter.py"), str(SPEC), str(FINAL)])
    if r.returncode != 0:
        sys.exit("Lettering failed (usually Chrome): python3 tools/check_setup.py")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lane", choices=["seedream", "nanobanana"])
    ap.add_argument("--letter-only", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    if a.letter_only:
        letter()
        print(json.dumps({"ok": True, "lettered": str(FINAL)}, indent=2))
        return
    lane, via = pick_lane(a.lane)
    if a.dry_run:
        print(json.dumps({"lane": lane, "via": via, "prompt": PROMPT,
                          "raw": str(RAW), "spec": str(SPEC), "lettered": str(FINAL)}, indent=2))
        return
    try:
        RAW.write_bytes(generate(lane, via))
    except Exception as e:
        sys.exit(f"Generation failed on {lane} via {via}: {str(e)[:600]}")
    SPEC.write_text(json.dumps(BALLOON, indent=2))  # fresh panel, fresh default balloon
    letter()
    print(json.dumps({"ok": True, "lane": lane, "via": via, "panel": str(RAW),
                      "spec": str(SPEC), "lettered": str(FINAL)}, indent=2))


if __name__ == "__main__":
    main()
