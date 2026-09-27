#!/usr/bin/env python3
"""Quick scan: nine varied panels, with the exact prompt and reference list behind each.

The reliability test that /kav-visual-style-lock runs before anything expensive is baked.
Generates nine different character/location combinations on the pack, captures what was
actually sent for every one, and writes a self-contained review page.

    python3 tools/quick_scan.py --story <slug> --out <page.html> [--seed N]

Combinations come from a spec file at stories/<slug>/style/scan.json, or are proposed
from briefs.json when none exists. Nothing is judged here — that is the agent's job, and
it happens before the page reaches the author.
"""
import argparse
import base64
import html
import io
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kav_env import REPO  # noqa: E402

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required: pip install Pillow")


def thumb(path, width):
    im = Image.open(path).convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=80, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def run(story, line, ar, seed):
    """Generate, then dry-run for the refs and prompt. Returns (path, refs, prompt).

    Generate first: a panel whose location plate has never been drawn draws it on the way
    through, which changes the reference list. Reading the plan afterwards reports what was
    actually sent rather than what would have been sent an instant earlier.
    """
    cmd = ["python3", "tools/generate.py", "--story", story, "--ar", ar, line, "--lane", "seedream"]
    if seed is not None:
        cmd += ["--seed", str(seed)]
    gen = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    if gen.returncode:
        raise SystemExit(f"generate failed for {line!r}:\n{gen.stderr}")
    dry = subprocess.run(["python3", "tools/generate.py", "--story", story, "--dry-run",
                          "--ar", ar, line], cwd=REPO, capture_output=True, text=True)
    if dry.returncode:
        raise SystemExit(f"dry-run failed for {line!r}:\n{dry.stderr}")
    plan = json.loads(dry.stdout)
    return json.loads(gen.stdout)["path"], plan["refs"], plan["prompt"]


PAGE = """<title>Quick Scan</title>
<style>
:root {{ color-scheme: light; --ink:#241a13; --ink2:#5c4636; --bg:#f7efe2; --panel:#fffaf1;
  --rule:#e0cdb6; --terra:#c8502c; --flag:#a8451f; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ color-scheme: dark;
  --ink:#f3e6d6; --ink2:#bda88f; --bg:#1a130d; --panel:#251a12; --rule:#4a3a2c;
  --terra:#e07048; --flag:#e08054; }} }}
:root[data-theme="dark"] {{ color-scheme: dark; --ink:#f3e6d6; --ink2:#bda88f; --bg:#1a130d;
  --panel:#251a12; --rule:#4a3a2c; --terra:#e07048; --flag:#e08054; }}
body {{ background:var(--bg); color:var(--ink); font:15px/1.55 system-ui,sans-serif;
  padding-block:26px 70px; padding-left:20px; padding-right:20px; max-width:1240px; margin:0 auto; }}
h1 {{ font-size:30px; margin:0 0 4px; }}
.sub {{ color:var(--ink2); margin:0 0 6px; max-width:70ch; }}
.grid {{ display:grid; gap:18px; grid-template-columns:repeat(auto-fill,minmax(330px,1fr)); margin-top:22px; }}
figure {{ margin:0; background:var(--panel); border:1px solid var(--rule); border-radius:3px;
  overflow:hidden; display:flex; flex-direction:column; }}
figure.flagged {{ border-color:var(--flag); border-width:2px; }}
.imgwrap {{ position:relative; }}
figure img.shot {{ width:100%; display:block; }}
.num {{ position:absolute; top:8px; left:8px; background:var(--terra); color:#fff7ec; font-weight:700;
  font-size:15px; padding:4px 11px; border-radius:2px; }}
.badge {{ position:absolute; top:8px; right:8px; background:var(--flag); color:#fff7ec; font-weight:700;
  font-size:11px; letter-spacing:.07em; text-transform:uppercase; padding:4px 9px; border-radius:2px; }}
figcaption {{ padding:11px 13px 14px; display:flex; flex-direction:column; gap:7px; }}
.what {{ font-size:13.5px; }}
.verdict {{ font-size:13px; color:var(--ink2); }}
.verdict.bad {{ color:var(--flag); font-weight:600; }}
details {{ border-top:1px solid var(--rule); padding-top:7px; }}
summary {{ cursor:pointer; font-size:11.5px; letter-spacing:.06em; text-transform:uppercase;
  color:var(--ink2); }}
.refs {{ display:grid; gap:5px; grid-template-columns:repeat(auto-fill,minmax(62px,1fr)); margin:9px 0; }}
.refs figure {{ border:1px solid var(--rule); border-radius:2px; }}
.refs img {{ width:100%; aspect-ratio:1/1; object-fit:cover; display:block; }}
.refs .cap {{ font-size:8.5px; padding:2px 3px; color:var(--ink2); line-height:1.25; }}
pre {{ white-space:pre-wrap; font-family:ui-monospace,monospace; font-size:11px; line-height:1.55;
  background:var(--bg); border:1px solid var(--rule); padding:9px 10px; margin:8px 0 0;
  max-height:260px; overflow:auto; }}
.ask {{ margin-top:36px; background:var(--panel); border:2px solid var(--terra); padding:18px 22px;
  border-radius:3px; }}
.ask h2 {{ font-family:inherit; font-size:20px; margin:0 0 8px; color:var(--terra); }}
.ask p {{ margin:0 0 8px; font-size:14.5px; max-width:70ch; }}
</style>
<h1>Quick scan</h1>
<p class="sub">{intro}</p>
<div class="grid">{cards}</div>
<div class="ask"><h2>Your call</h2>{ask}</div>
"""


def build(story, out_path, scan, intro, ask):
    cards = []
    for i, item in enumerate(scan, 1):
        refs = "".join(
            f'<figure><img src="{thumb(r["local"], 120)}" alt="">'
            f'<div class="cap">{i2}. {html.escape(r["kind"][:4])}<br>{html.escape(r["name"])}</div></figure>'
            for i2, r in enumerate(item["refs"], 1))
        flagged = " flagged" if item.get("flag") else ""
        badge = f'<span class="badge">{html.escape(item["flag"])}</span>' if item.get("flag") else ""
        vclass = "verdict bad" if item.get("flag") else "verdict"
        cards.append(
            f'<figure class="card{flagged}"><div class="imgwrap">'
            f'<img class="shot" src="{thumb(item["path"], 660)}" alt="">'
            f'<span class="num">{i}</span>{badge}</div>'
            f'<figcaption><span class="what">{html.escape(item["what"])}</span>'
            f'<span class="{vclass}">{html.escape(item["verdict"])}</span>'
            f'<details><summary>exact prompt and {len(item["refs"])} references</summary>'
            f'<div class="refs">{refs}</div><pre>{html.escape(item["prompt"])}</pre></details>'
            f'</figcaption></figure>')
    Path(out_path).write_text(PAGE.format(intro=html.escape(intro), cards="".join(cards), ask=ask))
    return out_path


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--story", required=True)
    ap.add_argument("--spec", help="JSON list of {what, line, ar}; default stories/<slug>/style/scan.json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int)
    a = ap.parse_args()

    spec_path = Path(a.spec) if a.spec else REPO / "stories" / a.story / "style" / "scan.json"
    combos = json.loads(Path(spec_path).read_text())
    scan = []
    for c in combos:
        path, refs, prompt = run(a.story, c["line"], c.get("ar", "4:5"), a.seed)
        scan.append({"what": c["what"], "line": c["line"], "path": path,
                     "refs": refs, "prompt": prompt, "verdict": "", "flag": ""})
        print(f"{len(scan)}/{len(combos)}  {c['what']}")
    out = REPO / "stories" / a.story / "style" / "worksheets" / "scan-raw.json"
    out.write_text(json.dumps(scan, ensure_ascii=False, indent=2))
    print(f"\n{out}\nNow judge every image, fill in verdict/flag, then call build().")


if __name__ == "__main__":
    main()
