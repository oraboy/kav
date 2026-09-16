#!/usr/bin/env python3
"""Letter a panel: draw balloons, captions and free text over a picked image.

Reads an overlay spec (JSON), builds an HTML compositing page and screenshots it with
headless Chrome at full panel resolution. Text is real text (browser shaping: RTL, fonts,
kerning); balloons are SVG shapes drawn under it. Writes <out.png> plus the <out.html> it
rendered. --phone renders the phone variant of a wide panel: captions sit against the
centre 4:5 crop instead of the page edges (save it as <panel>.phone.png; assemble.py
uses it for the carousel). See tools/examples/lettering.example.json.

Spec: panel (path relative to stories/<story>/ when "story" is set, else to the repo, or
absolute), size [w, h], style {speech|thought|shout|caption: fill, stroke, stroke_w, font,
color, size, weight, slant}, fonts [stylesheet URLs], overlays:
  {type: "balloon", kind: speech|thought|shout, cx, cy, rx, ry, tail: [x, y] (optional),
   lang: he|en|..., lines: [...], size?}
  {type: "caption", y, lang, lines}   full-width band, 1.5x text, right-aligned for he
  {type: "text", x, y, w, h, lang, lines, color?, weight?, font?: "balloon"}  free text, no box
"""
import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kav_env import REPO  # noqa: E402
import chrome  # noqa: E402

# Font stacks are cross-script: Latin comes from the first font, Hebrew (or another
# script) falls through to the first font that has the glyphs. Default faces: Varela
# Round for balloons, Karantina for captions, both OFL, loaded from Google Fonts on every
# render; a spec's "fonts" list adds further stylesheets on top.
DEFAULT_FONTS = [
    "https://fonts.googleapis.com/css2?family=Varela+Round&family=Karantina:wght@700&display=swap",
]
BALLOON_STACK = "'Varela Round', 'Raanana', 'Arial Hebrew', sans-serif"
DEFAULT_STYLE = {
    "speech": {
        "fill": "white", "stroke": "black", "stroke_w": 8,
        "font": BALLOON_STACK,
        "color": "black", "size": 76, "weight": "normal", "slant": "normal",
    },
    "thought": {
        "fill": "#f2f4f7", "stroke": "#333a45", "stroke_w": 7,
        "font": BALLOON_STACK,
        "color": "#2a2f3a", "size": 70, "weight": "normal", "slant": "italic",
    },
    "shout": {
        "fill": "white", "stroke": "black", "stroke_w": 12,
        "font": BALLOON_STACK,
        "color": "black", "size": 92, "weight": "bold", "slant": "normal",
    },
    "caption": {
        "fill": "#fdf6d8", "stroke": "black", "stroke_w": 7,
        "font": "'Karantina', 'New Peninim MT', sans-serif",
        "color": "black", "size": 100, "weight": "bold", "slant": "normal",
    },
}

# Captions: 50% larger than the theme size, a band across the full width of the image,
# text right-aligned for Hebrew. On a wide panel the phone keeps only the centre 4:5, so
# a --phone render sets the band against that crop instead of the page edges.
CAPTION_SCALE = 1.5
CAPTION_MARGIN = 40
PANEL_W = PANEL_H = 0
PHONE = False


def theme(spec, kind):
    t = dict(DEFAULT_STYLE[kind])
    t.update(spec.get("style", {}).get(kind, {}))
    return t


def ellipse_pt(cx, cy, rx, ry, a):
    return cx + rx * math.cos(a), cy + ry * math.sin(a)


def cloud_path(cx, cy, rx, ry, bumps=12, k=1.22):
    pts = [ellipse_pt(cx, cy, rx, ry, 2 * math.pi * i / bumps) for i in range(bumps)]
    d = f"M {pts[0][0]:.0f},{pts[0][1]:.0f} "
    for i in range(bumps):
        ctrl = ellipse_pt(cx, cy, rx * k, ry * k, 2 * math.pi * (i + 0.5) / bumps)
        p2 = pts[(i + 1) % bumps]
        d += f"Q {ctrl[0]:.0f},{ctrl[1]:.0f} {p2[0]:.0f},{p2[1]:.0f} "
    return d + "Z"


def burst_points(cx, cy, rx, ry, spikes=20, outer=1.18, inner=0.85):
    pts = []
    for i in range(spikes * 2):
        m = outer if i % 2 == 0 else inner
        x, y = ellipse_pt(cx, cy, rx * m, ry * m, math.pi * i / spikes)
        pts.append(f"{x:.0f},{y:.0f}")
    return " ".join(pts)


def stroke_attrs(t):
    return f'fill="{t["fill"]}" stroke="{t["stroke"]}" stroke-width="{t["stroke_w"]}" stroke-linejoin="round"'


def tail_svg(o, t):
    """Tail toward o['tail'] (the mouth), stopping ~12% short so it never sits on the face.

    A balloon with no 'tail' renders tailless: a continuation balloon, placed directly
    under the same speaker's previous balloon."""
    if not o.get("tail"):
        return ""
    cx, cy, ry = o["cx"], o["cy"], o["ry"]
    tx, ty = o["tail"]
    tx, ty = cx + 0.88 * (tx - cx), cy + 0.88 * (ty - cy)
    kind = o.get("kind", "speech")

    if kind == "thought":
        circles = ""
        for frac, r in ((0.30, 44), (0.58, 28), (0.82, 17)):
            bx = cx + frac * (tx - cx)
            by = (cy + ry * 0.8) + frac * (ty - (cy + ry * 0.8))
            circles += f'<circle cx="{bx:.0f}" cy="{by:.0f}" r="{r}" {stroke_attrs(t)}/>'
        return circles

    base_x = cx + (0.35 * o["rx"] if tx > cx else -0.35 * o["rx"])
    base_y = cy + ry - 40
    if kind == "shout":
        return (
            f'<polygon points="{base_x - 60:.0f},{base_y:.0f} {tx:.0f},{ty:.0f} '
            f'{base_x + 60:.0f},{base_y:.0f}" {stroke_attrs(t)}/>'
        )
    mid_x = (base_x + tx) / 2
    mid_y = (base_y + ty) / 2
    return (
        f'<path d="M {base_x - 70:.0f},{base_y:.0f} '
        f'Q {mid_x - 40:.0f},{mid_y:.0f} {tx:.0f},{ty:.0f} '
        f'Q {mid_x + 60:.0f},{mid_y:.0f} {base_x + 70:.0f},{base_y:.0f} Z" '
        f'{stroke_attrs(t)}/>'
    )


def body_svg(o, t):
    cx, cy, rx, ry = o["cx"], o["cy"], o["rx"], o["ry"]
    kind = o.get("kind", "speech")
    if kind == "thought":
        return f'<path d="{cloud_path(cx, cy, rx, ry)}" {stroke_attrs(t)}/>'
    if kind == "shout":
        return f'<polygon points="{burst_points(cx, cy, rx, ry)}" {stroke_attrs(t)}/>'
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" {stroke_attrs(t)}/>'


def text_div(o, t):
    lang = o.get("lang", "en")
    lines = "<br>".join(o["lines"])
    size = o.get("size", t["size"])
    if o["type"] == "caption":
        size = round(size * CAPTION_SCALE)
    font = t["font"]
    if o["type"] == "text" and o.get("font") == "balloon":
        font = BALLOON_STACK
    color = o.get("color", t["color"])
    common = (
        f"font-family:{font};font-size:{size}px;color:{color};"
        f"font-weight:{o.get('weight', t['weight'])};font-style:{t['slant']};line-height:1.2;"
    )
    if o["type"] == "balloon":
        # Spiky/scalloped edges eat into the box; shrink the text area.
        shrink = 0.78 if o.get("kind") in ("thought", "shout") else 1.0
        rx, ry = o["rx"] * shrink, o["ry"] * shrink
        style = (
            f"left:{o['cx'] - rx:.0f}px;top:{o['cy'] - ry:.0f}px;"
            f"width:{2 * rx:.0f}px;height:{2 * ry:.0f}px;"
            f"display:flex;align-items:center;justify-content:center;text-align:center;{common}"
        )
    elif o["type"] == "text":
        # Free text with no box: title cards.
        style = (
            f"left:{o['x']}px;top:{o['y']}px;width:{o['w']}px;height:{o['h']}px;"
            f"display:flex;align-items:center;justify-content:center;text-align:center;{common}"
        )
    else:
        wide = PANEL_H and PANEL_W / PANEL_H > 0.81
        if PHONE and wide:
            crop = PANEL_H * 0.8
            left, width = (PANEL_W - crop) / 2 + CAPTION_MARGIN, crop - 2 * CAPTION_MARGIN
        else:
            left, width = CAPTION_MARGIN, PANEL_W - 2 * CAPTION_MARGIN
        style = (
            f"left:{left:.0f}px;top:{o['y']}px;width:{width:.0f}px;"
            f"box-sizing:border-box;padding:{size * 0.22:.0f}px {size * 0.4:.0f}px;"
            f"background:{t['fill']};border:{t['stroke_w']}px solid {t['stroke']};"
            f"text-align:{'right' if lang == 'he' else 'left'};{common}"
        )
    direction = ' dir="rtl"' if lang in ("he", "ar", "fa", "ur", "yi") else ""
    return f'<div class="ov"{direction} style="{style}">{lines}</div>'


def panel_path(spec, spec_file):
    p = Path(spec["panel"]).expanduser()
    if p.is_absolute():
        return p
    # A spec's "story" key roots its panel path inside that story: everything a story
    # generates stays under stories/<slug>/, so two stories never mix.
    base = REPO / "stories" / spec["story"] if spec.get("story") else REPO
    if (base / p).exists() or spec.get("story"):
        return (base / p).resolve()
    return (Path(spec_file).parent / p).resolve()


def main():
    global PANEL_W, PANEL_H, PHONE
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", help="overlay spec JSON")
    ap.add_argument("out", help="output PNG (the HTML lands beside it)")
    ap.add_argument("--phone", action="store_true",
                    help="phone variant: captions against the centre 4:5 crop of a wide panel")
    a = ap.parse_args()
    PHONE = a.phone
    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    w, h = spec["size"]
    PANEL_W, PANEL_H = w, h
    panel = panel_path(spec, a.spec)
    if not panel.exists():
        sys.exit(f"Panel image not found: {panel}")

    shapes, texts = "", ""
    for o in spec["overlays"]:
        if o["type"] == "balloon":
            t = theme(spec, o.get("kind", "speech"))
            shapes += tail_svg(o, t) + body_svg(o, t)
            texts += text_div(o, t)
        else:
            texts += text_div(o, theme(spec, "caption"))

    font_links = "".join(f'<link rel="stylesheet" href="{u}">' for u in DEFAULT_FONTS + spec.get("fonts", []))

    html = f"""<!doctype html><html><head><meta charset="utf-8">{font_links}<style>
    html,body{{margin:0;padding:0;width:{w}px;height:{h}px;overflow:hidden}}
    .stage{{position:relative;width:{w}px;height:{h}px}}
    .stage img,.stage svg{{position:absolute;left:0;top:0;width:{w}px;height:{h}px}}
    .ov{{position:absolute}}
    </style></head><body><div class="stage">
    <img src="{panel.as_uri()}">
    <svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">{shapes}</svg>
    {texts}
    </div></body></html>"""

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    html_path = out.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")
    chrome.screenshot(html_path, out, w, h, scale=1, budget_ms=15000)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
