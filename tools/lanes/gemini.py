"""Google Gemini image client (Nano Banana), called directly with GEMINI_API_KEY.

Reference images go in as inline bytes in the same order the prompt's "image N"
preamble declares, followed by the prompt text.
"""
import base64
import json
import mimetypes
import os
import urllib.error
import urllib.request
from pathlib import Path

API = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_MODEL = os.environ.get("KAV_GEMINI_MODEL", "gemini-3-pro-image-preview")

# Gemini accepts a fixed set of ratios; the wide page-cell shapes map to the nearest one.
SUPPORTED = {"1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"}
NEAREST = {"8:5": "16:9", "12:5": "21:9"}


def aspect(ar):
    ar = ar or "9:16"
    return ar if ar in SUPPORTED else NEAREST.get(ar, "9:16")


def extract_image(resp):
    for cand in resp.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                return base64.b64decode(inline["data"])
    raise RuntimeError(f"no image in Gemini response: {json.dumps(resp)[:600]}")


def run(prompt, ref_paths, key, ar="9:16", model=None, seed=None):
    parts = []
    for p in ref_paths:
        mime = mimetypes.guess_type(str(p))[0] or "image/png"
        parts.append({"inline_data": {"mime_type": mime,
                                      "data": base64.b64encode(Path(p).read_bytes()).decode()}})
    parts.append({"text": prompt})
    config = {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": aspect(ar)}}
    if seed is not None:
        config["seed"] = int(seed)
    req = urllib.request.Request(
        f"{API}/{model or DEFAULT_MODEL}:generateContent",
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
        data=json.dumps({"contents": [{"parts": parts}], "generationConfig": config}).encode(),
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return extract_image(json.loads(r.read()))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Gemini HTTP {e.code}: {e.read().decode(errors='replace')[:400]}") from None
