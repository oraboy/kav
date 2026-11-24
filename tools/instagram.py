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

  python3 tools/instagram.py post <plan.json> [--yes] [--host fal] [--again]
      Without --yes: print exactly what would be posted and stop. With --yes: publish.
      One image is a single post, 2-10 a carousel.

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
        chunks = [panels[i:i + MAX_ITEMS] for i in range(0, len(panels), MAX_ITEMS)]
        lettering = sd / "chapters" / a.chapter / "panels" / "lettering"
        for n, chunk in enumerate(chunks, 1):
            name = a.name or (a.chapter if len(chunks) == 1 and not a.panels else
                              f"{a.chapter}-{chunk[0][0]}" if a.panels else f"{a.chapter}-part{n}")
            lines = [t for pid, _ in chunk for t in lettering_lines(lettering / f"{pid}.json")]
            results.append(write_plan(slug, name, a.chapter, "chapter", chunk, lines, "", credit))
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


def cmd_post(a):
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
    s.set_defaults(fn=cmd_draft)
    s = sub.add_parser("post", help="show what a plan would post; --yes publishes it")
    s.add_argument("plan")
    s.add_argument("--yes", action="store_true", help="publish (only after the author's explicit yes)")
    s.add_argument("--host", default="fal", help="where images without a url are uploaded (fal)")
    s.add_argument("--again", action="store_true", help="repost a plan that was already published")
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
