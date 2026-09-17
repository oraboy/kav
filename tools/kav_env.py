"""Shared plumbing for every Kav tool: repo root, story paths, API keys, image helpers.

No third-party imports at module level so `--help` works before Pillow is installed.
"""
import base64
import io
import json
import mimetypes
import os
import sys
from pathlib import Path

# Repo root: $KAV_HOME if set, otherwise the folder above tools/.
REPO = Path(os.environ["KAV_HOME"]).expanduser().resolve() if os.environ.get("KAV_HOME") \
    else Path(__file__).resolve().parents[1]

KEY_HELP = {
    "FAL_KEY": "Seedream and Nano Banana via fal.ai. Get one at https://fal.ai/dashboard/keys",
    "GEMINI_API_KEY": "Nano Banana (Gemini image) direct. Get one at https://aistudio.google.com/apikey",
}
KEY_HELP.update({
    "MAGNIFIC_API_KEY": "Seedream 4.5 via Magnific (formerly the Freepik API). Get one at https://www.magnific.com/api",
    "HIGGSFIELD_API_KEY": "Higgsfield Popcorn and Soul. Get one at https://cloud.higgsfield.ai/api-keys (paste the whole id:secret key)",
})
KEY_ALIASES = {"FAL_KEY": ("FAL_KEY", "FAL_API_KEY"),
               "GEMINI_API_KEY": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
               "MAGNIFIC_API_KEY": ("MAGNIFIC_API_KEY", "FREEPIK_API_KEY"),
               "HIGGSFIELD_API_KEY": ("HIGGSFIELD_API_KEY", "HIGGSFIELD_API_KEY_ID", "HF_CREDENTIALS")}


def story_dir(slug):
    d = REPO / "stories" / slug
    if not d.is_dir():
        raise SystemExit(f"No such story: {d}  (stories live at <repo>/stories/<slug>/)")
    return d


def chapter_dir(slug, chapter):
    return REPO / "stories" / slug / "chapters" / chapter


def resolve(path):
    """A CLI path: absolute, relative to the cwd if it exists there, else relative to the repo."""
    p = Path(path).expanduser()
    if p.is_absolute() or p.exists():
        return p.resolve()
    return (REPO / p).resolve()


def story_meta(slug):
    """stories/<slug>/story.json, or {} when absent."""
    f = REPO / "stories" / slug / "story.json"
    try:
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    except ValueError:
        return {}


def load_env_key(*names):
    """First non-empty value among `names`, from the environment or <repo>/.env."""
    for n in names:
        if os.environ.get(n):
            return os.environ[n].strip()
    env_file = REPO / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                k = k.strip().removeprefix("export ").strip()
                v = v.strip().strip('"').strip("'")
                if k in names and v:
                    return v
    return None


def get_key(canonical):
    return load_env_key(*KEY_ALIASES.get(canonical, (canonical,)))


def missing_key_message(canonical):
    alias = " or ".join(KEY_ALIASES.get(canonical, (canonical,)))
    return (f"Missing API key: {alias}.\n"
            f"  Used for: {KEY_HELP.get(canonical, '')}\n"
            f"  Put it in your environment or in {REPO / '.env'} as {canonical}=...  "
            f"(see .env.example)")


def require_key(canonical):
    key = get_key(canonical)
    if not key:
        sys.exit(missing_key_message(canonical))
    return key


def data_uri(path):
    """Raw file as a data: URI (used for API reference images)."""
    mime = mimetypes.guess_type(str(path))[0] or "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(Path(path).read_bytes()).decode()


def jpeg_bytes(path, max_px=1000, quality=80):
    """Downscale (longest side <= max_px) and re-encode as JPEG with Pillow."""
    from PIL import Image
    im = Image.open(path)
    if im.mode not in ("RGB", "L"):
        bg = Image.new("RGB", im.size, (0, 0, 0))
        rgba = im.convert("RGBA")
        bg.paste(rgba, mask=rgba.split()[-1])
        im = bg
    im.thumbnail((max_px, max_px), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    im.convert("RGB").save(buf, "JPEG", quality=quality)
    return buf.getvalue()


def jpeg_data_uri(path, max_px=1000, quality=80):
    return "data:image/jpeg;base64," + base64.b64encode(jpeg_bytes(path, max_px, quality)).decode()
