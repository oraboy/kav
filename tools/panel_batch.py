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


def run_one(story, lane, panel, k, out_dir):
    import generate as G
    set_story(story)
    # the default seed is the wall clock: candidates started in the same second would be
    # identical images, so every candidate gets its own seed
    seed = panel.get("seed", random.randrange(1, 100000)) + (k - 1) * 7919
    res = {}
    for _ in range(3):
        res = G.generate(panel["line"], lane=lane, ar=panel.get("ar", "9:16"), seed=seed,
                         style=panel.get("style"))
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
    return {"id": panel["id"], "k": k, "ok": True, "file": dst.name, "seed": res["seed"]}


def load_font(size):
    from PIL import ImageFont
    for f in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(f, size)
        except Exception:
            continue
    return ImageFont.load_default()


def contact_sheet(out_dir, panels, n, name):
    from PIL import Image, ImageDraw
    cell, pad = 440, 12
    cols = max([n] + [int(p.get("n", n)) for p in panels])
    W = pad + cols * (cell + pad)
    H = pad + len(panels) * (cell + 36 + pad)
    im = Image.new("RGB", (W, H), (28, 30, 34))
    d = ImageDraw.Draw(im)
    font = load_font(22)
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
                im.paste(t, (x + (cell - t.width) // 2, y + (cell - t.height) // 2))
                d.text((x + 6, y + 6), f"{k}", fill=(255, 220, 120), font=font)
            x += cell + pad
        y += cell + pad + 4
    out = out_dir / f"{name}_sheet.png"
    im.save(out)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("batch", help="path to the batch JSON")
    ap.add_argument("--sheet-only", action="store_true", help="rebuild the contact sheet, no generation")
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
    ok = True
    if not a.sheet_only:
        jobs = [(p, k) for p in panels for k in range(1, int(p.get("n", n)) + 1)]
        print(f"[{story}/{chapter}] {len(jobs)} generations on {lane} ...")
        with ThreadPoolExecutor(max_workers=int(spec.get("workers", 4))) as ex:
            results = list(ex.map(lambda j: run_one(story, lane, j[0], j[1], out_dir), jobs))
        for r in results:
            print("  ", json.dumps(r, ensure_ascii=False))
        ok = all(r["ok"] for r in results)
    sheet = contact_sheet(out_dir, spec["panels"], n, batch_path.stem)
    print("sheet:", sheet)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
