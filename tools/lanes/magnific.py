"""Magnific API client (formerly the Freepik API).

POST https://api.magnific.com/v1/ai/text-to-image/<model> with header x-magnific-api-key,
then poll GET .../<model>/<task_id> until COMPLETED and download data.generated[0].
Aspect ratios are a fixed enum, so the page-cell shapes map to the nearest one. Which
models exist, and their reference caps, come from models.json. Needs MAGNIFIC_API_KEY.
"""
import base64
import json
import time
import urllib.error
import urllib.request

BASE = "https://api.magnific.com/v1/ai/text-to-image"   # models and caps: models.json

ASPECT = {
    "1:1": "square_1_1", "16:9": "widescreen_16_9", "9:16": "social_story_9_16",
    "2:3": "portrait_2_3", "3:4": "traditional_3_4", "3:2": "standard_3_2",
    "4:3": "classic_4_3", "4:5": "traditional_3_4", "8:5": "widescreen_16_9",
    "12:5": "cinematic_21_9",
}


def api(url, key, payload=None, timeout=180):
    req = urllib.request.Request(url, headers={"x-magnific-api-key": key,
                                               "Content-Type": "application/json"})
    data = json.dumps(payload).encode() if payload is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"Magnific HTTP {e.code}: {body[:400]}") from None


def run(spec, prompt, ref_bytes, key, ar="9:16", seed=None, poll_s=3, max_polls=200):
    """spec: the model's entry from models.json. ref_bytes: JPEG bytes, best first."""
    model = spec["edit"] if ref_bytes else spec["text_to_image"]
    payload = {"prompt": prompt[:4096], "aspect_ratio": ASPECT.get(ar or "9:16", "social_story_9_16"),
               "enable_safety_checker": False}
    if ref_bytes:
        payload["reference_images"] = [base64.b64encode(b).decode() for b in ref_bytes]
    if seed is not None:
        payload["seed"] = int(seed)
    task = api(f"{BASE}/{model}", key, payload)["data"]
    for _ in range(max_polls):
        if task.get("status") == "COMPLETED" and task.get("generated"):
            break
        if task.get("status") == "FAILED":
            raise RuntimeError(f"Magnific task failed: {json.dumps(task)[:400]}")
        time.sleep(poll_s)
        task = api(f"{BASE}/{model}/{task['task_id']}", key)["data"]
    else:
        raise RuntimeError("timed out waiting for Magnific")
    with urllib.request.urlopen(task["generated"][0], timeout=180) as r:
        return r.read()
