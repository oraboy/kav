"""fal.ai queue client: submit a job, poll it, download the first image.

Endpoints used by Kav:
  SEEDREAM    fal-ai/bytedance/seedream/v4.5/edit   takes image_size {width, height}
  NANOBANANA  fal-ai/nano-banana-pro/edit           takes aspect_ratio + resolution
Needs FAL_KEY (or FAL_API_KEY).
"""
import json
import time
import urllib.error
import urllib.request

QUEUE = "https://queue.fal.run"
SEEDREAM = "fal-ai/bytedance/seedream/v4.5/edit"
NANOBANANA = "fal-ai/nano-banana-pro/edit"


def api(url, key, payload=None, timeout=180):
    # fal's balance-lock 403s flap (a cleared lock propagates slowly across their edge):
    # retry those a few times; every other error raises immediately with the body.
    req = urllib.request.Request(url, headers={
        "Authorization": f"Key {key}", "Content-Type": "application/json"})
    data = json.dumps(payload).encode() if payload is not None else None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            if e.code == 403 and ("TOP_UP" in body or "Exhausted balance" in body) and attempt < 3:
                time.sleep(10 * (attempt + 1))
                continue
            if e.code in (401, 403):
                raise RuntimeError(f"HTTP {e.code} from fal.ai (check FAL_KEY and account balance): "
                                   f"{body[:300]}") from None
            raise RuntimeError(f"HTTP {e.code}: {body[:300]}") from None
    raise RuntimeError("fal.ai: retry loop exhausted")


def run(endpoint, payload, key, poll_s=3, max_polls=120):
    """Submit to the queue, wait for completion, return the first image's bytes."""
    sub = api(f"{QUEUE}/{endpoint}", key, payload)
    for _ in range(max_polls):
        st = api(sub["status_url"], key)
        if st["status"] == "COMPLETED":
            break
        if st["status"] not in ("IN_QUEUE", "IN_PROGRESS"):
            raise RuntimeError(f"fal job failed: {st}")
        time.sleep(poll_s)
    else:
        raise RuntimeError("timed out waiting for the image")
    res = api(sub["response_url"], key)
    with urllib.request.urlopen(res["images"][0]["url"], timeout=180) as r:
        return r.read()
