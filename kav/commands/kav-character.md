---
name: kav-character
description: Bring a character into a story — take whatever exists (a portrait, an inspiration photo, or only a description) and build their reference mug shots so every later panel renders the same person. Use when the author types /kav-character <name>, adds or changes a character, or when a character keeps coming out looking wrong.
argument-hint: "<name> [--story <slug>]"
---

# /kav-character <name> — intake and mug shots

## Story scope — first

A story's cast is only what that story defines: `stories/<slug>/cast/*.md`. Never reuse a character, location or style pack from another story unless the author asks in words ("reuse the captain from my other story"). If something needed is missing, say so and offer to create it — a silently borrowed reference is worse than a missing one, because it looks correct. Build characters one at a time by name; never rebuild a whole registry.

## Why mug shots

A character enters loose: one portrait, a photo with the right energy, sometimes a sentence. That can't render them from an arbitrary angle — a three-quarter portrait carries no frontal information, so a selfie-angle panel invents a stranger. Intake turns it into a consistent set in `stories/<slug>/cast/<name>/`:

| File | What it is | Why it earns its slot |
|---|---|---|
| `front.png` | Head and shoulders, straight to camera, neutral | The view most often missing; close shots need it |
| `three-quarter.png` | Turned ~30°, eyes on lens | The everyday conversational angle |
| `smile.png` | Frontal, laughing openly | Stops every happy moment reverting to the neutral mouth |
| `full-body.png` | Standing, head to feet | Proportions, height, default wardrobe |
| `source.*` | What we started from | Provenance |

Animals and non-human characters get the same four views, adapted.

## Running intake

1. Seeds: copy the author's photos to `stories/<slug>/cast/<name>/source*.<ext>`.
2. Description: add or update `characters.<name>` in `stories/<slug>/briefs.json` — one English line of physical description. **This line goes into every prompt**, not just the mug shots.
3. Build:

```
python3 tools/build_mugshots.py --story <slug> --char <name> [--seed N]
```

Runs on the identity-strong lane (Nano Banana Pro), roughly $0.60 per character. Existing shots are skipped by the tool unless asked to rebuild (see its `--help`).

4. **Look at all four shots before moving on.** If the front has drifted from the source, that drift propagates into everything. Rebuild, or add a better seed.
5. **One detail wrong** (a scar missing, the ear shape, a collar colour)? Don't rebuild the set — touch it up:

```
python3 tools/touch_up.py --story <slug> --char <name> --shot front --instruction "<one detail>"
```

One instruction per call; look at the result.

## No reference at all

The author gives only a description. Generate a candidate source with `python3 tools/generate.py --story <slug> "<a plain photographic portrait of …>" --ar 4:5`, show 2–4 takes, and let the author pick or redirect — **casting a face is the author's call.** Copy the pick to `cast/<name>/source.png`, then run intake.

## Getting descriptions right

- **Ground them in what the photo shows.** Read the source image and describe it; don't guess from the name.
- **Thin descriptions cause drift.** "a young woman" gives the model nothing to hold. Name hair, eyes, skin, build, age, and one distinctive feature.
- **Direct the smile** with `mugshot_direction.<name>` when the default warm smile is wrong for the character ("a slow knowing half-smile, not a grin").

## Revising

Edit `briefs.json` → rebuild the one character → look at all four → regenerate one scene you know well to see the change downstream. A changed character marks panels that used the old set as candidates for review, not automatic rerolls — ask.

## Styled mug shots

Once a style is locked, styled sets are built by `/kav-visual-style-lock` into `cast/<name>/<pack>/`. Generation prefers the styled set when it exists: it reconciles identity and style once, up front, instead of in every panel.

## How the references are used

The tools send views best-first and scale the count to the cast size: more references for a solo shot, fewer per character in a crowd. References compete for influence; one mug shot per character in multi-character scenes, or a character can appear twice.

## Hard rules

- The author picks faces. Never adopt one on their behalf.
- Look at every shot before moving on.
- Story-local in and out.
