#!/usr/bin/env python3
"""Generate candidate images for a batch of panels, concurrently, into a chapter folder.

A batch JSON names a story, a chapter, a lane and a candidate count, plus a list of panels
({id, ar, line, text?, n?, seed?, picked?}); see tools/examples/batch.example.json. Each
panel gets `n` candidates written to
  stories/<story>/chapters/<chapter>/panels/candidates/<id>-<k>.png  (+ <id>-<k>.json)
and a contact sheet of the batch to .../candidates/<batch-stem>_sheet.png.
Panels with "picked" set are settled and skipped; "only": [ids] reruns a subset.
Nothing is promoted: the author picks (tools/review.py).
"""
import argparse
import json
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kav_env import REPO, resolve  # noqa: E402
from kav_refs import set_story  # noqa: E402

FONT_CANDIDATES = ["/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial.ttf",
                   "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/arial.ttf",
                   "DejaVuSans.ttf", "Arial.ttf"]


def chapter_of(out_dir):
    """chNN from .../chapters/chNN/panels/candidates — the ledger's stage."""
    for part in Path(out_dir).parts[::-1]:
        if part.startswith("ch") and part[2:].isdigit():
            return part
    return "chapter"


def run_one(story, lane, panel, k, out_dir):
    import generate as G
    set_story(story)
    # the default seed is the wall clock: candidates started in the same second would be
    # identical images, so every candidate gets its own seed
    seed = panel.get("seed", random.randrange(1, 100000)) + (k - 1) * 7919
    res = {}
    for _ in range(3):
        res = G.generate(panel["line"], lane=lane, ar=panel.get("ar", "9:16"), seed=seed,
                         style=panel.get("style"), stage=f"{chapter_of(out_dir)}:{panel['id']}")
        if res.get("ok"):
            break
        if "No cast member" in res.get("error", "") or "Missing API key" in res.get("error", ""):
            break
        time.sleep(5)
    if not res.get("ok"):
        return {"id": panel["id"], "k": k, "ok": False, "error": res.get("error")}
    src = G.playground() / res["file"]
    dst = out_dir / f"{panel['id']}-{k}.png"
    dst.write_bytes(src.read_bytes())
    (out_dir / f"{panel['id']}-{k}.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
    out = {"id": panel["id"], "k": k, "ok": True, "file": dst.name, "seed": res["seed"],
           "style": res.get("style")}
    if not res.get("style"):
        out["unstyled"] = True          # a stylised book never wants these in the picks
    if res.get("warning"):
        out["warning"] = res["warning"]
    return out


def load_font(size):
    from PIL import ImageFont
    for f in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(f, size)
        except Exception:
            continue
    return ImageFont.load_default()


def preflight(story, panel):
    """Resolve one panel without generating. Returns a problem string, or None.

    A locked style/style.md and a linked styles/<pack>/ do not bind anything by themselves:
    the pack reaches the prompt only when the scene line names it, --style passes it, or
    briefs.json carries defaults.style_pack. A batch that resolves to no style spends the
    whole chapter's money on the model's own look, so check before paying.
    """
    from kav_refs import (build_prompt, build_refs, default_style_pack, load_spec,
                          parse_quick_line, style_medium)
    spec = load_spec()
    brief = parse_quick_line(panel["line"], 0, list(spec["characters"]))
    if not brief:
        print(f"PREFLIGHT  {panel['id']}: no cast member named in the line")
        return "no cast"
    pack = panel.get("style") or brief.get("style_pack") or default_style_pack(spec)
    pack = None if pack == "none" else pack
    refs = build_refs(brief, spec, pack)
    kinds = {}
    for r in refs:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    medium = (style_medium(pack) or "")[:120] if pack else ""
    print(f"PREFLIGHT  {panel['id']}  style={pack or 'NONE'}  refs={kinds}  "
          f"cast={brief['characters']}  location={brief.get('location')}")
    if medium:
        print(f"           medium: {medium}...")
    print(f"           prompt: {build_prompt(brief, spec, pack)[:160]}...")
    story_has_pack = (REPO / "stories" / story / "styles").is_dir() and any(
        (REPO / "stories" / story / "styles").iterdir())
    if not pack and story_has_pack:
        return (f"{panel['id']} resolves to NO style, but the story has a style pack linked. "
                f"Set defaults.style_pack in briefs.json (or name the pack in every line).")
    if pack and not kinds.get("style"):
        return (f"{panel['id']} names style '{pack}' but sends 0 style references — check "
                f"styles/{pack}/ has images, and that the cast count is not eating the budget.")
    return None


LETTERS = "ABCDEFGH"


def contact_sheet(out_dir, panels, n, name):
    """One sheet per batch, every take labelled <id> A / B / C, burned into the image.

    The label has to survive being screenshotted, forwarded and read on a phone: the
    author picks by saying "s2p1 B", so order, column position or a filename underneath
    is not enough.
    """
    from PIL import Image, ImageDraw
    cell, pad = 440, 12
    cols = max([n] + [int(p.get("n", n)) for p in panels])
    W = pad + cols * (cell + pad)
    H = pad + len(panels) * (cell + 36 + pad)
    im = Image.new("RGB", (W, H), (28, 30, 34))
    d = ImageDraw.Draw(im)
    font = load_font(22)
    big = load_font(38)
    y = pad
    for p in panels:
        d.text((pad, y), f"{p['id']} · {p.get('ar', '9:16')} · {p['line'][:110]}", fill=(240, 235, 220), font=font)
        y += 32
        x = pad
        for k in range(1, cols + 1):
            f = out_dir / f"{p['id']}-{k}.png"
            if f.exists():
                t = Image.open(f).convert("RGB")
                t.thumbnail((cell, cell))
                px, py = x + (cell - t.width) // 2, y + (cell - t.height) // 2
                im.paste(t, (px, py))
                tag = f"{p['id']} {LETTERS[k - 1] if k <= len(LETTERS) else k}"
                tw = d.textlength(tag, font=big) + 18
                d.rectangle([px, py, px + tw, py + 52], fill=(16, 17, 20))
                d.text((px + 9, py + 6), tag, fill=(255, 208, 92), font=big)
            x += cell + pad
        y += cell + pad + 4
    out = out_dir / f"{name}_sheet.png"
    im.save(out)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("batch", help="path to the batch JSON")
    ap.add_argument("--sheet-only", action="store_true", help="rebuild the contact sheet, no generation")
    ap.add_argument("--preflight", action="store_true",
                    help="resolve the first panel and stop: shows the style, the references and "
                         "the medium line that would be sent, without generating anything")
    a = ap.parse_args()
    batch_path = resolve(a.batch)
    spec = json.loads(batch_path.read_text(encoding="utf-8"))
    story, chapter = spec["story"], spec["chapter"]
    set_story(story)
    lane = spec.get("lane", "seedream")
    n = int(spec.get("n", 2))
    out_dir = REPO / "stories" / story / "chapters" / chapter / "panels" / "candidates"
    out_dir.mkdir(parents=True, exist_ok=True)
    only = set(spec.get("only", []))
    if only:
        panels = [p for p in spec["panels"] if p["id"] in only]
    else:
        panels = [p for p in spec["panels"] if not p.get("picked")]
    if not panels:
        sys.exit("Nothing to generate: every panel in this batch is marked picked.")
    problem = preflight(story, panels[0])
    if problem:
        print(f"PROBLEM    {problem}")
    if a.preflight:
        sys.exit(1 if problem else 0)
    if problem and not a.sheet_only:
        sys.exit("Stopping before the batch — fix the binding, then run again "
                 "(--preflight re-checks for free).")

    ok = True
    if not a.sheet_only:
        jobs = [(p, k) for p in panels for k in range(1, int(p.get("n", n)) + 1)]
        print(f"[{story}/{chapter}] {len(jobs)} generations on {lane} ...")
        with ThreadPoolExecutor(max_workers=int(spec.get("workers", 4))) as ex:
            results = list(ex.map(lambda j: run_one(story, lane, j[0], j[1], out_dir), jobs))
        for r in results:
            print("  ", json.dumps(r, ensure_ascii=False))
        ok = all(r["ok"] for r in results)
        unstyled = [r["id"] for r in results if r.get("ok") and r.get("unstyled")]
        if unstyled:
            ok = False
            print(f"\n!! {len(unstyled)} candidate(s) generated with NO style pack bound: "
                  f"{', '.join(sorted(set(unstyled)))}.\n"
                  f"   In a stylised book that is a failed batch — don't show these for picking. "
                  f"Set defaults.style_pack in briefs.json and regenerate.")
    sheet = contact_sheet(out_dir, spec["panels"], n, batch_path.stem)
    print("sheet:", sheet)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
