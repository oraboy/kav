#!/usr/bin/env python3
"""Post a story's panels to Instagram, and read back how they did.

Uses the Instagram API with Instagram Login (graph.instagram.com): a professional
(Creator or Business) account and a long-lived token in <repo>/.env. No Facebook Page.
Setup walk-through: docs/know-how/instagram.md.

  python3 tools/instagram.py auth [--refresh]
      Who the token belongs to. --refresh trades it for a fresh 60-day token and
      rewrites INSTAGRAM_ACCESS_TOKEN in .env (the value is never printed).

  python3 tools/instagram.py draft --story <slug> --chapter chNN [--panels id,id,...]
  python3 tools/instagram.py draft --story <slug> --post <folder>
  python3 tools/instagram.py draft --story <slug> --images a.png b.png --unit <name>
      Write a post plan: the images as Instagram-ready JPEGs, and a caption drafted
      from the panels' own lettering (plus a post's "Post copy" when it has one).
      Nothing is sent anywhere. More than 10 chapter panels are split into several plans.

  python3 tools/instagram.py draft --story <slug> --chapter chNN --as-story [--panels ...]
      A chapter as an Instagram Story: 1080x1920 frames for a title frame (every panel in
      a grid, story and chapter titles from story.json and the storyboard card), each
      panel, and a chapter-end frame (emoji, next chapter's title, "continue reading").
      Writes a kind: story plan. Nothing is sent.

  python3 tools/instagram.py post <plan.json> [--yes] [--host fal] [--again] [--from N]
      Without --yes: print exactly what would be posted and stop. With --yes: publish.
      One image is a single post, 2-10 a carousel. A Story plan publishes each frame as
      its own Story (20s apart) and logs it to stories.jsonl, except the chapter-end
      frame: a link sticker can only be added in the app while making a Story, so the
      author posts that one by hand with the sticker (--include-end-frame to publish it
      without a link), then adds the Story to a Highlight.

  python3 tools/instagram.py link --story <slug> --unit chNN (--permalink URL | --media-id ID)
      Register a post made by hand, so stats count it.

  python3 tools/instagram.py stats --story <slug> [--comments] [--json]
      Likes, comments, views, reach, saves and shares for every recorded post,
      grouped by chapter. Writes stories/<slug>/instagram/stats.json and appends
      a snapshot to stats-history.jsonl.

Files, all under stories/<slug>/instagram/:
  drafts/<name>.json   post plans: {story, unit, panels, images: [{file, url?, user_tags?}],
                       caption, credit, published?}
  media/               the prepared JPEGs
  posts.jsonl          one row per published post
  stories.jsonl        one row per published Story frame
  stats.json           the latest stats snapshot

Images have to be fetched by Instagram from a public URL. An image entry with "url"
is used as-is (a reader the author already published). Otherwise --host fal uploads
the JPEG to fal.ai storage (needs FAL_KEY) and uses that link.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kav_env import REPO, get_key, load_env_key, require_key, resolve, story_dir, story_meta  # noqa: E402

HOST = "https://graph.instagram.com"
VERSION = os.environ.get("KAV_IG_API_VERSION", "v25.0")
MAX_ITEMS = 10            # the API's carousel cap (the app allows more)
MAX_CAPTION = 2200
MAX_MENTIONS = 20
MAX_HASHTAGS = 30
MIN_AR, MAX_AR = 4 / 5, 1.91
MAX_WIDTH = 1440
MAX_BYTES = 8 * 1024 * 1024
CREDIT = "Built with Kav · github.com/oraboy/kav"
INSIGHTS = ["views", "reach", "saved", "shares", "total_interactions"]
EXPIRY_KEY = "INSTAGRAM_TOKEN_EXPIRES"
HANDLE = re.compile(r"(?<![\w.])@([A-Za-z0-9_](?:[A-Za-z0-9_.]{0,28}[A-Za-z0-9_])?)")


# --- API -------------------------------------------------------------------------

def scrub(text, token):
    return text.replace(token, "<token>") if token else text


def api(method, path, token, params=None, timeout=120):
    """One Graph call. Raises RuntimeError with Meta's own message; never shows the token."""
    params = {k: v for k, v in (params or {}).items() if v is not None}
    url = path if path.startswith("http") else f"{HOST}/{VERSION}/{path.lstrip('/')}"
    data = None
    if method == "GET":
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode({**params, "access_token": token})
    else:
        data = urllib.parse.urlencode({**params, "access_token": token}).encode()
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            err = json.loads(body).get("error", {})
            msg = err.get("error_user_msg") or err.get("message") or body[:300]
            code = err.get("code")
        except ValueError:
            msg, code = body[:300], None
        hint = ""
        if code == 190:
            hint = "  (the token is invalid or expired: docs/know-how/instagram.md, step 4)"
        elif code == 10 or "permission" in str(msg).lower():
            hint = "  (the token is missing a permission: docs/know-how/instagram.md, step 3)"
        raise RuntimeError(scrub(f"Instagram API {e.code}: {msg}{hint}", token)) from None
    except urllib.error.URLError as e:
        raise RuntimeError(scrub(f"Could not reach Instagram: {e.reason}", token)) from None


def env_file_value(name):
    """NAME's value in <repo>/.env only, ignoring the shell environment."""
    env = REPO / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                if k.strip().removeprefix("export ").strip() == name and v.strip().strip("\"'"):
                    return v.strip().strip('"').strip("'")
    return None


def token_source():
    """(token, where it came from). Unlike Kav's other keys, the repo's .env wins over the
    shell: a token exported for another project would post to that project's account."""
    name = "INSTAGRAM_ACCESS_TOKEN"
    in_file, in_shell = env_file_value(name), (os.environ.get(name) or "").strip()
    if in_file:
        return in_file, ".env (a different one in the shell is ignored)" if in_shell and in_shell != in_file else ".env"
    return require_key(name), "shell environment"


def token():
    return token_source()[0]


def me(tok):
    return api("GET", "me", tok, {"fields": "user_id,username,account_type,media_count,followers_count"})


def expected_account(slug=None):
    """The handle this repo or story is meant to post as, without the @, or None."""
    name = (story_meta(slug).get("instagram") or {}).get("account") if slug else None
    name = name or env_file_value("INSTAGRAM_USERNAME") or load_env_key("INSTAGRAM_USERNAME")
    return name.lstrip("@").lower() if name else None


def set_env(name, value):
    """Set NAME=value in <repo>/.env, replacing an existing line."""
    env = REPO / ".env"
    lines = env.read_text(encoding="utf-8").splitlines() if env.exists() else []
    for i, line in enumerate(lines):
        if "=" in line and line.split("=", 1)[0].strip().removeprefix("export ").strip() == name:
            lines[i] = f"{name}={value}"
            break
    else:
        lines.append(f"{name}={value}")
    env.write_text("\n".join(lines) + "\n", encoding="utf-8")


def expiry_note():
    raw = load_env_key(EXPIRY_KEY)
    if not raw:
        return "token expiry unknown: run `auth --refresh` once to record it"
    try:
        left = (date.fromisoformat(raw) - date.today()).days
    except ValueError:
        return f"{EXPIRY_KEY} is not a date"
    if left < 0:
        return f"token expired on {raw}: make a new one (docs/know-how/instagram.md, step 4)"
    if left <= 10:
        return f"token expires in {left} days ({raw}): run `auth --refresh`"
    return f"token good until {raw}"


# --- story files -------------------------------------------------------------------

def ig_dir(slug):
    return story_dir(slug) / "instagram"


def read_jsonl(path):
    out = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue
    return out


def published(slug):
    return read_jsonl(ig_dir(slug) / "posts.jsonl")


def record_post(slug, row):
    p = ig_dir(slug) / "posts.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def lettering_lines(spec_path):
    """The text lettered onto a panel, one string per balloon or caption, in spec order."""
    try:
        spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    out = []
    for o in spec.get("overlays", []):
        text = " ".join(str(x).strip() for x in o.get("lines", []) if str(x).strip())
        if text:
            out.append(text)
    return out


def md_section(text, name):
    m = re.search(rf"^##\s+{re.escape(name)}\s*$\n(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    return m.group(1).strip() if m else ""


def plain(text):
    """Markdown post copy as caption text: [@x](url) becomes @x, other links keep their label."""
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*_`]{1,2}([^*_`\n]+)[*_`]{1,2}", r"\1", text)
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()


def prepare_jpeg(src, dst):
    """An Instagram-ready JPEG: RGB, at most 1440 wide, under 8 MB. Returns (w, h)."""
    from PIL import Image
    with Image.open(src) as im:
        if im.mode not in ("RGB", "L"):
            bg = Image.new("RGB", im.size, (255, 255, 255))
            rgba = im.convert("RGBA")
            bg.paste(rgba, mask=rgba.split()[-1])
            im = bg
        im = im.convert("RGB")
        ar = im.width / im.height
        if not (MIN_AR - 0.01 <= ar <= MAX_AR + 0.01):
            raise SystemExit(f"{src}: {im.width}x{im.height} is outside Instagram's feed shapes "
                             f"(4:5 portrait to 1.91:1 landscape). Crop it first: tools/cell_crop.py")
        if im.width > MAX_WIDTH:
            im = im.resize((MAX_WIDTH, round(im.height * MAX_WIDTH / im.width)), Image.Resampling.LANCZOS)
        dst.parent.mkdir(parents=True, exist_ok=True)
        for quality in (92, 86, 80, 72):
            im.save(dst, "JPEG", quality=quality, optimize=True)
            if dst.stat().st_size <= MAX_BYTES:
                break
        return im.width, im.height


def chapter_panels(slug, chapter):
    """[(panel id, carousel jpg)] in reading order."""
    d = story_dir(slug) / "chapters" / chapter / "pages" / "carousel"
    files = sorted(d.glob("*.jpg"))
    if not files:
        raise SystemExit(f"No carousel images in {d}. Build them: python3 tools/assemble.py "
                         f"stories/{slug}/chapters/{chapter}/pages/layout.json")
    return [(re.sub(r"^\d+-", "", f.stem), f) for f in files]


# --- draft -------------------------------------------------------------------------

def caption_problems(caption):
    out = []
    if len(caption) > MAX_CAPTION:
        out.append(f"caption is {len(caption)} characters; Instagram allows {MAX_CAPTION}")
    if len(HANDLE.findall(caption)) > MAX_MENTIONS:
        out.append(f"more than {MAX_MENTIONS} @mentions")
    if caption.count("#") > MAX_HASHTAGS:
        out.append(f"more than {MAX_HASHTAGS} hashtags")
    return out


def full_caption(plan):
    parts = [plan.get("caption", "").strip(), (plan.get("credit") or "").strip()]
    return "\n\n".join(p for p in parts if p)


def write_plan(slug, name, unit, kind, items, text_lines, extra_copy, credit):
    """items: [(panel id or None, source path)]."""
    sd = story_dir(slug)
    images, shapes = [], []
    for i, (pid, src) in enumerate(items, 1):
        dst = ig_dir(slug) / "media" / f"{name}-{i:02d}.jpg"
        shapes.append(prepare_jpeg(src, dst))
        entry = {"file": str(dst.relative_to(sd)), "source": str(Path(src).resolve().relative_to(sd))
                 if Path(src).resolve().is_relative_to(sd) else str(src)}
        if pid:
            entry["panel"] = pid
        images.append(entry)
    caption = "\n".join(text_lines)
    if extra_copy:
        caption = (caption + "\n\n" + extra_copy).strip()
    plan = {"story": slug, "unit": unit, "kind": kind, "panels": [p for p, _ in items if p],
            "images": images, "caption": caption, "credit": credit}
    path = ig_dir(slug) / "drafts" / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    warnings = caption_problems(full_caption(plan))
    if len({round(w / h, 2) for w, h in shapes}) > 1:
        warnings.append("images differ in shape; Instagram crops a carousel to the first one's")
    return {"plan": str(path.relative_to(REPO)), "unit": unit, "images": len(images),
            "caption": full_caption(plan), "mentions": ["@" + h for h in HANDLE.findall(caption)],
            "warnings": warnings}


def cmd_draft(a):
    slug = a.story
    sd = story_dir(slug)
    meta = (story_meta(slug).get("instagram") or {})
    credit = "" if a.no_credit else (a.credit or meta.get("credit") or CREDIT)
    results = []
    if a.chapter:
        panels = chapter_panels(slug, a.chapter)
        if a.panels:
            want = [p.strip() for p in a.panels.split(",") if p.strip()]
            by_id = dict(panels)
            missing = [p for p in want if p not in by_id]
            if missing:
                raise SystemExit(f"Not in {a.chapter}'s carousel: {', '.join(missing)}. "
                                 f"There: {', '.join(p for p, _ in panels)}")
            panels = [(p, by_id[p]) for p in want]
        if a.as_story:
            print(json.dumps(draft_story(a, slug, panels, not a.no_credit), ensure_ascii=False, indent=2))
            return
        chunks = [panels[i:i + MAX_ITEMS] for i in range(0, len(panels), MAX_ITEMS)]
        lettering = sd / "chapters" / a.chapter / "panels" / "lettering"
        for n, chunk in enumerate(chunks, 1):
            name = a.name or (a.chapter if len(chunks) == 1 and not a.panels else
                              f"{a.chapter}-{chunk[0][0]}" if a.panels else f"{a.chapter}-part{n}")
            lines = [t for pid, _ in chunk for t in lettering_lines(lettering / f"{pid}.json")]
            results.append(write_plan(slug, name, a.chapter, "chapter", chunk, lines, "", credit))
    elif a.as_story:
        raise SystemExit("--as-story needs --chapter chNN")
    elif a.post:
        d = sd / "posts" / a.post
        final = d / "final.png"
        if not final.is_file():
            raise SystemExit(f"No final image at {final}")
        brief = (d / "brief.md").read_text(encoding="utf-8") if (d / "brief.md").exists() else ""
        results.append(write_plan(slug, a.name or a.post, a.post, "post", [(None, final)],
                                  lettering_lines(d / "lettering.json"),
                                  plain(md_section(brief, "Post copy")), credit))
    elif a.images:
        if not a.unit:
            raise SystemExit("--images needs --unit <name> (the chapter or post these belong to)")
        if len(a.images) > MAX_ITEMS:
            raise SystemExit(f"A carousel holds at most {MAX_ITEMS} images through the API.")
        items = [(None, resolve(p)) for p in a.images]
        results.append(write_plan(slug, a.name or a.unit, a.unit, "images", items, [], "", credit))
    else:
        raise SystemExit("Give --chapter, --post or --images.")
    print(json.dumps(results if len(results) > 1 else results[0], ensure_ascii=False, indent=2))


# --- story frames -----------------------------------------------------------------
# A chapter as an Instagram Story: a title frame (a grid of every panel under the story and
# chapter titles), each panel, then a chapter-end frame that points at the next chapter.
# Every frame is 1080x1920 with the 4:5 image centred on a background colour. The API cannot
# add a link sticker, so the author adds one to the end frame in the app.

STORY_W, STORY_H = 1080, 1920
CARD_W, CARD_H = 1080, 1350
STORY_BG = "#15130f"          # behind the panels and the title frame
END_BG = "#0f1720"            # the reader's ink, behind the chapter-end frame
STORY_PAUSE_S = 20            # between frames, to stay clear of Meta's rapid-upload block
STORY_CREDIT = "Built with Kav · AI co-writer for graphic novels · github.com/oraboy/kav"
RTL_LANGS = {"he", "ar", "fa", "ur", "yi"}
CHAPTER_WORD = {"he": "פרק"}
MORE_LABEL = {"he": "להמשך קריאה ←"}
STICKER_NOTE = ("The API cannot add a link sticker, and Instagram only takes one while a Story is "
                "being made, never on a frame that is already up. So the chapter-end frame is not "
                "published here: post it by hand in the Instagram app with a Link sticker, then add "
                "the Story to a Highlight so it stays on the profile after 24 hours.")
NO_STICKER_NOTE = ("--include-end-frame: the chapter-end frame is published too, so it carries no link. "
                   "Save the Story to a Highlight in the app to keep it after 24 hours.")


def end_frame_note(plan, sd):
    """What the author does by hand with the held-back chapter-end frame."""
    f = sd / plan["images"][-1]["file"]
    rel = str(f.relative_to(REPO)) if f.is_relative_to(REPO) else str(f)
    target = plan.get("next_url") or "the next chapter's reader"
    return (f"Post {rel} in the Instagram app as the Story's last frame, with a Link sticker to "
            f"{target}, then add it to the chapter's Highlight.")
FONT_LINK = ('<link href="https://fonts.googleapis.com/css2?family=Varela+Round&display=block" '
             'rel="stylesheet">')


def chapter_heading(slug, chapter, word):
    """'<word> N · name' from the storyboard card's '# Ch NN — name' heading, or None."""
    card = story_dir(slug) / "storyboard" / f"{chapter}.md"
    if not card.is_file():
        return None
    first = card.read_text(encoding="utf-8").splitlines()[:1]
    m = re.match(r"#\s*(.+)", first[0]) if first else None
    if not m:
        return None
    head = m.group(1).strip()
    parts = re.match(r"(?:Ch(?:apter)?\.?\s*)?0*(\d+)\s*[—–:·-]+\s*(.+)", head, re.I)
    return f"{word} {parts.group(1)} · {parts.group(2).strip()}" if parts else head


def next_chapter(chapter):
    m = re.fullmatch(r"ch(\d+)", chapter)
    return f"ch{int(m.group(1)) + 1:0{len(m.group(1))}d}" if m else None


def render_card(html_body, png, direction, bg):
    """Render a 1080x1350 HTML card to PNG through headless Chrome (Hebrew shapes correctly)."""
    import tempfile
    from chrome import screenshot
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "card.html"
        page.write_text(
            f"<!doctype html><html dir='{direction}'><head><meta charset='utf-8'>{FONT_LINK}<style>"
            f"html,body{{margin:0;width:{CARD_W}px;height:{CARD_H}px;overflow:hidden;background:{bg};"
            f"color:#f4efe6;font-family:'Varela Round','Arial Hebrew',sans-serif}}</style></head>"
            f"<body>{html_body}</body></html>", encoding="utf-8")
        screenshot(page, png, CARD_W, CARD_H, budget_ms=8000)
    return png


def grid_cols(n, room=920, gap=6, pad=9):
    """Fewest columns (at least 3) that fit n 4:5 thumbnails into `room` pixels of height."""
    for cols in range(3, 13):
        w = (CARD_W - 2 * pad - (cols - 1) * gap) / cols
        rows = -(-n // cols)
        if rows * w * 1.25 + (rows - 1) * gap <= room:
            return cols
    return 12


def to_story_frame(src, dst, bg):
    """Centre an image on a 1080x1920 frame of colour bg, saved as JPEG."""
    from PIL import Image
    with Image.open(src) as im:
        im = im.convert("RGB")
        if im.width != STORY_W:
            im = im.resize((STORY_W, round(im.height * STORY_W / im.width)), Image.Resampling.LANCZOS)
        if im.height > STORY_H:
            top = (im.height - STORY_H) // 2
            im = im.crop((0, top, STORY_W, top + STORY_H))
        frame = Image.new("RGB", (STORY_W, STORY_H), bg)
        frame.paste(im, (0, (STORY_H - im.height) // 2))
        dst.parent.mkdir(parents=True, exist_ok=True)
        frame.save(dst, "JPEG", quality=92, optimize=True)


def draft_story(a, slug, panels, credit_on):
    """Build a chapter's Story frames and write a kind: story plan. Sends nothing."""
    import html as H
    from kav_env import jpeg_data_uri
    meta = story_meta(slug)
    igm = meta.get("instagram") or {}
    lang = meta.get("lang", "en")
    direction = meta.get("dir") or ("rtl" if lang in RTL_LANGS else "ltr")
    word = a.chapter_label or CHAPTER_WORD.get(lang, "Chapter")
    bg = a.bg or igm.get("story_bg") or STORY_BG
    title = meta.get("title") or slug
    warnings = []
    heading = chapter_heading(slug, a.chapter, word)
    if not heading:
        heading = a.chapter
        warnings.append(f"no '# Ch NN — name' heading in storyboard/{a.chapter}.md; the title frame says {a.chapter}")
    nxt_id = next_chapter(a.chapter)
    nxt = a.next if a.next is not None else (chapter_heading(slug, nxt_id, word) if nxt_id else None)
    if a.next is None and not nxt:
        warnings.append(f"no storyboard card for {nxt_id or 'the next chapter'}; the end frame has no next-chapter line (--next sets one)")
    mark = a.end_mark if a.end_mark is not None else igm.get("end_mark", "📖")
    more = a.more or igm.get("more_label") or MORE_LABEL.get(lang, "Continue reading →" if direction == "ltr" else "← Continue reading")

    name = a.name or f"{a.chapter}-story"
    media = ig_dir(slug) / "media"
    for old in media.glob(f"{name}-*.jpg"):
        old.unlink()
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        cols = grid_cols(len(panels))
        cells = "".join(f"<img src='{jpeg_data_uri(p, 360, 80)}'>" for _, p in panels)
        # the credit line sits in the space left between the chapter title and the grid, centred
        kav = f'<div class="kav">{H.escape(STORY_CREDIT)}</div>' if credit_on else ""
        cover = render_card(f"""
<style>
.top{{height:410px;display:flex;flex-direction:column}}
.head{{display:flex;flex-direction:column;align-items:center;gap:22px;text-align:center;
      padding-top:{80 if credit_on else 0}px;{'' if credit_on else 'flex:1;justify-content:center'}}}
.t{{font-size:96px;line-height:1.15}} .c{{font-size:46px;line-height:1.15;opacity:.8}}
.kav{{flex:1;display:flex;align-items:center;justify-content:center;direction:ltr;font-size:21px;opacity:.55}}
.grid{{display:grid;grid-template-columns:repeat({cols},1fr);gap:6px;padding:0 9px;direction:{direction}}}
.grid img{{width:100%;aspect-ratio:4/5;object-fit:cover;display:block}}
</style>
<div class="top"><div class="head"><div class="t">{H.escape(title)}</div><div class="c">{H.escape(heading)}</div></div>{kav}</div>
<div class="grid">{cells}</div>""", tmp / "cover.png", direction, bg)
        end = render_card(f"""
<style>
.box{{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center}}
.e{{font-size:150px;line-height:1;margin-bottom:56px}}
.n{{font-size:46px;color:#d8d2c4;padding:0 60px}}
.b{{font-size:50px;color:#1c1712;background:#d9a066;padding:34px 84px;border-radius:999px;margin-top:62px}}
</style>
<div class="box">{f'<div class="e">{H.escape(mark)}</div>' if mark else ''}
{f'<div class="n">{H.escape(nxt)}</div>' if nxt else ''}<div class="b">{H.escape(more)}</div></div>""",
                          tmp / "end.png", direction, END_BG)
        sources = [(None, cover, bg), *[(pid, p, bg) for pid, p in panels], (None, end, END_BG)]
        sd = story_dir(slug)
        frames = []
        for i, (pid, src, colour) in enumerate(sources, 1):
            dst = media / f"{name}-{i:02d}.jpg"
            to_story_frame(src, dst, colour)
            entry = {"file": str(dst.relative_to(sd))}
            if pid:
                entry["panel"] = pid
            else:
                entry["frame"] = "title" if i == 1 else "chapter-end"
            frames.append(entry)
    plan = {"story": slug, "unit": a.chapter, "kind": "story", "panels": [p for p, _ in panels],
            "images": frames, "pause_s": a.pause, "title": title, "chapter_title": heading,
            "next_title": nxt or "", "next_url": a.next_url or ""}
    path = ig_dir(slug) / "drafts" / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"plan": str(path.relative_to(REPO)), "unit": a.chapter, "kind": "story",
            "frames": len(frames), "title_frame": f"{title} / {heading}",
            "end_frame": " / ".join(x for x in (mark, nxt, more) if x),
            "media": str(media.relative_to(REPO)), "link_sticker": STICKER_NOTE,
            "by_hand": end_frame_note(plan, story_dir(slug)), "warnings": warnings}


# --- post --------------------------------------------------------------------------

def fal_upload(path, key):
    """Upload a file to fal.ai storage and return its public URL."""
    name = Path(path).name
    req = urllib.request.Request(
        "https://rest.alpha.fal.ai/storage/upload/initiate?storage_type=fal-cdn-v3",
        data=json.dumps({"content_type": "image/jpeg", "file_name": name}).encode(),
        headers={"Authorization": f"Key {key}", "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            slot = json.loads(r.read())
        put = urllib.request.Request(slot["upload_url"], data=Path(path).read_bytes(),
                                     headers={"Content-Type": "image/jpeg"}, method="PUT")
        with urllib.request.urlopen(put, timeout=180):
            pass
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"fal.ai storage upload failed (HTTP {e.code}): "
                           f"{e.read().decode(errors='replace')[:200]}") from None
    return slot["file_url"]


# Meta soft-blocks an account that creates many containers quickly, and the only sign is a
# container that stays in ERROR with no detail. Retrying extends the block (it clears in
# 24-72h), so a persistent ERROR starts a cooldown that `post --yes` respects. One ERROR
# poll can be transient, so it takes several in a row.
COOLDOWN = REPO / ".instagram-cooldown"
COOLDOWN_S = 3600
ERROR_POLLS = 3


def check_cooldown():
    if COOLDOWN.exists():
        age = time.time() - COOLDOWN.stat().st_mtime
        if age < COOLDOWN_S:
            raise SystemExit(
                f"Cooldown: Instagram refused the last post {int(age / 60)} min ago with no reason, "
                f"which usually means a temporary spam block (24-72h). Retrying makes it longer. "
                f"Post this one by hand, or wait. To override, delete {COOLDOWN.name}.")


def wait_ready(container, tok, tries=40, pause=5):
    streak = 0
    for _ in range(tries):
        st = api("GET", container, tok, {"fields": "status_code,status"})
        code = st.get("status_code")
        if code in ("FINISHED", "PUBLISHED"):
            return
        if code == "EXPIRED":
            raise RuntimeError("The upload expired before it was published.")
        if code == "ERROR":
            streak += 1
            if streak >= ERROR_POLLS:
                COOLDOWN.touch()
                raise RuntimeError(f"Instagram could not take the image: {st.get('status') or 'no reason given'}. "
                                   f"Do not retry now: a silent refusal is usually a temporary spam "
                                   f"block, and a retry extends it. Post this one by hand.")
        else:
            streak = 0
        time.sleep(pause)
    raise RuntimeError("Instagram is still processing the image. Try again in a few minutes.")


def quota_left(uid, tok):
    """Posts left in the 24-hour window, or None when it cannot be read."""
    try:
        lim = api("GET", f"{uid}/content_publishing_limit", tok, {"fields": "quota_usage,config"})["data"][0]
        return int(lim["config"]["quota_total"]) - int(lim["quota_usage"])
    except (RuntimeError, LookupError, TypeError, ValueError):
        return None


def refresh_quietly(tok):
    """Renew the token after a successful post, so a regular poster never sees it expire."""
    try:
        res = api("GET", f"{HOST}/refresh_access_token", tok, {"grant_type": "ig_refresh_token"})
        set_env("INSTAGRAM_ACCESS_TOKEN", res["access_token"])
        set_env(EXPIRY_KEY, (date.today() + timedelta(seconds=int(res.get("expires_in", 0)))).isoformat())
    except (RuntimeError, LookupError, ValueError):
        pass          # a token younger than 24 hours cannot be refreshed; that is fine


def load_plan(path):
    p = resolve(path)
    plan = json.loads(p.read_text(encoding="utf-8"))
    slug = plan.get("story")
    if not slug:
        raise SystemExit(f"{p}: the plan needs \"story\"")
    sd = story_dir(slug)
    problems = caption_problems(full_caption(plan))
    images = plan.get("images") or []
    if not 1 <= len(images) <= MAX_ITEMS:
        problems.append(f"{len(images)} images; a post takes 1 to {MAX_ITEMS}")
    for im in images:
        f = sd / im.get("file", "")
        if not im.get("url") and not f.is_file():
            problems.append(f"missing image file {f}")
        for t in im.get("user_tags") or []:
            if not t.get("username") or not all(0 <= float(t.get(k, -1)) <= 1 for k in ("x", "y")):
                problems.append(f"user_tags need a username and x, y between 0 and 1: {t}")
    return p, plan, sd, problems


def story_plan_problems(plan, sd):
    from PIL import Image
    problems = []
    frames = plan.get("images") or []
    if not frames:
        problems.append("the plan has no frames")
    for fr in frames:
        f = sd / fr.get("file", "")
        if not f.is_file():
            problems.append(f"missing frame file {f}")
            continue
        with Image.open(f) as im:
            if im.size != (STORY_W, STORY_H):
                problems.append(f"{f.name} is {im.width}x{im.height}; a Story frame is {STORY_W}x{STORY_H}")
    return problems


def post_story(a, path, plan, sd):
    """Publish a kind: story plan, one STORIES container and one publish per frame."""
    slug, all_frames = plan["story"], plan["images"]
    pause = a.pause if a.pause is not None else int(plan.get("pause_s") or STORY_PAUSE_S)
    start = a.start or 1
    want = expected_account(slug)
    problems = story_plan_problems(plan, sd)
    # The chapter-end frame needs a link sticker, which only the app can add while making a
    # Story. Unless the author wants it without a link, it is held back for them to post.
    hold_end = bool(all_frames) and all_frames[-1].get("frame") == "chapter-end" and not a.include_end_frame
    frames = all_frames[:-1] if hold_end else all_frames
    if not 1 <= start <= max(len(frames), 1):
        problems.append(f"--from {start}: the API publishes frames 1-{len(frames)} of this plan")
    done = (plan.get("published") or {}).get("frames") or []
    if done and not a.again and start == 1:
        problems.append(f"{len(done)} of {len(frames)} frames already posted on "
                        f"{datetime.fromtimestamp(plan['published']['at']).strftime('%Y-%m-%d %H:%M')} "
                        f"(--from N to finish a cut-off Story, --again to post it all again)")
    todo = frames[start - 1:]
    summary = {"would_post" if not a.yes else "posting":
               f"Story of {len(todo)} frames" + (f" (frames {start}-{len(frames)})" if start > 1 else ""),
               "account": f"@{want}" if want else "whoever the token belongs to (set INSTAGRAM_USERNAME to pin it)",
               "unit": plan.get("unit"),
               "title_frame": f"{plan.get('title', '')} / {plan.get('chapter_title', '')}",
               "next_title": plan.get("next_title") or "(none)",
               "frames": [fr["file"] for fr in todo],
               "hosting": f"{len(todo)} image(s) uploaded to fal.ai storage for Instagram to fetch",
               "pace": f"{pause}s between frames, about {round(pause * (len(todo) - 1) / 60)} min in all",
               "quota": f"uses {len(todo)} of the account's 24-hour publishing quota (one per frame)",
               "link_sticker": STICKER_NOTE if hold_end else NO_STICKER_NOTE,
               "problems": problems}
    if hold_end:
        summary["by_hand"] = end_frame_note(plan, sd)
    if not a.yes or problems:
        if not a.yes:
            summary["next"] = "nothing was sent. Show this to the author; on their yes, rerun with --yes"
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        sys.exit(1 if problems else 0)

    check_cooldown()
    tok = token()
    who = me(tok)
    if want and who.get("username", "").lower() != want:
        raise SystemExit(f"The token belongs to @{who.get('username')}, but this posts as @{want}. Nothing sent.")
    if a.host != "fal":
        raise SystemExit(f"Unknown --host {a.host!r}")
    fal_key = get_key("FAL_KEY")
    if not fal_key:
        raise SystemExit("FAL_KEY is not set; Story frames need a public URL for Instagram to fetch. Nothing sent.")
    uid = who.get("user_id") or who["id"]
    left = quota_left(uid, tok)
    if left is not None and left < len(todo):
        raise SystemExit(f"Only {left} posts left in Instagram's 24-hour quota; this Story needs {len(todo)}. Nothing sent.")
    log = ig_dir(slug) / "stories.jsonl"
    media_ids = list(done) if start > 1 else []
    plan_rel = str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)
    for n, fr in enumerate(todo, start):
        try:
            url = fal_upload(sd / fr["file"], fal_key)
            cid = api("POST", f"{uid}/media", tok, {"image_url": url, "media_type": "STORIES"})["id"]
            wait_ready(cid, tok)
            mid = api("POST", f"{uid}/media_publish", tok, {"creation_id": cid})["id"]
        except RuntimeError as e:
            up = n - 1
            msg = (f"Frame {n}/{len(frames)} failed: {e}\n"
                   + (f"Frames 1-{up} are up; nothing after was sent. To finish later: "
                      f"post {plan_rel} --from {n} --yes" if up else "No frame of this Story was published."))
            raise SystemExit(msg)
        media_ids.append(mid)
        with log.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"at": int(time.time()), "story": slug, "unit": plan.get("unit"),
                                 "frame": n, "of": len(frames), "file": fr["file"],
                                 "media_id": mid, "account": who.get("username"), "plan": plan_rel},
                                ensure_ascii=False) + "\n")
        plan["published"] = {"frames": media_ids, "at": int(time.time()), "complete": n == len(frames),
                             "end_frame": "by hand" if hold_end else "published"}
        path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"frame {n}/{len(frames)} up", flush=True)
        if n < len(frames):
            time.sleep(pause)
    refresh_quietly(tok)
    done_msg = {"ok": True, "posted": f"Story of {len(todo)} frames", "account": "@" + who.get("username", ""),
                "logged": str(log.relative_to(REPO))}
    if hold_end:
        done_msg["by_hand"] = end_frame_note(plan, sd)
    else:
        done_msg["next"] = NO_STICKER_NOTE
    print(json.dumps(done_msg, ensure_ascii=False, indent=2))


def cmd_post(a):
    p = resolve(a.plan)
    raw = json.loads(p.read_text(encoding="utf-8"))
    if raw.get("kind") == "story":
        if not raw.get("story"):
            raise SystemExit(f"{p}: the plan needs \"story\"")
        return post_story(a, p, raw, story_dir(raw["story"]))
    if a.start or a.pause is not None or a.include_end_frame:
        raise SystemExit("--from, --pause and --include-end-frame are for Story plans (draft --as-story)")
    path, plan, sd, problems = load_plan(a.plan)
    slug, images, caption = plan["story"], plan["images"], full_caption(plan)
    want = expected_account(slug)
    kind = "single image" if len(images) == 1 else f"carousel of {len(images)}"
    need_host = [im for im in images if not im.get("url")]
    summary = {"would_post" if not a.yes else "posting": kind,
               "account": f"@{want}" if want else "whoever the token belongs to (set INSTAGRAM_USERNAME to pin it)",
               "unit": plan.get("unit"),
               "images": [im.get("url") or im["file"] for im in images],
               "photo_tags": [t["username"] for im in images for t in im.get("user_tags") or []],
               "caption": caption,
               "hosting": (f"{len(need_host)} image(s) uploaded to fal.ai storage for Instagram to fetch"
                           if need_host else "the images' own public URLs"),
               "problems": problems}
    if plan.get("published") and not a.again:
        summary["problems"].append(f"already posted: {plan['published'].get('permalink')} (--again to repost)")
    if not a.yes or summary["problems"]:
        if not a.yes:
            summary["next"] = "nothing was sent. Show this to the author; on their yes, rerun with --yes"
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        sys.exit(1 if summary["problems"] else 0)

    check_cooldown()
    tok = token()
    who = me(tok)
    if want and who.get("username", "").lower() != want:
        raise SystemExit(f"The token belongs to @{who.get('username')}, but this posts as @{want}. Nothing sent.")
    fal_key = get_key("FAL_KEY")
    if need_host:
        if a.host != "fal":
            raise SystemExit(f"Unknown --host {a.host!r}")
        if not fal_key:
            raise SystemExit("These images have no public URL and FAL_KEY is not set. Either put a "
                             "\"url\" on each image in the plan (a published reader's image) or set FAL_KEY.")
    uid = who.get("user_id") or who["id"]
    if quota_left(uid, tok) == 0:
        raise SystemExit("Instagram's 24-hour publishing quota for this account is used up. Nothing sent.")
    try:
        for im in need_host:
            im["url"] = fal_upload(sd / im["file"], fal_key)
        single = len(images) == 1
        children = []
        for im in images:
            params = {"image_url": im["url"]}
            if im.get("user_tags"):
                params["user_tags"] = json.dumps(im["user_tags"])
            if single:
                params["caption"] = caption
            else:
                params["is_carousel_item"] = "true"
            cid = api("POST", f"{uid}/media", tok, params)["id"]
            wait_ready(cid, tok)
            children.append(cid)
        if single:
            creation = children[0]
        else:
            creation = api("POST", f"{uid}/media", tok, {"media_type": "CAROUSEL", "caption": caption,
                                                         "children": ",".join(children)})["id"]
            wait_ready(creation, tok)
        media_id = api("POST", f"{uid}/media_publish", tok, {"creation_id": creation})["id"]
    except RuntimeError as e:
        raise SystemExit(f"{e}\nNothing was published.")
    try:
        permalink = api("GET", media_id, tok, {"fields": "permalink"}).get("permalink")
    except RuntimeError:
        permalink = None
    row = {"at": int(time.time()), "story": slug, "unit": plan.get("unit"), "kind": plan.get("kind"),
           "panels": plan.get("panels") or [], "media_id": media_id, "permalink": permalink,
           "account": who.get("username"), "images": len(images), "plan": str(path.relative_to(REPO))
           if path.is_relative_to(REPO) else str(path), "caption": caption}
    record_post(slug, row)
    plan["published"] = {"media_id": media_id, "permalink": permalink, "at": row["at"]}
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    refresh_quietly(tok)
    print(json.dumps({"ok": True, "posted": kind, "account": "@" + who.get("username", ""),
                      "permalink": permalink, "media_id": media_id}, ensure_ascii=False, indent=2))


# --- link --------------------------------------------------------------------------

def cmd_link(a):
    story_dir(a.story)
    tok = token()
    media_id, permalink = a.media_id, a.permalink
    fields = "id,permalink,caption,timestamp,media_type"
    if media_id:
        item = api("GET", media_id, tok, {"fields": fields})
    else:
        want = permalink.split("?")[0].rstrip("/")
        page, item = api("GET", "me/media", tok, {"fields": fields, "limit": 50}), None
        for _ in range(20):
            item = next((m for m in page.get("data", []) if m.get("permalink", "").rstrip("/") == want), None)
            nxt = page.get("paging", {}).get("next")
            if item or not nxt:
                break
            page = api("GET", nxt, tok)
        if not item:
            raise SystemExit(f"No post with that link on this account: {permalink}")
    if any(r.get("media_id") == item["id"] for r in published(a.story)):
        raise SystemExit("That post is already recorded for this story.")
    at = int(datetime.fromisoformat(item["timestamp"].replace("+0000", "+00:00")).timestamp()) \
        if item.get("timestamp") else int(time.time())
    row = {"at": at, "story": a.story, "unit": a.unit, "kind": "linked", "panels": [],
           "media_id": item["id"], "permalink": item.get("permalink"), "caption": item.get("caption", "")}
    record_post(a.story, row)
    print(json.dumps({"ok": True, "linked": item.get("permalink"), "unit": a.unit}, indent=2))


# --- stats -------------------------------------------------------------------------

def insights(media_id, tok):
    """{metric: value} for what this post supports, plus the metrics that were refused."""
    def read(metrics):
        res = api("GET", f"{media_id}/insights", tok, {"metric": ",".join(metrics)})
        return {d["name"]: (d.get("values") or [{}])[0].get("value", d.get("total_value", {}).get("value"))
                for d in res.get("data", [])}
    try:
        return read(INSIGHTS), []
    except RuntimeError:
        got, refused = {}, []
        for m in INSIGHTS:
            try:
                got.update(read([m]))
            except RuntimeError:
                refused.append(m)
        return got, refused


def cmd_stats(a):
    rows = published(a.story)
    if not rows:
        raise SystemExit(f"Nothing recorded as posted for {a.story} yet "
                         f"(stories/{a.story}/instagram/posts.jsonl). Post with `post`, or register "
                         f"a post made by hand with `link`.")
    tok = token()
    posts, notes = [], set()
    for r in rows:
        p = {"unit": r.get("unit"), "panels": r.get("panels") or [], "permalink": r.get("permalink"),
             "media_id": r["media_id"], "posted": datetime.fromtimestamp(r["at"], timezone.utc).strftime("%Y-%m-%d")}
        try:
            base = api("GET", r["media_id"], tok, {"fields": "like_count,comments_count,media_type,permalink"})
        except RuntimeError as e:
            p["error"] = str(e)
            posts.append(p)
            continue
        p.update(likes=base.get("like_count"), comments=base.get("comments_count"),
                 media_type=base.get("media_type"))
        got, refused = insights(r["media_id"], tok)
        p.update({k: got.get(k) for k in INSIGHTS})
        if refused:
            notes.add(f"not available for some posts: {', '.join(refused)}")
        if a.comments and p["comments"]:
            try:
                res = api("GET", f"{r['media_id']}/comments", tok,
                          {"fields": "username,from,text,timestamp,like_count", "limit": 50})
                p["comment_list"] = [{"user": c.get("username") or (c.get("from") or {}).get("username"),
                                      "text": c.get("text"),
                                      "likes": c.get("like_count")} for c in res.get("data", [])]
            except RuntimeError as e:
                notes.add(f"comment text not read: {e}")
        posts.append(p)

    keys = ["likes", "comments", "views", "reach", "saved", "shares"]
    units = {}
    for p in posts:
        u = units.setdefault(p["unit"] or "?", {"posts": 0, **{k: 0 for k in keys}})
        u["posts"] += 1
        for k in keys:
            u[k] += p.get(k) or 0
    snapshot = {"story": a.story, "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
                "units": units, "posts": posts, "notes": sorted(notes)}
    d = ig_dir(a.story)
    (d / "stats.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (d / "stats-history.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"at": snapshot["at"], "units": units, "posts": [
            {"media_id": p["media_id"], **{k: p.get(k) for k in keys}} for p in posts
            if not p.get("error")]}, ensure_ascii=False) + "\n")
    if a.json:
        print(json.dumps(snapshot, ensure_ascii=False, indent=2))
        return
    head = f"{'':<22}{'posts':>6}" + "".join(f"{k:>10}" for k in keys)
    print(f"{a.story} on Instagram · {snapshot['at']}\n{head}")
    for name in sorted(units):
        u = units[name]
        print(f"{name:<22}{u['posts']:>6}" + "".join(f"{u[k]:>10}" for k in keys))
    print(f"{'total':<22}{len(posts):>6}" + "".join(f"{sum(u[k] for u in units.values()):>10}" for k in keys))
    for n in snapshot["notes"]:
        print(f"  note: {n}")
    for p in posts:
        if p.get("error"):
            print(f"  {p['unit']} {p['permalink']}: {p['error']}")
    print(f"  per-post detail and any comment text: stories/{a.story}/instagram/stats.json")


# --- auth --------------------------------------------------------------------------

def cmd_auth(a):
    tok = token()
    if a.refresh:
        res = api("GET", f"{HOST}/refresh_access_token", tok, {"grant_type": "ig_refresh_token"})
        set_env("INSTAGRAM_ACCESS_TOKEN", res["access_token"])
        until = (date.today() + timedelta(seconds=int(res.get("expires_in", 0)))).isoformat()
        set_env(EXPIRY_KEY, until)
        tok = res["access_token"]
        print(f"Token refreshed and saved to .env · good until {until}")
    who = me(tok)
    want = expected_account()
    out = {"account": "@" + who.get("username", "?"), "type": who.get("account_type"),
           "posts": who.get("media_count"), "followers": who.get("followers_count"),
           "token": expiry_note(), "token_from": token_source()[1]}
    if want and who.get("username", "").lower() != want:
        out["problem"] = f"INSTAGRAM_USERNAME says @{want}; this token is for another account"
    left = quota_left(who.get("user_id") or who["id"], tok)
    if left is None:
        out["publishing"] = "could not read the publishing quota: the token may lack instagram_business_content_publish"
    else:
        out["posts_left_today"] = left
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(1 if out.get("problem") else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("auth", help="check the token; --refresh renews it")
    s.add_argument("--refresh", action="store_true")
    s.set_defaults(fn=cmd_auth)
    s = sub.add_parser("draft", help="write a post plan from panels (sends nothing)")
    s.add_argument("--story", required=True)
    s.add_argument("--chapter")
    s.add_argument("--panels", help="comma-separated panel ids, in posting order")
    s.add_argument("--post", help="a folder under stories/<slug>/posts/")
    s.add_argument("--images", nargs="+")
    s.add_argument("--unit", help="with --images: the chapter or post these belong to")
    s.add_argument("--name", help="plan file name (default: from the chapter or post)")
    s.add_argument("--credit", help=f"closing line (default: {CREDIT!r})")
    s.add_argument("--no-credit", action="store_true")
    g = s.add_argument_group("Story (with --chapter --as-story)")
    g.add_argument("--as-story", action="store_true",
                   help="build 1080x1920 Story frames: title frame, every panel, chapter-end frame")
    g.add_argument("--next", help="next-chapter line on the end frame (default: the next storyboard card's title)")
    g.add_argument("--end-mark", help="emoji on the end frame (default: story.json instagram.end_mark, else 📖; '' for none)")
    g.add_argument("--more", help="the end frame's pill text (default: 'להמשך קריאה ←' in Hebrew, else 'Continue reading →')")
    g.add_argument("--chapter-label", help="word before the chapter number (default: 'פרק' in Hebrew, else 'Chapter')")
    g.add_argument("--bg", help=f"background behind the panels (default: story.json instagram.story_bg, else {STORY_BG})")
    g.add_argument("--pause", type=int, default=STORY_PAUSE_S, help=f"seconds between frames when posting (default {STORY_PAUSE_S})")
    g.add_argument("--next-url", help="the next chapter's reader, named in the by-hand step for the end frame's link sticker")
    s.set_defaults(fn=cmd_draft)
    s = sub.add_parser("post", help="show what a plan would post; --yes publishes it")
    s.add_argument("plan")
    s.add_argument("--yes", action="store_true", help="publish (only after the author's explicit yes)")
    s.add_argument("--host", default="fal", help="where images without a url are uploaded (fal)")
    s.add_argument("--again", action="store_true", help="repost a plan that was already published")
    s.add_argument("--from", dest="start", type=int, help="Story plans: start at frame N (finish a cut-off Story)")
    s.add_argument("--pause", type=int, help="Story plans: seconds between frames (default: the plan's, 20)")
    s.add_argument("--include-end-frame", action="store_true",
                   help="Story plans: publish the chapter-end frame too (it then carries no link; "
                        "by default it is left for the author to post in the app with a link sticker)")
    s.set_defaults(fn=cmd_post)
    s = sub.add_parser("link", help="register a post made by hand")
    s.add_argument("--story", required=True)
    s.add_argument("--unit", required=True)
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument("--permalink")
    g.add_argument("--media-id")
    s.set_defaults(fn=cmd_link)
    s = sub.add_parser("stats", help="likes, comments, views per post and per chapter")
    s.add_argument("--story", required=True)
    s.add_argument("--comments", action="store_true", help="also read comment text")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_stats)
    a = ap.parse_args()
    try:
        a.fn(a)
    except RuntimeError as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
