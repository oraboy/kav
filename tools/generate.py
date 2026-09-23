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
from kav_refs import (build_prompt, build_refs, current_story, default_style_pack,  # noqa: E402
                      load_spec, out_dir, parse_quick_line, plan_refs, ref_warning, set_story)
import lanes  # noqa: E402
import ledger  # noqa: E402

# The centre 4:5 of a wider panel is its phone crop, so subject and balloons stay there.
ASPECTS = lanes.ASPECTS


def playground():
    """Generated images land inside the story, never in a shared scratch folder."""
    return out_dir("playground")


def slugify(text, limit=48):
    keep = [c.lower() if c.isalnum() else "-" for c in text]
    return "".join(keep).strip("-").replace("--", "-")[:limit] or "scene"


def out_name(line, lane):
    # timestamp alone collides when two lanes finish the same second
    return f"{int(time.time())}-{lane}-{slugify(line)}.png"


def generate(line, style=None, lane="seedream", seed=None, ar=None, provider=None, stage=None):
    """Returns {ok, file, prompt, refs, cast, location, style, seed, ...} or {ok: False, error}."""
    spec = load_spec()
    brief = parse_quick_line(line, 0, list(spec["characters"]))
    if not brief:
        return {"ok": False, "error": "No cast member named. Mention at least one of: "
                                      + ", ".join(spec["characters"])}
    pack = style or brief.get("style_pack") or default_style_pack(spec)
    if pack == "none" or style == "none":
        pack = None

    try:
        via = lanes.resolve(lane, provider)
    except SystemExit as e:
        return {"ok": False, "error": str(e)}
    cap = lanes.max_refs(via, lane)
    prompt = build_prompt(brief, spec, pack, max_refs=cap)
    refs = build_refs(brief, spec, pack, max_refs=cap)
    warning = ref_warning(plan_refs(brief, spec, pack, cap), pack, cap)
    seed = seed if seed is not None else int(time.time()) % 100000
    try:
        img, via = lanes.generate(prompt, [r["local"] for r in refs], lane=lane, ar=ar,
                                  seed=seed, provider=via)
        name = out_name(line, f"{lane}-{via}")
        (playground() / name).write_bytes(img)
    except Exception as e:
        ledger.record(current_story(), stage=stage or "playground", tool="generate.py",
                      provider=via, lane=lane, ar=ar, seed=seed, outcome="error",
                      error=e, line=line)
        return {"ok": False, "error": str(e)[:600]}
    ledger.record(current_story(), stage=stage or "playground", tool="generate.py",
                  provider=via, lane=lane, ar=ar, seed=seed,
                  file=playground() / name, line=line)

    meta = {"ok": True, "file": name, "path": str(playground() / name), "line": line,
            "prompt": prompt, "cast": brief["characters"], "location": brief.get("location"),
            "objects": brief.get("objects", []), "style": pack, "lane": lane, "via": via,
            "ar": ar or "9:16", "seed": seed, "story": current_story(), "at": int(time.time()),
            "refs": [{"kind": r["kind"], "name": r["name"]} for r in refs]}
    if warning:
        meta["warning"] = warning
    (playground() / (name + ".json")).write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    return meta


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("line", nargs="+", help="the scene, in plain English, naming at least one character")
    ap.add_argument("--story", required=True, help="story slug (stories/<slug>/)")
    ap.add_argument("--lane", default="seedream", choices=list(lanes.LANES))
    ap.add_argument("--provider", choices=list(lanes.PROVIDERS),
                    help="who runs the lane (default: $KAV_PROVIDER, else the first configured)")
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
        pack = a.style or brief.get("style_pack") or default_style_pack(spec)
        pack = None if pack == "none" or a.style == "none" else pack
        via = lanes.resolve(a.lane, a.provider)
        cap = lanes.max_refs(via, a.lane)
        out = {"brief": brief, "provider": via, "max_refs": cap,
               "refs": [{"kind": r["kind"], "name": r["name"], "local": str(r["local"])}
                        for r in build_refs(brief, spec, pack, max_refs=cap)],
               "prompt": build_prompt(brief, spec, pack, max_refs=cap)}
        warn = ref_warning(plan_refs(brief, spec, pack, cap), pack, cap)
        if warn:
            out["warning"] = warn
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return
    res = generate(line, style=a.style, lane=a.lane, seed=a.seed, ar=a.ar, provider=a.provider)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    if not res.get("ok"):
        sys.exit(1)


if __name__ == "__main__":
    main()
