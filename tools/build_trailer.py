#!/usr/bin/env python3
"""Build a story's trailer: a phone-first slide deck that is also the doorway into the book.

Reads stories/<slug>/package/trailer.json (see tools/examples/trailer.example.json) and
writes stories/<slug>/package/trailer.html, one self-contained page with images embedded.
Navigation works like a phone story: swipe, tap the right two-thirds to go forward and the
left third to go back, arrow keys, dots. Chapter slides carry one pill per reading mode
(story = carousel reader, comic = classic pages); a chapter without reader links shows
the "wip" label. --statics also renders every slide to package/slides/slide-NN.png at
1080x1920 for posting as an image carousel (needs Chrome).

Image paths in trailer.json are relative to stories/<slug>/. Cast items take "char"
(portrait from cast/<char>/[<portrait_pack>/]front.png) or an explicit "image".
"""
import argparse
import html as H
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kav_env import jpeg_data_uri, story_dir  # noqa: E402
import kav_refs  # noqa: E402

DEFAULT_FONT_URL = "https://fonts.googleapis.com/css2?family=Karantina:wght@400;700&family=Varela+Round&display=swap"
DEFAULT_LABELS = {"story": "Story", "comic": "Comic", "wip": "In progress", "chapter": "Chapter",
                  "prev": "Previous", "next": "Next"}

CSS = '''
:root{--ink:#0f1720;--ink2:#182233;--cream:#f4ecd6;--sand:#cfc2a3;--mute:#9a9078;--accent:#d9a066}
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:var(--ink);color:var(--cream);font-family:__BODY__;overflow:hidden;-webkit-user-select:none;user-select:none;-webkit-touch-callout:none}
.deck{display:flex;height:100dvh;overflow-x:auto;overflow-y:hidden;scroll-snap-type:x mandatory;scroll-behavior:smooth;scrollbar-width:none;direction:ltr;touch-action:pan-x pinch-zoom;cursor:pointer}
.deck::-webkit-scrollbar{display:none}
.slide{position:relative;flex:0 0 100%;width:100%;height:100dvh;scroll-snap-align:start;scroll-snap-stop:always;overflow:hidden;background:var(--ink);direction:__DIR__}
.bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center top;pointer-events:none}
.shade{position:absolute;inset:0;background:linear-gradient(to top,rgba(15,23,32,.96) 0%,rgba(15,23,32,.75) 30%,rgba(15,23,32,.15) 60%,rgba(15,23,32,0) 100%)}
.shade.top{background:linear-gradient(to bottom,rgba(15,23,32,.9) 0%,rgba(15,23,32,.55) 28%,rgba(15,23,32,0) 55%)}
.txt{position:absolute;right:0;left:0;bottom:0;padding:0 28px calc(env(safe-area-inset-bottom) + 84px)}
.txt.top{bottom:auto;top:0;padding:calc(env(safe-area-inset-top) + 56px) 28px 0}
.txt.center{top:0;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding-bottom:84px}
h1{font-family:__HEADING__;font-weight:700;font-size:clamp(84px,22vw,150px);line-height:.88;margin:0 0 14px;letter-spacing:.01em}
h2{font-family:__HEADING__;font-weight:700;font-size:clamp(46px,12vw,76px);line-height:.95;margin:0 0 12px}
.eyebrow{font-size:13px;letter-spacing:.14em;color:var(--accent);margin:0 0 10px;font-weight:700}
.sub{font-size:17px;line-height:1.65;color:var(--sand);margin:0;max-width:36ch;min-height:2.5em}
.opener .sub{font-size:19px;color:var(--cream);max-width:34ch}
.divider .txt{padding-bottom:0}
.start .modes{justify-content:center}
.divider h2{font-size:clamp(70px,20vw,120px)}
.cast .portrait{width:min(60vw,280px);aspect-ratio:1;margin:0 auto 30px}
.cast .portrait img{width:100%;height:100%;object-fit:cover;border-radius:50%;border:3px solid var(--cream);box-shadow:0 18px 40px rgba(0,0,0,.6);pointer-events:none}
.cast .sub{max-width:30ch}
.also h2{font-size:clamp(70px,20vw,120px)}
.modes{position:relative;z-index:6;display:flex;gap:10px;margin-top:18px}
.read{display:inline-block;padding:10px 22px;border-radius:24px;background:var(--cream);color:var(--ink);font-size:15px;font-weight:700;text-decoration:none;letter-spacing:.02em}
.read.alt{background:transparent;color:var(--cream);border:1px solid rgba(244,236,214,.55);font-weight:400}
.wip{display:inline-block;margin-top:18px;padding:10px 22px;border-radius:24px;border:1px solid rgba(244,236,214,.3);color:var(--sand);font-size:14px}
.dots{position:fixed;bottom:calc(env(safe-area-inset-bottom) + 22px);left:0;right:0;display:flex;justify-content:center;gap:7px;pointer-events:none;z-index:5}
.dots i{width:6px;height:6px;border-radius:50%;background:rgba(244,236,214,.28);transition:all .25s}
.dots i.on{background:var(--cream);width:18px;border-radius:3px}
.nav{position:fixed;top:50%;transform:translateY(-50%);width:44px;height:44px;border-radius:50%;border:1px solid rgba(244,236,214,.25);background:rgba(15,23,32,.55);color:var(--cream);font-size:22px;display:none;align-items:center;justify-content:center;cursor:pointer;z-index:5}
.nav.prev{left:14px} .nav.next{right:14px}
@media (hover:hover) and (min-width:700px){.nav{display:flex} .deck{width:480px;margin:0 auto;box-shadow:0 0 0 1px rgba(244,236,214,.12)} .nav.prev{left:calc(50% - 240px - 58px)} .nav.next{right:calc(50% - 240px - 58px)} }
@media (prefers-reduced-motion:reduce){.deck{scroll-behavior:auto}}
'''

JS = '''
const STATIC = !!window.__STATIC__;
const deck=document.getElementById('deck');
const slides=[...deck.querySelectorAll('.slide')];
const dots=[...document.querySelectorAll('#dots i')];
let cur=0;
function setDot(i){dots.forEach((d,k)=>d.classList.toggle('on',k===i));cur=i;}
function go(i){i=Math.max(0,Math.min(slides.length-1,i));slides[i].scrollIntoView({behavior:'smooth',inline:'start',block:'nearest'});}
if(!STATIC){
  setDot(0);
  const io=new IntersectionObserver(es=>{es.forEach(e=>{if(e.isIntersecting&&e.intersectionRatio>.6)setDot(slides.indexOf(e.target));});},{root:deck,threshold:[.6]});
  slides.forEach(s=>io.observe(s));
  document.getElementById('next').onclick=()=>go(cur+1);
  document.getElementById('prev').onclick=()=>go(cur-1);
}
// Story-style navigation: swipe, or tap a side. Touch swiping is the browser's own
// (scroll-snap); a tap on the right two-thirds goes forward, the left third goes back.
// A tap that lands on a link is the link's. Browsers suppress the click that ends a touch
// scroll, so a swipe never double-fires as a tap.
deck.addEventListener('click',e=>{
  if(STATIC||e.target.closest('a,button')) return;
  const r=deck.getBoundingClientRect();
  go(e.clientX-r.left < r.width*0.33 ? cur-1 : cur+1);
});
deck.addEventListener('dragstart',e=>e.preventDefault());
// preventDefault on the arrows: the deck is a scroll container, and the browser's own
// arrow-key nudge would get snapped into a whole slide on top of our own move.
addEventListener('keydown',e=>{
  if(e.key==='ArrowRight'){ e.preventDefault(); if(!e.repeat) go(cur+1); }
  if(e.key==='ArrowLeft'){ e.preventDefault(); if(!e.repeat) go(cur-1); }
  if(e.code==='Space'){ e.preventDefault(); if(!e.repeat) go(cur+1); }
});
'''


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--story", required=True, help="story slug")
    ap.add_argument("--config", help="trailer JSON (default stories/<slug>/package/trailer.json)")
    ap.add_argument("--out", help="output HTML (default stories/<slug>/package/trailer.html)")
    ap.add_argument("--statics", action="store_true",
                    help="also render package/slides/slide-NN.png at 1080x1920 (needs Chrome)")
    a = ap.parse_args()

    S = story_dir(a.story)
    kav_refs.set_story(a.story)
    cfg_path = Path(a.config) if a.config else S / "package" / "trailer.json"
    if not cfg_path.exists():
        sys.exit(f"No trailer config at {cfg_path} (see tools/examples/trailer.example.json)")
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    out_html = Path(a.out) if a.out else S / "package" / "trailer.html"
    slides_dir = out_html.parent / "slides"
    labels = {**DEFAULT_LABELS, **cfg.get("labels", {})}
    direction = cfg.get("dir", "ltr")
    fonts = cfg.get("fonts") or {}
    font_urls = fonts.get("urls", [DEFAULT_FONT_URL])
    heading = fonts.get("heading", "'Karantina',sans-serif")
    body = fonts.get("body", "'Varela Round','Arial Hebrew',sans-serif")
    pack = cfg.get("portrait_pack")

    def img(rel, px=1100, q=72):
        p = (S / rel) if not Path(rel).is_absolute() else Path(rel)
        if not p.exists():
            sys.exit(f"Trailer image not found: {p}")
        return jpeg_data_uri(p, px, q)

    def sub(text):
        # always visible: the deck reads like a phone story, nothing to reveal or wait for
        return f'<p class="sub">{H.escape(text or "")}</p>'

    def read_links(ch):
        """A drawn chapter offers one pill per reading mode; an undrawn one says so."""
        urls = (ch or {}).get("readers") or {}
        pills = [f'<a class="{cls}" href="{H.escape(urls[key], quote=True)}" target="_top">'
                 f'{H.escape(labels[key])}</a>'
                 for key, cls in (("story", "read"), ("comic", "read alt")) if urls.get(key)]
        if not pills:
            return f'<span class="wip">{H.escape(labels["wip"])}</span>'
        return '<div class="modes">' + "".join(pills) + '</div>'

    chapters_by_num = {}
    for sec in cfg.get("sections", []):
        if sec.get("type") == "chapters":
            for it in sec.get("items", []):
                chapters_by_num[str(it.get("num"))] = it

    title = cfg.get("title", a.story)
    slides = []
    op = cfg.get("opener") or {}
    title_html = "<br>".join(H.escape(t) for t in title.split("\n"))
    slides.append(f'''
<section class="slide opener">
  {f'<img class="bg" src="{img(op["image"])}" alt="">' if op.get("image") else ''}
  <div class="shade"></div>
  <div class="txt">
    <h1>{title_html}</h1>
    {sub(op.get("sub", ""))}
  </div>
</section>''')

    for sec in cfg.get("sections", []):
        kind = sec.get("type")
        if kind == "divider":
            slides.append(f'''
<section class="slide divider">
  <div class="txt center">
    <h2>{H.escape(sec.get("title", ""))}</h2>
    {sub(sec["sub"]) if sec.get("sub") else ''}
  </div>
</section>''')
        elif kind == "cast":
            for it in sec.get("items", []):
                if it.get("image"):
                    src = img(it["image"], 900)
                else:
                    src = jpeg_data_uri(kav_refs.portrait_path(it["char"], it.get("pack", pack)), 900, 72)
                name = it.get("name") or it.get("char", "")
                slides.append(f'''
<section class="slide cast">
  <div class="txt center">
    <div class="portrait"><img src="{src}" alt="{H.escape(name, quote=True)}"></div>
    <h2>{H.escape(name)}</h2>
    {sub(it.get("line", ""))}
  </div>
</section>''')
        elif kind == "also":
            slides.append(f'''
<section class="slide also">
  {f'<img class="bg" src="{img(sec["image"])}" alt="">' if sec.get("image") else ''}
  <div class="shade top"></div>
  <div class="txt top">
    <h2>{H.escape(sec.get("title", ""))}</h2>
    {sub(sec.get("sub", ""))}
  </div>
</section>''')
        elif kind == "chapters":
            for it in sec.get("items", []):
                slides.append(f'''
<section class="slide chapter">
  {f'<img class="bg" src="{img(it["image"])}" alt="">' if it.get("image") else ''}
  <div class="shade"></div>
  <div class="txt">
    <p class="eyebrow">{H.escape(labels["chapter"])} {H.escape(str(it.get("num", "")))}</p>
    <h2>{H.escape(it.get("title", ""))}</h2>
    {sub(it.get("synopsis", ""))}
    {read_links(it)}
  </div>
</section>''')
        elif kind == "closer":
            num = str(sec.get("chapter", "01"))
            slides.append(f'''
<section class="slide divider start">
  <div class="txt center">
    <h2>{H.escape(sec.get("title") or (labels["chapter"] + " " + num))}</h2>
    {read_links(chapters_by_num.get(num))}
  </div>
</section>''')
        else:
            sys.exit(f"Unknown section type: {kind!r} (divider, cast, also, chapters, closer)")

    n = len(slides)
    dots = "".join("<i></i>" for _ in range(n))
    css = CSS.replace("__DIR__", direction).replace("__HEADING__", heading).replace("__BODY__", body)
    links = "".join(f'<link rel="stylesheet" href="{H.escape(u, quote=True)}">' for u in font_urls)

    def render(static_index=None):
        head = ""
        if static_index is not None:
            head = ('<script>window.__STATIC__=1</script>'
                    '<style>.slide{display:none!important}'
                    f'.slide:nth-child({static_index + 1}){{display:block!important;flex-basis:100%!important;margin:0!important}}'
                    '.dots,.nav{display:none!important}</style>')
        # <title> is what a link unfurler shows as the card headline: reader-facing text.
        return f'''<!doctype html><html lang="{H.escape(cfg.get("lang", ""), quote=True)}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{H.escape(title.replace(chr(10), " "))}</title>
{links}
<style>{css}</style>
{head}</head><body>
<div class="deck" id="deck">{''.join(slides)}</div>
<div class="dots" id="dots">{dots}</div>
<button class="nav prev" id="prev" aria-label="{H.escape(labels["prev"], quote=True)}">‹</button>
<button class="nav next" id="next" aria-label="{H.escape(labels["next"], quote=True)}">›</button>
<script>{JS}</script>
</body></html>
'''

    out_html.parent.mkdir(parents=True, exist_ok=True)
    page = render()
    out_html.write_text(page, encoding="utf-8")
    print(f"wrote {out_html} ({len(page.encode()) / 1e6:.1f} MB, {n} slides)")

    if a.statics:
        import chrome
        tmp = Path(tempfile.mkdtemp(prefix="kav-trailer-"))
        slides_dir.mkdir(parents=True, exist_ok=True)
        for i in range(n):
            f = tmp / f"slide-{i + 1:02d}.html"
            f.write_text(render(i), encoding="utf-8")
            png = slides_dir / f"slide-{i + 1:02d}.png"
            chrome.screenshot(f, png, 540, 960, scale=2, budget_ms=6000)
            print("static", png)


if __name__ == "__main__":
    main()
