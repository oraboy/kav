"""Image generation, one entry point for every tool.

Two independent choices:
  lane      the model: seedream (cheap, the panel default), nanobanana (identity-strong),
            or a provider's own — popcorn, soul
  provider  who runs it: fal, magnific, higgsfield, gemini

What each provider and model can do — endpoints, reference caps, aspect handling, price,
how far it has been tested and when that was last checked — lives in `models.json`, not in
code. Adding or refreshing a model is an edit there plus a bake-off run.

`generate(...)` takes a prompt, reference image paths, a lane and a size and returns
(image_bytes, provider). The provider is --provider, else $KAV_PROVIDER, else the first
configured provider (registry order) that runs the lane.
"""
import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kav_env import data_uri, get_key  # noqa: E402

REGISTRY = json.loads((Path(__file__).resolve().parent / "models.json").read_text())
PROVIDERS = {k: v for k, v in REGISTRY["providers"].items()}
PROVIDER_ORDER = list(PROVIDERS)
ASPECTS = {k: tuple(v) for k, v in REGISTRY["aspects"].items() if not k.startswith("_")}
LANES = tuple(dict.fromkeys(m for p in PROVIDERS.values() for m in p["models"]))
STALE_DAYS = 120        # after this, check_setup nudges someone to re-verify an entry


def model(provider, lane):
    return PROVIDERS[provider]["models"].get(lane)


def max_refs(provider, lane=None):
    """The provider's reference cap for a lane: None means Kav's full stack."""
    if lane:
        m = model(provider, lane)
        return m.get("max_refs") if m else None
    caps = [m.get("max_refs") for m in PROVIDERS[provider]["models"].values()]
    caps = [c for c in caps if c]
    return max(caps) if caps else None


def days_since_verified(provider, lane=None):
    entry = model(provider, lane) if lane else PROVIDERS[provider]
    try:
        y, m, d = (int(x) for x in entry["verified_on"].split("-"))
        return (date.today() - date(y, m, d)).days
    except Exception:
        return None


def _nearest_ar(size):
    w, h = size
    return min(ASPECTS, key=lambda k: abs(ASPECTS[k][0] / ASPECTS[k][1] - w / h))


def _fal(spec, lane, prompt, refs, ar, size, seed):
    from . import fal
    endpoint = spec["edit"] if refs else spec["text_to_image"]
    if spec["takes"] == "size":
        w, h = size or ASPECTS.get(ar or "9:16", ASPECTS["9:16"])
        payload = {"prompt": prompt, "image_size": {"width": w, "height": h}}
    else:
        from .gemini import aspect as nb_aspect      # 8:5 → 16:9, 12:5 → 21:9
        payload = {"prompt": prompt, "aspect_ratio": nb_aspect(ar), "resolution": "2K",
                   "safety_tolerance": "5", "output_format": "png"}
    if refs:
        payload["image_urls"] = [data_uri(p) for p in refs]
    if seed is not None:
        payload["seed"] = seed
    return fal.run(endpoint, payload, get_key("FAL_KEY"))


def _gemini(spec, lane, prompt, refs, ar, size, seed):
    from . import gemini
    return gemini.run(prompt, list(refs), get_key("GEMINI_API_KEY"), ar=ar or "9:16",
                      model=spec["edit"], seed=seed)


def _magnific(spec, lane, prompt, refs, ar, size, seed):
    from . import magnific
    from kav_env import jpeg_bytes
    return magnific.run(spec, prompt, [jpeg_bytes(p, max_px=1600) for p in refs],
                        get_key("MAGNIFIC_API_KEY"), ar=ar or (_nearest_ar(size) if size else None),
                        seed=seed)


def _higgsfield(spec, lane, prompt, refs, ar, size, seed):
    from . import higgsfield
    from kav_env import jpeg_bytes
    return higgsfield.run(lane, spec, prompt, [jpeg_bytes(p, max_px=1600) for p in refs],
                          get_key("HIGGSFIELD_API_KEY"),
                          ar=ar or (_nearest_ar(size) if size else None), seed=seed)


CLIENTS = {"fal": _fal, "gemini": _gemini, "magnific": _magnific, "higgsfield": _higgsfield}


def configured():
    """Providers whose keys are all set, in registry order."""
    return [p for p, v in PROVIDERS.items() if all(get_key(k) for k in v["keys"])]


def resolve(lane, provider=None):
    """The provider to use for a lane, or SystemExit with what to set."""
    provider = provider or os.environ.get("KAV_PROVIDER") or None
    if provider:
        if provider not in PROVIDERS:
            sys.exit(f"Unknown provider {provider!r}. Known: {', '.join(PROVIDERS)}")
        entry = PROVIDERS[provider]
        if lane not in entry["models"]:
            sys.exit(f"{entry['title']} does not run the {lane} lane "
                     f"(it runs: {', '.join(entry['models'])})")
        missing = [k for k in entry["keys"] if not get_key(k)]
        if missing:
            sys.exit(f"{entry['title']} needs {', '.join(missing)}. Run: python3 tools/check_setup.py")
        return provider
    for p in configured():
        if lane in PROVIDERS[p]["models"]:
            return p
    sys.exit(f"No configured provider runs the {lane} lane. Run: python3 tools/check_setup.py")


def cheapest():
    """(lane, provider, approx $) for the cheapest configured option, or None."""
    options = [(m["price"], lane, p) for p in configured()
               for lane, m in PROVIDERS[p]["models"].items() if m.get("price")]
    if not options:
        return None
    price, lane, p = min(options)
    return lane, p, price


def generate(prompt, refs=(), lane="seedream", ar=None, size=None, seed=None, provider=None):
    """Image bytes and the provider used. `size` (w, h) overrides `ar` where supported."""
    p = resolve(lane, provider)
    spec = model(p, lane)
    cap = spec.get("max_refs")
    refs = [Path(r) for r in refs][:cap] if cap else [Path(r) for r in refs]
    return CLIENTS[p](spec, lane, prompt, refs, ar, size, seed), p
