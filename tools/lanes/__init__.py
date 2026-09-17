"""Image generation, one entry point for every tool.

Two independent choices:
  lane      the model family: seedream (cheap, default for panels) or nanobanana
            (identity-strong, default for mug shots)
  provider  who runs it: fal (fal.ai), gemini (Google direct, nanobanana only),
            and further providers as their clients land in this package

`generate(...)` takes a prompt, reference image paths, a lane and a size and returns
(png_bytes, provider). The provider is --provider, else $KAV_PROVIDER, else the first
provider in PROVIDER_ORDER that has a key and runs the lane.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kav_env import data_uri, get_key  # noqa: E402

LANES = ("seedream", "nanobanana", "popcorn", "soul")

# Seedream takes pixel sizes (kept near its 8 MP ceiling); the others take the ratio.
# Page cells are 4:5; a panel spans 1, 2 or 3 cells (4:5, 8:5, 12:5).
ASPECTS = {
    "9:16": (2160, 3840), "16:9": (3840, 2160), "1:1": (2880, 2880),
    "3:4": (2496, 3328), "4:3": (3328, 2496), "2:3": (2304, 3456), "3:2": (3456, 2304),
    "4:5": (2304, 2880), "8:5": (3456, 2160), "12:5": (3840, 1600),
}


def _fal(lane, prompt, refs, ar, size, seed):
    from . import fal
    key = get_key("FAL_KEY")
    if lane == "seedream":
        w, h = size or ASPECTS.get(ar or "9:16", ASPECTS["9:16"])
        payload = {"prompt": prompt, "image_size": {"width": w, "height": h}}
        endpoint = fal.SEEDREAM if refs else fal.SEEDREAM_T2I
    else:
        from .gemini import aspect as nb_aspect      # 8:5 → 16:9, 12:5 → 21:9
        payload = {"prompt": prompt, "aspect_ratio": nb_aspect(ar), "resolution": "2K",
                   "safety_tolerance": "5", "output_format": "png"}
        endpoint = fal.NANOBANANA if refs else fal.NANOBANANA_T2I
    if refs:
        payload["image_urls"] = [data_uri(p) for p in refs]
    if seed is not None:
        payload["seed"] = seed
    return fal.run(endpoint, payload, key)


def _gemini(lane, prompt, refs, ar, size, seed):
    from . import gemini
    return gemini.run(prompt, list(refs), get_key("GEMINI_API_KEY"), ar=ar or "9:16", seed=seed)


def _magnific(lane, prompt, refs, ar, size, seed):
    from . import magnific
    from kav_env import jpeg_bytes
    if size and not ar:
        ar = _nearest_ar(size)
    return magnific.run(lane, prompt, [jpeg_bytes(p, max_px=1600) for p in refs[:magnific.MAX_REFS]],
                        get_key("MAGNIFIC_API_KEY"), ar=ar, seed=seed)


def _higgsfield(lane, prompt, refs, ar, size, seed):
    from . import higgsfield
    from kav_env import jpeg_bytes
    if size and not ar:
        ar = _nearest_ar(size)
    cap = higgsfield.MAX_REFS.get(lane, 0)
    return higgsfield.run(lane, prompt, [jpeg_bytes(p, max_px=1600) for p in refs[:cap]],
                          get_key("HIGGSFIELD_API_KEY"), ar=ar, seed=seed)


def _nearest_ar(size):
    w, h = size
    return min(ASPECTS, key=lambda k: abs(ASPECTS[k][0] / ASPECTS[k][1] - w / h))


# name: (key names that must all be set, lanes it runs, client, rough $ per image by lane)
PROVIDERS = {
    "fal": (("FAL_KEY",), LANES, _fal, {"seedream": 0.04, "nanobanana": 0.15}),
    "gemini": (("GEMINI_API_KEY",), ("nanobanana",), _gemini, {"nanobanana": 0.15}),
    "magnific": (("MAGNIFIC_API_KEY",), ("seedream",), _magnific, {"seedream": 0.05}),
    "higgsfield": (("HIGGSFIELD_API_KEY",), ("popcorn", "soul"), _higgsfield,
                   {"popcorn": 0.05, "soul": 0.05}),
}
PROVIDER_ORDER = ["fal", "magnific", "higgsfield", "gemini"]


MAX_REFS = {"magnific": 5, "higgsfield": 8}   # reference caps; others take Kav's full set


def max_refs(provider, lane=None):
    if provider == "higgsfield" and lane == "soul":
        return 1
    return MAX_REFS.get(provider)


def configured():
    """Providers whose keys are all set, in preference order."""
    return [p for p in PROVIDER_ORDER if all(get_key(k) for k in PROVIDERS[p][0])]


def resolve(lane, provider=None):
    """The provider to use for a lane, or SystemExit with what to set."""
    provider = provider or os.environ.get("KAV_PROVIDER") or None
    if provider:
        if provider not in PROVIDERS:
            sys.exit(f"Unknown provider {provider!r}. Known: {', '.join(PROVIDERS)}")
        keys, lanes, _, _ = PROVIDERS[provider]
        if lane not in lanes:
            sys.exit(f"Provider {provider} does not run the {lane} lane (it runs: {', '.join(lanes)})")
        missing = [k for k in keys if not get_key(k)]
        if missing:
            sys.exit(f"Provider {provider} needs {', '.join(missing)}. Run: python3 tools/check_setup.py")
        return provider
    for p in configured():
        if lane in PROVIDERS[p][1]:
            return p
    sys.exit(f"No configured provider runs the {lane} lane. Run: python3 tools/check_setup.py")


def cheapest():
    """(lane, provider, approx $) for the cheapest configured option, or None."""
    options = [(cost, lane, p) for p in configured() for lane, cost in PROVIDERS[p][3].items()]
    if not options:
        return None
    cost, lane, p = min(options)
    return lane, p, cost


def generate(prompt, refs=(), lane="seedream", ar=None, size=None, seed=None, provider=None):
    """PNG/JPEG bytes and the provider used. `size` (w, h) overrides `ar` where supported."""
    p = resolve(lane, provider)
    return PROVIDERS[p][2](lane, prompt, [Path(r) for r in refs], ar, size, seed), p
