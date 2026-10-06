#!/usr/bin/env python3
"""A short, shareable report of how far a Kav install has got. Nothing is sent anywhere.

Prints the Kav version, the machine (OS and Python only), the setup check, and for each
story which planning blocks are locked, how many pieces exist and how many images Kav made.
`/kav-report` adds the author's own words and hands them the text to send.

What it leaves out, on purpose: every word of the story, every image, every file path,
and every API key (only whether one is set). Story names are left out too unless asked:

  python3 tools/report.py              the report, stories shown as "story 1", "story 2"
  python3 tools/report.py --names      the same, with each story's folder name
  python3 tools/report.py --json       machine-readable
"""
import argparse
import datetime
import json
import platform
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kav_env import REPO  # noqa: E402
import ledger  # noqa: E402

BLOCKS = ("concept", "cast", "locations", "objects", "style", "visual lock", "pitch", "storyboard", "package")
DONE = ("locked", "done", "complete", "sufficient", "registered")


def run(cmd):
    try:
        r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=60)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def machine():
    mac = platform.mac_ver()[0]
    if platform.system() == "Darwin":
        return f"macOS {mac or f'(Darwin {platform.release()})'} {platform.machine()}"
    return f"{platform.system()} {platform.release()} {platform.machine()}"


def setup():
    """The health check, reduced to names and yes/no: no paths, no key values."""
    raw = run([sys.executable, str(REPO / "tools" / "check_setup.py"), "--json"])
    try:
        data = json.loads(raw)
    except ValueError:
        return {"checks": [], "image_lane": None}
    checks = [{"check": c["check"], "ok": bool(c["ok"])} for c in data.get("checks", [])
              if c["check"] not in ("Kav version", "image lane")]
    lane = data.get("image_lane") or None
    return {"checks": checks,
            "image_lane": f"{lane['lane']} via {lane['via']}" if lane else None}


def blocks(state):
    """{block: status} from the flight-plan table in kickoff-state.md."""
    out = {}
    for line in state.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        name = re.sub(r"\(.*?\)", "", cells[0].replace("*", "")).strip().lower()
        name = re.sub(r"\s*\(?story\.md\)?$", "", name)
        if name not in BLOCKS:
            continue
        out[name] = status(cells[1])
    return out


def status(cell):
    """One word for a status cell. Authors and agents write these freely, so read generously."""
    text = cell.replace("*", "").strip().lower()
    m = re.match(r"(locked|done|complete|sufficient|registered|empty|in[- ]progress)", text)
    if m:
        return m.group(1).replace(" ", "-")
    if re.search(r"\blocked\b", text[:80]):
        return "locked"
    return "in-progress" if text else "empty"


def story(sd):
    state = (sd / "kickoff-state.md").read_text(encoding="utf-8") if (sd / "kickoff-state.md").is_file() else ""
    count = lambda folder: len(list((sd / folder).glob("*.md"))) if (sd / folder).is_dir() else 0  # noqa: E731
    chapters = sorted(p for p in (sd / "chapters").glob("ch*") if p.is_dir()) if (sd / "chapters").is_dir() else []
    cost = ledger.summarise(sd.name)
    return {"name": sd.name, "blocks": blocks(state),
            "cast": count("cast"), "locations": count("locations"), "objects": count("objects"),
            "chapters_started": len(chapters),
            "chapters_readable": sum(1 for c in chapters if (c / "pages" / "reader-story.html").is_file()),
            "images": cost["images"], "cost_usd": cost["documented_minimum_usd"],
            "failed_requests": cost["failed_requests"]}


def milestones(setup_info, stories, welcome):
    done = lambda s, b: s["blocks"].get(b, "").startswith(DONE)  # noqa: E731
    best = max(stories, key=lambda s: sum(done(s, b) for b in BLOCKS), default=None)
    return [("installed", bool(setup_info["checks"]) and all(c["ok"] for c in setup_info["checks"]
                                                              if not c["check"].endswith("_KEY"))),
            ("image key set", bool(setup_info["image_lane"])),
            ("test panel drawn", welcome),
            ("story started", bool(stories)),
            ("concept", bool(best) and (done(best, "concept") or done(best, "pitch"))),
            ("2+ cast", bool(best) and best["cast"] >= 2),
            ("1+ location", bool(best) and best["locations"] >= 1),
            ("style", bool(best) and (done(best, "style") or done(best, "visual lock"))),
            ("a chapter you can read", any(s["chapters_readable"] for s in stories))]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--names", action="store_true", help="show each story's folder name")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    version = (REPO / "VERSION").read_text(encoding="utf-8").strip() if (REPO / "VERSION").is_file() else "unknown"
    commit = run(["git", "rev-parse", "--short", "HEAD"])
    info = setup()
    root = REPO / "stories"
    stories = [story(p) for p in sorted(root.iterdir()) if p.is_dir() and not p.name.startswith(".")] if root.is_dir() else []
    welcome = (REPO / "setup" / "welcome.png").is_file()
    steps = milestones(info, stories, welcome)
    if not a.names:
        for i, s in enumerate(stories, 1):
            s["name"] = f"story {i}"

    if a.json:
        print(json.dumps({"date": datetime.date.today().isoformat(), "version": version, "commit": commit,
                          "machine": machine(), "python": platform.python_version(), "setup": info,
                          "welcome_panel": welcome, "stories": stories,
                          "milestones": {k: v for k, v in steps}}, indent=2, ensure_ascii=False))
        return

    print(f"Kav report · {datetime.date.today().isoformat()}")
    print(f"Kav {version}{f' ({commit})' if commit else ''} · {machine()} · Python {platform.python_version()}")
    print("\nSetup")
    for c in info["checks"]:
        # one image key is enough, so an unset key is not a fault
        absent = "not set" if c["check"].endswith("_KEY") else "missing"
        print(f"  {'ok' if c['ok'] else absent:<7}  {c['check']}")
    print(f"  image lane: {info['image_lane'] or 'none yet'} · test panel: {'drawn' if welcome else 'not yet'}")
    print(f"\nStories: {len(stories)}")
    for s in stories:
        print(f"  {s['name']}")
        print("    " + (" · ".join(f"{b} {s['blocks'][b]}" for b in BLOCKS if b in s["blocks"]) or "no planning blocks yet"))
        print(f"    {s['cast']} cast · {s['locations']} locations · {s['objects']} objects · "
              f"{s['chapters_started']} chapters started, {s['chapters_readable']} readable")
        print(f"    {s['images']} images made, about ${s['cost_usd']}"
              + (f" · {s['failed_requests']} failed requests" if s["failed_requests"] else ""))
    print("\nHow far")
    print("  " + " · ".join(f"{'✓' if ok else '–'} {k}" for k, ok in steps))


if __name__ == "__main__":
    main()
