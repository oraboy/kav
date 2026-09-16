#!/usr/bin/env python3
"""Build the two self-contained reader pages for one or more chapters of a story.

  reader-comic.html   every assembled page stacked top to bottom, a header per chapter
  reader-story.html  every carousel panel as one 4:5 slide (swipe, tap sides, arrows,
                        pinch-zoom), with a divider slide before each chapter

Images are embedded (downscaled JPEG data URIs), so each file stands alone. Inputs come
from assemble.py: stories/<story>/chapters/<ch>/pages/pNN.png and pages/carousel/*.jpg.
Chapter titles are the first "# heading" of stories/<story>/storyboard/<ch>.md, else the
chapter id. Every reader links home (--home-url) and, at the end, on to the same mode of
the next chapter (--next-story-url for the carousel, --next-pages-url for the classic).
All links use target=_top so they work inside an embedding frame. Text direction and the
brand line default from stories/<story>/story.json ("dir", "lang", "title").
"""
import argparse
import html as H
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kav_env import REPO, jpeg_data_uri, story_meta  # noqa: E402

FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
         'family=Karantina:wght@700&family=Varela+Round&display=swap">')
RTL_LANGS = {"he", "ar", "fa", "ur", "yi"}


def chapter_title(story, ch, label=""):
    card = REPO / "stories" / story / "storyboard" / f"{ch}.md"
    if card.exists():
        lines = card.read_text(encoding="utf-8").splitlines()
        m = re.match(r"#\s*(.+)", lines[0]) if lines else None
        if m:
            t = m.group(1).strip()
            if label:
                t = re.sub(r"^Ch(?:apter)?\s*0?", label + " ", t).strip()
            return t
    return ch


def page_files(pages_dir):
    return sorted((p for p in pages_dir.glob("p*.png") if re.fullmatch(r"p\d+", p.stem)),
                  key=lambda p: int(p.stem[1:]))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--story", required=True, help="story slug")
    ap.add_argument("--chapters", nargs="+", required=True, help="chapter ids, e.g. ch01 ch02")
    ap.add_argument("--title", required=True, help="page title (tab title and classic header)")
    ap.add_argument("--out", required=True, help="output folder (relative to the repo or absolute)")
    ap.add_argument("--brand", default=None,
                    help="story name above the chapter name on each divider (default: story.json title, or empty)")
    ap.add_argument("--next", default="", help="line on the final slide, e.g. 'Chapter 4 · coming soon'")
    ap.add_argument("--next-story-url", default="", help="next chapter, carousel reader")
    ap.add_argument("--next-pages-url", default="", help="next chapter, classic reader")
    ap.add_argument("--next-label", default="Next chapter →")
    ap.add_argument("--home-url", default="", help="link back to the story's trailer or home page")
    ap.add_argument("--home-label", default="Home")
    ap.add_argument("--chapter-label", default="",
                    help="word replacing a leading 'Ch'/'Chapter' in storyboard headings")
    ap.add_argument("--end-mark", default="", help="small line (e.g. an emoji) above the final slide text")
    ap.add_argument("--dir", choices=["rtl", "ltr"], help="text direction (default from story.json)")
    ap.add_argument("--footer", default="")
    # A whole book of panels gets heavy; these dial the embedded images back.
    ap.add_argument("--page-px", type=int, default=1500)
    ap.add_argument("--slide-px", type=int, default=1080)
    ap.add_argument("--slide-q", type=int, default=82)
    a = ap.parse_args()

    meta = story_meta(a.story)
    brand = a.brand if a.brand is not None else meta.get("title", "")
    direction = a.dir or meta.get("dir") or ("rtl" if meta.get("lang") in RTL_LANGS else "ltr")
    out = Path(a.out) if Path(a.out).is_absolute() else REPO / a.out
    out.mkdir(parents=True, exist_ok=True)

    def onward_link(url):
        return (f'<a class="onward" href="{H.escape(url, quote=True)}" target="_top">'
                f'{H.escape(a.next_label)}</a>') if url else ""

    house = ('<svg class="hico" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path '
             'd="M3 11.5 12 4l9 7.5M5.5 9.5V20h5v-6h3v6h5V9.5" fill="none" stroke="currentColor" '
             'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>')
    home = (f'<a class="home" href="{H.escape(a.home_url, quote=True)}" target="_top">{house}'
            f'<span>{H.escape(a.home_label)}</span></a>' if a.home_url else "")
    onward = onward_link(a.next_story_url)
    onward_classic = (f'<div class="onwrap">{onward_link(a.next_pages_url)}</div>'
                      if a.next_pages_url else "")

    classic_parts, slides = [], []
    for ch in a.chapters:
        pages_dir = REPO / "stories" / a.story / "chapters" / ch / "pages"
        if not pages_dir.is_dir():
            sys.exit(f"No pages for {ch}: run assemble.py first ({pages_dir})")
        title = chapter_title(a.story, ch, a.chapter_label)
        classic_parts.append(f'<h2 class="chead">{H.escape(title)}</h2>')
        for p in page_files(pages_dir):
            classic_parts.append(f'<img class="page" src="{jpeg_data_uri(p, a.page_px, 80)}" alt="">')
        slides.append(f'''
<section class="slide divider"><div class="txt center"><p class="brand">{H.escape(brand)}</p>
<h2>{H.escape(title)}</h2>{home}</div></section>''')
        for c in sorted((pages_dir / "carousel").glob("*.jpg")):
            slides.append(f'<section class="slide"><div class="frame">'
                          f'<img src="{jpeg_data_uri(c, a.slide_px, a.slide_q)}" alt=""></div>'
                          f'<p class="sub" data-text=""></p></section>')

    if a.next or onward:
        mark = f'<p class="paw">{H.escape(a.end_mark)}</p>' if a.end_mark else ""
        slides.append(f'''
<section class="slide opener"><div class="txt center">{mark}
<p class="sub" data-text="{H.escape(a.next, quote=True)}"></p>{onward}{home}</div></section>''')

    footer = a.footer or a.title
    classic = f'''<title>{H.escape(a.title)}</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
{FONTS}
<style>
:root{{--ink:#0f1720;--cream:#f4ecd6;--sand:#cfc2a3;--accent:#d9a066}}
body{{margin:0;background:var(--ink);color:var(--cream);
     font-family:'Varela Round','Arial Hebrew',sans-serif;direction:{direction}}}
header{{text-align:center;padding:44px 20px 10px}}
h1{{font-family:'Karantina',sans-serif;font-weight:700;font-size:clamp(56px,10vw,96px);
   line-height:.9;margin:0}}
.chead{{font-family:'Karantina',sans-serif;font-weight:700;font-size:clamp(34px,6vw,52px);
       text-align:center;color:var(--accent);margin:52px 0 6px}}
.pages{{max-width:1100px;margin:0 auto;padding:10px 12px 80px;display:flex;
       flex-direction:column;gap:26px}}
.page{{width:100%;height:auto;display:block;border-radius:6px;
      box-shadow:0 20px 60px rgba(0,0,0,.6)}}
.onwrap{{text-align:center;padding:34px 0 10px}}
.home{{display:inline-flex;align-items:center;gap:8px;margin-top:14px;color:var(--sand);font-size:15px;text-decoration:none;
      border-bottom:1px solid rgba(207,194,163,.4);padding-bottom:2px}}
.onward{{display:inline-block;padding:14px 30px;border-radius:28px;background:var(--accent);
        color:var(--ink);font-size:17px;font-weight:700;text-decoration:none}}
footer{{text-align:center;color:var(--sand);font-size:13px;padding:0 0 50px}}
</style>
<header><h1>{H.escape(a.title)}</h1>{home}</header>
<div class="pages">{''.join(classic_parts)}{onward_classic}<div class="onwrap">{home}</div></div>
<footer>{H.escape(footer)}</footer>
'''
    (out / "reader-comic.html").write_text(classic, encoding="utf-8")
    print(f"wrote {out / 'reader-comic.html'} ({len(classic.encode()) / 1e6:.1f} MB)")

    n = len(slides)
    dots = "".join("<i></i>" for _ in range(n))
    carousel = f'''<title>{H.escape(a.title)}</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
{FONTS}
<style>
:root{{--ink:#0f1720;--cream:#f4ecd6;--sand:#cfc2a3;--accent:#d9a066}}
*{{box-sizing:border-box}}
html,body{{margin:0;height:100%;background:var(--ink);color:var(--cream);
          font-family:'Varela Round','Arial Hebrew',sans-serif;overflow:hidden;
          user-select:none;-webkit-user-select:none}}
/* pinch-zoom: touch-action must name it explicitly, or the browser hands every gesture to
   the horizontal scroller and a pinch does nothing. While zoomed, snapping and the tap
   zones get out of the way so the reader can pan around the panel. */
.deck{{display:flex;height:100dvh;overflow-x:auto;overflow-y:hidden;scroll-snap-type:x mandatory;
      scroll-behavior:smooth;scrollbar-width:none;direction:ltr;
      touch-action:pan-x pinch-zoom;cursor:pointer}}
body.zoomed .deck{{scroll-snap-type:none;touch-action:auto;overflow:auto}}
body.zoomed .dots,body.zoomed .nav{{opacity:0;pointer-events:none}}
.deck::-webkit-scrollbar{{display:none}}
.slide{{position:relative;flex:0 0 100%;width:100%;height:100dvh;scroll-snap-align:start;
       scroll-snap-stop:always;overflow:hidden;background:var(--ink);direction:{direction};
       display:flex;align-items:center;justify-content:center}}
.frame{{width:100%;max-width:min(100vw,calc((100dvh - 90px) * 0.8));padding:0 10px}}
.frame img{{width:100%;height:auto;display:block;border-radius:4px;pointer-events:none}}
.txt.center{{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;
            align-items:center;text-align:center;padding:0 28px 84px}}
h1{{font-family:'Karantina',sans-serif;font-weight:700;font-size:clamp(84px,22vw,150px);
   line-height:.88;margin:0 0 14px}}
h2{{font-family:'Karantina',sans-serif;font-weight:700;font-size:clamp(30px,6.4vw,64px);
   line-height:1;margin:0;color:var(--cream);white-space:nowrap}}
.brand{{font-family:'Karantina',sans-serif;font-weight:700;font-size:clamp(22px,4.4vw,40px);
       line-height:1;margin:0 0 10px;color:var(--accent);white-space:nowrap;letter-spacing:.01em}}
.divider{{background:var(--ink)}}
.paw{{font-size:60px;margin:0 0 8px}}
.sub{{font-size:17px;line-height:1.65;color:var(--sand);margin:0;max-width:34ch;min-height:1em}}
.slide:not(.opener):not(.divider) .sub{{position:absolute;bottom:56px}}
.dots{{position:fixed;bottom:calc(env(safe-area-inset-bottom) + 18px);left:0;right:0;display:flex;
      justify-content:center;gap:3px;pointer-events:none;z-index:5;flex-wrap:wrap;padding:0 20px}}
.dots i{{width:4px;height:4px;border-radius:50%;background:rgba(244,236,214,.28);transition:all .25s}}
.dots i.on{{background:var(--cream);width:14px;border-radius:3px}}
.home{{display:inline-flex;align-items:center;justify-content:center;gap:8px;margin-top:22px;color:var(--sand);font-size:15px;text-decoration:none;
      position:relative;z-index:6}}
.onward{{display:inline-block;margin-top:22px;padding:14px 30px;border-radius:28px;
        background:var(--accent);color:var(--ink);font-size:17px;font-weight:700;
        text-decoration:none;position:relative;z-index:6}}
.nav{{position:fixed;top:50%;transform:translateY(-50%);width:44px;height:44px;border-radius:50%;
     border:1px solid rgba(244,236,214,.25);background:rgba(15,23,32,.55);color:var(--cream);
     font-size:22px;display:none;align-items:center;justify-content:center;cursor:pointer;z-index:5}}
.nav.prev{{left:14px}} .nav.next{{right:14px}}
@media (hover:hover) and (min-width:700px){{.nav{{display:flex}}
  .deck{{width:520px;margin:0 auto;box-shadow:0 0 0 1px rgba(244,236,214,.12)}}
  .nav.prev{{left:calc(50% - 260px - 58px)}} .nav.next{{right:calc(50% - 260px - 58px)}} }}
</style>
<div class="deck" id="deck">{''.join(slides)}</div>
<div class="dots" id="dots">{dots}</div>
<button class="nav prev" id="prev" aria-label="Previous">‹</button>
<button class="nav next" id="next" aria-label="Next">›</button>
<script>
const deck=document.getElementById('deck');
const slides=[...deck.querySelectorAll('.slide')];
const subs=slides.map(s=>s.querySelector('.sub'));
const dots=[...document.querySelectorAll('#dots i')];
let cur=0, zoomed=false;
subs.forEach(sub=>{{ if(sub) sub.textContent=sub.dataset.text||''; }});
function setDot(i){{dots.forEach((d,k)=>d.classList.toggle('on',k===i));cur=i;}}
function go(i){{i=Math.max(0,Math.min(slides.length-1,i));
  slides[i].scrollIntoView({{behavior:'smooth',inline:'start',block:'nearest'}});}}
setDot(0);
const io=new IntersectionObserver(es=>{{es.forEach(e=>{{if(e.isIntersecting&&e.intersectionRatio>.6)
  setDot(slides.indexOf(e.target));}});}},{{root:deck,threshold:[.6]}});
slides.forEach(s=>io.observe(s));
document.getElementById('next').onclick=()=>go(cur+1);
document.getElementById('prev').onclick=()=>go(cur-1);
// Story-style navigation: swipe, or tap a side. A tap on a link is the link's; browsers
// suppress the click that ends a touch scroll, so a swipe never double-fires as a tap.
deck.addEventListener('click',e=>{{ if(zoomed||e.target.closest('a,button')) return;
  const r=deck.getBoundingClientRect();
  go(e.clientX-r.left < r.width*0.33 ? cur-1 : cur+1); }});
deck.addEventListener('dragstart',e=>e.preventDefault());
// While pinched in, the deck stops behaving like a deck: no snap, no tap-flip, so panning
// around a zoomed panel doesn't skip slides.
if(window.visualViewport){{
  const vv=window.visualViewport;
  const sync=()=>{{ const z=vv.scale>1.05; if(z!==zoomed){{ zoomed=z;
    document.body.classList.toggle('zoomed',z); }} }};
  vv.addEventListener('resize',sync); vv.addEventListener('scroll',sync);
}}
addEventListener('keydown',e=>{{ if(zoomed) return;
  if(e.key==='ArrowRight'||e.code==='Space'){{ e.preventDefault(); if(!e.repeat) go(cur+1); }}
  if(e.key==='ArrowLeft'){{ e.preventDefault(); if(!e.repeat) go(cur-1); }} }});
</script>
'''
    (out / "reader-story.html").write_text(carousel, encoding="utf-8")
    print(f"wrote {out / 'reader-story.html'} ({len(carousel.encode()) / 1e6:.1f} MB, {n} slides)")


if __name__ == "__main__":
    main()
