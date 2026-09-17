"""Higgsfield Cloud API client.

Auth: `Authorization: Key <key_id>:<secret>` (the console shows it as one combined key).
Reference images are uploaded first (POST /files/generate-upload-url, PUT to the presigned
URL) and passed by public URL. Submissions return a request id; poll
GET /requests/<id>/status until completed and download images[0].url.

Models Kav uses, by lane:
  popcorn  /higgsfield-ai/popcorn/auto     up to 8 reference images (multi-reference scenes)
  soul     /higgsfield-ai/soul/reference   Higgsfield's own look; one style reference image
           /higgsfield-ai/soul/standard    text only
Needs HIGGSFIELD_API_KEY (HIGGSFIELD_API_KEY_ID accepted).
"""
import json
import random
import time
import urllib.error
import urllib.request

BASE = "https://api.higgsfield.ai"
UA = "kav/1.0 (+https://github.com/oraboy/kav)"
MAX_REFS = {"popcorn": 8, "soul": 1}
ASPECTS = {"popcorn": {"1:1", "4:3", "3:4", "3:2", "2:3", "16:9", "9:16"},
           "soul": {"9:16", "16:9", "4:3", "3:4", "1:1", "2:3", "3:2"}}
NEAREST = {"4:5": "3:4", "8:5": "16:9", "12:5": "16:9"}


def api(path_or_url, key, payload=None, timeout=180):
    url = path_or_url if path_or_url.startswith("http") else BASE + path_or_url
    # Cloudflare in front of the API rejects Python's default user agent (error 1010)
    req = urllib.request.Request(url, headers={"Authorization": f"Key {key}",
                                               "Content-Type": "application/json",
                                               "Accept": "application/json",
                                               "User-Agent": UA})
    data = json.dumps(payload).encode() if payload is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"Higgsfield HTTP {e.code} on {url}: {body[:400]}") from None


def upload(jpeg, key):
    slot = api("/files/generate-upload-url", key, {"content_type": "image/jpeg"})
    req = urllib.request.Request(slot["upload_url"], data=jpeg, method="PUT",
                                 headers=slot.get("upload_headers") or {"Content-Type": "image/jpeg"})
    with urllib.request.urlopen(req, timeout=180):
        pass
    return slot["public_url"]


def aspect(lane, ar):
    ar = ar or "9:16"
    ar = ar if ar in ASPECTS[lane] else NEAREST.get(ar, "3:4")
    return ar if ar in ASPECTS[lane] else "3:4"


def run(lane, prompt, ref_bytes, key, ar="9:16", seed=None, max_wait_s=600):
    if lane not in MAX_REFS:
        raise RuntimeError(f"Higgsfield runs: {', '.join(MAX_REFS)}")
    urls = [upload(b, key) for b in ref_bytes[:MAX_REFS[lane]]]
    body = {"prompt": prompt, "aspect_ratio": aspect(lane, ar)}
    if seed is not None:
        body["seed"] = max(1, int(seed) % 1000000)
    if lane == "popcorn":
        path = "/higgsfield-ai/popcorn/auto"
        body.update({"num_images": 1, "resolution": "1600p"})
        if urls:
            body["image_urls"] = urls
    elif urls:
        path = "/higgsfield-ai/soul/reference"
        body.update({"batch_size": 1, "resolution": "1080p", "image_reference_url": urls[0]})
    else:
        path = "/higgsfield-ai/soul/standard"
        body = {"prompt": prompt, "num_images": 1, "resolution": "2K", "aspect_ratio": body["aspect_ratio"]}
    sub = api(path, key, body)
    status_url = sub.get("status_url") or f"/requests/{sub['request_id']}/status"
    delay, waited = 2, 0
    while waited < max_wait_s:
        st = api(status_url, key)
        state = st.get("status")
        if state == "completed":
            images = st.get("images") or []
            if not images:
                raise RuntimeError(f"Higgsfield completed without images: {json.dumps(st)[:400]}")
            with urllib.request.urlopen(images[0]["url"], timeout=180) as r:
                return r.read()
        if state in ("failed", "nsfw", "canceled"):
            raise RuntimeError(f"Higgsfield request {state}: {json.dumps(st)[:400]}")
        time.sleep(delay + random.random())
        waited += delay
        delay = min(10, delay * 1.5)
    raise RuntimeError("timed out waiting for Higgsfield")
