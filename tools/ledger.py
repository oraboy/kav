#!/usr/bin/env python3
"""What a story cost: one row per generation request, written when the request is made.

A file count is not a cost ledger. Rerolls, rejected takes and failures that still charged
all cost money and none of them survive in the final folder, so every tool that calls an
image API appends a row here the moment it calls — before the image is judged, kept or
thrown away.

  stories/<slug>/ledger.jsonl   one JSON object per line:
    at, stage, tool, provider, lane, ar, seed, outcome (ok|error), price, file, error, line

Report:
  python3 tools/ledger.py --story <slug>              totals by stage and model
  python3 tools/ledger.py --story <slug> --detail     every row
  python3 tools/ledger.py --story <slug> --json

The total is a **documented minimum**: it covers what Kav generated through its own tools
for this story. A provider dashboard covers the whole account — other stories, other
projects, other people — so the two never match and the dashboard figure is not this
book's cost.
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kav_env import REPO  # noqa: E402


def ledger_path(story):
    return REPO / "stories" / story / "ledger.jsonl"


def record(story, *, stage, tool, provider=None, lane=None, ar=None, seed=None,
           outcome="ok", price=None, file=None, error=None, line=None):
    """Append one row. Never raises: a broken ledger must not lose an image."""
    if not story:
        return
    try:
        if price is None and provider and lane:
            import lanes
            m = lanes.model(provider, lane) or {}
            price = m.get("price")
        row = {"at": int(time.time()), "stage": stage, "tool": tool, "provider": provider,
               "lane": lane, "ar": ar, "seed": seed, "outcome": outcome, "price": price,
               "file": str(file) if file else None}
        if error:
            row["error"] = str(error)[:300]
        if line:
            row["line"] = line[:300]
        p = ledger_path(story)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def rows(story):
    p = ledger_path(story)
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
    return out


def summarise(story):
    data = rows(story)
    total = sum(r.get("price") or 0 for r in data if r.get("outcome") == "ok")
    by_model, by_stage = {}, {}
    for r in data:
        if r.get("outcome") != "ok":
            continue
        key = f"{r.get('provider')}/{r.get('lane')}"
        m = by_model.setdefault(key, {"images": 0, "cost": 0.0})
        m["images"] += 1
        m["cost"] += r.get("price") or 0
        s = by_stage.setdefault(r.get("stage") or "?", {"images": 0, "cost": 0.0})
        s["images"] += 1
        s["cost"] += r.get("price") or 0
    errors = [r for r in data if r.get("outcome") != "ok"]
    unpriced = [r for r in data if r.get("outcome") == "ok" and not r.get("price")]
    return {"story": story, "images": sum(m["images"] for m in by_model.values()),
            "documented_minimum_usd": round(total, 2), "by_model": by_model,
            "by_stage": by_stage, "failed_requests": len(errors),
            "unpriced_rows": len(unpriced), "rows": len(data)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--story", required=True)
    ap.add_argument("--detail", action="store_true", help="print every row")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    s = summarise(a.story)
    if a.json:
        print(json.dumps({**s, "detail": rows(a.story) if a.detail else None}, indent=2))
        return
    if not s["rows"]:
        print(f"No ledger yet for {a.story} (stories/{a.story}/ledger.jsonl). "
              f"Images generated before the ledger existed are not counted.")
        return
    print(f"{a.story}: {s['images']} images · documented minimum ${s['documented_minimum_usd']}")
    for key, m in sorted(s["by_model"].items()):
        print(f"  {key:<24} {m['images']:>4} images  ${round(m['cost'], 2)}")
    print("  by stage:")
    for key, m in sorted(s["by_stage"].items()):
        print(f"    {key:<22} {m['images']:>4} images  ${round(m['cost'], 2)}")
    if s["failed_requests"]:
        print(f"  {s['failed_requests']} failed request(s) — some providers still charge for these")
    if s["unpriced_rows"]:
        print(f"  {s['unpriced_rows']} row(s) with no price on record")
    print("  Documented minimum: what Kav generated for this story through its own tools. "
          "A provider dashboard covers the whole account and is not this book's cost.")
    if a.detail:
        for r in rows(a.story):
            print("   ", json.dumps(r, ensure_ascii=False))


if __name__ == "__main__":
    main()
