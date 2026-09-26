#!/usr/bin/env python3
"""The Ideas tab: every note in pitch-inbox.md as a sticky note, plus a drop box so the
author can pin a thought the moment it arrives.

`tools/build_map.py` includes this as the Ideas tab of the story's board; run this
file directly only for a standalone board.

The inbox file is the truth. Published as a Claude artifact with capabilities
{"db": {}}, the drop box writes each new thought to the artifact's `drops`
collection; Kav reads that collection (ArtifactData list), files every unfiled drop
into pitch-inbox.md as the next N00N, marks the drop {filed: true, note_id}, then
rebuilds and republishes. Anywhere without the capability (a local file, ChatGPT,
Codex) the box says to drop ideas in the chat instead.

Tags the board understands at the end of a note: `[not-yet-agreed]` (open),
`[adopted: ch03]` or `[adopted → cast/imi]` (used, and where), `[dropped]`.

  python3 tools/build_ideas.py --story <slug> [--out <file.html>]
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kav_env import REPO  # noqa: E402

TYPES = {"chapter-concept": ("scene", "--coral"), "visual": ("visual", "--rose"), "gimmick": ("gimmick", "--mint"),
         "concept": ("concept", "--butter"), "twist": ("twist", "--violet"),
         "beat": ("beat", "--sky"), "other": ("other", "--sand")}
NOTE = re.compile(r"^- \*\*(N\d+)\s*·\s*([\w-]+)\*\*\s*(?:\(([^)]*)\))?:?\s*(.*?)\s*(?:`\[([^\]]+)\]`)?\s*$")


def esc(s):
    return html.escape(str(s), quote=True)


def parse(text):
    notes = []
    for line in text.splitlines():
        m = NOTE.match(line.strip())
        if not m:
            continue
        nid, kind, date, body, tag = m.groups()
        tag = (tag or "not-yet-agreed").strip()
        state, where = "open", ""
        if tag.lower().startswith("adopted"):
            state, where = "used", re.sub(r"^adopted\s*[:→\->]*\s*", "", tag, flags=re.I).strip()
        elif tag.lower().startswith("dropped"):
            state = "dropped"
        notes.append({"id": nid, "type": kind if kind in TYPES else "other", "date": date or "",
                      "text": body, "state": state, "where": where})
    return notes


CSS = """
.ideas{--cork:#b88a5c;--cork-dark:#8f6640;--cork-light:#d4a878;--frame:#5d3f24;--frame-hi:#7a5534;
--ink:#2b221c;--ink-soft:#5c4a3c;--label:#f7f1e3;--paper:#fffaf0;--focus:#1f5fbf;
--coral:#f3a58f;--rose:#f4bccb;--mint:#aee3c9;--butter:#f9e39b;--violet:#cfbdf0;--sky:#acd3f2;--sand:#e6d6b8;color:var(--ink)}
.ideas .intro{margin:0 0 18px;display:flex;flex-direction:column;gap:10px;max-width:720px;color:var(--page-ink,#1d2330);--ink-code:var(--page-ink,#1d2330)}
.ideas .intro p{margin:0;font-size:15px;line-height:1.5}
.ideas .intro .lbl{font-size:12.5px;color:var(--soft,#6a7080);margin-bottom:-4px}
.ideas .intro .cmd{display:flex;gap:6px}
.ideas .intro .cmd code{flex:1;min-width:0;font:13.5px/1.4 ui-monospace,Menlo,monospace;background:var(--code,#f0eee9);border:1px solid var(--line,#e2dfd8);
border-radius:6px;padding:8px 10px;overflow-wrap:anywhere;unicode-bidi:plaintext;color:var(--ink-code,#1d2330)}
.ideas .intro .cmd button{font:inherit;font-size:12.5px;border:1px solid var(--line,#e2dfd8);background:var(--surface,#fff);color:var(--ink-code,#1d2330);border-radius:6px;padding:0 12px;cursor:pointer}
.ideas .intro .cmd button:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
.ideas .board{border-radius:8px;padding:clamp(18px,3vw,32px);background-color:var(--cork);
background-image:radial-gradient(circle at 20% 30%,var(--cork-dark) 0 1.2px,transparent 1.6px),radial-gradient(circle at 70% 60%,var(--cork-light) 0 1px,transparent 1.5px),
radial-gradient(circle at 45% 85%,var(--cork-dark) 0 .9px,transparent 1.3px),radial-gradient(circle at 85% 15%,var(--cork-light) 0 1.3px,transparent 1.7px);
background-size:23px 19px,31px 27px,17px 21px,41px 37px;box-shadow:inset 0 0 0 10px var(--frame-hi),inset 0 0 0 12px var(--frame),inset 0 6px 24px rgba(0,0,0,.25)}
.ideas .legend{display:flex;flex-wrap:wrap;gap:8px;list-style:none;margin:0 0 22px;padding:0}
.ideas .legend li{display:flex;align-items:center;gap:7px;background:rgba(247,241,227,.9);border-radius:999px;padding:5px 12px 5px 7px;font-size:12px;box-shadow:0 1px 3px rgba(0,0,0,.2)}
.ideas .legend .dot{width:14px;height:14px;border-radius:3px;box-shadow:inset 0 0 0 1px rgba(0,0,0,.12)}
.ideas .legend .n{font-variant-numeric:tabular-nums;color:var(--ink-soft)}.ideas .legend li.empty{opacity:.55}
.ideas .notes{columns:3 250px;column-gap:26px}
.ideas .note{break-inside:avoid;display:block;margin:0 0 28px;padding:30px 18px 16px;position:relative;background:var(--bg,var(--sand));
box-shadow:0 1px 1px rgba(0,0,0,.15),0 8px 16px -6px rgba(0,0,0,.35);transform:rotate(var(--tilt,0deg));transition:transform .2s ease}
.ideas .note:hover{transform:rotate(0deg) translateY(-2px)}
.ideas .note::before{content:"";position:absolute;top:9px;left:50%;width:16px;height:16px;margin-left:-8px;border-radius:50%;
background:radial-gradient(circle at 35% 35%,#ff8a7a,#c0352a 60%,#7d1f18);box-shadow:0 2px 3px rgba(0,0,0,.4)}
.ideas .note.used{opacity:.62;filter:saturate(.55)}
.ideas .note.used::before{background:radial-gradient(circle at 35% 35%,#c9c9c9,#7e7e7e 60%,#4a4a4a)}
.ideas .note.dropped{opacity:.4}
.ideas .meta{display:flex;justify-content:space-between;align-items:baseline;gap:8px;margin-bottom:10px;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-soft)}
.ideas .id{font-family:var(--display,system-ui);font-size:22px;letter-spacing:.02em;text-transform:none;color:var(--ink)}
.ideas .text{margin:0;font-size:15px;line-height:1.6;unicode-bidi:plaintext;white-space:pre-wrap;overflow-wrap:anywhere}
.ideas .foot{margin-top:14px;display:flex;justify-content:space-between;align-items:center;gap:8px;font-size:11px;color:var(--ink-soft);font-variant-numeric:tabular-nums}
.ideas .tag{border:1px dashed rgba(43,34,28,.45);border-radius:3px;padding:2px 6px;letter-spacing:.04em}
.ideas .note.fresh{--bg:var(--paper)}.ideas .note.fresh .tag{border-style:solid;border-color:#c0352a;color:#8a2a20}
.ideas .drop{--bg:var(--paper);--tilt:-.6deg}
.ideas .drop label{display:block;font-family:var(--display,system-ui);font-size:30px;line-height:1;margin-bottom:8px}
.ideas .drop textarea{box-sizing:border-box;width:100%;min-height:96px;resize:vertical;border:1px solid rgba(43,34,28,.3);border-radius:4px;background:#fff;
font:inherit;font-size:15px;line-height:1.5;padding:8px 10px;color:var(--ink)}
.ideas .drop textarea:focus-visible,.ideas .drop button:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
.ideas .drop .row{display:flex;justify-content:flex-end;margin-top:10px}
.ideas .drop button{font:inherit;font-size:14px;border:0;border-radius:999px;padding:8px 18px;background:var(--ink);color:var(--paper);cursor:pointer}
.ideas .drop button[disabled]{opacity:.5;cursor:default}
.ideas .drop .msg{font-size:12.5px;color:var(--ink-soft);min-height:1.2em;margin:8px 0 0}
.ideas .drop .offline{margin:0;font-size:14.5px;line-height:1.55}
.ideas .drop code{font-family:ui-monospace,Menlo,monospace;font-size:12.5px;background:rgba(43,34,28,.08);padding:1px 5px;border-radius:3px}
@media (prefers-reduced-motion:reduce){.ideas .note{transition:none}}
"""

JS = r"""
document.querySelectorAll('.ideas .intro .cmd button').forEach(b=>b.addEventListener('click',()=>{
  const code=b.previousElementSibling,t=code.textContent;
  const pick=()=>{const r=document.createRange();r.selectNodeContents(code);const s=getSelection();s.removeAllRanges();s.addRange(r)};
  try{navigator.clipboard.writeText(t).then(()=>{b.textContent='Copied';setTimeout(()=>b.textContent='Copy',1400)},pick)}catch(_){pick()}
}));
(function(){
const FILED=new Set(%s);
const box=document.getElementById('drop-box'),ta=document.getElementById('drop-text'),btn=document.getElementById('drop-pin'),
msg=document.getElementById('drop-msg'),fresh=document.getElementById('fresh'),count=document.getElementById('ideas-count');
const base=count?+count.dataset.n:0;
function paint(docs){
  fresh.textContent='';let n=0;
  docs.forEach(d=>{const v=d.data()||{};if(v.filed&&FILED.has(v.note_id))return;n++;
    const el=document.createElement('article');el.className='note fresh';el.style.setProperty('--tilt',((d.id.charCodeAt(0)%%5)-2)*.5+'deg');
    const meta=document.createElement('div');meta.className='meta';const id=document.createElement('span');id.className='id';id.textContent=v.note_id||'new';
    const k=document.createElement('span');k.textContent='just dropped';meta.append(id,k);
    const p=document.createElement('p');p.className='text';p.dir='auto';p.textContent=v.text||'';
    const f=document.createElement('div');f.className='foot';const dt=document.createElement('span');dt.textContent=(v.created||'').slice(0,10);
    const t=document.createElement('span');t.className='tag';t.textContent=v.filed?'filed as '+v.note_id:'Kav files it next';f.append(dt,t);
    el.append(meta,p,f);fresh.append(el);});
  if(count)count.textContent=base+n;
}
function offline(){box.querySelector('.live').hidden=true;box.querySelector('.offline').hidden=false}
if(!window.claude||!window.claude.use){offline();return}
window.claude.use('db').then(db=>{
  if(!db){offline();return}
  const drops=db.collection('drops');
  drops.orderBy('created','desc').onSnapshot(s=>paint(s.docs),()=>{});
  async function pin(){
    const text=ta.value.trim();if(!text)return;
    btn.disabled=true;msg.textContent='Pinning…';
    try{await drops.add({text,created:new Date().toISOString(),filed:false,note_id:null});
      ta.value='';msg.textContent='Pinned.';}
    catch(e){msg.textContent=e&&e.code==='quota_exceeded'?'The board is full. Ask Kav to archive filed ideas, then try again.':
      e&&e.code==='invalid_argument'?'This view can read the board but not pin to it.':'That didn’t save. Try again in a moment.';}
    finally{btn.disabled=false;ta.focus()}
  }
  btn.addEventListener('click',pin);
  ta.addEventListener('keydown',e=>{if(e.key==='Enter'&&(e.metaKey||e.ctrlKey)){e.preventDefault();pin()}});
});
})();
"""


def render_note(n, i):
    label, var = TYPES[n["type"]]
    tilt = [-1.6, 1.3, -.7, .9, -1.1, .6][i % 6]
    tag = {"open": "not yet agreed", "used": f"used · {n['where']}" if n["where"] else "used", "dropped": "dropped"}[n["state"]]
    cls = "note" + ("" if n["state"] == "open" else f" {n['state']}")
    return (f'<article class="{cls}" style="--bg:var({var});--tilt:{tilt}deg"><div class="meta"><span class="id">{esc(n["id"])}</span>'
            f'<span>{esc(label)}</span></div><p class="text" dir="auto">{esc(n["text"])}</p>'
            f'<div class="foot"><span>{esc(n["date"])}</span><span class="tag">{esc(tag)}</span></div></article>')


def ideas_section(sd, suggestion=None):
    """(html, css, js, n_notes) for the Ideas tab of a story's board.

    suggestion: an example note written by Kav from what it knows of the story; defaults to
    package/idea-suggestion.txt when that file exists."""
    if suggestion is None:
        sf = Path(sd) / "package" / "idea-suggestion.txt"
        suggestion = sf.read_text(encoding="utf-8").strip() if sf.is_file() else ""
    inbox = Path(sd) / "pitch-inbox.md"
    notes = parse(inbox.read_text(encoding="utf-8")) if inbox.is_file() else []
    counts = {k: sum(1 for n in notes if n["type"] == k) for k in TYPES}
    legend = "".join(f'<li class="{"" if counts[k] else "empty"}"><span class="dot" style="background:var({v})"></span>{esc(lbl)} '
                     f'<span class="n">{counts[k]}</span></li>' for k, (lbl, v) in TYPES.items()) if notes else ""
    ordered = [n for n in notes if n["state"] == "open"] + [n for n in notes if n["state"] != "open"]
    drop = ('<article class="note drop" id="drop-box"><div class="live"><label for="drop-text">Drop an idea</label>'
            '<textarea id="drop-text" dir="auto" placeholder="A scene, a line, a what-if. Anything."></textarea>'
            '<div class="row"><button id="drop-pin" type="button">Pin it</button></div>'
            '<p class="msg" id="drop-msg" aria-live="polite"></p></div>'
            '<p class="offline" hidden>Drop ideas in the chat with <code>/kav-note</code>, and they land here.</p></article>')

    def cmd(text):
        return f'<div class="cmd"><code dir="auto">{esc(text)}</code><button type="button">Copy</button></div>'

    intro = ('<div class="intro"><p>Jot ideas about your story here. Scenes, situations, visuals. '
             'Kav will read them and factor them into the work.</p>'
             '<span class="lbl">Or paste this into the chat</span>' + cmd("/kav-note <jot your note>")
             + (f'<span class="lbl">Something like</span>{cmd("/kav-note " + suggestion)}' if suggestion else "") + "</div>")
    body = (f'<div class="ideas">{intro}<div class="board">{f"<ul class=legend>{legend}</ul>" if legend else ""}'
            f'<section class="notes">{drop}<div id="fresh" style="display:contents"></div>'
            + "".join(render_note(n, i) for i, n in enumerate(ordered)) + "</section></div></div>")
    return body, CSS, JS % json.dumps([n["id"] for n in notes]), len(notes)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--story", required=True, help="slug under this repo's stories/, or a path to any story folder")
    ap.add_argument("--out")
    ap.add_argument("--suggest", help="an example note to show; default: package/idea-suggestion.txt")
    a = ap.parse_args()
    sd = Path(a.story).expanduser().resolve() if "/" in a.story else REPO / "stories" / a.story
    if not sd.is_dir():
        sys.exit(f"No such story: {sd}")
    meta = json.loads((sd / "story.json").read_text(encoding="utf-8")) if (sd / "story.json").is_file() else {}
    body, css, js, n = ideas_section(sd, a.suggest)
    title = meta.get("title") or sd.name
    page = (f'<meta charset="utf-8"><title>{esc(title)} · Ideas</title>'
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Karantina:wght@700&family=Varela+Round&display=swap">'
            f'<style>body{{background:#f4f3f0;font-family:"Varela Round",system-ui,sans-serif;padding:20px 16px}}'
            f'.ideas{{--display:"Karantina",system-ui,sans-serif;max-width:1120px;margin:0 auto}}{css}</style>{body}<script>{js}</script>')
    out = Path(a.out) if a.out else sd / "package" / "idea-board.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"{out} · {n} notes")


if __name__ == "__main__":
    main()
