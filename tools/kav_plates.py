"""Location plates: a place drawn once in the book's style, then reused like a mug shot.

A photograph of a real place and a stylised drawing of a character are two different kinds
of picture, and a panel that binds both has to reconcile them — silently, differently every
take. A plate moves that reconciliation out of the panel: the location is redrawn once in
the pack's style, the author looks at it, and from then on every panel set there binds the
drawing. Measured on nero-pizza (2026-09-27): the same panel at the same three seeds went
from 2/3 to 3/3 on character identity, and the place stopped drifting toward a generic
version of itself.

Plates are per shot, not per location, exactly as mug shots are per angle. A scene at the
window counter and a scene arriving from the street are two different views of Brooklyn and
want two different plates. Shots are declared in briefs.json:

    "locations": {"brooklyn": {
        "default_shot": "window-counter",
        "shots": {"window-counter": {"photo": "...", "words": [...], "description": "..."}}}}

Plates are built on demand and cached at locations/<loc>/plates/<shot>.png: the first panel
that needs a view pays for it (one Seedream call, ~$0.04), every later panel is free. Nothing
is generated up front.
"""
import os
import re

from kav_refs import root, style_pack_images, styles_dir

FRAME = (
    "Image 1 is a photograph of a real place. Images 2 to {n} are the rendering target. "
    "Redraw the place in image 1 exactly as it is — the same building, the same frontage, "
    "the same signage with the same wording and the same lettering, the same fittings, "
    "furniture, colours and light, from the same viewpoint. Change nothing about the place "
    "and invent nothing that is not in the photograph. Draw no people. "
    "Keep the photograph's orientation exactly: the ground stays at the bottom of the frame "
    "and the sky or ceiling at the top, furniture stands on the floor, and the view is never "
    "mirrored, tilted or turned over. "
    "Copy every piece of lettering glyph for glyph from the photograph, in the same script "
    "and the same spelling. Where a sign is cut off, turned away, or too small to read, draw "
    "it blank or leave it out — never fill it with invented words. A plate is bound by every "
    "panel set in this place, so a sign invented here is wrong on every page of the book. "
    "Render the entire final image as a {medium}, matching the style pack's line quality, "
    "colour palette, shading, texture and level of abstraction throughout."
)


def shots(spec, loc):
    """The declared shots for a location, or {} for a location that has none yet."""
    return (spec.get("locations", {}).get(loc) or {}).get("shots") or {}


def pick_shot(brief, spec):
    """Which view of the location this scene wants: (shot key, photo path) or (None, None).

    Matched on the scene line, so "outside Brooklyn, walking up" gets the shopfront and "at
    the window counter" gets the interior. **The most specific cue wins, not the longest.**
    Ranking by string length put a La Tigre panel on the terrace because "pavement" is
    longer than "neon" — and the terrace plate has neither the neon disc nor the mural the
    line asked for. A cue that names a feature of the place beats one that names furniture,
    and a multi-word cue beats a single word at equal specificity.

    No match falls back to the location's `default_shot`, which is where generic words
    belong: a scene that only says "at a table" wants the default view, and saying so by
    silence is more honest than a cue list full of words every scene contains.
    """
    loc = brief.get("location")
    if not loc:
        return None, None
    declared = shots(spec, loc)
    if not declared:
        return None, None
    low = (brief.get("scene") or "").lower()
    best, best_rank = None, (0, 0)
    for key, cfg in declared.items():
        for w in cfg.get("words", []):
            if not re.search(re.escape(w.lower()), low):
                continue
            rank = (len(w.split()), len(w))   # a phrase outranks a word; then the longer word
            if rank > best_rank:
                best, best_rank = key, rank
    key = best or spec["locations"][loc].get("default_shot") or next(iter(declared))
    cfg = declared.get(key)
    return (key, root() / cfg["photo"]) if cfg else (None, None)


def plate_path(loc, shot):
    return root() / "locations" / loc / "plates" / f"{shot}.png"


def build_plate(loc, shot, photo, style_pack, seed=11, provider=None, camera=None):
    """Draw one shot of one location in the pack's style and cache it. Returns the path.

    `camera` replaces "from the same viewpoint" when a photograph will not copy — a wide
    downward view of round café tables inverted on three separate seeds, the tabletops read
    as ceiling lamps, until the camera was stated outright. A shot may carry one in
    briefs.json as `camera`.
    """
    import lanes

    medium = (styles_dir() / style_pack / "medium.txt").read_text(encoding="utf-8").strip()
    refs = [photo] + style_pack_images(style_pack, limit=3)
    prompt = FRAME.format(n=len(refs), medium=medium)
    if camera:
        prompt = prompt.replace("from the same viewpoint.", f"{camera.rstrip('.')}.")
    img, _ = lanes.generate(prompt, refs, lane="seedream",
                            size=(1536, 1152), seed=seed, provider=provider)
    out = plate_path(loc, shot)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(img)
    return out


def ensure_plate(brief, spec, style_pack, provider=None):
    """The plate this scene should bind, drawing it first if it does not exist yet.

    Returns the path, or None when the location has no shots declared, no style pack is in
    play, or KAV_NO_PLATES is set — in which case the planner falls back to the raw
    photographs. Never called on a dry run: a dry run must not spend money.
    """
    if not style_pack or os.environ.get("KAV_NO_PLATES"):
        return None
    shot, photo = pick_shot(brief, spec)
    if not shot:
        return None
    loc = brief["location"]
    out = plate_path(loc, shot)
    if out.exists():
        return out
    cfg = shots(spec, loc).get(shot) or {}
    return build_plate(loc, shot, photo, style_pack, provider=provider,
                       camera=cfg.get("camera"))
