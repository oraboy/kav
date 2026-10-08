#!/usr/bin/env python3
"""Bring images made outside Kav's own image lanes into a batch as takes to pick from.

For an author who draws with the agent's built-in image generator (ChatGPT / Codex image
generation, an MCP image tool) or any other tool: generate ONE PANEL per image, save the
files anywhere, and add them here. Each lands as the panel's next take,
  stories/<story>/chapters/<chapter>/panels/candidates/<id>-<k>.png  (+ <id>-<k>.json)
exactly where panel_batch.py puts its own, so the contact sheet, tools/review.py, lettering
and page assembly treat it like any other take. Nothing is promoted: the author picks.

  python3 tools/add_candidate.py <batch.json> <panel-id> <image> [<image> ...] --source "codex image generation"
  python3 tools/add_candidate.py <batch.json> <panel-id> take1.png take2.png take3.png --fit

The panel's shape comes from its "ar" in the batch. An image of another shape is added
anyway with a warning, since a page cell and the phone crop will cut it; --fit centre-crops
it to the panel's shape instead. Never add a whole page with several panels drawn into one
image: Kav letters and assembles single panels, and this tool cannot tell the difference.

Each take is written to the story's ledger as provider "agent" with no price, because Kav
cannot see what another tool charged.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kav_env import REPO, resolve  # noqa: E402
import ledger  # noqa: E402


def ratio(ar):
    w, h = (float(x) for x in ar.split(":"))
    return w / h


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("batch", help="the batch JSON the panel belongs to")
    ap.add_argument("panel", help="panel id in that batch, e.g. s1p2")
    ap.add_argument("images", nargs="+", help="one or more image files, one panel each")
    ap.add_argument("--source", default="agent image tool",
                    help='what made the image, in plain words (default "agent image tool")')
    ap.add_argument("--fit", action="store_true", help="centre-crop to the panel's shape")
    a = ap.parse_args()

    from PIL import Image
    batch_path = resolve(a.batch)
    spec = json.loads(batch_path.read_text(encoding="utf-8"))
    story, chapter = spec["story"], spec["chapter"]
    panel = next((p for p in spec["panels"] if p["id"] == a.panel), None)
    if not panel:
        sys.exit(f"No panel '{a.panel}' in {batch_path.name}. Panels: {', '.join(p['id'] for p in spec['panels'])}")
    if panel.get("picked"):
        sys.exit(f"{a.panel} is already picked (take {panel['picked']}). Remove \"picked\" from the batch to reopen it.")
    out_dir = REPO / "stories" / story / "chapters" / chapter / "panels" / "candidates"
    out_dir.mkdir(parents=True, exist_ok=True)
    taken = [int(f.stem.rsplit("-", 1)[1]) for f in out_dir.glob(f"{a.panel}-*.png")
             if f.stem.rsplit("-", 1)[1].isdigit()]
    k = max(taken, default=0)
    want = ratio(panel.get("ar", "9:16"))

    for src in a.images:
        src = resolve(src)
        if not src.is_file():
            sys.exit(f"No such image: {src}")
        im = Image.open(src).convert("RGB")
        have = im.width / im.height
        off = abs(have - want) / want
        if off > 0.04 and a.fit:
            if have > want:
                w = round(im.height * want)
                im = im.crop(((im.width - w) // 2, 0, (im.width - w) // 2 + w, im.height))
            else:
                h = round(im.width / want)
                im = im.crop((0, (im.height - h) // 2, im.width, (im.height - h) // 2 + h))
            print(f"   fitted {src.name} to {panel.get('ar', '9:16')} by centre crop — look that nothing was cut")
        elif off > 0.04:
            print(f"!! {src.name} is {im.width}x{im.height}, not the panel's {panel.get('ar', '9:16')}. "
                  f"Added as it is; the page cell and the phone crop will cut it. "
                  f"Regenerate at the panel's shape, or pass --fit to centre-crop.")
        k += 1
        dst = out_dir / f"{a.panel}-{k}.png"
        im.save(dst)
        (out_dir / f"{a.panel}-{k}.json").write_text(json.dumps(
            {"ok": True, "provider": "agent", "source": a.source, "from": src.name, "line": panel.get("line", ""),
             "note": "made outside Kav's image lanes: references were bound by the tool that drew it, not by Kav"},
            indent=2, ensure_ascii=False), encoding="utf-8")
        ledger.record(story, stage=f"{chapter}:{a.panel}", tool="add_candidate", provider="agent",
                      lane=a.source, ar=panel.get("ar"), file=dst, line=panel.get("line"))
        print(f"added {dst.relative_to(REPO)}")

    import panel_batch
    n = max([int(spec.get("n", 2)), k] + [int(p.get("n", 0)) for p in spec["panels"]])
    print("sheet:", panel_batch.contact_sheet(out_dir, spec["panels"], n, batch_path.stem))


if __name__ == "__main__":
    main()
