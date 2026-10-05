#!/usr/bin/env python3
"""Visual Calibration Lock: nine stress-test images, rated, with the author's ratings on top.

The question is never "is this model any good". It is: **given this story's cast, locations
and style pack, can we generate an image that works as a page of this book, reliably?**
Nine scenes chosen to push on the things that break — one, two, three and four characters,
every location, day and night, and the moods and poses the story actually calls for.

Four things are rated, each out of five:
  Consistency  faces match their mug shots, and match the other good takes
  Style        the pack's look, and the same look across the nine
  Adherence    what the line asked for is what is in the frame
  Quality      no broken bodies, no artefacts, nothing the eye snags on

Kav rates every image before the author sees it; the author overrides any rating and adds
feedback. A superseded take moves to Previous Generations with the reason it was replaced,
so an iteration is visible rather than silently overwritten.

  python3 tools/calibrate.py --story <slug> [--only c4,c7] [--static out.html]

Scenes come from stories/<slug>/style/calibration.json; state (images, ratings, feedback,
history) lives in stories/<slug>/style/calibration-state.json.
"""
import argparse
import html as H
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kav_env import REPO  # noqa: E402

CATS = [
    ("consistency", "Consistency",
     "Do the cast look like their mug shots — and like themselves in the other images here? "
     "Does the place match its reference?"),
    ("style", "Style",
     "Is this the book's look, and is it the same look across all nine? Line weight, palette, "
     "how flat or rendered."),
    ("adherence", "Adherence",
     "Did we get what the line asked for? If it says smiling, he is smiling; if it says holding "
     "a slice, he is holding one."),
    ("quality", "Quality",
     "Anything the eye snags on: broken hands, fused bodies, melted faces, stray artefacts."),
]
THRESHOLD = 3.0      # below this, an image is not usable as a page
FLOOR = 2.0          # "unacceptable for use"


# --- state ------------------------------------------------------------------

def paths(story):
    d = REPO / "stories" / story / "style"
    return d / "calibration.json", d / "calibration-state.json"


def load_state(story):
    _, sp = paths(story)
    if sp.exists():
        return json.loads(sp.read_text(encoding="utf-8"))
    return {"story": story, "confirmed": False, "images": []}


def save_state(story, state):
    _, sp = paths(story)
    sp.parent.mkdir(parents=True, exist_ok=True)
    sp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        build_face(story, state)
    except Exception:
        pass       # the face is a convenience for the Story Tool, never a reason to lose ratings


def build_face(story, state):
    """A 2x2 of the two best and the two worst takes, for the Story Tool's tile.

    Best and worst together, because a tile that shows only the good ones says the
    calibration passed when it has not.
    """
    from PIL import Image

    rated = sorted((i for i in state["images"] if i.get("path") and blended(i)),
                   key=blended, reverse=True)
    if len(rated) < 4:
        return None
    picks = rated[:2] + rated[-2:]
    cell = 420
    sheet = Image.new("RGB", (cell * 2, cell * 2), "#f7efe2")
    for n, img in enumerate(picks):
        im = Image.open(img["path"]).convert("RGB")
        side = min(im.size)
        im = im.crop(((im.width - side) // 2, 0, (im.width + side) // 2, side))
        im = im.resize((cell, cell), Image.LANCZOS)
        sheet.paste(im, ((n % 2) * cell, (n // 2) * cell))
    out = REPO / "stories" / story / "style" / "concept-art.png"
    sheet.save(out)
    return out


def blended(img):
    """One number out of five: the author's rating where they gave one, else Kav's."""
    kav, author = img.get("kav") or {}, img.get("author") or {}
    vals = [author.get(k) or kav.get(k) for k, _, _ in CATS]
    vals = [v for v in vals if v]
    return round(sum(vals) / len(vals), 1) if vals else 0


# --- generation -------------------------------------------------------------

def generate(story, line, ar, seed=None, tries=3):
    """Generate, then read the plan back, so the captured refs include a plate drawn on
    the way through. Returns (path, refs, prompt).

    Retries on upload and network errors: a nine-image run takes a quarter of an hour, and
    losing it to one timed-out upload wastes every image already paid for.
    """
    cmd = ["python3", "tools/generate.py", "--story", story, "--ar", ar, line, "--lane", "seedream"]
    if seed is not None:
        cmd += ["--seed", str(seed)]
    for attempt in range(1, tries + 1):
        gen = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
        if not gen.returncode:
            break
        if attempt == tries:
            raise SystemExit(f"generate failed for {line!r}:\n{gen.stdout}\n{gen.stderr}")
        print(f"    retry {attempt}/{tries - 1} after: "
              f"{gen.stdout.strip()[-160:] or gen.stderr.strip()[-160:]}", flush=True)
        time.sleep(6 * attempt)
    dry = subprocess.run(["python3", "tools/generate.py", "--story", story, "--dry-run",
                          "--ar", ar, line], cwd=REPO, capture_output=True, text=True)
    plan = json.loads(dry.stdout)
    return json.loads(gen.stdout)["path"], plan["refs"], plan["prompt"]


def supersede(img, why):
    """Move the current take into history with the reason, ready for a fresh one."""
    if img.get("path"):
        img.setdefault("history", []).append(
            {"path": img["path"], "kav": img.get("kav"), "why": why,
             "at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    img["path"], img["kav"], img["prompt"], img["refs"] = None, None, "", []


def prebuild_plates(story, scenes):
    """Draw any missing location plate before the batch fans out.

    Two scenes at the same place would otherwise race to draw the same plate — paying
    twice and leaving whichever finished last. Serial here, once, is cheaper than a lock.
    """
    sys.path.insert(0, str(REPO / "tools"))
    import kav_plates
    import kav_refs

    kav_refs.set_story(story)
    spec = kav_refs.load_spec()
    pack = kav_refs.default_style_pack(spec)
    for sc in scenes:
        brief = kav_refs.parse_quick_line(sc["line"], 0, list(spec["characters"]))
        if not brief:
            continue
        shot, _ = kav_plates.pick_shot(brief, spec)
        if shot and not kav_plates.plate_path(brief["location"], shot).exists():
            print(f"    drawing plate {brief['location']}/{shot}", flush=True)
            kav_plates.ensure_plate(brief, spec, pack)


def run(story, only=None, seed=None, workers=3):
    """Generate the set. Concurrent, because the wall-clock is fal's render queue.

    A single image is ~100s and almost all of it is waiting on their side, so nine in
    sequence is a quarter of an hour of nothing. Three at a time turns that into about
    five minutes without hammering the endpoint.
    """
    scenes = json.loads(paths(story)[0].read_text(encoding="utf-8"))
    state = load_state(story)
    by_id = {i["id"]: i for i in state["images"]}
    todo, out = [], []
    for n, sc in enumerate(scenes, 1):
        sid = sc.get("id") or f"c{n}"
        img = by_id.get(sid, {"id": sid})
        img.update({"what": sc["what"], "line": sc["line"], "ar": sc.get("ar", "4:5")})
        img.setdefault("kav", None)
        img.setdefault("author", {})
        out.append(img)
        if not only or sid in only:
            todo.append((sc, img))

    prebuild_plates(story, [sc for sc, _ in todo])
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(generate, story, sc["line"], img["ar"], seed): (sc, img)
                   for sc, img in todo}
        for fut in as_completed(futures):
            sc, img = futures[fut]
            img["path"], img["refs"], img["prompt"] = fut.result()
            done += 1
            print(f"{done}/{len(todo)}  {sc['what']}", flush=True)

    state["images"] = out
    state["generatedAt"] = int(time.time())
    save_state(story, state)
    return state


# --- page -------------------------------------------------------------------

def jpeg(path, width, quality=80):
    from io import BytesIO

    from PIL import Image
    im = Image.open(path).convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True)
    return buf.getvalue()


def thumb(path, width, quality=80):
    from base64 import b64encode
    return "data:image/jpeg;base64," + b64encode(jpeg(path, width, quality)).decode()


STARS = ('<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 1.6l2.5 5.3 5.6.8-4.1 4.1 1 5.8'
         '-5-2.7-5 2.7 1-5.8L1.9 7.7l5.6-.8z"/></svg>')

CSS = """
:root { color-scheme: light; --ink:#241a13; --ink2:#6b5342; --bg:#f7efe2; --panel:#fffaf1;
  --rule:#e2d1bb; --terra:#c8502c; --star:#d9962a; --dim:#cbbca6; --good:#2e9d5b; --bad:#a8451f; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { color-scheme: dark;
  --ink:#f3e6d6; --ink2:#bda88f; --bg:#181209; --panel:#241a11; --rule:#4a3a2c; --terra:#e07048;
  --star:#e8b055; --dim:#5b4c3a; --good:#43b872; --bad:#e07048; } }
:root[data-theme="dark"] { color-scheme: dark; --ink:#f3e6d6; --ink2:#bda88f; --bg:#181209;
  --panel:#241a11; --rule:#4a3a2c; --terra:#e07048; --star:#e8b055; --dim:#5b4c3a;
  --good:#43b872; --bad:#e07048; }
* { box-sizing:border-box; }
body { background:var(--bg); color:var(--ink); margin:0 auto; max-width:1180px;
  font:15.5px/1.6 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;
  padding:28px 16px 90px; }
h1 { font-size:clamp(25px,4vw,34px); margin:0 0 6px; letter-spacing:-.015em; }
.lede { color:var(--ink2); max-width:66ch; margin:0 0 4px; }
.todo { background:var(--panel); border:1px solid var(--rule); border-left:4px solid var(--terra);
  padding:14px 16px; margin:18px 0 28px; max-width:72ch; }
.todo b { color:var(--terra); }
.todo ol { margin:8px 0 0; padding-left:20px; }
.todo li { margin:3px 0; }
.card { background:var(--panel); border:1px solid var(--rule); margin:0 0 20px; overflow:hidden; }
.card.weak { border-color:var(--bad); }
.top { display:flex; gap:18px; align-items:flex-start; padding:16px; flex-wrap:wrap; }
.shot { flex:0 0 clamp(220px,34%,380px); }
.shot img { width:100%; display:block; border:1px solid var(--rule); cursor:zoom-in; }
.meta { flex:1 1 320px; min-width:270px; }
.num { display:inline-block; background:var(--terra); color:#fff; font-size:12px; font-weight:700;
  padding:1px 7px; margin-bottom:6px; }
.what { font-weight:600; margin:0 0 2px; }
.line { color:var(--ink2); font-size:13.5px; margin:0 0 12px; }
.overall { display:flex; align-items:center; gap:9px; margin:0 0 14px; }
.overall .val { font-size:21px; font-weight:700; }
.overall .lab { color:var(--ink2); font-size:12.5px; text-transform:uppercase; letter-spacing:.07em; }
.cats { display:grid; gap:7px; }
.row { display:grid; grid-template-columns:118px auto; align-items:center; gap:10px; }
.row .name { font-size:13px; color:var(--ink2); border-bottom:1px dotted var(--dim); cursor:help; }
.stars { display:flex; gap:2px; }
.stars svg { width:17px; height:17px; fill:var(--dim); }
.stars svg.on { fill:var(--star); }
.stars.edit svg { cursor:pointer; }
.stars.edit svg:hover { fill:var(--star); opacity:.65; }
details { border-top:1px solid var(--rule); }
summary { cursor:pointer; padding:9px 16px; font-size:13px; color:var(--ink2); list-style:none; }
summary::-webkit-details-marker { display:none; }
summary::before { content:"▸ "; }
details[open] summary::before { content:"▾ "; }
summary:hover { color:var(--ink); }
.body { padding:0 16px 16px; font-size:14px; }
.body p { margin:0 0 9px; }
pre { background:var(--bg); border:1px solid var(--rule); padding:11px 13px; white-space:pre-wrap;
  font:12px/1.65 ui-monospace,SFMono-Regular,monospace; margin:10px 0 0; }
.refs { display:flex; gap:7px; flex-wrap:wrap; margin-top:4px; }
.refs figure { margin:0; width:88px; }
.refs img { width:100%; display:block; border:1px solid var(--rule); }
.refs figcaption { font-size:10px; color:var(--ink2); padding-top:2px; line-height:1.3; }
.fb { border-top:1px solid var(--rule); background:var(--bg); padding:14px 16px; }
.fb h4 { margin:0 0 10px; font-size:12.5px; text-transform:uppercase; letter-spacing:.07em;
  color:var(--terra); }
.fb .cats { max-width:330px; margin-bottom:11px; }
textarea { width:100%; min-height:62px; background:var(--panel); color:var(--ink);
  border:1px solid var(--rule); padding:9px 11px; font:inherit; font-size:14px; resize:vertical; }
.clear { background:none; border:0; color:var(--ink2); font-size:11.5px; cursor:pointer;
  text-decoration:underline; padding:0 0 0 6px; }
h2 { font-size:19px; margin:44px 0 4px; border-bottom:2px solid var(--terra); padding-bottom:6px; }
.prev { display:grid; gap:14px; grid-template-columns:repeat(auto-fill,minmax(210px,1fr)); }
.prev figure { margin:0; background:var(--panel); border:1px solid var(--rule); }
.prev img { width:100%; display:block; cursor:zoom-in; }
.prev figcaption { padding:8px 10px; font-size:12px; color:var(--ink2); }
.prev .why { color:var(--ink); }
.verdict-box { background:var(--panel); border:1px solid var(--rule); border-top:4px solid var(--terra);
  padding:18px 20px 16px; margin:0 0 22px; }
.verdict-box h3 { margin:0 0 8px; font-size:20px; }
.verdict-box p { margin:0 0 12px; max-width:74ch; }
.verdict-box h4 { margin:14px 0 4px; font-size:12.5px; text-transform:uppercase;
  letter-spacing:.07em; color:var(--terra); }
.verdict-box ul { margin:0; padding-left:20px; }
.verdict-box li { margin:4px 0; max-width:74ch; }
.verdict-box .ask { margin-top:14px; padding-top:12px; border-top:1px solid var(--rule); }
.score { background:var(--panel); border:1px solid var(--rule); padding:14px 18px 16px;
  margin:0 0 26px; }
.score h3 { margin:0 0 9px; font-size:13px; text-transform:uppercase; letter-spacing:.07em;
  color:var(--ink2); }
.srow { display:grid; grid-template-columns:118px auto 42px 1fr; align-items:center; gap:10px;
  margin:4px 0; }
.srow .sv { font-weight:700; }
.srow .sn { font-size:12.5px; color:var(--ink2); }
.bar { position:fixed; left:0; right:0; bottom:0; background:var(--panel);
  border-top:1px solid var(--rule); padding:11px 16px; display:flex; gap:14px;
  align-items:center; justify-content:center; }
button.save { background:var(--terra); color:#fff; border:0; padding:10px 22px; font:inherit;
  font-weight:600; cursor:pointer; }
button.save:hover { filter:brightness(1.08); }
.status { font-size:13.5px; color:var(--ink2); }
.lb { position:fixed; inset:0; background:#000d; display:none; align-items:center;
  justify-content:center; z-index:50; cursor:zoom-out; }
.lb img { max-width:94vw; max-height:94vh; }
.lb.on { display:flex; }
@media (max-width:640px) { .shot { flex:1 1 100%; } .row { grid-template-columns:104px auto; } }
"""

JS = """
const STATE = __STATE__, MODE = "__MODE__";
function setStars(el, n) {
  [...el.querySelectorAll('svg')].forEach((s, i) => s.classList.toggle('on', i < n));
}
function recompute(id) {
  const img = STATE.images.find(i => i.id === id);
  const vals = ['consistency','style','adherence','quality']
    .map(k => (img.author && img.author[k]) || (img.kav && img.kav[k])).filter(Boolean);
  const v = vals.length ? (vals.reduce((a,b)=>a+b,0)/vals.length) : 0;
  const card = document.querySelector(`[data-card="${id}"]`);
  card.querySelector('.overall .val').textContent = v ? v.toFixed(1) : '–';
  setStars(card.querySelector('.overall .stars'), Math.round(v));
  card.classList.toggle('weak', v > 0 && v < 3);
}
document.querySelectorAll('.stars.edit').forEach(el => {
  const id = el.dataset.img, cat = el.dataset.cat;
  el.querySelectorAll('svg').forEach((s, i) => s.onclick = () => {
    const img = STATE.images.find(x => x.id === id);
    img.author = img.author || {};
    img.author[cat] = i + 1;
    setStars(el, i + 1);
    recompute(id);
    dirty();
  });
});
document.querySelectorAll('.clear').forEach(b => b.onclick = () => {
  const id = b.dataset.img, cat = b.dataset.cat;
  const img = STATE.images.find(x => x.id === id);
  if (img.author) delete img.author[cat];
  const el = document.querySelector(`.stars.edit[data-img="${id}"][data-cat="${cat}"]`);
  setStars(el, (img.kav && img.kav[cat]) || 0);
  recompute(id);
  dirty();
});
document.querySelectorAll('textarea').forEach(t => t.oninput = () => {
  const img = STATE.images.find(x => x.id === t.dataset.img);
  img.author = img.author || {};
  img.author.feedback = t.value;
  dirty();
});
let clean = true;
function dirty() { clean = false; document.querySelector('.status').textContent = 'Unsaved changes'; }

// Ratings live in the artifact's own store, so Kav reads them back without the author
// copying anything anywhere. The page renders and works with no store at all; only Save
// needs it.
// `window.claude` exists only on claude.ai. The same file opened from disk or a preview
// pane has no runtime, so feature-check before calling: the page must render and be
// readable anywhere, and only Save needs the store.
let DB = null;
Promise.resolve(window.claude && window.claude.use ? window.claude.use('db') : null).then(d => {
  DB = d;
  if (!DB) return;
  DB.collection('calibration').onSnapshot(docs => {
    for (const doc of docs) {
      const img = STATE.images.find(i => i.id === doc.id);
      if (!img || doc === undefined) continue;
      const incoming = doc.data || doc;
      if (JSON.stringify(incoming.author || {}) === JSON.stringify(img.author || {})) continue;
      img.author = incoming.author || {};
      for (const [c] of [['consistency'],['style'],['adherence'],['quality']]) {
        const el = document.querySelector(`.stars.edit[data-img="${img.id}"][data-cat="${c}"]`);
        if (el) setStars(el, img.author[c] || (img.kav && img.kav[c]) || 0);
      }
      const t = document.querySelector(`textarea[data-img="${img.id}"]`);
      if (t && document.activeElement !== t) t.value = img.author.feedback || '';
      recompute(img.id);
    }
  });
}).catch(() => {});

document.querySelector('button.save').onclick = async () => {
  const s = document.querySelector('.status');
  if (!DB) {
    s.textContent = 'Cannot save here — open the artifact link to rate.';
    return;
  }
  s.textContent = 'Saving…';
  try {
    for (const img of STATE.images) {
      await DB.doc('calibration/' + img.id).set({
        id: img.id, what: img.what, kav: img.kav || null,
        author: img.author || {}, savedAt: new Date().toISOString(),
      });
    }
    s.textContent = 'Saved. Tell Kav "please continue".';
    clean = true;
  } catch (e) { s.textContent = 'Save failed: ' + (e && e.code || e); }
};
window.onbeforeunload = e => clean ? undefined : (e.preventDefault(), '');
const lb = document.querySelector('.lb');
document.querySelectorAll('img[data-full]').forEach(i => i.onclick = () => {
  lb.querySelector('img').src = i.dataset.full; lb.classList.add('on');
});
lb.onclick = () => lb.classList.remove('on');
document.onkeydown = e => { if (e.key === 'Escape') lb.classList.remove('on'); };
"""


def stars(n, editable=False, img_id="", cat=""):
    on = "".join(STARS.replace("<svg ", '<svg class="on" ') for _ in range(int(n or 0)))
    off = "".join(STARS for _ in range(5 - int(n or 0)))
    cls = "stars edit" if editable else "stars"
    attrs = f' data-img="{img_id}" data-cat="{cat}"' if editable else ""
    return f'<div class="{cls}"{attrs}>{on}{off}</div>'


def cat_rows(img, editable):
    kav, author = img.get("kav") or {}, img.get("author") or {}
    out = []
    for key, label, tip in CATS:
        val = (author.get(key) if editable else None) or kav.get(key)
        clear = (f'<button class="clear" data-img="{img["id"]}" data-cat="{key}">reset</button>'
                 if editable and author.get(key) else "")
        out.append(f'<div class="row"><span class="name" title="{H.escape(tip)}">{label}</span>'
                   f'<span style="display:flex;align-items:center">'
                   f'{stars(val, editable, img["id"], key)}{clear}</span></div>')
    return f'<div class="cats">{"".join(out)}</div>'


def ref_strip(refs):
    return '<div class="refs">' + "".join(
        f'<figure><img src="{thumb(r["local"], 110, 70)}" alt="">'
        f'<figcaption>{i}. {H.escape(r["kind"][:4])}<br>{H.escape(str(r["name"] or ""))}'
        f'</figcaption></figure>' for i, r in enumerate(refs, 1)) + "</div>"


def card(img, n, px):
    # One encoding per image, reused by the lightbox. Embedding a second, larger copy for
    # zoom is what made this page 5 MB for nine panels — more than a 20-panel chapter
    # reader, which embeds each page exactly once.
    shot = thumb(img["path"], px)
    v = blended(img)
    weak = " weak" if 0 < v < THRESHOLD else ""
    kav = img.get("kav") or {}
    note = kav.get("note") or "Not rated yet."
    fb = (img.get("author") or {}).get("feedback", "")
    return (
        f'<article class="card{weak}" data-card="{img["id"]}">'
        f'<div class="top">'
        f'<div class="shot"><img src="{shot}" data-full="{shot}" alt=""></div>'
        f'<div class="meta"><span class="num">{n}</span>'
        f'<p class="what">{H.escape(img["what"])}</p>'
        f'<p class="line">{H.escape(img["line"])}</p>'
        f'<div class="overall"><span class="val">{v or "–"}</span>{stars(round(v))}'
        f'<span class="lab">overall</span></div>'
        f'{cat_rows(img, False)}</div></div>'
        f'<details><summary>Kav evaluation</summary><div class="body"><p>{note}</p></div></details>'
        f'<details><summary>Exact prompt and {len(img.get("refs") or [])} references</summary>'
        f'<div class="body">{ref_strip(img.get("refs") or [])}'
        f'<pre>{H.escape(img.get("prompt") or "")}</pre></div></details>'
        f'<div class="fb"><h4>Your rating and feedback</h4>{cat_rows(img, True)}'
        f'<textarea data-img="{img["id"]}" placeholder="What is wrong with this one, or what would '
        f'make it right?">{H.escape(fb)}</textarea></div>'
        f'</article>')


def prev_section(state, px):
    items = []
    for img in state["images"]:
        for h in img.get("history", []):
            if not Path(h["path"]).exists():
                continue
            v = blended({"kav": h.get("kav")})
            small = thumb(h["path"], px)
            items.append(
                f'<figure><img src="{small}" data-full="{small}" alt="">'
                f'<figcaption><b>{H.escape(img["what"].split("·")[0].strip())}</b> · {v or "–"}/5'
                f'<br><span class="why">{H.escape(h.get("why", ""))}</span></figcaption></figure>')
    if not items:
        return ""
    return (f'<h2>Previous generations</h2>'
            f'<p class="lede">Takes that were replaced, and why. Kept so an iteration is visible '
            f'rather than overwritten.</p><div class="prev">{"".join(items)}</div>')


HEAD = """<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Visual Calibration Lock</title><style>%s</style>"""

INTRO = """
<h1>Visual Calibration Lock</h1>
<p class="lede">Kav generated several concept images using this story's cast, locations and style,
to find out whether we can draw this book reliably before any of it is drawn for real.</p>
<div class="todo"><b>What to do here.</b>
<ol>
<li>Look at each image and change any rating you disagree with — hover a category name to see what
it means.</li>
<li>Write what is wrong, or what would make it right, in the feedback box.</li>
<li>Press <b>Save</b>, then tell Kav <b>"please continue"</b>.</li>
</ol></div>
"""


def scorecard(state):
    """Per category, not just an average — an average hides a category that is failing
    everywhere. Five images consistent at 2 and clean at 5 average to a comfortable number
    and describe a book that cannot be drawn."""
    imgs = [i for i in state["images"] if i.get("path")]
    if not imgs:
        return ""
    rows = []
    for key, label, tip in CATS:
        vals = [((i.get("author") or {}).get(key) or (i.get("kav") or {}).get(key)) for i in imgs]
        vals = [v for v in vals if v]
        avg = sum(vals) / len(vals) if vals else 0
        low = sum(1 for v in vals if v < 3)
        rows.append(
            f'<div class="srow"><span class="name" title="{H.escape(tip)}">{label}</span>'
            f'{stars(round(avg))}<span class="sv">{avg:.1f}</span>'
            f'<span class="sn">{"all clear" if not low else f"{low} below 3"}</span></div>')
    return f'<div class="score"><h3>Where it stands</h3>{"".join(rows)}</div>'


# The page shows the set as it stands: the images, what is wrong with each, what each
# replaced. Recommendations, plans and what changed since last time are conversation —
# they date the moment they are acted on, and a page that argues with itself is not a
# record of anything. The verdict stays in `calibration-state.json` for Kav to speak from.


def build(story, out_path, state, mode="artifact"):
    n_img = len([i for i in state["images"] if i.get("path")])
    px = 820 if n_img <= 9 else 620
    body = "".join(card(i, n, px) for n, i in enumerate(
        [i for i in state["images"] if i.get("path")], 1))
    page = (HEAD % CSS) + INTRO + scorecard(state) + body + prev_section(state, 320) + (
        '<div class="bar"><button class="save">Save</button>'
        '<span class="status">Nothing changed yet</span></div>'
        '<div class="lb"><img alt=""></div>'
        "<script>" + JS.replace("__STATE__", json.dumps(state, ensure_ascii=False))
                        .replace("__MODE__", mode) + "</script>")
    Path(out_path).write_text(page, encoding="utf-8")
    return out_path


# --- server -----------------------------------------------------------------

def serve(story, port=8731):
    _, state_path = paths(story)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            state = load_state(story)
            tmp = REPO / "stories" / story / "style" / "worksheets" / "calibration.html"
            tmp.parent.mkdir(parents=True, exist_ok=True)
            build(story, tmp, state, mode="server")
            data = tmp.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            incoming = json.loads(self.rfile.read(n))
            state = load_state(story)
            by_id = {i["id"]: i for i in incoming.get("images", [])}
            for img in state["images"]:
                if img["id"] in by_id:
                    img["author"] = by_id[img["id"]].get("author", {})
            state["reviewedAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            save_state(story, state)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")

    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"http://127.0.0.1:{port}/   (Ctrl+C to stop)  ->  {state_path}")
    srv.serve_forever()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--story", required=True)
    ap.add_argument("--generate", action="store_true", help="generate (or regenerate) the images")
    ap.add_argument("--only", help="comma list of scene ids to regenerate, e.g. c4,c7")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--static", help="write a standalone page here instead of serving")
    ap.add_argument("--serve", action="store_true", help="serve the page and save ratings")
    ap.add_argument("--port", type=int, default=8731)
    a = ap.parse_args()

    if a.generate:
        run(a.story, set(a.only.split(",")) if a.only else None, a.seed)
    if a.static:
        print(build(a.story, a.static, load_state(a.story), mode="static"))
    if a.serve:
        serve(a.story, a.port)


if __name__ == "__main__":
    main()
