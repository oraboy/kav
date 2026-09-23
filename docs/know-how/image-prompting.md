# Image prompting — the operating manual

How Kav builds image-generation calls: reference ordering, style packs, prompt wording, model choice, and the failure modes measured in real production (several hundred generations across a bake-off and a finished book). Where a claim comes from vendor docs rather than our own runs, it says so.

## Story scope

Every reference in a call — cast, location, object, style — belongs to the story being drawn. Resolve the roster from `stories/<slug>/cast/*.md` and places from that story's `locations/`. If a scene needs something the story doesn't have, say so and offer to create it.

## The call shape

One call carries every reference, in this order:

1. **Cast** — mug shots per character (styled set when it exists)
2. **Location** — the real photograph(s) or approved earlier panels
3. **Objects** — the photograph of a thing that must be identical every time
4. **Style pack** — the images in the linked `styles/<pack>/`

The prompt names each by index *and* role: *"Image 1 shows <name>: …"*, *"Image 3 shows the real location the scene takes place in"*, *"Images 4 to 6 are the rendering target."* Indices disambiguate for the model; roles make the log readable.

**Everything is an image.** No written styles, no described-only locations: photographs are what make a place recognisable, and word-defined styles drift.

## Prompt rules that measurably changed output

- **Name the medium in prose.** The pack's `medium.txt` line goes into every prompt. The single most effective lever found: it turned failed style transfers into correct ones and made seeds agree stylistically. Its wording rules are in `/kav-style`.
- **Frame positively; assign every slot.** Negative commands underperform (Google documents this for Gemini; our runs agree). Instead of "take nothing of their subject matter", write "the final image shows only the scene described above; its subject, composition and setting come entirely from images 1 to 2."
- **Say "including the background."** Style drift shows up in backgrounds first.
- **Set the aspect ratio explicitly** (`--ar`). On Nano Banana the model otherwise takes it from the *last* image — the style pack's shape would decide the framing.
- **Give the subject a position.** A character lost in a crowd comes back with "in the foreground centre, close to the camera, face clear" plus their identity words repeated.
- **Name the expression, always.** A line that carries the action and not the face returns the model's default: a mild, pleasant, camera-aware smile, on a character dangling off a railing in a storm. Nothing in the reference stack corrects it, because mug shots are neutral by design. Write the face as an instruction — "jaw set, eyes narrowed against the rain, not looking at the camera" — and write it even when it seems obvious from the beat. It is never obvious to the model. A panel spec without an expression is an incomplete spec.
- **Carry the scene state into every panel of the scene.** Time of day, weather, light source, wet or dry, hurt or whole, and what each character is wearing. Panels are generated independently; anything the line doesn't say gets re-invented per panel, so a midnight storm turns into a blue afternoon three panels later and a jacket becomes a summer top. See below.
- **Keep real place names out of the line** once the photo binds — the name becomes invented signage.
- **Wide panels:** put the subject in the centre third; the phone crop keeps only the middle.
- **Never put story dialogue in the line.** Lettering is post-process.

## Choosing a model

| Need | Use | Why |
|---|---|---|
| Non-Latin text in frame (e.g. Hebrew signage) | **Nano Banana Pro** | The only model tested that spells it correctly; others render convincing nonsense — worse than no text |
| A real place must be recognisable | **Nano Banana Pro** | Rebuilds a location and re-stages the camera within it |
| A precise emotional beat or body language | **Nano Banana Pro** | Best at turning a written moment into that moment |
| Style-heavy work, volume, exploration | **Seedream 4.5** | Transfers a pack's visual language more faithfully, looks better, costs ~$0.04 vs $0.15 |

Nano Banana at "2K" costs the same as "1K" — never run below it.

## Style packs

- **2–5 images, three is the default** (matches documented vendor caps and practitioner experience; convention, not proof).
- **No faces in the pack** — they compete with the cast for identity.
- **Internally coherent** — same artist, same day. Disagreeing images average into mush.
- **No text in references** — it bleeds into output.
- **Test on bright daylight exteriors.** Both models hold stylised looks in dim interiors and drift toward ordinary colour illustration outdoors, where the location photo's light fights the pack.

## Objects — putting a specific thing in frame

The wording decides whether it works, by a wide margin. "An object to place in the scene, reproduce its lettering" transferred only the object's *shape* and invented the text. This transferred the text correctly on the same model and seed:

> Image N is a photograph of a real physical object. Place this exact object into the scene unchanged, as though it were photographed there. Any lettering on it is copied verbatim, glyph for glyph, in the same script and spelling — it is never re-typeset, translated, or replaced with different words.

- This is how the cheap lane gets correct non-Latin text: it can't spell from a prompt, but it carries text off an object photo. Treat signage as pick-from-two, not one-shot.
- **Photograph objects alone.** A dress photographed on a model gave the character wearing it the model's haircut; the flat-lay dress came through exactly.
- **Making a sign:** render it with PIL and a font that covers the script. PIL applies bidi itself — pass the logical string, don't pre-reverse it. Verify by checking the first glyph sits on the correct edge.

## Every reference tends to become a thing in the frame

The most useful mental model: a reference exerts pressure to appear *as an object in the picture*.
- Two mug shots of one character can produce two of that character in one frame. **One mug shot per character in multi-character scenes.**
- An object reference can produce a second copy of the object. Word objects as belonging to the scene ("the car they are riding in").
- A style line that names a noun (clouds, foliage) paints that noun into every frame.

## Continuity by reference

When a place drifts across panels, bind an **approved earlier panel** of it as an extra location reference (copy it into `locations/<name>/`, add it to `photos` in `briefs.json`). The next generation binds the drawn place, not only the photo. Adjectives in the prompt don't fix drift; references do.

## Scene state — what drifts when nobody names it

References hold identity. They hold nothing about the moment. Every panel is an independent call, so whatever the line leaves out, the model invents fresh — and it invents toward the pleasant and the well-lit.

Five things drift, in rough order of how badly they break a reader:

| Drifts | Looks like | Carry it in the line |
|---|---|---|
| **Expression** | the same mild smile through terror, exhaustion and fury | the face, as an instruction, in every panel |
| **Time and weather** | a midnight storm rendered as a blue afternoon at the climax | the hour, the sky, the sea state, the light source, every panel |
| **Wardrobe** | a zipped jacket becomes a summer top mid-scene | the character's clothes for *this chapter*, from their cast file |
| **Condition** | soaked and bleeding in one panel, dry and neat in the next | wet, torn, bruised, carrying-something |
| **Identity of the second and third character** | the mother and the sister become interchangeable | one distinguishing feature per supporting character, named every time |

A **scene-state line** written once at the top of a scene and pasted into every panel of it costs nothing and fixes most of this. Put it in `panels/plan.md` at the scene header so the author can see it and change it.

Two notes on where this bites hardest. Supporting characters drift far more than the protagonist, because the protagonist usually has one loud visual anchor (a signature jacket, a braid) doing the identity work — which means the moment that anchor is out of frame, they drift too; give every principal a feature that survives a costume change. And the climax is the most likely scene in a book to be rendered in daylight, because it tends to be planned last, at the end of a long batch, when scene state has quietly stopped being repeated.

## Debugging a wrong image

1. Read the candidate's `.json` sidecar: which cast, location, objects and style actually bound?
2. Location triggers are first-match. A generic word ("apartment", "room", "street") in one location's triggers steals scenes meant for another. Put specific places first; drop generic words.
3. Only then rewrite the line — for a named reason.

## Known failure modes

- **Invented lettering in frame.** Any surface that could carry text — a control panel, a sign, a schematic, a map, a notebook — comes back with confident nonsense ("FINKTESSTATICK CHECK"). It reads as a typo to the author and as a broken world to a reader. Either keep text surfaces out of the framing, or promote the thing to an object and bind its photograph (see above).
- **Hallucinated artist signatures.** A scrawl in a bottom corner that looks like a signature, because the style pack's references have them. It is a made-up human name signed on the author's page. Check every corner of every picked candidate; crop or reroll.
- **Three-plus characters** get less reliable as the count rises.
- **Seed-to-seed style drift** — first suspect an ambiguous `medium.txt`.
- **Interiors losing their ceiling** — the location photo doesn't show it; get a photo that does.
- **fal 403** — balance locked, not rate limiting. Top up; known cases stay locked briefly after top-up.
- **fal CDN files expire in 7 days and are public URLs** — the tools download immediately.

## Things that are not real

- **Seedream "reference weights"** (Character 1.0, Style 0.9…) described in popular guides don't exist in any API surface.
- **Locked seeds as a consistency mechanism** — seeds are a variation knob, not identity control.

## Cost shape

Explore on Seedream (~$0.04/image), publish on Nano Banana Pro (~$0.15 at 2K) when a panel needs it. Many books run Seedream end to end. A chapter of ~25 panels at 3 takes each plus rerolls is roughly 100 images: ~$4 on Seedream. Mug shots are ~$0.60 per character on Nano Banana. Prices as of 2026; check fal.ai and Google AI Studio for current rates.
