#!/usr/bin/env python3
"""Render a story's board: an Overview tab (one square per piece, green check when
ready, grey when not) and an Ideas tab (the notes, plus a box to pin a new one).

Overview rows: cast, locations, objects, styles (the one in use, every custom pack,
and any that ship with Kav), the story (concept, storyboard), chapters. A square shows
the piece and its name, with two counts: reference images the author gave (white) and
images Kav made (dark). Hover says why a grey square isn't ready; click for a short
description, what to do next as copyable commands, the images, links, and the file.

story-map.json beside the page lists every piece's images in the order they're shown,
so "the second photo of Oren" resolves to a real file.

  python3 tools/build_map.py --story <slug | path/to/stories/slug> [--out <file.html>]
"""
import argparse
import hashlib
import html
import json
import re
import subprocess
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


# --- small readers -------------------------------------------------------------

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
    body = re.sub(r"^\*?\((?:the author'?s? (?:own )?lines?|[^)]*verbatim)[^)]*\)\*?\s*>?\s*", "", body, flags=re.I).strip(" >*")
    return "" if body.lower().startswith(("(open", "(omitted", "<")) else body


def section(text, word):
    m = re.search(r"^(#{2,4})[^\n]*" + re.escape(word) + r"[^\n]*\n(.*?)(?=^#{1,4}\s|\Z)", text, re.M | re.S | re.I)
    return m.group(2).strip() if m else ""


def pitch_line(story):
    m = re.search(r"Pitch line\**\s*(?:[—–:-]\s*)?(.*?)(?:\n\s*\n|\n\d+\.)", story, re.S | re.I)
    return re.sub(r"\s+", " ", m.group(1)).strip(" *—-") if m else ""


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


def need(reason, text, cmd=None, *alts):
    return {"reason": reason, "text": text, "cmd": cmd, "alts": list(alts)}


def piece(row, pid, name, *, needs=(), state=None, refs=(), gens=(), pages=(), face=None, text="", source=None,
          links=(), extra="", about="", extras=(), tile_text="", placeholder="+"):
    needs = list(needs)
    if state is None:
        reasons = [n["reason"] for n in needs]
        state = next((r for r in (IMAGES, DESCRIPTION, PENDING) if r in reasons), reasons[0] if reasons else "ready")
    refs, gens, pages = list(refs), list(gens), list(pages)
    face = face or (gens[0] if gens else None) or (refs[0] if refs else None) or (pages[0] if pages else None)
    return {"row": row, "id": pid, "name": name, "state": state, "needs": needs, "refs": refs, "gens": gens,
            "pages": pages, "face": face, "text": text, "source": source, "links": list(links), "extra": extra,
            "about": about, "extras": list(extras), "tile_text": tile_text, "placeholder": placeholder}


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
        out.append(cast_piece(sd, md.stem, text, keys, chars, pack, md))
    for k in chars:
        if k not in claimed and k not in stems:
            out.append(cast_piece(sd, k, "", [k], chars, pack, sd / "briefs.json"))
    return out


def cast_piece(sd, stem, text, keys, chars, pack, src):
    principal = bool(re.search(r"class:\**\s*principal", text, re.I))
    full = principal and not re.search(r"depth:\s*(sketch|light)", text, re.I)
    as_is = bool(re.search(r"complete as is", text, re.I))
    refs, gens = [], []
    for k in keys or [stem]:
        d = sd / "cast" / k
        refs += sorted(p for p in d.glob("source*") if p.suffix.lower() in IMG) if d.is_dir() else []
        gens += [d / pack / f"{s}.png" for s in SHOTS if pack and (d / pack / f"{s}.png").is_file()]
        gens += [d / f"{s}.png" for s in SHOTS if (d / f"{s}.png").is_file()]
    refs += [sd / r for r in re.findall(r"cast/images/[\w.\-]+", text) if (sd / r).is_file()]
    refs, gens = unique(refs), unique(gens)

    name = heading(text, stem)
    one_liner = field(text, "Who they are") or field(text, "What they are") or field(text, "Bio")
    look = next((chars[k] for k in keys if k in chars), "") or field(text, "Appearance")
    dna = [(s, field(text, s)) for s in DNA if field(text, s)]
    about = "\n".join([one_liner] + [f"{s}: {v}" for s, v in dna]) if (one_liner or dna) else ""

    c = f"/kav-character {name}"
    skip = ("To skip this step", f"{c} complete as is")
    needs = []
    if not refs:
        needs.append(need(IMAGES, "To complete this character, run this and drop a few photos in the chat, or any picture that shows the look", c))
    if not as_is:
        if not one_liner and (text or not look):
            needs.append(need(DESCRIPTION, "To complete this character, add a line on who they are",
                              f"{c} <who they are, in one line>", skip))
        elif full and not dna:
            needs.append(need(DESCRIPTION, "To complete this character, tell Kav what they want and what trips them up",
                              f"{c} build a dna", skip))
    if refs and not keys:
        needs.append(need(PENDING, "Kav still has to set them up for drawing", c))
    elif principal and refs and not gens:
        needs.append(need(PENDING, "Kav still has to build their portraits", c))
    elif principal and pack and keys and not all((sd / "cast" / k / pack / "front.png").is_file() for k in keys):
        needs.append(need(PENDING, f"Kav still has to build their portraits in the {pack} style", f"/kav-visual-style-lock {pack}"))
    extras = []
    if principal and not full and not dna:
        extras.append(("You can also build their full DNA for a complete personality. It helps Kav come up with better "
                       "story and dialogue ideas for them.", f"{c} build a dna"))
    face = next((g for g in gens if g.name == "front.png" and pack and g.parent.name == pack), None) or \
        next((g for g in gens if g.name == "front.png"), None)
    return piece("cast", f"cast-{stem}", name, needs=needs, refs=refs, gens=gens, face=face, text=text, source=src,
                 about=about or look, extras=extras)


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
        out.append(place_piece(sd, section_key, md.stem, text, keys, reg, reg_photos, own, md))
    for k in reg:
        if k not in claimed and k not in stems:
            out.append(place_piece(sd, section_key, k, "", [k], reg, reg_photos, [], sd / "briefs.json"))
    return out


def place_piece(sd, section_key, stem, text, keys, reg, reg_photos, own, src):
    photos = unique([p for k in keys for p in reg_photos.get(k, [])] + own)
    gens = [p for p in photos if re.search(r"ch\d\d", p.stem)]
    refs = [p for p in photos if p not in gens]
    name = heading(text, stem)
    what = field(text, "What it is") or next(((reg.get(k) or {}).get("description", "") for k in keys if reg.get(k)), "")
    turf = field(text, "Whose turf")
    as_is = bool(re.search(r"complete as is", text, re.I))
    loc = section_key == "locations"
    c = f"/kav-location {name}" if loc else f"new object: {name}"
    needs = []
    if not refs:
        needs.append(need(IMAGES, "To complete this place, run this and drop its photos in the chat" if loc
                          else "To complete this object, drop a photo of it in the chat with this", c))
    if not (text or what) and not as_is:
        needs.append(need(DESCRIPTION, "Add a line on what it is", f"{c} <what it is, in one line>" if loc else c,
                          ("To skip this step", f"{c} complete as is") if loc else None))
    if refs and not keys:
        needs.append(need(PENDING, "Kav still has to set it up for drawing", c))
    row = "location" if loc else "object"
    return piece(row, f"{row}-{stem}", name, needs=needs, refs=refs, gens=gens, face=refs[0] if refs else None,
                 text=text, source=src, about="\n".join(x for x in (what, turf and f"Whose turf: {turf}") if x))


# --- styles ----------------------------------------------------------------------

def shipped(repo):
    try:
        out = subprocess.run(["git", "-C", str(repo), "ls-files", "styles"], capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return set()
    return {Path(line).parts[1] for line in out.splitlines() if len(Path(line).parts) > 2}


def style_row(sd, repo, briefs, principals):
    active = (briefs.get("defaults", {}) or {}).get("style_pack", "")
    style = read(sd / "style" / "style.md")
    builtin = shipped(repo)
    packs = {}
    for base in (repo / "styles", sd / "styles"):
        if base.is_dir():
            for p in sorted(base.iterdir()):
                if p.is_dir() and images(p):
                    packs.setdefault(p.name, p)
    out = []
    for name, p in sorted(packs.items(), key=lambda kv: (kv[0] != active, kv[0] in builtin, kv[0])):
        refs = images(p)
        kind = "built in" if name in builtin else "custom"
        medium = read(p / "medium.txt").strip()
        if name != active:
            out.append(piece("style", f"style-{name}", name, state="available", refs=refs, text=medium, source=p / "medium.txt",
                             about=medium, tile_text=kind))
            continue
        samples = [s for s in images(sd / "style" / "samples") if "old" not in s.stem]
        needs = []
        if "locked" not in style.lower()[:600]:
            needs.append(need(PENDING, "The look hasn't been tested and locked yet", f"/kav-visual-style-lock {name}"))
        missing = [k for k in principals if not (sd / "cast" / k / name / "front.png").is_file()]
        if missing:
            needs.append(need(PENDING, f"Portraits in this style still to build: {', '.join(missing)}",
                              f"/kav-visual-style-lock {name}"))
        look = field(style, "The look") or medium
        out.append(piece("style", f"style-{name}", name, needs=needs, refs=refs, gens=samples,
                         face=samples[0] if samples else (refs[0] if refs else None), text=style,
                         source=sd / "style" / "style.md", about=look, tile_text=f"{kind} · in use"))
    if not out:
        out.append(piece("style", "style-none", "Style",
                         needs=[need(IMAGES, "Pick a style, or add 2–5 images of the look you want", "/kav-style <name>")]))
    return out


# --- story and chapters ------------------------------------------------------------

def chapter_face(sd, ch):
    for pat in (f"style/samples/brief-{ch}.*", f"storyboard/{ch}-concept*", f"style/samples/{ch}-concept*"):
        hits = [p for p in sorted(sd.glob(pat)) if p.suffix.lower() in IMG and "old" not in p.stem]
        if hits:
            return hits[0]
    panels = sd / "chapters" / ch / "panels"
    for p in (panels / f"p01-panel1.png", *sorted(panels.glob("p01-panel*.png"))):
        if p.is_file():
            return p
    pages = images(sd / "chapters" / ch / "pages")
    return next((p for p in pages if re.match(r"p\d+\.", p.name)), None)


def storyboard_html(sd, story, ch_ids):
    parts = []
    for label, body in (("Shape", section(story, "Shape")), ("Intention and obstacle", section(story, "I/O"))):
        parts.append(f"<h4>{label}</h4>" + (f'<div class="prose" dir="auto">{esc(body[:1400])}</div>' if body else
                                             '<p class="missing">Not written yet</p>'))
    board = read(sd / "storyboard" / "storyboard.md")
    if board:
        parts.append(f'<details><summary>The whole storyboard</summary><pre dir="auto">{esc(board[:5000])}</pre></details>')
    for ch in ch_ids:
        card = read(sd / "storyboard" / f"{ch}.md")
        m = re.search(r"^#\s*Ch\s*\d+\s*[—–-]\s*(.+)$", card, re.M)
        title = m.group(1).strip() if m else ""
        art = chapter_face(sd, ch)
        src = thumb(art, 480) if art else None
        rows = [("Question", field(card, "Chapter question")), ("Intention and obstacle", field(card, "Chapter I/O")),
                ("Synopsis", field(card, "Synopsis"))]
        body = "".join(f'<p dir="auto"><b>{k}:</b> {esc(v)}</p>' if v else f'<p class="missing">{k}: not written yet</p>'
                       for k, v in rows)
        img = f'<img alt="" loading="lazy" src="{src}">' if src else '<p class="missing">No concept art yet</p>'
        head = f'<h5 dir="auto">{esc(ch[2:])}{" · " + esc(title) if title else ""}</h5>'
        parts.append(f'<div class="card">{head}{img}{body}</div>' if card else
                     f'<div class="card">{head}<p class="missing">Not planned yet</p></div>')
    return "".join(parts)


def story_row(sd, slug, ch_ids):
    story = read(sd / "story.md")
    state_md = read(sd / "kickoff-state.md")
    concept_text = story.split("## Pitch")[0]
    line = pitch_line(story)
    synopsis = section(concept_text, "Synopsis") or field(concept_text, "Synopsis")
    k = f"/kav-kickoff {slug}"
    needs = []
    if not line and not synopsis:
        needs.append(need(DESCRIPTION, "Tell Kav the story in a line, and roughly what happens", k))
    elif not re.search(r"locked", story.split("## Pitch", 1)[1][:600] if "## Pitch" in story else "", re.I):
        needs.append(need("In progress", "The story's shape isn't settled yet", k))
    brief = [("brief", u) for _, u in links_in(state_md, r"brief")][-1:]
    cover = sd / "package" / "cover.png"
    out = [piece("story", "concept", "Concept", needs=needs, gens=[cover] if cover.is_file() else [], face=None,
                 text=concept_text, source=sd / "story.md", links=brief, about=line or synopsis,
                 tile_text=line or synopsis[:200])]

    cards = sorted((sd / "storyboard").glob("ch[0-9]*.md"))
    missing = [c for c in ch_ids if not (sd / "storyboard" / f"{c}.md").is_file()]
    needs = []
    if not cards:
        needs.append(need("Not started", "Plan the chapters", k))
    elif missing:
        needs.append(need("In progress", f"{len(missing)} chapter{'s' if len(missing) > 1 else ''} still to plan", k))
    arts = [a for a in (chapter_face(sd, c) for c in ch_ids) if a]
    out.append(piece("story", "storyboard", "Storyboard", needs=needs, gens=arts,
                     source=(sd / "storyboard" / "storyboard.md") if (sd / "storyboard" / "storyboard.md").is_file() else None,
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
        c = f"/kav-chapter {ch[2:]}"
        if readers and pages:
            needs = []
        elif pages:
            needs = [need(PENDING, "Pages are drawn; Kav still has to build the reader", "/kav-publish")]
        elif drawn:
            needs = [need("Being drawn", "Pictures are being picked and lettered", c)]
        elif planned:
            needs = [need("Being written", "Scenes are planned; drawing hasn't started", c)]
        elif card:
            needs = [need("Not started", "Planned on the storyboard; not written yet", c)]
        else:
            needs = [need("Not started", "Not planned yet", f"/kav-kickoff {sd.name}")]
        m = re.search(r"^#\s*Ch\s*\d+\s*[—–-]\s*(.+)$", card, re.M)
        links = links_in(read(d / "chapter-state.md")) if d else []
        links = [(lbl, u) for lbl, u in links if lbl in ("classic", "carousel", "story", "comic", "reader", "published", "site")]
        face = chapter_face(sd, ch)
        out.append(piece("chapter", ch, ch[2:], needs=needs, pages=pages, face=face,
                         gens=[face] if face and face not in pages else [], text=card,
                         source=(sd / "storyboard" / f"{ch}.md") if card else None, links=links,
                         about="\n".join(x for x in ((m.group(1).strip() if m else ""), field(card, "Synopsis")) if x),
                         placeholder=ch[2:]))
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
:root{--bg:#f4f3f0;--surface:#ffffff;--ink:#1d2330;--soft:#6a7080;--line:#e2dfd8;--ready:#2e9d5b;--wait:#b6b9c1;--focus:#1f5fbf;--code:#f0eee9;
--display:"Karantina","Arial Narrow",system-ui,sans-serif;--body:"Varela Round","Segoe UI",system-ui,sans-serif;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#14171c;--surface:#1c2027;--ink:#e8eaee;--soft:#9aa0ac;--line:#2c323c;--ready:#43b872;--wait:#555b66;--focus:#7fb0ff;--code:#252a33;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#14171c;--surface:#1c2027;--ink:#e8eaee;--soft:#9aa0ac;--line:#2c323c;--ready:#43b872;--wait:#555b66;--focus:#7fb0ff;--code:#252a33;color-scheme:dark}
*,*::before,*::after{box-sizing:border-box}
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
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(118px,1fr));gap:14px 10px}
.tile{all:unset;box-sizing:border-box;cursor:pointer;display:flex;flex-direction:column;gap:6px;transition:transform .15s ease}
.tile .sq{position:relative;aspect-ratio:1/1;border-radius:10px;overflow:hidden;background:var(--surface);box-shadow:0 0 0 3px var(--wait)}
.tile.ready .sq{box-shadow:0 0 0 3px var(--ready)}
.tile.available .sq{box-shadow:0 0 0 1px var(--line)}
.tile .name{font-size:13px;line-height:1.3;text-align:center;unicode-bidi:plaintext;overflow-wrap:anywhere;color:var(--ink)}
.tile .kind{display:block;font-size:11px;color:var(--soft)}
.tile:hover{transform:translateY(-2px)}
.tile:focus-visible{outline:3px solid var(--focus);outline-offset:4px;border-radius:10px}
.tile img{width:100%;height:100%;object-fit:cover;display:block}
.tile:not(.ready):not(.available) img{filter:grayscale(1) opacity(.7)}
.tile .ph{width:100%;height:100%;display:grid;place-items:center;font-family:var(--display);font-size:44px;color:var(--wait)}
.tile .txt{position:absolute;inset:0;padding:12px;font-size:13px;line-height:1.45;color:var(--ink);unicode-bidi:plaintext;text-align:start;
display:-webkit-box;-webkit-line-clamp:6;-webkit-box-orient:vertical;overflow:hidden;text-overflow:ellipsis}
.tile .txt::after{content:""}
.tile .counts{position:absolute;top:6px;inset-inline-end:6px;display:flex;gap:3px}
.tile .counts span{min-width:14px;padding:1px 6px;border-radius:999px;font-size:11px;text-align:center;font-variant-numeric:tabular-nums}
.tile .counts .r{background:rgba(255,255,255,.92);color:#1d2330}
.tile .counts .g{background:rgba(20,23,28,.72);color:#fff}
.tile .ok{position:absolute;bottom:6px;inset-inline-start:6px;width:20px;height:20px;border-radius:5px;background:var(--ready);display:grid;place-items:center}
#panel{position:fixed;inset-block:0;inset-inline-end:0;width:min(480px,100%);background:var(--surface);border-inline-start:1px solid var(--line);
box-shadow:-12px 0 30px -18px rgba(0,0,0,.5);overflow-y:auto;overflow-x:hidden;padding:22px 20px 40px;padding-top:calc(22px + env(safe-area-inset-top,0px))}
#panel h3{font-family:var(--display);font-size:40px;line-height:.95;margin:0 36px 10px 0;unicode-bidi:plaintext;overflow-wrap:anywhere}
#panel .ok-line{font-size:14px;margin:0 0 12px;color:var(--ready)}
#panel .close{all:unset;cursor:pointer;position:absolute;top:calc(14px + env(safe-area-inset-top,0px));inset-inline-end:14px;font-size:26px;line-height:1;color:var(--soft);padding:4px 8px;border-radius:6px}
#panel .close:focus-visible,#panel button:focus-visible{outline:2px solid var(--focus)}
#panel .about{font-size:14.5px;line-height:1.55;white-space:pre-wrap;unicode-bidi:plaintext;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;margin:0}
#panel .about.open{display:block}
#panel .more{all:unset;cursor:pointer;font-size:13px;color:var(--focus);margin:4px 0 14px;display:inline-block}
#panel .todo{background:var(--bg);border-radius:10px;padding:12px 14px;margin:0 0 16px}
#panel .todo h4{margin-top:0}
#panel .todo p{font-size:14px;line-height:1.45;margin:10px 0 6px}
#panel .todo p:first-of-type{margin-top:0}
#panel .todo p.alt{color:var(--soft);font-size:13px}
#panel .cmd{display:flex;align-items:stretch;gap:6px}
#panel .cmd code{flex:1;min-width:0;font:13px/1.4 ui-monospace,Menlo,monospace;background:var(--code);border:1px solid var(--line);border-radius:6px;padding:7px 9px;overflow-wrap:anywhere;unicode-bidi:plaintext}
#panel .cmd button{font:inherit;font-size:12.5px;border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:6px;padding:0 10px;cursor:pointer}
#panel .links{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 14px}
#panel .links a{font-size:13.5px;color:var(--focus);text-decoration:none;border:1px solid var(--line);border-radius:999px;padding:4px 12px}
#panel .links a:hover{border-color:var(--focus)}
#panel h4{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--soft);margin:16px 0 8px}
#panel .imgs{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:8px}
#panel .imgs img{width:100%;border-radius:6px;display:block}
#panel .card{border-top:1px solid var(--line);padding-top:12px;margin-top:14px}
#panel .card h5{font-family:var(--display);font-size:26px;line-height:1;margin:0 0 8px;unicode-bidi:plaintext}
#panel .card img{width:100%;border-radius:6px;margin-bottom:8px}
#panel .card p,#panel .prose{font-size:14px;line-height:1.55;margin:0 0 6px;unicode-bidi:plaintext;white-space:pre-wrap}
#panel .missing{font-size:13px;color:var(--soft);font-style:italic;margin:0 0 6px}
#panel details{margin-top:18px}
#panel details summary{cursor:pointer;font:12px/1.4 ui-monospace,Menlo,monospace;color:var(--soft);overflow-wrap:anywhere}
#panel pre{white-space:pre-wrap;font-family:var(--body);font-size:13px;line-height:1.55;background:var(--bg);border-radius:8px;padding:12px;margin:8px 0 0;max-height:380px;overflow:auto;unicode-bidi:plaintext}
@media (prefers-reduced-motion:reduce){.tile{transition:none}}
"""

JS = """
const panel=document.getElementById('panel'),body=document.getElementById('panel-body');let last=null;
document.querySelectorAll('.tile').forEach(b=>b.addEventListener('click',()=>{const s=document.getElementById('d-'+b.dataset.id);if(!s)return;
last=b;body.innerHTML=s.innerHTML;panel.hidden=false;panel.scrollTop=0;
const a=body.querySelector('.about'),m=body.querySelector('.more');if(a&&m)m.hidden=a.scrollHeight<=a.clientHeight+2;
panel.querySelector('.close').focus()}));
function closePanel(){panel.hidden=true;if(last)last.focus()}
panel.addEventListener('click',e=>{
  if(e.target.closest('.close')){closePanel();return}
  const more=e.target.closest('.more');if(more){const a=body.querySelector('.about');const open=a.classList.toggle('open');more.textContent=open?'Show less':'Read more';return}
  const b=e.target.closest('.cmd button');if(!b)return;const code=b.previousElementSibling,t=code.textContent;
  const done=()=>{b.textContent='Copied';setTimeout(()=>b.textContent='Copy',1400)};
  const pick=()=>{const r=document.createRange();r.selectNodeContents(code);const s=getSelection();s.removeAllRanges();s.addRange(r)};
  try{navigator.clipboard.writeText(t).then(done,pick)}catch(_){pick()}
});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!panel.hidden)closePanel()});
const tabs=document.querySelectorAll('.tabs button');
function show(id){tabs.forEach(t=>{const on=t.dataset.tab===id;t.setAttribute('aria-selected',on);document.getElementById('tab-'+t.dataset.tab).hidden=!on});
if(id!=='overview')panel.hidden=true;try{localStorage.setItem('kav-tab',id)}catch(e){}}
tabs.forEach(t=>t.addEventListener('click',()=>show(t.dataset.tab)));
let first='overview';try{first=localStorage.getItem('kav-tab')||'overview'}catch(e){}
if(first!=='ideas')first='overview';
show(location.hash==='#ideas'?'ideas':(location.hash==='#overview'||location.hash==='#map')?'overview':first);
"""


def esc(s):
    return html.escape(str(s), quote=True)


def tile(p):
    cls = "ready" if p["state"] == "ready" else ("available" if p["state"] == "available" else "")
    why = {"ready": "ready", "available": "available, not used in this story"}.get(p["state"], p["state"])
    src = thumb(p["face"], 320) if p["face"] else None
    if p["row"] == "story" and p["id"] == "concept" and p["tile_text"]:
        inner = f'<span class="txt" dir="auto">{esc(p["tile_text"])}</span>'
    elif src:
        inner = f'<img alt="" src="{src}">'
    else:
        inner = f'<span class="ph" aria-hidden="true">{esc(p["placeholder"])}</span>'
    n_gen = len(p["gens"]) + len(p["pages"])
    counts = (f'<span class="r">{len(p["refs"])}</span>' if p["refs"] else "") + \
             (f'<span class="g">{n_gen}</span>' if n_gen else "")
    tip = f'{p["name"]} · {why}' + (f' · {len(p["refs"])} reference, {n_gen} made by Kav' if p["refs"] or n_gen else "")
    kind = f'<span class="kind">{esc(p["tile_text"])}</span>' if p["row"] == "style" and p["tile_text"] else ""
    return (f'<button class="tile {cls}" data-id="{esc(p["id"])}" title="{esc(tip)}" aria-label="{esc(tip)}"><span class="sq">{inner}'
            + (f'<span class="counts">{counts}</span>' if counts and p["id"] != "concept" else "")
            + (f'<span class="ok">{CHECK}</span>' if cls == "ready" else "")
            + f'</span><span class="name" dir="auto">{esc(p["name"])}{kind}</span></button>')


def cmdbox(cmd):
    return f'<div class="cmd"><code dir="ltr">{esc(cmd)}</code><button type="button">Copy</button></div>'


def detail(p):
    parts = [f'<button class="close" aria-label="Close">×</button><h3 dir="auto">{esc(p["name"])}</h3>']
    if p["state"] == "ready":
        parts.append('<p class="ok-line">✓ Ready</p>')
    elif p["state"] == "available":
        parts.append('<p class="ok-line" style="color:var(--soft)">Available, not used in this story</p>')
    if p["about"]:
        parts.append(f'<p class="about" dir="auto">{esc(p["about"].strip())}</p><button class="more" type="button">Read more</button>')
    if p["needs"] or p["extras"]:
        todo = []
        for n in p["needs"]:
            todo.append(f'<p dir="auto">{esc(n["text"])}</p>' + (cmdbox(n["cmd"]) if n["cmd"] else ""))
            for alt in n["alts"]:
                if alt:
                    todo.append(f'<p class="alt">{esc(alt[0])}</p>' + (cmdbox(alt[1]) if alt[1] else ""))
        for text, cmd in p["extras"]:
            todo.append(f'<p class="alt">{esc(text)}</p>' + cmdbox(cmd))
        parts.append(f'<div class="todo"><h4>{"To do" if p["needs"] else "Optional"}</h4>{"".join(todo)}</div>')
    if p["links"]:
        parts.append('<div class="links">' + "".join(
            f'<a href="{esc(u)}" target="_blank" rel="noopener">{esc(lbl.capitalize())} ↗</a>' for lbl, u in p["links"]) + "</div>")
    for items, title in ((p["refs"], "Reference images"), (p["gens"], "Made by Kav"), (p["pages"], "Pages")):
        figs = "".join(f'<img alt="" loading="lazy" src="{u}">' for u in (thumb(i, 420) for i in items) if u)
        if figs:
            parts.append(f'<h4>{title}</h4><div class="imgs">{figs}</div>')
    if p["extra"]:
        parts.append(p["extra"])
    if p["source"] and (p["text"].strip() or Path(p["source"]).is_file()):
        body = p["text"].strip() or read(p["source"]).strip()
        parts.append(f'<details><summary>{esc(p["source"])}</summary><pre dir="auto">{esc(body[:5000])}</pre></details>')
    return f'<div hidden id="d-{esc(p["id"])}">{"".join(parts)}</div>'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--story", required=True, help="slug under this repo's stories/, or a path to any story folder")
    ap.add_argument("--out")
    a = ap.parse_args()
    sd = Path(a.story).expanduser().resolve() if "/" in a.story else (REPO / "stories" / a.story).resolve()
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
            "story": story_row(sd, slug, ch_ids), "chapter": chapters}

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
<nav class="tabs" role="tablist"><button role="tab" data-tab="overview" aria-selected="true">Overview</button>
<button role="tab" data-tab="ideas" aria-selected="false">Ideas<span class="n" id="ideas-count" data-n="{n_ideas}">{n_ideas}</span></button></nav>
<div id="tab-overview" role="tabpanel">{sections}</div>
<div id="tab-ideas" role="tabpanel" hidden>{ideas_html}</div></div>
<aside id="panel" hidden><div id="panel-body"></div></aside>
{details}
<script>{JS}</script>
<script>{ideas_js}</script>
"""
    out = Path(a.out) if a.out else sd / "package" / "story-map.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")

    def rel(x):
        return str(x.relative_to(sd)) if x.is_relative_to(sd) else str(x)

    manifest = {p["id"]: {"name": p["name"], "row": p["row"], "state": p["state"],
                          "source": str(p["source"]) if p["source"] else None,
                          "reference_images": [rel(x) for x in p["refs"]],
                          "made_by_kav": [rel(x) for x in p["gens"]], "pages": [rel(x) for x in p["pages"]]}
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
