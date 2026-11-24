#!/usr/bin/env python3
"""Audit a chapter's scene list against the story's registry before any image is made.

Every panel binds its references by words. A character binds when the line names a key
of `characters` in briefs.json, a place when the line hits one of its `location_words`,
an object when it hits one of its `object_words`. A scene that names a place no entry
claims binds no location at all, and the panel comes back as the model's own generic
scenery — quietly, with a sidecar that looks correct. This runs the generator's own
matching over the plan (and, with --batch, over the lines that will actually be sent)
and says what would bind and what would not, so each gap is closed with /kav-character,
/kav-location or /kav-object before money is spent. It also lists registry entries with
nothing behind them: a `characters` line with no sheet, a sheet with no `characters`
line (so no way to bind), a location missing from `location_words`.

  python3 tools/plan_audit.py --story <slug> --chapter chNN              CH/panels/plan.md
  python3 tools/plan_audit.py --story <slug> --plan <path/to/plan.md>
  python3 tools/plan_audit.py --story <slug> --batch CH/panels/batch-s1-s2.json [...]
  python3 tools/plan_audit.py --story <slug> --chapter chNN --json

What it cannot see: a name, place or prop the scene list uses that no registry entry
claims at all. It reports which registered entry a scene's words reach; whether "the
kiosk" is a place the book needs is the agent's read of the list. Exit code 1 when
anything needs the author before an image is generated, 0 otherwise. Reads only.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kav_env import REPO, chapter_dir, resolve  # noqa: E402
import kav_refs as R  # noqa: E402

IMAGES = (".png", ".jpg", ".jpeg", ".webp")
SCENE_HEADING = re.compile(r"^(s\d+\b|scene\b)", re.I)
# a Hebrew name in a plan often carries a one-letter prefix (ו, ה, ל, ב, כ, מ, ש)
HE_PREFIX = "והלבכמש"


def _images_under(d):
    if not d.is_dir():
        return False
    for f in d.rglob("*"):
        if f.suffix.lower() in IMAGES and "_excluded" not in f.parts and "draft" not in f.parts:
            return True
    return False


def _sheet_aliases(path):
    """Names a plan may use for the sheet at `path`, from its first heading:
    '# ברקוביץ (ברקו) — slug DNA' -> ['ברקוביץ', 'ברקו']."""
    try:
        first = next((ln for ln in path.read_text(encoding="utf-8").splitlines()
                      if ln.startswith("# ")), "")
    except OSError:
        return []
    head = re.split(r"\s[—–-]\s", first[2:], maxsplit=1)[0]
    return [t for t in re.split(r"[^\w]+", head) if len(t) >= 2]


def registry(spec):
    """Each layer as the drawing sees it, with what is behind every entry on disk.

    `findings` are binding problems (the gate); `notes` are sheets missing beside a working
    entry — the writing side, not the drawing side — and never block a batch."""
    root = R.root()
    out = {"characters": {}, "locations": {}, "objects": {}, "findings": [], "notes": []}

    cast_sheets = {p.stem: p for p in sorted((root / "cast").glob("*.md"))}
    for name, desc in (spec.get("characters") or {}).items():
        row = {"sheet": name in cast_sheets, "images": _images_under(root / "cast" / name),
               "description": bool((desc or "").strip())}
        out["characters"][name] = row
        if not row["description"]:
            out["findings"].append(f"{name}: empty description in briefs.json — nothing reaches the prompt")
        if not row["images"]:
            out["findings"].append(f"{name}: no reference images under cast/{name}/ — the face is invented per panel")
        if not row["sheet"]:
            out["notes"].append(f"{name}: draws, but has no cast sheet (cast/{name}.md) — no DNA, no Voice")
    for stem in cast_sheets:
        if stem not in out["characters"]:
            out["findings"].append(
                f"{stem}: cast sheet with no `characters` line in briefs.json — nothing binds it; "
                f"register it (/kav-character {stem})")

    words = spec.get("location_words") or {}
    loc_sheets = {p.stem for p in (root / "locations").glob("*.md")}
    for name, cfg in (spec.get("locations") or {}).items():
        photos = [root / p for p in (cfg or {}).get("photos", [])]
        row = {"sheet": name in loc_sheets, "photos": sum(p.exists() for p in photos),
               "words": list(words.get(name, [])) if words else [name]}
        out["locations"][name] = row
        if not photos:
            out["findings"].append(f"{name}: no photos listed — the place is invented per panel")
        elif row["photos"] < len(photos):
            out["findings"].append(f"{name}: {len(photos) - row['photos']} listed photo(s) missing on disk")
        if words and not words.get(name):
            out["findings"].append(f"{name}: not in location_words — no scene line can ever bind it")
        if not row["sheet"]:
            out["notes"].append(f"{name}: draws, but has no location sheet (locations/{name}.md)")
    for stem in sorted(loc_sheets - set(out["locations"])):
        out["findings"].append(
            f"{stem}: location sheet with no `locations` entry of that name — nothing binds it; "
            f"register it (/kav-location {stem}), or rename the sheet to match the entry it describes")

    owords = spec.get("object_words") or {}
    obj_sheets = {p.stem for p in (root / "objects").glob("*.md")}
    for name, cfg in (spec.get("objects") or {}).items():
        photo = any((root / "objects" / f"{name}{e}").exists() for e in IMAGES) or any(
            (root / p).exists() for p in (cfg or {}).get("photos", []))
        row = {"sheet": name in obj_sheets, "photo": photo,
               "words": list(owords.get(name, [])) if owords else [name]}
        out["objects"][name] = row
        if not photo:
            out["findings"].append(f"{name}: no object photo on disk — it will be invented per panel")
        if owords and not owords.get(name):
            out["findings"].append(f"{name}: not in object_words — no scene line can ever bind it")
        if not row["sheet"]:
            out["notes"].append(f"{name}: draws, but has no object sheet (objects/{name}.md)")
    for stem in sorted(obj_sheets - set(out["objects"])):
        out["findings"].append(
            f"{stem}: object sheet with no `objects` entry of that name — nothing binds it "
            f"(/kav-object {stem})")
    return out


def _label(head):
    """A scene heading short enough to name it in a finding: 'S3 · המקלט'."""
    short = re.split(r"\s[—–]\s", head, maxsplit=1)[0].strip()
    return short if len(short) <= 48 else short[:47] + "…"


def _aliases(spec):
    """name -> [words a plan may use for it], from briefs.json keys and cast sheet headings."""
    root = R.root()
    al = {name: [name] for name in (spec.get("characters") or {})}
    for p in (root / "cast").glob("*.md"):
        if p.stem in al:
            al[p.stem] += [a for a in _sheet_aliases(p) if a not in al[p.stem]]
    return al


def _names_in(text, aliases):
    low = text.lower()
    found = []
    for name, words in aliases.items():
        for w in words:
            w = w.lower()
            if re.search(rf"(?:\b|(?<=[{HE_PREFIX}]))" + re.escape(w) + r"\b", low):
                found.append(name)
                break
    return found


def _places_in(text):
    """Every location whose words the text hits, in spec order: the first is what binds."""
    low = text.lower()
    return [loc for loc, words in R.location_words().items()
            if any(w.lower() in low for w in words)]


def _objects_in(text):
    low = text.lower()
    return [o for o, words in R.object_words().items() if any(w.lower() in low for w in words)]


def sections(plan_text):
    """The plan split at its '## ' headings: [(heading, body)]."""
    out, head, body = [], None, []
    for ln in plan_text.splitlines():
        if ln.startswith("## "):
            if head is not None:
                out.append((head, "\n".join(body)))
            head, body = ln[3:].strip(), []
        elif head is not None:
            body.append(ln)
    if head is not None:
        out.append((head, "\n".join(body)))
    return out


def audit_plan(path, spec):
    aliases = _aliases(spec)
    secs = sections(path.read_text(encoding="utf-8"))
    scene_like = [h for h, _ in secs if SCENE_HEADING.match(h)]
    rows, findings = [], []
    for head, body in secs:
        text = head + "\n" + body
        places = _places_in(text)
        row = {"section": head, "scene": bool(SCENE_HEADING.match(head)) or not scene_like,
               "characters": _names_in(text, aliases), "place": places[0] if places else None,
               "also_places": places[1:], "objects": _objects_in(text)}
        rows.append(row)
        if not row["scene"]:
            continue
        if not row["characters"]:
            findings.append(f"{_label(head)}: names no registered character — a panel line without one is refused")
        if not row["place"]:
            findings.append(f"{_label(head)}: no registered place matches its words — the panel binds no "
                            f"location and falls back to generic scenery")
    return {"plan": str(path), "sections": rows, "findings": findings}


def audit_batch(path, spec):
    data = json.loads(path.read_text(encoding="utf-8"))
    rows, findings = [], []
    for p in data.get("panels", []):
        if p.get("picked"):
            continue
        brief = R.parse_quick_line(p.get("line", ""), 0, list(spec.get("characters") or {}))
        if not brief:
            rows.append({"id": p.get("id"), "characters": [], "place": None, "objects": []})
            findings.append(f"{p.get('id')}: names no registered character — panel_batch will refuse it")
            continue
        row = {"id": p.get("id"), "characters": brief["characters"],
               "place": brief.get("location"), "objects": brief.get("objects", [])}
        rows.append(row)
        if not row["place"]:
            findings.append(f"{p.get('id')}: no registered place in the line — generic scenery")
    return {"batch": str(path), "panels": rows, "findings": findings}


def _fmt(names):
    return ", ".join(names) if names else "—"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--story", help="story slug (read from the first --batch when omitted)")
    ap.add_argument("--chapter", help="chNN: audit chapters/chNN/panels/plan.md")
    ap.add_argument("--plan", help="a plan.md to audit instead of the chapter's")
    ap.add_argument("--batch", nargs="*", default=[], help="batch json file(s): audit their panel lines")
    ap.add_argument("--json", action="store_true", help="machine-readable")
    a = ap.parse_args()

    batches = [resolve(b) for b in a.batch]
    story = a.story
    if not story and batches:
        story = json.loads(batches[0].read_text(encoding="utf-8")).get("story")
    if not story:
        ap.error("--story is required (or a --batch that names one)")
    R.set_story(story)
    spec = R.load_spec()

    plan = None
    if a.plan:
        plan = resolve(a.plan)
    elif a.chapter:
        plan = chapter_dir(story, a.chapter) / "panels" / "plan.md"
    if plan and not plan.exists():
        sys.exit(f"No scene list at {plan}")
    if not plan and not batches:
        ap.error("give --chapter, --plan or --batch")

    report = {"story": story, "registry": registry(spec), "plan": None, "batches": []}
    if plan:
        report["plan"] = audit_plan(plan, spec)
    for b in batches:
        report["batches"].append(audit_batch(b, spec))
    findings = list(report["registry"]["findings"])
    if report["plan"]:
        findings += report["plan"]["findings"]
    for b in report["batches"]:
        findings += b["findings"]
    report["findings"] = findings

    if a.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        sys.exit(1 if findings else 0)

    reg = report["registry"]
    print(f"Registry — {story}")
    print(f"  characters: {len(reg['characters'])} registered · "
          f"{sum(r['sheet'] for r in reg['characters'].values())} with a sheet · "
          f"{sum(r['images'] for r in reg['characters'].values())} with reference images")
    print(f"  locations:  {len(reg['locations'])} registered · "
          f"{sum(r['sheet'] for r in reg['locations'].values())} with a sheet")
    print(f"  objects:    {len(reg['objects'])} registered")
    for f in reg["findings"]:
        print(f"  ! {f}")
    for n in reg["notes"]:
        print(f"  · {n}")

    if report["plan"]:
        pl = report["plan"]
        rel = Path(pl["plan"])
        rel = rel.relative_to(REPO) if rel.is_relative_to(REPO) else rel
        print(f"\nScene list — {rel}")
        for r in pl["sections"]:
            if not r["scene"]:
                continue
            place = r["place"] or "NONE"
            also = f"  (also matches: {', '.join(r['also_places'])})" if r["also_places"] else ""
            print(f"  {_label(r['section']):<48}  cast: {_fmt(r['characters'])}  ·  place: {place}{also}"
                  f"  ·  objects: {_fmt(r['objects'])}")
    for b in report["batches"]:
        rel = Path(b["batch"])
        rel = rel.relative_to(REPO) if rel.is_relative_to(REPO) else rel
        print(f"\nBatch — {rel}")
        for r in b["panels"]:
            print(f"  {r['id']:<8} cast: {_fmt(r['characters'])}  ·  place: {r['place'] or 'NONE'}"
                  f"  ·  objects: {_fmt(r['objects'])}")

    if findings:
        print("\nNeeds the author before any image is generated:")
        for f in findings:
            print(f"  - {f}")
        print("\nCreate what is missing with /kav-character, /kav-location or /kav-object, add the words "
              "a scene uses to location_words / object_words, or record in plan.md that a place stays "
              "scenery on purpose.")
    else:
        print("\nEvery scene binds a character and a place; the registry is consistent.")
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
