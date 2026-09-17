"""Reference assembly: from a scene brief to an ordered list of reference images plus one prompt.

Each brief becomes an ordered list of reference images (characters first, then the
location photo, then objects, then style-pack images) plus one prompt that binds names
to image indices, so the same brief runs identically on every image backend.

Story layout this module reads (all under <repo>/stories/<slug>/):
  briefs.json                      characters, locations, objects, word maps, defaults
  cast/<name>/front.png ...        mug shots (optionally cast/<name>/<pack>/front.png ...)
  cast/<name>/source*.jpg          seed photos a mug-shot set is built from
  locations/<loc>/...              location photos, listed in briefs.json
  objects/<obj>.png                object photos
  scenes.md                        optional extra briefs
Style packs are shared across stories: <repo>/styles/<pack>/*.png + medium.txt.
"""
import json
import os
import re

from kav_env import REPO, data_uri, load_env_key  # noqa: F401  (re-exported)

# --- story scope -------------------------------------------------------------
# A story owns its cast, locations, objects and spec. Resolving through root() means
# a story can never silently bind another story's character — the failure mode that
# looks correct and therefore never gets caught by eye.
_STORY = os.environ.get("KAV_STORY", "").strip()


def set_story(slug):
    """Scope every asset lookup to stories/<slug>/. Empty/None = repo root."""
    global _STORY
    _STORY = (slug or "").strip()
    if _STORY and not (REPO / "stories" / _STORY).is_dir():
        raise SystemExit(f"No such story: stories/{_STORY}")
    return root()


def current_story():
    return _STORY or None


def root():
    """Where cast/, locations/, objects/ and briefs.json resolve from."""
    return REPO / "stories" / _STORY if _STORY else REPO


def spec_path():
    return root() / "briefs.json"


def cast_dir():
    return root() / "cast"


def scenes_path():
    return root() / "scenes.md"


def styles_dir():
    """Style packs are the one shared thing: a look is reusable across stories.
    Everything else (cast, locations, spec, generated output) is story-local."""
    return REPO / "styles"


def _spec_json():
    p = spec_path()
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def registered_packs():
    """Style packs on disk, usable by name in a quick scene line."""
    d = styles_dir()
    return sorted(p.name for p in d.iterdir() if p.is_dir()) if d.exists() else []


def location_words():
    """Keywords that map a plain-English scene line to a location.

    A story's spec may carry `location_words`; otherwise every location matches on
    its own name. There is no shared fallback set: a story that fell back to one
    would match another story's places.
    """
    spec = _spec_json()
    if not spec:
        return {}
    if spec.get("location_words"):
        return spec["location_words"]
    return {loc: [loc] for loc in spec.get("locations", {})}


def object_words():
    """Keywords that map a scene line to a registered object.

    Objects are the third reference layer beside cast and locations: a thing that must
    look exactly the same every time it appears (a chocolate bar, a sword, a dress).
    """
    spec = _spec_json()
    if not spec:
        return {}
    if spec.get("object_words"):
        return spec["object_words"]
    return {o: [o] for o in spec.get("objects", {})}


def parse_quick_line(text, n, characters):
    """A plain-English one-liner into a brief: cast, location, objects and style
    detected, the rest kept as the scene."""
    low = text.lower()

    chars = [name for name in characters if re.search(rf"\b{re.escape(name.lower())}\b", low)]
    if not chars:
        return None

    # word lists are checked in spec order: put the more specific location first
    location = next((loc for loc, words in location_words().items()
                     if any(w.lower() in low for w in words)), None)
    objects = [o for o, words in object_words().items() if any(w.lower() in low for w in words)]
    # word-boundary match, longest name first: "sc2" must never match the "sc" pack
    pack = next((p for p in sorted(registered_packs(), key=len, reverse=True)
                 if re.search(rf"\b{re.escape(p.lower())}\b", low)), None)
    if pack:
        scene = re.sub(rf",?\s*(?:using|in|with)?\s*(?:the\s+)?{re.escape(pack)}[\w-]*(?:\s+style)?",
                       "", text, flags=re.I)
        scene = re.sub(r",?\s*style\b", "", scene, flags=re.I)
    else:
        scene = text
    for name in chars:
        scene = re.sub(rf"\b{re.escape(name)}\b", "{" + name + "}", scene, flags=re.I)
    scene = " ".join(scene.split()).strip(" ,.") + "."

    brief = {"id": f"q{n}-" + "-".join(chars[:2] + ([location] if location else [])),
             "test": "Q", "characters": chars, "scene": scene}
    if location:
        brief["location"] = location
    if objects:
        brief["objects"] = objects
    if pack:
        brief["style"] = pack
        brief["style_pack"] = pack
    return brief


def parse_scenes(path=None):
    """Briefs authored as markdown in scenes.md.

    Either `- one quick line` bullets (parsed like a generate.py line), or blocks:
    `### <id>`, then `key: value` lines (chars, objects, location, style), then scene text.
    """
    path = path or scenes_path()
    if not path.exists():
        return []
    briefs, cur, body, in_fence, quick_n = [], None, [], False, 0
    known_chars = list((_spec_json() or {}).get("characters", {}))

    def flush():
        if cur and body:
            cur["scene"] = " ".join(" ".join(body).split())
            briefs.append(cur)

    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        quick = re.match(r"^\s*(?:-|\d+\.)\s+(.*\S)", line)
        if quick and cur is None:
            quick_n += 1
            b = parse_quick_line(quick.group(1), quick_n, known_chars)
            if b:
                briefs.append(b)
            continue
        if line.startswith("### "):
            flush()
            cur, body = {"id": line[4:].strip(), "test": "S", "characters": []}, []
            continue
        if cur is None:
            continue
        stripped = line.strip()
        if not stripped:
            continue
        key, sep, val = stripped.partition(":")
        key, val = key.strip().lower(), val.strip()
        if sep and not body and key in {"chars", "characters", "objects", "location", "style", "test"}:
            if key in ("chars", "characters"):
                cur["characters"] = [c.strip() for c in val.split(",") if c.strip()]
            elif key == "objects":
                cur["objects"] = [o.strip() for o in val.split(",") if o.strip()]
            else:
                cur[key] = val
            continue
        body.append(stripped)
    flush()
    return briefs


def load_spec():
    p = spec_path()
    if not p.exists():
        where = p.relative_to(REPO) if p.is_relative_to(REPO) else p
        raise SystemExit(f"No spec at {where}.\n"
                         f"A story owns its own cast and locations: create stories/<slug>/briefs.json "
                         f"(see tools/examples/briefs.example.json).")
    spec = json.loads(p.read_text(encoding="utf-8"))
    spec.setdefault("briefs", [])
    spec.setdefault("locations", {})
    spec.setdefault("defaults", {})
    known = {b["id"] for b in spec["briefs"]}
    spec["briefs"].extend(b for b in parse_scenes() if b["id"] not in known)
    return spec


def title(name):
    return name[0].upper() + name[1:]


IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def out_dir(*parts):
    """Every generated file lands under the story, never in a shared scratch folder,
    so two stories can generate at the same time without their output mixing."""
    d = root().joinpath(*parts)
    d.mkdir(parents=True, exist_ok=True)
    return d


def style_pack_images(name, limit=None):
    """Images in styles/<name>/ that define a look by example.

    Narrative-still packs (real film/comic frames) often show other people or a whole
    scene, not just a rendering technique; sending all of them into a single-character
    mug shot invites the model to copy that content wholesale. `limit` caps how many are
    sent: mug-shot generation passes a small number, scene generation passes none (all).
    """
    d = styles_dir() / name
    if not d.exists():
        return []
    images = sorted(p for p in d.iterdir() if p.suffix.lower() in IMG_EXT)
    return images[:limit] if limit is not None else images


def style_medium(name):
    """One line naming the medium, from styles/<name>/medium.txt.

    Naming the medium in prose measurably strengthens style transfer; it is the closest
    thing these endpoints have to a style-weight knob.
    """
    f = styles_dir() / name / "medium.txt"
    return f.read_text(encoding="utf-8").strip() if f.exists() else ""


MUGSHOT_ORDER = ["front", "three-quarter", "smile", "full-body"]

REF_BUDGET = None          # a runner may override how many views per character


def char_budget(n_chars):
    """How many mug shots each character gets in a scene.

    Three when alone, two otherwise. Dropping to one for a four-character scene broke
    identity: a single frontal against eight style stills loses the face and hair. The
    style pack is trimmed instead (see style_budget).
    """
    return REF_BUDGET or (3 if n_chars == 1 else 2)


def style_budget(n_chars, has_location=False):
    """How many style-pack images a scene gets: all of them for one or two characters in
    no particular place; four once the cast reaches three, or whenever a real location
    photo is bound (a single photo against eight stills loses the place)."""
    return 4 if n_chars >= 3 or has_location else None


def mugshots(name, n_chars=1, style_pack=None):
    """A character's mug shots, best-first.

    Frontal comes first: it is what a selfie or a close two-shot needs, and a
    three-quarter portrait alone leaves the model to invent the face. How many are sent
    scales down with cast size, since references compete for influence.

    If a set exists for the style being rendered, it wins: identity and rendering arrive
    already reconciled instead of being negotiated in every scene.
    """
    if style_pack:
        styled = cast_dir() / name / style_pack
        if styled.is_dir():
            found = [styled / f"{s}.png" for s in MUGSHOT_ORDER if (styled / f"{s}.png").exists()]
            if found:
                return found[:char_budget(n_chars)]
    folder = cast_dir() / name
    if folder.is_dir():
        found = [folder / f"{s}.png" for s in MUGSHOT_ORDER if (folder / f"{s}.png").exists()]
        if found:
            return found[:char_budget(n_chars)]
        src = sorted(p for p in folder.glob("source*") if p.suffix.lower() in IMG_EXT)
        if src:
            # A background character can be more than one individual (two cats under one
            # name): truncating to the first source photo would drop the second entirely.
            return src[:char_budget(n_chars)]
    legacy = cast_dir() / f"{name}.png"
    return [legacy] if legacy.exists() else []


def portrait_path(name, pack=None):
    """The best single front-facing image of a character, for covers and cast slides."""
    base = cast_dir() / name
    candidates = []
    if pack:
        candidates.append(base / pack / "front.png")
    candidates.append(base / "front.png")
    if base.is_dir():
        candidates += sorted(base.glob("*/front.png"))
        candidates += sorted(p for p in base.glob("source*") if p.suffix.lower() in IMG_EXT)
    for c in candidates:
        if c.exists():
            return c
    raise SystemExit(f"No portrait for '{name}': expected {base}/[<pack>/]front.png")


def plan_refs(brief, spec, style_pack=None, max_refs=None):
    """What each reference slot holds: {characters: {name: [paths]}, location: [paths],
    objects: [(name, path)], style: [paths]}. `max_refs` is a provider's image cap: past it,
    each character keeps its best shot, the location its first photo, objects stay, and the
    style pack gets what is left."""
    chars = brief["characters"]
    shots = {n: mugshots(n, len(chars), style_pack) for n in chars}
    loc = brief.get("location")
    loc_photos = [root() / p for p in spec["locations"][loc].get("photos", [])] if loc else []
    objects = []
    for obj in brief.get("objects", []):
        p = next((root() / "objects" / f"{obj}{e}" for e in (".png", ".jpg", ".jpeg", ".webp")
                  if (root() / "objects" / f"{obj}{e}").exists()), None)
        if p:
            objects.append((obj, p))
    style = style_pack_images(style_pack, limit=style_budget(len(chars), bool(loc))) if style_pack else []
    total = sum(len(v) for v in shots.values()) + len(loc_photos) + len(objects) + len(style)
    if max_refs and total > max_refs:
        shots = {n: v[:1] for n, v in shots.items()}
        loc_photos = loc_photos[:1]
        used = sum(len(v) for v in shots.values()) + len(loc_photos) + len(objects)
        style = style[:max(0, max_refs - used)]
    return {"characters": shots, "location": loc_photos, "objects": objects, "style": style}


def ref_warning(plan, style_pack, max_refs=None):
    """The style cliff on a capped provider, in one line, or None.

    With a cap (Magnific: 5 images), every character, the location photo and each object
    take a slot before the style pack does. Past three characters — or three counting a
    bound object — the pack is left one image or none, and the panel comes back in the
    model's own house style instead of the story's. Proven on berko-and-olive's ch01 s7p1
    and ch03 s6p3 (2026-09-17). The fix is the panel, not the provider: split the cast.
    """
    if not style_pack or not max_refs:
        return None
    if len(plan["style"]) >= 2:
        return None
    n = len(plan["characters"]) + len(plan["objects"])
    return (f"style pack got {len(plan['style'])} reference(s): {n} characters/objects plus the "
            f"location fill the {max_refs}-image budget. Expect the look to drift. Split the panel "
            f"or drop a character.")


def build_refs(brief, spec, style_pack=None, max_refs=None):
    """Ordered reference images: characters, then location photos, then objects, then
    style-pack images. Returns a list of {kind, name, local}."""
    plan = plan_refs(brief, spec, style_pack, max_refs)
    refs = []
    for name, paths in plan["characters"].items():
        refs += [{"kind": "character", "name": name, "local": p} for p in paths]
    refs += [{"kind": "location", "name": brief.get("location"), "local": p} for p in plan["location"]]
    refs += [{"kind": "object", "name": n, "local": p} for n, p in plan["objects"]]
    refs += [{"kind": "style", "name": style_pack, "local": p} for p in plan["style"]]
    return refs


def build_prompt(brief, spec, style_pack=None, max_refs=None):
    """One prompt string: image-index preamble, scene with bound names, location/style blocks.

    A style pack (images) replaces the spec's written register: defining the look by
    example is the point of the pack. The image numbers follow plan_refs, the same plan
    build_refs sends, so the preamble always points at the right picture.
    """
    plan = plan_refs(brief, spec, style_pack, max_refs)
    chars = brief["characters"]
    lines, n = [], 0
    at = {}                    # where each character's images actually start
    for name in chars:
        shots = plan["characters"][name]
        first = n + 1
        at[name] = first
        n += max(1, len(shots))
        desc = spec["characters"].get(name, "")
        if n == first:
            lines.append(f"Image {first} shows {title(name)}: {desc}.")
        else:
            lines.append(f"Images {first} to {n} show {title(name)} — one character, "
                         f"photographed from several angles: {desc}.")
    loc = brief.get("location")
    if loc and plan["location"]:
        first, n = n + 1, n + len(plan["location"])
        if n == first:
            lines.append(f"Image {n} shows the real location the scene takes place in.")
        else:
            lines.append(f"Images {first} to {n} show the real location the scene takes place in.")
    for obj, _ in plan["objects"]:
        n += 1
        desc = spec.get("objects", {}).get(obj, {}).get("description", "")
        lines.append(f"Image {n} is a photograph of a real physical object — the "
                     f"{obj.replace('-', ' ')}." + (f" {desc}" if desc else ""))
    if brief.get("objects"):
        # framing these as photographs of real things, rather than objects to draw,
        # is what makes lettering on them carry across verbatim
        lines.append("Place those objects into the scene exactly as they appear, unchanged, as "
                     "though they had been photographed there. Any lettering on them is copied "
                     "verbatim, glyph for glyph, in the same script and spelling — never "
                     "re-typeset, translated, or replaced with different words.")
    pack = plan["style"]
    if pack:
        first, last = n + 1, n + len(pack)
        span = f"Image {first}" if len(pack) == 1 else f"Images {first} to {last}"
        lines.append(f"{span} (style pack: {style_pack}) are the rendering target.")
    preamble = " ".join(lines)

    scene = brief["scene"]
    for name in chars:
        # point at where this character's images really start: with more than one mug
        # shot each, a positional guess sends the model to the wrong face
        scene = scene.replace("{" + name + "}", f"{title(name)} (the character in image {at[name]})")

    parts = [preamble, scene] if lines else [scene]

    # identity is the first thing a style pack erodes: anchor it explicitly
    if chars:
        who = " and ".join(title(c) for c in chars)
        parts.append(
            f"{who} must remain recognisably the same {'characters' if len(chars) > 1 else 'character'} "
            f"as in their reference images: keep each face's structure, eye shape and spacing, nose, "
            f"mouth, jawline, hairline, hair colour and hair texture, and their apparent age. The "
            f"rendering changes how they are drawn; it never changes who they are."
        )

    # "a selfie" means the phone IS the camera, not a subject in someone else's photo
    if "selfie" in scene.lower():
        parts.append(
            "This image is the photograph that phone took. The camera is the phone's own front lens "
            "held at arm's length, so the frame is what the lens sees: faces close to camera, slight "
            "wide-angle distortion at the edges, subjects looking into the lens. There is no second "
            "camera and no outside observer — the phone being held is not visible in the picture, "
            "though the near arm reaching toward the lens may be."
        )
    if pack:
        # Positive framing throughout: negative commands ("take nothing of their subject")
        # underperform. Every slot is assigned instead, so there is nothing left for the
        # style refs to fill. The named medium is the verbal reinforcement.
        medium = style_medium(style_pack)
        as_medium = f"as a {medium}" if medium else "in the style of the style-reference images"
        n_content = n          # n counts content images only; style images come after
        span = "image 1" if n_content == 1 else f"images 1 to {n_content}"
        parts.append(
            f"Render the entire final image {as_medium}, matching the style pack's line quality, "
            f"colour palette, shading, texture and level of abstraction throughout, including the "
            f"background. The final image shows only the scene described above; its subject, "
            f"composition and setting come entirely from {span}."
        )
    elif spec.get("defaults", {}).get("register"):
        parts.append(spec["defaults"]["register"])
    return " ".join(parts)
