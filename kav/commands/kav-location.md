---
name: kav-location
description: Bring a place into a story — take the author's photos (or a description, or a generated candidate they pick) and register it so every later panel draws the same place. Use when the author types /kav-location <name>, drops photos of a place, says "add a location", "new place", or when a place keeps coming out wrong.
argument-hint: "<name> [--story <slug>]"
---

# /kav-location <name> — a place Kav can draw the same way every time

A place enters as a few photos, sometimes one sentence. It leaves as three things under `stories/<slug>/`, all named with the same `<name>` so nothing has to be matched up later:

| File | What it is |
|---|---|
| `locations/<name>/<name>-NN.<ext>` | the reference photos, copied from what the author gave |
| `locations/<name>.md` | the sheet: what it is, whose place it is, what it looks like |
| `briefs.json` → `locations.<name>` + `location_words.<name>` | how drawing finds it: the photos, one English description, the words that trigger it |

Story-local, always: a place from another story is never borrowed unless the author asks in words.

## Taking a place in

1. **Name → key.** Lowercase-kebab (`corner-cafe`). The sheet, the photo folder and the registry entry all use it. One place, one name.
2. **Photos.** Copy the author's photos into `locations/<name>/<name>-01.<ext>`, `-02`… Keep the originals where they landed. **Photos must show every surface panels will need**: a ceiling and a wall-to-ceiling corner for an interior (without one, tall panels open the room to the sky), the floor, the doorway, the view out of the window. If a surface is missing, ask for one more photo rather than describing it.
3. **The sheet** (`docs/templates.md`, locations): what it is · whose turf · what it looks like · the reference images. Ask the author for a line on what it is, and whose place it is; don't invent the rest. Dramatic uses of a place are decided at PITCH, not here.
4. **Registry.** In `briefs.json`, add `locations.<name>` with `photos` and one English description of what the photos actually show (it goes into every prompt), and `location_words.<name>` with the words a scene line will use for it. Triggers are first-match: a specific place (`shop-entrance`) is listed before a general one (`shop`), and generic words ("room", "street", "apartment") stay out — they steal scenes meant for other places.
5. **Prove it.** Generate one test scene in the place (`python3 tools/generate.py --story <slug> "<a character> in <the place>"`), read the candidate's `.json` sidecar to confirm this location bound, and show it. If it came out wrong, fix the photos or the words, not the adjectives.
6. **Update the board** (`docs/know-how/story-board.md`), then offer the next step: another place, or move on.

## No photos

The author has only a description. Generate 2–4 candidate views with `tools/generate.py`, let the author pick — **choosing what a place looks like is the author's call** — and copy the pick in as `<name>-01.png`. Label it on the board as made by Kav, never as the author's photo.

## When a place drifts in chapters

Adjectives don't fix drift; references do. Copy an **approved panel** of the place into `locations/<name>/<name>-chNN.png` and add it to `photos` — the next generation binds the drawn place. It shows on the board as made by Kav.

## Removing an image

"Remove REF02 from the café": resolve the label through the board's `story-map.json`, move the file to `locations/<name>/_excluded/` (park, don't delete), take it out of `photos`, and update the board.

## Hard rules

- One place, one name, across sheet, folder and registry.
- The author picks every image that stands for a place.
- A reference photo that doesn't show a surface can't be fixed by describing it.
- Story-local in and out.
