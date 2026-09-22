#!/usr/bin/env python3
"""Check a Kav install in one command, and optionally import API keys from another .env.

Reports Python, dependencies, Chrome, .env and every image key Kav knows, as OK /
missing with the fix. Key values are never printed: only whether a key is set and
where it came from (shell environment or the repo's .env).

  python3 tools/check_setup.py                 the health check (table)
  python3 tools/check_setup.py --json          the same, machine-readable
  python3 tools/check_setup.py --import PATH   copy known keys from another .env file into
                                               the repo's .env (names only are reported;
                                               keys already set are kept unless --overwrite)

The "image lane" line names the cheapest configured lane, used by tools/welcome_panel.py.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kav_env import KEY_ALIASES, KEY_HELP, REPO  # noqa: E402
import lanes  # noqa: E402

ENV = REPO / ".env"


def parse_env(path):
    """{name: value} for the non-empty assignments in an env file."""
    out = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if "=" not in line or line.startswith("#"):
            continue
        k, v = line.split("=", 1)
        k = k.strip().removeprefix("export ").strip()
        v = v.strip().strip('"').strip("'")
        if v:
            out[k] = v
    return out


def key_source(canonical):
    names = KEY_ALIASES[canonical]
    if any(os.environ.get(n) for n in names):
        return "shell"
    if ENV.exists() and any(n in parse_env(ENV) for n in names):
        return ".env"
    return None


def cheapest_lane():
    """The cheapest configured lane/provider pair (tools/lanes/__init__.py knows the costs)."""
    best = lanes.cheapest()
    if not best:
        return None
    return {"lane": best[0], "via": best[1], "approx_cost_usd": best[2],
            "providers": lanes.configured()}


def version():
    f = REPO / "VERSION"
    return f.read_text().strip() if f.exists() else "unknown"


def checks():
    rows = [{"check": "Kav version", "ok": True, "detail": version(), "fix": ""}]
    ok_py = sys.version_info >= (3, 10)
    rows.append({"check": "Python 3.10+", "ok": ok_py, "detail": sys.version.split()[0],
                 "fix": "install Python 3.10+ (python.org, or `brew install python`)"})
    try:
        import PIL  # noqa: F401
        rows.append({"check": "Python deps", "ok": True, "detail": "Pillow", "fix": ""})
    except ImportError:
        rows.append({"check": "Python deps", "ok": False, "detail": "Pillow missing",
                     "fix": "pip install -r requirements.txt"})
    chrome = subprocess.run([sys.executable, str(REPO / "tools" / "chrome.py")],
                            capture_output=True, text=True)
    rows.append({"check": "Chrome / Chromium", "ok": chrome.returncode == 0,
                 "detail": (chrome.stdout or chrome.stderr).strip().splitlines()[-1:][0]
                 if (chrome.stdout or chrome.stderr).strip() else "",
                 "fix": "install Google Chrome or Chromium, or set KAV_CHROME in .env"})
    rows.append({"check": ".env", "ok": ENV.exists(), "detail": "present" if ENV.exists() else "absent",
                 "fix": "cp .env.example .env"})
    for canonical in KEY_ALIASES:
        src = key_source(canonical)
        rows.append({"check": canonical, "ok": bool(src),
                     "detail": f"set ({src})" if src else "not set",
                     "fix": KEY_HELP[canonical]})
    lane = cheapest_lane()
    rows.append({"check": "image lane", "ok": bool(lane),
                 "detail": f"{lane['lane']} via {lane['via']}, ~${lane['approx_cost_usd']}/image"
                 + (f" · configured: {', '.join(lane['providers'])}" if lane else "") if lane
                 else "none: writing works, images need an image-provider key",
                 "fix": "set FAL_KEY (one key covers Seedream and Nano Banana)"})
    return rows


def models_table():
    """Every provider and model in the registry: key set or not, status, price, age."""
    out = []
    for name, p in lanes.PROVIDERS.items():
        have = all(key_source(k) for k in p["keys"] if k in KEY_ALIASES)
        for lane_name, m in p["models"].items():
            age = lanes.days_since_verified(name, lane_name)
            out.append({"provider": name, "lane": lane_name, "title": f"{p['title']} · {m['title']}",
                        "key_set": have, "status": m.get("status"), "price": m.get("price"),
                        "max_refs": m.get("max_refs"), "verified_on": m.get("verified_on"),
                        "days_since_verified": age,
                        "stale": bool(age and age > lanes.STALE_DAYS), "notes": m.get("notes", "")})
    return out


def import_keys(src, overwrite=False):
    src = Path(src).expanduser()
    if not src.is_file():
        sys.exit(f"No such file: {src}")
    if src.resolve() == ENV.resolve():
        sys.exit("That is Kav's own .env already.")
    found = parse_env(src)
    if not ENV.exists():
        example = REPO / ".env.example"
        shutil.copy(example, ENV) if example.exists() else ENV.write_text("")
    lines = ENV.read_text(encoding="utf-8").splitlines()
    current = parse_env(ENV)
    report = []
    for canonical, names in KEY_ALIASES.items():
        hit = next((n for n in names if n in found), None)
        if not hit:
            report.append(f"{canonical}: not in {src.name}")
            continue
        if any(n in current for n in names) and not overwrite:
            report.append(f"{canonical}: already set in .env, kept (use --overwrite to replace)")
            continue
        value = found[hit]
        replaced = False
        for i, line in enumerate(lines):
            k = line.split("=", 1)[0].strip().removeprefix("export ").strip() if "=" in line else ""
            if k == canonical:
                lines[i] = f"{canonical}={value}"
                replaced = True
        if not replaced:
            lines.append(f"{canonical}={value}")
        report.append(f"{canonical}: copied (from {hit})")
    ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--import", dest="import_from", metavar="PATH")
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args()
    if a.import_from:
        for line in import_keys(a.import_from, a.overwrite):
            print(line)
        return
    rows = checks()
    if a.json:
        print(json.dumps({"version": version(), "checks": rows, "image_lane": cheapest_lane(),
                          "models": models_table()}, indent=2))
        return
    for r in rows:
        mark = "OK     " if r["ok"] else "MISSING"
        fix = "" if r["ok"] else f"  -> {r['fix']}"
        print(f"{mark}  {r['check']:<18} {r['detail']}{fix}")
    print("\nImage models (tools/lanes/models.json):")
    for m in models_table():
        mark = "set    " if m["key_set"] else "no key "
        price = f"~${m['price']}" if m["price"] else ""
        caps = (f"{m['max_refs']} ref max" if m["max_refs"] == 1 else
                f"{m['max_refs']} refs max") if m["max_refs"] else "full refs"
        stale = f"  (last verified {m['verified_on']} — worth re-checking)" if m["stale"] else ""
        print(f"  {mark} {m['provider']:<11} --lane {m['lane']:<11} {m['status']:<16} "
              f"{price:<7} {caps}{stale}")


if __name__ == "__main__":
    main()
