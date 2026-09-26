#!/usr/bin/env python3
"""Render a story's world map: one square per piece, green check when ready, grey when not.

Rows: cast, locations, objects, styles (every available pack, the one in use marked),
the story (concept, storyboard), chapters. A square shows the piece's image and two
counts: reference images the author gave, and images Kav made. Hovering says why it
isn't ready; clicking shows what's needed, the images with their labels, and links.

Every image carries a label (REF01 for a reference the author gave, GEN01 for one Kav
made, P01 for a chapter page) so the author can say "remove GEN02 from Oren". The
labels are written to story-map.json beside the page; resolve them there, never by
guessing a filename.

  python3 tools/build_map.py --story <slug | path/to/stories/slug> [--out <file.html>]
"""
import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kav_env import REPO, jpeg_data_uri  # noqa: E402
from build_ideas import ideas_section  # noqa: E402

IMG = (".png", ".jpg", ".jpeg", ".webp")
DNA = ["Desires", "Skills", "Tendencies", "Shadows", "Don't", "Relationships", "Voice"]
SHOTS = ("front", "three-quarter", "smile", "full-body")
IMAGES, DESCRIPTION, PENDING = "Reference images missing", "Description missing", "Kav processing pending"
_thumbs, _hashes = {}, {}


def read(p):
    try:
        return Path(p).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def heading(text, fallback):
    m = re.search(r"^#\s+(.+)$", text, re.M)
    return re.split(r"\s+[—–-]\s+", m.group(1).strip())[0].replace("`", "").strip() if m else fallback


def field(text, label):
    m = re.search(r"\*\*" + re.escape(label) + r"[^*\n]*\*\*\s*:?(.*?)(?=\n\s*\*\*[^*\n]+\*\*|\n#|\Z)", text, re.S)
    body = re.sub(r"\s+", " ", m.group(1)).strip(" -·*_>") if m else ""
    return "" if body.lower().startswith(("(open", "(omitted", "<")) else body


def section(text, word):
    """Body of the first markdown heading whose title contains `word`."""
    m = re.search(r"^(#{2,4})[^\n]*" + re.escape(word) + r"[^\n]*\n(.*?)(?=^#{1,4}\s|\Z)", text, re.M | re.S | re.I)
    return m.group(2).strip() if m else ""


def images(folder):
    folder = Path(folder)
    if not folder.is_dir():
        return []
    return sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMG and not p.name.startswith("."))


def digest(p):
    if p not in _hashes:
        try:
            _hashes[p] = hashlib.sha1(Path(p).read_bytes()).hexdigest()
        except OSError:
            _hashes[p] = None
    return _hashes[p]


def unique(paths):
    seen, out = set(), []
    for p in paths:
        h = digest(p) or str(p)
        if h not in seen:
            seen.add(h)
            out.append(p)
    return out


def thumb(path, px):
    key = (str(path), px)
    if key not in _thumbs:
        try:
            _thumbs[key] = jpeg_data_uri(path, max_px=px, quality=72)
        except Exception:
            _thumbs[key] = None
    return _thumbs[key]


def links_in(text, want=None):
    """[(label, url)] from lines like 'classic https://… · carousel (slider) https://…'."""
    out = []
    for line in text.splitlines():
        if want and not re.search(want, line, re.I):
            continue
        for m in re.finditer(r"([A-Za-z][\w-]*)\s*(?:\([^)]*\))?\s*:?\s*(https://[^\s)>`\"'·]+)", line):
            out.append((m.group(1).lower(), m.group(2).rstrip(".,")))
    latest = {}
    for label, url in out:
        latest[label] = url
    return list(latest.items())


def piece(row, pid, name, *, needs=(), state=None, refs=(), gens=(), pages=(), face=None, text="", links=(), extra=""):
    needs = list(needs)
    if state is None:
        reasons = [r for r, _ in needs]
        state = next((r for r in (IMAGES, DESCRIPTION, PENDING) if r in reasons), reasons[0] if reasons else "ready")
    labelled = ([(f"REF{i:02d}", p, "ref") for i, p in enumerate(refs, 1)] +
                [(f"GEN{i:02d}", p, "gen") for i, p in enumerate(gens, 1)] +
                [(f"P{i:02d}", p, "page") for i, p in enumerate(pages, 1)])
    face_entry = next((e for e in labelled if e[1] == face), None) if face else None
    face_entry = face_entry or next((e for e in labelled if e[2] != "ref"), None) or (labelled[0] if labelled else None)
    return {"row": row, "id": pid, "name": name, "state": state, "needs": [n for _, n in needs], "images": labelled,
            "face": face_entry, "text": text, "links": list(links), "extra": extra,
            "n_ref": len(refs), "n_gen": len(gens) + len(pages)}


# --- cast ------------------------------------------------------------------------

def cast_row(sd, briefs, pack):
    chars = briefs.get("characters", {}) or {}
    mds = sorted((sd / "cast").glob("*.md"))
    stems = {m.stem for m in mds}
    out, claimed = [], set()
    for md in mds:
        text = read(md)
        keys = [md.stem] if md.stem in chars else []
        keys += [k for k in chars if k not in stems and k not in keys
                 and re.search(r"[-/_]" + re.escape(k) + r"\.(jpe?g|png|webp)", text, re.I)]
        claimed.update(keys)
        out.append(cast_piece(sd, md.stem, text, keys, chars, pack))
    for k in chars:
        if k not in claimed and k not in stems:
            out.append(cast_piece(sd, k, "", [k], chars, pack))
    return out


def cast_piece(sd, stem, text, keys, chars, pack):
    principal = bool(re.search(r"class:\**\s*principal", text, re.I))
    refs, gens = [], []
    for k in keys or [stem]:
        d = sd / "cast" / k
        refs += sorted(p for p in d.glob("source*") if p.suffix.lower() in IMG) if d.is_dir() else []
        gens += [d / pack / f"{s}.png" for s in SHOTS if pack and (d / pack / f"{s}.png").is_file()]
        gens += [d / f"{s}.png" for s in SHOTS if (d / f"{s}.png").is_file()]
    refs += [sd / r for r in re.findall(r"cast/images/[\w.\-]+", text) if (sd / r).is_file()]
    refs, gens = unique(refs), unique(gens)

    full = principal and not re.search(r"depth:\s*(sketch|light)", text, re.I)
    one_liner = field(text, "Who they are") or field(text, "What they are") or field(text, "Bio")
    look = any(k in chars for k in keys) or field(text, "Appearance")
    needs = []
    if not refs:
        needs.append((IMAGES, "Add a few photos, or any picture that shows the look"))
    if text and not one_liner:
        needs.append((DESCRIPTION, "Add a line on who they are"))
    elif not text and not look:
        needs.append((DESCRIPTION, "Add a one-line description of who they are"))
    if full and not any(field(text, s) for s in DNA):
        needs.append((DESCRIPTION, "Say what they want and what trips them up"))
    if refs and not keys:
        needs.append((PENDING, "Kav still has to set them up for drawing"))
    elif principal and refs and not gens:
        needs.append((PENDING, "Kav still has to build their portraits"))
    elif principal and pack and keys and not all((sd / "cast" / k / pack / "front.png").is_file() for k in keys):
        needs.append((PENDING, f"Kav still has to build their portraits in the {pack} style"))
    face = next((g for g in gens if g.name == "front.png" and pack and g.parent.name == pack), None) or \
        next((g for g in gens if g.name == "front.png"), None)
    return piece("cast", f"cast-{stem}", heading(text, stem), needs=needs, refs=refs, gens=gens, face=face, text=text)


# --- locations and objects -------------------------------------------------------

def place_row(sd, briefs, section_key, folder):
    reg = briefs.get(section_key, {}) or {}
    mds = sorted((sd / folder).glob("*.md"))
    stems = {m.stem for m in mds}
    reg_photos = {k: [sd / p for p in (v or {}).get("photos", []) if (sd / p).is_file()] for k, v in reg.items()}
    out, claimed = [], set()
    for md in mds:
        text = read(md)
        own = [sd / r for r in re.findall(rf"{folder}/images/[\w.\-]+", text) if (sd / r).is_file()]
        own += [p for p in (sd / folder).glob(f"{md.stem}*") if p.suffix.lower() in IMG]
        own_hashes = {digest(p) for p in own} - {None}
        tokens = [t for t in re.split(r"[-_]", md.stem) if len(t) >= 4]
        keys = [k for k in reg if k == md.stem]
        for k in reg:
            if k in keys or k in stems or k in claimed:
                continue
            if (re.search(r"\b" + re.escape(k) + r"\b", text) or any(t in k for t in tokens)
                    or own_hashes & {digest(p) for p in reg_photos[k]}):
                keys.append(k)
        claimed.update(keys)
        out.append(place_piece(section_key, md.stem, text, keys, reg, reg_photos, own))
    for k in reg:
        if k not in claimed and k not in stems:
            out.append(place_piece(section_key, k, "", [k], reg, reg_photos, []))
    return out


def place_piece(section_key, stem, text, keys, reg, reg_photos, own):
    photos = unique([p for k in keys for p in reg_photos.get(k, [])] + own)
    gens = [p for p in photos if re.search(r"ch\d\d", p.stem)]
    refs = [p for p in photos if p not in gens]
    described = bool(text) or any((reg.get(k) or {}).get("description") for k in keys)
    needs = []
    if not refs:
        needs.append((IMAGES, "Add photos of it" if section_key == "objects" else "Add photos of this place"))
    if not described:
        needs.append((DESCRIPTION, "Describe it in a line or two"))
    if refs and not keys:
        needs.append((PENDING, "Kav still has to set it up for drawing"))
    row = "location" if section_key == "locations" else "object"
    return piece(row, f"{row}-{stem}", heading(text, stem), needs=needs, refs=refs, gens=gens,
                 face=refs[0] if refs else None, text=text)


# --- styles ----------------------------------------------------------------------

def style_row(sd, repo, briefs, principals):
    active = (briefs.get("defaults", {}) or {}).get("style_pack", "")
    style = read(sd / "style" / "style.md")
    packs = {}
    for base in (repo / "styles", sd / "styles"):
        if base.is_dir():
            for p in sorted(base.iterdir()):
                if p.is_dir() and images(p):
                    packs.setdefault(p.name, p)
    out = []
    for name, p in sorted(packs.items(), key=lambda kv: (kv[0] != active, kv[0])):
        refs = images(p)
        if name != active:
            out.append(piece("style", f"style-{name}", name, state="available", refs=refs, text=read(p / "medium.txt")))
            continue
        gens = images(sd / "style" / "samples")
        needs = []
        if "locked" not in style.lower()[:600]:
            needs.append((PENDING, "The look hasn't been tested and locked yet"))
        missing = [k for k in principals if not (sd / "cast" / k / name / "front.png").is_file()]
        if missing:
            needs.append((PENDING, f"Portraits in this style still to build: {', '.join(missing)}"))
        out.append(piece("style", f"style-{name}", name, needs=needs, refs=refs, gens=gens, face=refs[0] if refs else None,
                         text=style))
    if not out:
        out.append(piece("style", "style-none", "Style", needs=[(IMAGES, "Pick a style, or add 2–5 images of the look you want")]))
    return out


# --- story and chapters ------------------------------------------------------------

def storyboard_html(sd, story, ch_ids):
    """The storyboard as the author reads it: the shape, the I/O, then each chapter."""
    parts = []
    shape = section(story, "Shape")
    io = section(story, "I/O")
    board = read(sd / "storyboard" / "storyboard.md")
    for label, body in (("Shape", shape), ("Intention and obstacle", io)):
        parts.append(f"<h4>{label}</h4>" + (f'<p class="prose" dir="auto">{esc(body[:1400])}</p>' if body else
                                             '<p class="missing">Not written yet</p>'))
    if board:
        parts.append(f'<details><summary>The whole storyboard</summary><pre dir="auto">{esc(board[:5000])}</pre></details>')
    for ch in ch_ids:
        card = read(sd / "storyboard" / f"{ch}.md")
        m = re.search(r"^#\s*Ch\s*\d+\s*[—–-]\s*(.+)$", card, re.M)
        title = m.group(1).strip() if m else ch.replace("ch", "Chapter ")
        art = next(iter(sorted((sd / "storyboard").glob(f"{ch}-concept*.png"))), None)
        src = thumb(art, 480) if art else None
        rows = [("Question", field(card, "Chapter question")), ("Intention and obstacle", field(card, "Chapter I/O")),
                ("Synopsis", field(card, "Synopsis"))]
        body = "".join(f'<p dir="auto"><b>{k}:</b> {esc(v)}</p>' if v else f'<p class="missing">{k}: not written yet</p>'
                       for k, v in rows)
        img = f'<img alt="" loading="lazy" src="{src}">' if src else '<p class="missing">No concept art yet</p>'
        parts.append(f'<div class="card"><h5 dir="auto">{esc(ch.replace("ch", "Ch "))} · {esc(title)}</h5>{img}{body}</div>'
                     if card else f'<div class="card"><h5>{esc(ch.replace("ch", "Ch "))}</h5><p class="missing">Not planned yet</p></div>')
    return "".join(parts)


def story_row(sd, ch_ids):
    story = read(sd / "story.md")
    state_md = read(sd / "kickoff-state.md")
    concept_text = story.split("## Pitch")[0]
    needs = []
    if not re.search(r"pitch line|synopsis", concept_text, re.I):
        needs.append((DESCRIPTION, "Tell Kav the story in a line, and roughly what happens"))
    elif not re.search(r"locked", story.split("## Pitch", 1)[1][:600] if "## Pitch" in story else "", re.I):
        needs.append(("In progress", "The story's shape isn't settled yet"))
    cover = sd / "package" / "cover.png"
    brief = [("brief", u) for _, u in links_in(state_md, r"brief")][-1:]
    out = [piece("story", "concept", "Concept", needs=needs, gens=[cover] if cover.is_file() else [],
                 text=concept_text, links=brief)]

    cards = sorted((sd / "storyboard").glob("ch[0-9]*.md"))
    concepts = sorted((sd / "storyboard").glob("*concept*.png"))
    missing = [c for c in ch_ids if not (sd / "storyboard" / f"{c}.md").is_file()]
    needs = []
    if not cards:
        needs.append(("Not started", "Plan the chapters"))
    elif missing:
        needs.append(("In progress", f"{len(missing)} chapter{'s' if len(missing) > 1 else ''} still to plan"))
    out.append(piece("story", "storyboard", "Storyboard", needs=needs, gens=concepts,
                     extra=storyboard_html(sd, story, ch_ids)))
    return out


def chapter_row(sd, n_hint):
    cards = {c.stem for c in (sd / "storyboard").glob("ch[0-9]*.md")}
    dirs = {d.name: d for d in (sd / "chapters").glob("ch[0-9]*") if d.is_dir()} if (sd / "chapters").is_dir() else {}
    ids = sorted(cards | set(dirs) | {f"ch{i:02d}" for i in range(1, n_hint + 1)})
    out = []
    for ch in ids:
        card = read(sd / "storyboard" / f"{ch}.md")
        d = dirs.get(ch)
        pages = [p for p in images(d / "pages") if re.match(r"p\d+\.", p.name)] if d else []
        drawn = d and ((d / "panels" / "candidates").is_dir() or list((d / "panels").glob("p*-panel*.png")))
        planned = d and ((d / "panels" / "plan.md").is_file() or (d / "script.md").is_file())
        readers = d and (d / "pages" / "reader-story.html").is_file()
        if readers and pages:
            needs = []
        elif pages:
            needs = [(PENDING, "Pages are drawn; Kav still has to build the reader")]
        elif drawn:
            needs = [("Being drawn", "Pictures are being picked and lettered")]
        elif planned:
            needs = [("Being written", "Scenes are planned; drawing hasn't started")]
        elif card:
            needs = [("Not started", "Planned on the storyboard; not written yet")]
        else:
            needs = [("Not started", "Not planned yet")]
        m = re.search(r"^#\s*Ch\s*\d+\s*[—–-]\s*(.+)$", card, re.M)
        links = links_in(read(d / "chapter-state.md")) if d else []
        links = [(lbl, u) for lbl, u in links if lbl in ("classic", "carousel", "story", "comic", "reader", "published", "site")]
        out.append(piece("chapter", ch, m.group(1).strip() if m else ch.replace("ch", "Chapter "),
                         needs=needs, pages=pages, text=field(card, "Synopsis"), links=links))
    return out, ids


# --- page ----------------------------------------------------------------------

def hints(slug):
    return {"cast": "To add someone, use /kav-character &lt;name&gt;",
            "location": "To add a place, use /kav-location &lt;name&gt;",
            "object": "To add an object, drop a photo in the chat and say “new object”",
            "style": "To add a look, use /kav-style &lt;name&gt; with 2–5 images",
            "story": f"To change the story, use /kav-kickoff {esc(slug)}",
            "chapter": "To write the next chapter, use /kav-chapter &lt;NN&gt;"}


ROWS = [("cast", "Cast"), ("location", "Locations"), ("object", "Objects"), ("style", "Styles"),
        ("story", "Story"), ("chapter", "Chapters")]

CHECK = ('<svg viewBox="0 0 16 16" width="12" height="12" aria-hidden="true"><path d="M3.5 8.5l3 3 6-7" fill="none" '
         'stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>')

CSS = """
:root{--bg:#f4f3f0;--surface:#ffffff;--ink:#1d2330;--soft:#6a7080;--line:#e2dfd8;--ready:#2e9d5b;--wait:#b6b9c1;--focus:#1f5fbf;
--display:"Karantina","Arial Narrow",system-ui,sans-serif;--body:"Varela Round","Segoe UI",system-ui,sans-serif;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#14171c;--surface:#1c2027;--ink:#e8eaee;--soft:#9aa0ac;--line:#2c323c;--ready:#43b872;--wait:#555b66;--focus:#7fb0ff;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#14171c;--surface:#1c2027;--ink:#e8eaee;--soft:#9aa0ac;--line:#2c323c;--ready:#43b872;--wait:#555b66;--focus:#7fb0ff;color-scheme:dark}
body{background:var(--bg);color:var(--ink);font-family:var(--body);padding-inline:16px;padding-block:20px 48px}
.wrap{max-width:1100px;margin:0 auto}
h1{font-family:var(--display);font-size:clamp(40px,7vw,64px);line-height:.95;margin:0 0 14px;text-wrap:balance}
.tabs{display:flex;gap:4px;border-bottom:1px solid var(--line);margin:0 0 22px}
.tabs button{all:unset;cursor:pointer;font-family:var(--display);font-size:28px;line-height:1;padding:6px 14px 8px;color:var(--soft);border-bottom:3px solid transparent;margin-bottom:-1px}
.tabs button[aria-selected="true"]{color:var(--ink);border-bottom-color:var(--ink)}
.tabs button:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
.tabs .n{font-family:var(--body);font-size:12px;vertical-align:4px;margin-inline-start:6px;padding:1px 7px;border-radius:999px;background:var(--line);color:var(--ink)}
section{margin-bottom:26px}
h2{font-family:var(--display);font-size:30px;line-height:1;margin:0;color:var(--soft)}
.hint{margin:2px 0 10px;font-size:12.5px;color:var(--soft)}
.none{font-size:13px;color:var(--soft);margin:0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(118px,1fr));gap:10px}
.tile{all:unset;box-sizing:border-box;cursor:pointer;display:flex;flex-direction:column;gap:6px;transition:transform .15s ease}
.tile .sq{position:relative;aspect-ratio:1/1;border-radius:10px;overflow:hidden;background:var(--surface);box-shadow:0 0 0 3px var(--wait)}
.tile.ready .sq{box-shadow:0 0 0 3px var(--ready)}
.tile.available .sq{box-shadow:0 0 0 1px var(--line)}
.tile .name{font-size:13px;line-height:1.3;text-align:center;unicode-bidi:plaintext;overflow-wrap:anywhere;color:var(--ink)}
.tile:hover{transform:translateY(-2px)}
.tile:focus-visible{outline:3px solid var(--focus);outline-offset:4px;border-radius:10px}
.tile img{width:100%;height:100%;object-fit:cover;display:block}
.tile:not(.ready):not(.available) img{filter:grayscale(1) opacity(.7)}
.tile .ph{width:100%;height:100%;display:grid;place-items:center;font-family:var(--display);font-size:44px;color:var(--wait);unicode-bidi:plaintext}
.tile .counts{position:absolute;top:6px;inset-inline-end:6px;display:flex;gap:3px}
.tile .counts span{min-width:14px;padding:1px 6px;border-radius:999px;font-size:11px;text-align:center;font-variant-numeric:tabular-nums}
.tile .counts .r{background:rgba(255,255,255,.92);color:#1d2330}
.tile .counts .g{background:rgba(20,23,28,.72);color:#fff}
.tile .lbl{position:absolute;bottom:6px;inset-inline-end:6px;font:10px/1 ui-monospace,Menlo,monospace;padding:3px 5px;border-radius:4px;
background:rgba(20,23,28,.6);color:#fff;letter-spacing:.03em}
.tile .ok{position:absolute;bottom:6px;inset-inline-start:6px;width:20px;height:20px;border-radius:5px;background:var(--ready);display:grid;place-items:center}
#panel{position:fixed;inset-block:0;inset-inline-end:0;width:min(480px,100%);background:var(--surface);border-inline-start:1px solid var(--line);
box-shadow:-12px 0 30px -18px rgba(0,0,0,.5);overflow-y:auto;padding:22px 20px 40px;padding-top:calc(22px + env(safe-area-inset-top,0px))}
#panel h3{font-family:var(--display);font-size:40px;line-height:.95;margin:0 36px 6px 0;unicode-bidi:plaintext}
#panel .state{font-size:14px;margin:0 0 12px;color:var(--soft)}
#panel .state.ok{color:var(--ready)}
#panel .close{all:unset;cursor:pointer;position:absolute;top:calc(14px + env(safe-area-inset-top,0px));inset-inline-end:14px;font-size:26px;line-height:1;color:var(--soft);padding:4px 8px;border-radius:6px}
#panel .close:focus-visible{outline:2px solid var(--focus)}
#panel ul{margin:0 0 14px;padding-inline-start:18px;display:flex;flex-direction:column;gap:5px;font-size:14.5px;line-height:1.45}
#panel .links{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 14px}
#panel .links a{font-size:13.5px;color:var(--focus);text-decoration:none;border:1px solid var(--line);border-radius:999px;padding:4px 12px}
#panel .links a:hover{border-color:var(--focus)}
#panel h4{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--soft);margin:16px 0 8px}
#panel .imgs{display:grid;grid-template-columns:repeat(auto-fill,minmax(118px,1fr));gap:8px}
#panel figure{margin:0}
#panel figure img{width:100%;border-radius:6px;display:block}
#panel figcaption{font:11px/1.4 ui-monospace,Menlo,monospace;color:var(--soft);margin-top:3px}
#panel .card{border-top:1px solid var(--line);padding-top:12px;margin-top:14px}
#panel .card h5{font-family:var(--display);font-size:26px;line-height:1;margin:0 0 8px;unicode-bidi:plaintext}
#panel .card img{width:100%;border-radius:6px;margin-bottom:8px}
#panel .card p,#panel .prose{font-size:14px;line-height:1.55;margin:0 0 6px;unicode-bidi:plaintext;white-space:pre-wrap}
#panel .missing{font-size:13px;color:var(--soft);font-style:italic;margin:0 0 6px}
#panel details{margin-top:14px}
#panel details summary{cursor:pointer;font-size:13px;color:var(--soft)}
#panel pre{white-space:pre-wrap;font-family:var(--body);font-size:13px;line-height:1.55;background:var(--bg);border-radius:8px;padding:12px;margin:8px 0 0;max-height:380px;overflow:auto;unicode-bidi:plaintext}
@media (prefers-reduced-motion:reduce){.tile{transition:none}}
"""

JS = """
const panel=document.getElementById('panel'),body=document.getElementById('panel-body');let last=null;
document.querySelectorAll('.tile').forEach(b=>b.addEventListener('click',()=>{const s=document.getElementById('d-'+b.dataset.id);if(!s)return;
last=b;body.innerHTML=s.innerHTML;panel.hidden=false;panel.scrollTop=0;panel.querySelector('.close').focus()}));
function closePanel(){panel.hidden=true;if(last)last.focus()}
panel.addEventListener('click',e=>{if(e.target.closest('.close'))closePanel()});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!panel.hidden)closePanel()});
const tabs=document.querySelectorAll('.tabs button');
function show(id){tabs.forEach(t=>{const on=t.dataset.tab===id;t.setAttribute('aria-selected',on);document.getElementById('tab-'+t.dataset.tab).hidden=!on});
if(id!=='map')panel.hidden=true;try{localStorage.setItem('kav-tab',id)}catch(e){}}
tabs.forEach(t=>t.addEventListener('click',()=>show(t.dataset.tab)));
let first='map';try{first=localStorage.getItem('kav-tab')||'map'}catch(e){}
show(location.hash==='#ideas'?'ideas':location.hash==='#map'?'map':first);
"""


def esc(s):
    return html.escape(str(s), quote=True)


def tile(p):
    cls = "ready" if p["state"] == "ready" else ("available" if p["state"] == "available" else "")
    why = {"ready": "ready", "available": "available, not used in this story"}.get(p["state"], p["state"])
    face = p["face"]
    src = thumb(face[1], 320) if face else None
    inner = f'<img alt="" src="{src}">' if src else f'<span class="ph" aria-hidden="true">{esc(p["name"][:1])}</span>'
    counts = (f'<span class="r" title="reference images">{p["n_ref"]}</span>' if p["n_ref"] else "") + \
             (f'<span class="g" title="made by Kav">✦ {p["n_gen"]}</span>' if p["n_gen"] else "")
    tip = f'{p["name"]} · {why} · {p["n_ref"]} reference, {p["n_gen"]} made by Kav'
    name = f'<span class="name" dir="auto">{esc(p["name"])}</span>' if p["row"] in ("cast", "location") else ""
    return (f'<button class="tile {cls}" data-id="{esc(p["id"])}" title="{esc(tip)}" aria-label="{esc(tip)}"><span class="sq">{inner}'
            + (f'<span class="counts">{counts}</span>' if counts else "")
            + (f'<span class="lbl">{esc(face[0])}</span>' if face and src else "")
            + (f'<span class="ok">{CHECK}</span>' if cls == "ready" else "") + f"</span>{name}</button>")


def detail(p):
    ok = p["state"] == "ready"
    state = {"ready": "Ready", "available": "Available style, not used in this story"}.get(p["state"], p["state"])
    parts = [f'<button class="close" aria-label="Close">×</button><h3 dir="auto">{esc(p["name"])}</h3>',
             f'<p class="state{" ok" if ok else ""}">{esc(state)}</p>']
    if p["needs"]:
        parts.append("<ul>" + "".join(f"<li>{esc(n)}</li>" for n in p["needs"]) + "</ul>")
    if p["links"]:
        parts.append('<div class="links">' + "".join(
            f'<a href="{esc(u)}" target="_blank" rel="noopener">{esc(lbl.capitalize())} ↗</a>' for lbl, u in p["links"]) + "</div>")
    for kind, title in (("ref", "Reference images"), ("gen", "Made by Kav"), ("page", "Pages")):
        figs = "".join(f'<figure><img alt="" loading="lazy" src="{u}"><figcaption>{esc(lbl)}</figcaption></figure>'
                       for lbl, path, k in p["images"] if k == kind for u in [thumb(path, 420)] if u)
        if figs:
            parts.append(f'<h4>{title}</h4><div class="imgs">{figs}</div>')
    if p["extra"]:
        parts.append(p["extra"])
    elif p["text"].strip():
        parts.append(f'<details><summary>From the file</summary><pre dir="auto">{esc(p["text"].strip()[:4000])}</pre></details>')
    return f'<div hidden id="d-{esc(p["id"])}">{"".join(parts)}</div>'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--story", required=True, help="slug under this repo's stories/, or a path to any story folder")
    ap.add_argument("--out")
    a = ap.parse_args()
    sd = Path(a.story).expanduser().resolve() if "/" in a.story else REPO / "stories" / a.story
    if not sd.is_dir():
        sys.exit(f"No such story: {sd}")
    repo = sd.parent.parent
    slug = sd.name
    briefs = json.loads(read(sd / "briefs.json") or "{}")
    meta = json.loads(read(sd / "story.json") or "{}")
    story_md = read(sd / "story.md")
    title = meta.get("title") or heading(story_md, slug).split("(")[0].strip()
    pack = (briefs.get("defaults", {}) or {}).get("style_pack", "")
    m = re.search(r"(\d+)\s*chapters", story_md + read(sd / "kickoff-state.md"))
    n_hint = int(m.group(1)) if m else 0

    cast = cast_row(sd, briefs, pack)
    principals = [p["id"].split("-", 1)[1] for p in cast
                  if re.search(r"class:\**\s*principal", p["text"], re.I) and (sd / "cast" / p["id"].split("-", 1)[1]).is_dir()]
    chapters, ch_ids = chapter_row(sd, n_hint)
    rows = {"cast": cast, "location": place_row(sd, briefs, "locations", "locations"),
            "object": place_row(sd, briefs, "objects", "objects"), "style": style_row(sd, repo, briefs, principals),
            "story": story_row(sd, ch_ids), "chapter": chapters}

    hint = hints(slug)
    sections = "".join(
        f'<section><h2>{label}</h2><p class="hint">{hint[k]}</p>'
        + (f'<div class="grid">{"".join(tile(p) for p in rows[k])}</div>' if rows[k] else '<p class="none">None yet</p>')
        + "</section>" for k, label in ROWS)
    details = "".join(detail(p) for ps in rows.values() for p in ps)
    ideas_html, ideas_css, ideas_js, n_ideas = ideas_section(sd)
    page = f"""<meta charset="utf-8">
<title>{esc(title)} · World Map</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Karantina:wght@700&family=Varela+Round&display=swap">
<style>{CSS}{ideas_css}</style>
<div class="wrap"><h1 dir="auto">{esc(title)}</h1>
<nav class="tabs" role="tablist"><button role="tab" data-tab="map" aria-selected="true">Map</button>
<button role="tab" data-tab="ideas" aria-selected="false">Ideas<span class="n" id="ideas-count" data-n="{n_ideas}">{n_ideas}</span></button></nav>
<div id="tab-map" role="tabpanel">{sections}</div>
<div id="tab-ideas" role="tabpanel" hidden>{ideas_html}</div></div>
<aside id="panel" hidden><div id="panel-body"></div></aside>
{details}
<script>{JS}</script>
<script>{ideas_js}</script>
"""
    out = Path(a.out) if a.out else sd / "package" / "story-map.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    manifest = {p["id"]: {"name": p["name"], "row": p["row"], "state": p["state"],
                          "images": {lbl: str(path.relative_to(sd)) if path.is_relative_to(sd) else str(path)
                                     for lbl, path, _ in p["images"]}}
                for ps in rows.values() for p in ps}
    out.with_suffix(".json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    all_p = [p for ps in rows.values() for p in ps]
    ready = sum(p["state"] == "ready" for p in all_p)
    print(f"{out} · {ready} of {len(all_p)} ready · {len(page) // 1024} KB")
    for p in all_p:
        if p["state"] not in ("ready", "available"):
            print(f"  {p['row']:9} {p['name']}: {p['state']}")


if __name__ == "__main__":
    main()
