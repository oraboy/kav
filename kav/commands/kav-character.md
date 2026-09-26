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

6. **Update the board** (`docs/know-how/story-board.md`) — or open it, if this is the story's first piece — then offer the fork in one line: another character, or move on.

"Remove the second portrait of Oren": resolve it through the board's `story-map.json` (the piece's images, in the order the board shows them), confirm which one, park the file in `cast/<name>/_excluded/` with a one-line why in the cast file, and rebuild the board.

## Arguments the board hands out

The board's to-do lines give the author these ready to copy. `<name>` is the display name on the board; match it against each sheet's heading and file name, and ask if two match.

- `/kav-character <name> <one line>` — write the line into the sheet's **Who they are**, verbatim. Nothing else changes.
- `/kav-character <name> complete as is` — the author's decision that this character is deep enough. Write `*Complete as is — the author's call, <date>.*` under the heading; the board stops asking for more. Never argue it.
- `/kav-character <name> build a dna` — run the full DNA interview (kickoff CAST, full DNA) one section at a time, keeping every line the author already gave. It helps Kav come up with better story and dialogue ideas for them.

## No reference at all

The author gives only a description. Generate a candidate source with `python3 tools/generate.py --story <slug> "<a plain photographic portrait of …>" --ar 4:5`, show 2–4 takes, and let the author pick or redirect — **casting a face is the author's call.** Copy the pick to `cast/<name>/source.png`, then run intake.

## Choosing which references stay active

More images is not better. References compete, and conflicting ones average into a weaker likeness: a photo from a different decade, a different haircut, a three-quarter squint against a straight-on smile, a childhood picture beside an adult one. Keep the active set deliberately narrow — the shots that agree about this person.

- **One person per source image.** Crop a group photo down to the one character before copying it in. Two characters seeded from the same two-person selfie both render as the more prominent person in it, and nothing catches it: each mug set is internally consistent, which is all the tooling checks. It surfaces weeks later as "why does she look like her friend?"
- **`source.jpeg` dominates — pick the plainest one.** The first source outweighs the rest, and the front shot leans on it hardest. A reference in a strong-coloured jacket against a strong-coloured wall returns a mug shot wearing that jacket on that ground, whatever `mugshot_direction` asks for. Lead with the photo that has the plainest clothing and the plainest background; order the rest behind it.
- **Park, don't delete.** Move a reference out of `cast/<name>/source*` into `cast/<name>/_excluded/` and note in `cast/<name>.md` which one and **why** ("2019 beard, reads as a different man"). A deleted photo comes back as an argument six weeks later.
- **Aging a reference: ask for a photograph, don't write harder.** Apparent age follows the photographs, not the description — in both directions. A character written as 35 whose every photo is of a 50-year-old comes back 50; one written as 50 from a sunny 35-year-old photo comes back 35. Two rounds of correction, first in `mugshot_direction` and then in the character description, both failed on the same character; three photographs at the intended age fixed it on the first build. So say the target age out loud and check the result at it — but when the result is wrong, **the next move is asking the author for a photo at that age**, not another sentence. When no such photo exists, say so plainly and let the author choose: accept the age the photos give, or accept re-rolling for luck.
- **Check mug shots for inherited wardrobe and ground, not only for the face.** A mug set is meant to be neutral so panels can dress and light a character freely.

## Hard visual traits

A few traits carry identity more than the rest: eye colour, a scar, a birthmark, the shape of an ear, a hairline. Name them explicitly in `briefs.json` and in the cast file's **Hard traits** line, and treat them as canon.

When one changes or turns out wrong, **fix the whole approved set**, not one shot. A set with three brown-eyed shots and one green-eyed one poisons every later panel, because panels bind two or three shots at a time and the odd one out wins about a third of the time. The cheap route is `touch_up.py` on each finished shot (one detail per call), not regenerating a set the author already approved — regeneration rerolls the whole face and loses things nobody asked to change.

## Getting descriptions right

- **Ground them in what the photo shows.** Read the source image and describe it; don't guess from the name.
- **Thin descriptions cause drift.** "a young woman" gives the model nothing to hold. Name hair, eyes, skin, build, age, and one distinctive feature.
- **Describe a trait by what it is, never by what it is not.** The prompt rule that negations underperform applies to `briefs.json` descriptions exactly as it does to `medium.txt`, and it is not obvious there. A character written *"muted hazel-green eyes — soft, greenish-brown, never a vivid or emerald green"* rendered vivid emerald in every scene for a whole session: the sentence says *green* three times, and that is what the model drew. Rewriting it without the negation and without the colour name — *"warm hazel eyes, the colour of olive oil — brown flecked through with a little moss, darker at the rim"* — fixed it on the first try. Reach for a substance rather than a colour word when a colour keeps going wrong.
- **Direct the smile** with `mugshot_direction.<name>` when the default warm smile is wrong for the character ("a slow knowing half-smile, not a grin").
- **`mugshot_direction` never reaches a panel prompt.** It steers `build_mugshots.py` only. Anything a panel must honour — an age correction, a colour, a feature — belongs in the character description. And an *expression* instruction there fights the shot names: writing "give her the wide open smile" makes the `front` shot fight its own convention. Describe the face; let the shot name drive the expression ("wherever the shot calls for a smile, it is a wide open one that…").

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
- The author's own photos stay theirs: keep originals where they landed, and never present a generated portrait as the source image. A cast presentation shows the real reference next to the generated canon, each labelled for what it is.
- A hard trait fixed in one shot is fixed in all of them, or not at all.
