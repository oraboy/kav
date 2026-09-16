#!/usr/bin/env python3
"""Local panel-review page: candidates side by side, pick or reroll, edit text, one submit.

Reads the same batch JSON panel_batch.py consumes and the candidates it produced
(stories/<story>/chapters/<chapter>/panels/candidates/<id>-<k>.png). Panels appear in batch
order. Settled panels ("picked" in the batch) show only the picked image, locked, still open
for text edits. Wide panels show the full image and the phone's centre 4:5 crop side by side.

By default starts a small local web server (stdlib only), opens the browser, and on Submit
writes stories/<story>/chapters/<chapter>/panels/reviews/<batch-stem>.json:
  {batch, story, chapter, submittedAt, panels: {id: {pick, reroll, comment, text}}}
An existing review file pre-fills the page. Stop the server with Ctrl+C.
--static out.html writes a standalone page instead (images linked by relative path); its
Submit button shows the JSON to copy, since there is no server to save it.
"""
import argparse
import html as H
import json
import mimetypes
import sys
import threading
import urllib.parse
import webbrowser
from datetime import datetime, timezone
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kav_env import REPO, jpeg_bytes, resolve  # noqa: E402


def paths(batch_path):
    spec = json.loads(batch_path.read_text(encoding="utf-8"))
    story, chapter = spec["story"], spec["chapter"]
    panels_dir = REPO / "stories" / story / "chapters" / chapter / "panels"
    return spec, panels_dir / "candidates", panels_dir / "reviews" / f"{batch_path.stem}.json"


def build_page(batch_path, img_url, title=None, mode="server"):
    """img_url(Path) -> src string. mode: 'server' posts to /submit, 'static' shows JSON."""
    spec, cand_dir, review_file = paths(batch_path)
    stem = batch_path.stem
    story, chapter = spec["story"], spec["chapter"]
    title = title or f"{chapter} · {stem}"
    prior = {}
    if review_file.exists():
        try:
            prior = json.loads(review_file.read_text(encoding="utf-8")).get("panels", {})
        except ValueError:
            prior = {}

    blocks, seed = [], {}
    for p in spec["panels"]:
        pid = p["id"]
        picked = p.get("picked")
        files = sorted(cand_dir.glob(f"{pid}-*.png"),
                       key=lambda f: (len(f.stem), f.stem))
        files = [f for f in files if f.stem.rsplit("-", 1)[1].isdigit()]
        if picked:
            files = [f for f in files if f.stem.rsplit("-", 1)[1] == str(picked)]
        if not files:
            continue
        st = {"pick": str(picked) if picked else None, "reroll": False,
              "comment": "", "text": p.get("text", "")}
        old = prior.get(pid) or {}
        for k in ("pick", "reroll", "comment", "text"):
            if k in old and old[k] is not None:
                st[k] = old[k]
        if picked:
            st["pick"], st["reroll"] = str(picked), False
        seed[pid] = st
        # The phone keeps the centre 4:5 of a wide panel: show that crop as its own image
        # beside the full one. A 4:5 panel is already the phone frame, so it shows once.
        try:
            aw, ah = (float(x) for x in p.get("ar", "9:16").split(":"))
            wide = (aw / ah) > 0.81
        except Exception:
            aw, ah, wide = 4.0, 5.0, False

        def card(f):
            n = f.stem.rsplit("-", 1)[1]
            src = H.escape(img_url(f), quote=True)
            if wide:
                views = (f'<span class="view full" style="flex:{aw / ah:.3f}">'
                         f'<img src="{src}" alt="" loading="lazy"><span class="cap">full</span></span>'
                         f'<span class="view phone"><img src="{src}" alt="" loading="lazy">'
                         f'<span class="cap">phone</span></span>')
            else:
                views = f'<span class="view solo"><img src="{src}" alt="" loading="lazy"></span>'
            return (f'<button class="cand{" wide" if wide else ""}" data-panel="{H.escape(pid)}" '
                    f'data-pick="{n}"><span class="pair">{views}</span><span class="n">{n}</span></button>')

        cards = "".join(card(f) for f in files)
        settled = " settled" if picked else ""
        blocks.append(f'''
<section class="panel{settled}" data-panel="{H.escape(pid)}">
  <header><h2>{H.escape(pid)}</h2><span class="ar">{H.escape(p.get("ar", "9:16"))}</span>
    {'<span class="tag">locked</span>' if picked else ''}</header>
  <p class="line">{H.escape(p.get("line", ""))}</p>
  <div class="cands">{cards}</div>
  <div class="row">
    {'' if picked else f'<button class="reroll" data-panel="{H.escape(pid)}">reroll</button>'}
    <span class="state" data-panel="{H.escape(pid)}"></span>
  </div>
  <label class="lbl">text on this panel (edit freely)</label>
  <textarea class="text" dir="auto" data-panel="{H.escape(pid)}" rows="4">{H.escape(st["text"])}</textarea>
  <label class="lbl">notes on the image</label>
  <textarea class="note" dir="auto" data-panel="{H.escape(pid)}" rows="2" placeholder="what to change">{H.escape(st["comment"])}</textarea>
</section>''')

    if not blocks:
        blocks.append(f'<p class="sub">No candidates found in {H.escape(str(cand_dir))}. '
                      f'Run tools/panel_batch.py on this batch first.</p>')

    def js(v):
        return json.dumps(v, ensure_ascii=False).replace("</", "<\\/")

    return f'''<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{H.escape(title)}</title>
<style>
:root{{--ink:#0f1720;--card:#182233;--cream:#f4ecd6;--sand:#cfc2a3;--accent:#d9a066;--ok:#7fbf7f}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--ink);color:var(--cream);
     font-family:'Varela Round',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}}
.wrap{{max-width:1180px;margin:0 auto;padding:28px 18px 140px}}
h1{{font-size:26px;margin:0 0 4px}}
.sub,.legend{{color:var(--sand);font-size:14px;margin:0 0 12px}}
.legend{{margin-bottom:24px;font-size:13px}}
.panel{{background:var(--card);border-radius:12px;padding:16px 16px 18px;margin:0 0 22px}}
.panel header{{display:flex;align-items:baseline;gap:10px}}
h2{{font-size:19px;margin:0}}
.ar{{color:var(--accent);font-size:12px;letter-spacing:.08em}}
.line{{color:var(--sand);font-size:13px;line-height:1.5;margin:8px 0 14px}}
.cands{{display:flex;gap:12px;flex-wrap:wrap}}
.cand{{position:relative;flex:1 1 0;min-width:200px;padding:0;border:3px solid transparent;
      border-radius:8px;background:none;cursor:pointer;overflow:hidden;line-height:0}}
.cand img{{width:100%;height:auto;display:block;border-radius:5px}}
.cand .n{{position:absolute;top:8px;right:8px;z-index:2;background:rgba(15,23,32,.8);color:var(--cream);
         font-size:13px;line-height:1;padding:5px 9px;border-radius:20px}}
.cand.on{{border-color:var(--ok)}}
.cand.on .n{{background:var(--ok);color:#0f1720;font-weight:700}}
.cand.wide{{flex:1 1 100%}}
.pair{{display:flex;gap:6px;align-items:stretch}}
.view{{position:relative;display:block;line-height:0}}
.view img{{width:100%;height:100%;display:block;border-radius:5px}}
.view.full{{min-width:0}}
.view.phone{{flex:0.8;aspect-ratio:4/5;overflow:hidden;border-radius:5px}}
.view.phone img{{object-fit:cover;object-position:center}}
.view.solo{{flex:1}}
.cap{{position:absolute;bottom:6px;left:6px;background:rgba(15,23,32,.8);color:var(--sand);
     font-size:11px;letter-spacing:.06em;line-height:1;padding:4px 7px;border-radius:10px}}
.row{{display:flex;align-items:center;gap:12px;margin:12px 0 10px}}
.reroll{{background:none;border:1px solid rgba(244,236,214,.3);color:var(--cream);
        font-size:13px;padding:7px 16px;border-radius:20px;cursor:pointer}}
.reroll.on{{background:var(--accent);border-color:var(--accent);color:#0f1720;font-weight:700}}
.state{{font-size:13px;color:var(--ok)}}
.tag{{font-size:11px;letter-spacing:.1em;color:var(--ok);border:1px solid var(--ok);
     border-radius:20px;padding:2px 9px}}
.settled .cands{{max-width:720px}}
.settled .cand{{cursor:default}}
.lbl{{display:block;font-size:12px;letter-spacing:.06em;color:var(--sand);margin:12px 0 5px}}
textarea{{width:100%;background:#0f1720;color:var(--cream);border:1px solid rgba(244,236,214,.18);
         border-radius:8px;padding:10px 12px;font:inherit;font-size:14px;resize:vertical}}
textarea.text{{font-size:15px;line-height:1.6}}
.bar{{position:fixed;bottom:0;left:0;right:0;background:rgba(15,23,32,.96);
     border-top:1px solid rgba(244,236,214,.15);padding:14px 18px;display:flex;flex-wrap:wrap;
     gap:14px;align-items:center;justify-content:center}}
#send{{background:var(--cream);color:#0f1720;border:0;font:inherit;font-size:16px;font-weight:700;
      padding:12px 34px;border-radius:24px;cursor:pointer}}
#send:disabled{{opacity:.45;cursor:default}}
#msg{{font-size:14px;color:var(--sand)}}
#dump{{display:none;width:100%;max-width:900px;height:160px;font-family:ui-monospace,monospace;font-size:12px}}
</style></head><body>
<div class="wrap">
  <h1>{H.escape(title)}</h1>
  <p class="sub">Pick one per panel, or mark it for a reroll. Notes are optional. One submit at the end.</p>
  <p class="legend">Wide panels show twice: the full image, and beside it exactly what the phone keeps.</p>
  {''.join(blocks)}
</div>
<div class="bar"><button id="send">Submit picks</button><span id="msg"></span><textarea id="dump" readonly></textarea></div>
<script>
const MODE = {js(mode)};
const BATCH = {js(stem)}, STORY = {js(story)}, CHAPTER = {js(chapter)};
const LOCKED = new Set({js([p["id"] for p in spec["panels"] if p.get("picked")])});
const state = {js(seed)};
function ent(id){{ return state[id] || (state[id] = {{pick:null, reroll:false, comment:"", text:""}}); }}
function paint(id){{
  const s = ent(id);
  document.querySelectorAll('.cand[data-panel="'+CSS.escape(id)+'"]').forEach(b =>
    b.classList.toggle('on', !s.reroll && s.pick === b.dataset.pick));
  const r = document.querySelector('.reroll[data-panel="'+CSS.escape(id)+'"]');
  if (r) r.classList.toggle('on', s.reroll);
  const st = document.querySelector('.state[data-panel="'+CSS.escape(id)+'"]');
  if (st) st.textContent = s.reroll ? 'reroll' : (s.pick ? 'picked #' + s.pick : '');
}}
document.querySelectorAll('.cand').forEach(b => b.onclick = () => {{
  if (LOCKED.has(b.dataset.panel)) return;
  const s = ent(b.dataset.panel); s.pick = b.dataset.pick; s.reroll = false; paint(b.dataset.panel);
}});
document.querySelectorAll('.reroll').forEach(b => b.onclick = () => {{
  const s = ent(b.dataset.panel); s.reroll = !s.reroll; if (s.reroll) s.pick = null; paint(b.dataset.panel);
}});
document.querySelectorAll('textarea.note').forEach(t => t.oninput = () => {{ ent(t.dataset.panel).comment = t.value; }});
document.querySelectorAll('textarea.text').forEach(t => t.oninput = () => {{ ent(t.dataset.panel).text = t.value; }});
Object.keys(state).forEach(paint);

const send = document.getElementById('send'), msg = document.getElementById('msg'), dump = document.getElementById('dump');
send.onclick = async () => {{
  const payload = {{batch: BATCH, story: STORY, chapter: CHAPTER,
                   submittedAt: new Date().toISOString(), panels: state}};
  if (MODE !== 'server') {{
    dump.style.display = 'block'; dump.value = JSON.stringify(payload, null, 2); dump.select();
    msg.textContent = "No server here: copy this JSON to your AI, or run tools/review.py without --static.";
    return;
  }}
  send.disabled = true; msg.textContent = "saving…";
  try {{
    const r = await fetch('/submit', {{method:'POST', headers:{{'Content-Type':'application/json'}},
                                     body: JSON.stringify(payload)}});
    const j = await r.json();
    if (!r.ok || !j.ok) throw new Error(j.error || ('HTTP ' + r.status));
    msg.textContent = "Saved — tell your AI 'picks in'";
    send.disabled = false; send.textContent = "Submit again";
  }} catch (e) {{
    msg.textContent = "could not save: " + (e && e.message ? e.message : e);
    send.disabled = false;
  }}
}};
</script></body></html>'''


def make_handler(batch_path, title):
    spec, cand_dir, review_file = paths(batch_path)
    cand_root = cand_dir.resolve()

    @lru_cache(maxsize=256)
    def thumb(path_str, mtime):
        return jpeg_bytes(path_str, 1000, 76)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def send(self, code, body, ctype):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            url = urllib.parse.urlparse(self.path)
            if url.path in ("/", "/index.html"):
                page = build_page(batch_path, lambda f: "/img/" + urllib.parse.quote(f.name), title)
                return self.send(200, page.encode("utf-8"), "text/html; charset=utf-8")
            if url.path.startswith("/img/"):
                name = urllib.parse.unquote(url.path[len("/img/"):])
                f = (cand_dir / name).resolve()
                if f.parent != cand_root or not f.is_file():
                    return self.send(404, b"not found", "text/plain")
                try:
                    return self.send(200, thumb(str(f), f.stat().st_mtime), "image/jpeg")
                except Exception:
                    ctype = mimetypes.guess_type(str(f))[0] or "application/octet-stream"
                    return self.send(200, f.read_bytes(), ctype)
            if url.path == "/review.json" and review_file.exists():
                return self.send(200, review_file.read_bytes(), "application/json")
            return self.send(404, b"not found", "text/plain")

        def do_POST(self):
            if urllib.parse.urlparse(self.path).path != "/submit":
                return self.send(404, b"not found", "text/plain")
            try:
                n = int(self.headers.get("Content-Length", "0"))
                data = json.loads(self.rfile.read(n).decode("utf-8"))
                panels = {}
                for pid, s in (data.get("panels") or {}).items():
                    s = s or {}
                    panels[str(pid)] = {"pick": None if s.get("pick") in (None, "") else str(s["pick"]),
                                        "reroll": bool(s.get("reroll")),
                                        "comment": str(s.get("comment") or ""),
                                        "text": str(s.get("text") or "")}
                out = {"batch": batch_path.stem, "story": spec["story"], "chapter": spec["chapter"],
                       "submittedAt": data.get("submittedAt")
                       or datetime.now(timezone.utc).isoformat(timespec="seconds"),
                       "panels": panels}
                review_file.parent.mkdir(parents=True, exist_ok=True)
                review_file.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
                print(f"saved {review_file}", flush=True)
                body = json.dumps({"ok": True, "path": str(review_file)}).encode()
                return self.send(200, body, "application/json")
            except Exception as e:
                return self.send(400, json.dumps({"ok": False, "error": str(e)}).encode(), "application/json")

    return Handler


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("batch", help="batch JSON (same file panel_batch.py consumed)")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--no-open", action="store_true", help="do not open a browser")
    ap.add_argument("--title", help="page title (default '<chapter> · <batch-stem>')")
    ap.add_argument("--static", metavar="OUT_HTML", help="write a standalone page and exit, no server")
    a = ap.parse_args()
    batch_path = resolve(a.batch)
    if not batch_path.exists():
        sys.exit(f"No such batch: {batch_path}")
    _, _, review_file = paths(batch_path)

    if a.static:
        out = Path(a.static).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        import os
        page = build_page(batch_path, lambda f: urllib.parse.quote(
            os.path.relpath(Path(f).resolve(), out.parent).replace(os.sep, "/")), a.title, mode="static")
        out.write_text(page, encoding="utf-8")
        print(f"wrote {out}")
        return

    server = ThreadingHTTPServer((a.host, a.port), make_handler(batch_path, a.title))
    url = f"http://{a.host}:{server.server_address[1]}/"
    print(f"review page: {url}")
    print(f"picks will be saved to: {review_file}")
    print("Ctrl+C to stop.", flush=True)
    if not a.no_open:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
