#!/usr/bin/env python3
"""Generate one image from a plain-English scene line, bound to a story's references.

A line like "mira and the cat on the lighthouse stairs, inkwash" becomes a brief (cast,
location, objects and style pack detected from stories/<slug>/briefs.json and styles/),
then the same reference assembly and prompt every panel uses. The image and a .json
sidecar (prompt, seed, refs) land in stories/<slug>/playground/. Prints the result JSON.

Lanes: seedream (fal.ai, FAL_KEY) and nanobanana (fal.ai when FAL_KEY is set, otherwise
Google Gemini direct with GEMINI_API_KEY). --ar picks the panel shape: 4:5 is one page
cell, 8:5 two cells, 12:5 three cells, 9:16 a full phone screen.
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kav_env import get_key, missing_key_message  # noqa: E402
from kav_refs import (build_prompt, build_refs, current_story, data_uri, load_spec,  # noqa: E402
                      out_dir, parse_quick_line, set_story)

LANES = {
    "seedream": ("fal-ai/bytedance/seedream/v4.5/edit",
                 {"image_size": {"width": 2160, "height": 3840}}),
    "nanobanana": ("fal-ai/nano-banana-pro/edit",
                   {"aspect_ratio": "9:16", "resolution": "2K",
                    "safety_tolerance": "5", "output_format": "png"}),
}

# Panel shapes. Seedream takes pixel sizes (kept near its 8 MP ceiling); Nano Banana
# takes the ratio. Page cells are 4:5; a panel spans 1, 2 or 3 cells (4:5, 8:5, 12:5).
# The centre 4:5 of a wider panel is its phone crop, so subject and balloons stay there.
ASPECTS = {
    "9:16": (2160, 3840), "16:9": (3840, 2160), "1:1": (2880, 2880),
    "3:4": (2496, 3328), "4:3": (3328, 2496), "2:3": (2304, 3456), "3:2": (3456, 2304),
    "4:5": (2304, 2880), "8:5": (3456, 2160), "12:5": (3840, 1600),
}


def playground():
    """Generated images land inside the story, never in a shared scratch folder."""
    return out_dir("playground")


def lane_payload(lane, ar):
    endpoint, extra = LANES.get(lane, LANES["seedream"])
    extra = dict(extra)
    if ar and ar in ASPECTS:
        if "image_size" in extra:
            w, h = ASPECTS[ar]
            extra["image_size"] = {"width": w, "height": h}
        else:
            extra["aspect_ratio"] = ar
    return endpoint, extra


def slugify(text, limit=48):
    keep = [c.lower() if c.isalnum() else "-" for c in text]
    return "".join(keep).strip("-").replace("--", "-")[:limit] or "scene"


def out_name(line, lane):
    # timestamp alone collides when two lanes finish the same second
    return f"{int(time.time())}-{lane}-{slugify(line)}.png"


def generate(line, style=None, lane="seedream", seed=None, ar=None):
    """Returns {ok, file, prompt, refs, cast, location, style, seed, ...} or {ok: False, error}."""
    from lanes import fal, gemini
    spec = load_spec()
    brief = parse_quick_line(line, 0, list(spec["characters"]))
    if not brief:
        return {"ok": False, "error": "No cast member named. Mention at least one of: "
                                      + ", ".join(spec["characters"])}
    pack = style or brief.get("style_pack")
    if pack == "none":
        pack = None

    prompt = build_prompt(brief, spec, pack)
    refs = build_refs(brief, spec, pack)
    seed = seed if seed is not None else int(time.time()) % 100000
    fal_key = get_key("FAL_KEY")
    via = "fal"
    try:
        if fal_key:
            endpoint, extra = lane_payload(lane, ar)
            payload = {"prompt": prompt, "image_urls": [data_uri(r["local"]) for r in refs],
                       "seed": seed, **extra}
            img = fal.run(endpoint, payload, fal_key)
        elif lane == "nanobanana" and get_key("GEMINI_API_KEY"):
            via = "gemini"
            img = gemini.run(prompt, [r["local"] for r in refs], get_key("GEMINI_API_KEY"),
                             ar=ar or "9:16", seed=seed)
        else:
            return {"ok": False, "error": missing_key_message("FAL_KEY") + (
                "\n  (or set GEMINI_API_KEY to use --lane nanobanana without fal.ai)"
                if lane == "nanobanana" else "")}
        name = out_name(line, lane)
        (playground() / name).write_bytes(img)
    except Exception as e:
        return {"ok": False, "error": str(e)[:600]}

    meta = {"ok": True, "file": name, "path": str(playground() / name), "line": line,
            "prompt": prompt, "cast": brief["characters"], "location": brief.get("location"),
            "objects": brief.get("objects", []), "style": pack, "lane": lane, "via": via,
            "ar": ar or "9:16", "seed": seed, "story": current_story(), "at": int(time.time()),
            "refs": [{"kind": r["kind"], "name": r["name"]} for r in refs]}
    (playground() / (name + ".json")).write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    return meta


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("line", nargs="+", help="the scene, in plain English, naming at least one character")
    ap.add_argument("--story", required=True, help="story slug (stories/<slug>/)")
    ap.add_argument("--lane", default="seedream", choices=list(LANES))
    ap.add_argument("--ar", choices=list(ASPECTS), help="panel shape (default 9:16)")
    ap.add_argument("--seed", type=int, help="fixed seed (default: from the clock)")
    ap.add_argument("--style", help="style pack under styles/ (overrides one named in the line; 'none' = no pack)")
    ap.add_argument("--dry-run", action="store_true", help="print the brief, refs and prompt; no API call")
    a = ap.parse_args()
    set_story(a.story)
    line = " ".join(a.line)
    if a.dry_run:
        spec = load_spec()
        brief = parse_quick_line(line, 0, list(spec["characters"]))
        if not brief:
            sys.exit("No cast member named. Known: " + ", ".join(spec["characters"]))
        pack = a.style or brief.get("style_pack")
        pack = None if pack == "none" else pack
        print(json.dumps({"brief": brief,
                          "refs": [{"kind": r["kind"], "name": r["name"], "local": str(r["local"])}
                                   for r in build_refs(brief, spec, pack)],
                          "prompt": build_prompt(brief, spec, pack)}, indent=2, ensure_ascii=False))
        return
    res = generate(line, style=a.style, lane=a.lane, seed=a.seed, ar=a.ar)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    if not res.get("ok"):
        sys.exit(1)


if __name__ == "__main__":
    main()
