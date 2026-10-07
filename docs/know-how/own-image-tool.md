# Drawing with the author's own image tool

Kav ships with image lanes it has tested (fal.ai, Magnific, Higgsfield, Gemini: `tools/lanes/models.json`). They are a head start, not a fence. An author who would rather draw with the image generator built into their AI tool (ChatGPT / Codex image generation, a Gemini or MCP image tool), or with any other tool they already pay for, can. **Say yes, and bring what it makes into Kav's pipeline.**

What Kav adds does not depend on who drew the pixels: one panel at a time, several takes to choose from, the author's pick recorded, lettering as a separate step, pages and readers assembled from the picks. An image made elsewhere gets all of that once it is saved as a take.

## Say this at the start

The moment the author chooses their own tool, tell them the deal in two or three lines, then get on with it:

> Sure, we'll draw with <tool>. I'll make **one panel per image** and a few takes of each, so you can pick the best or ask for another go. Then Kav letters the panels and assembles the pages, so text and layout never depend on the image tool.

Say once what is different from Kav's own lanes, without talking them out of it: Kav cannot see what the other tool charges, so the cost report won't include it; and a character stays consistent only as well as that tool holds a reference image.

## The rules that keep it in the pipeline

1. **One image is one panel. Never a whole page.** No panel borders, gutters or several scenes in one image. A page drawn as a single image cannot be lettered panel by panel, cannot be re-rolled one panel at a time, and has no phone version. When a fix is needed, a single panel is redrawn and the rest of the page is untouched.
2. **No text in the image.** No captions, balloons, sound effects or signatures. Lettering is post-process (`tools/letter.py`), in every lane.
3. **The panel's shape comes from the plan**, not from the tool's default: 4:5 for one cell, 8:5 for two, 12:5 for three, or the story's own page format. Ask the tool for that shape.
4. **Two to four takes per panel**, same as any lane. One take is a result to accept; three are a choice.
5. **Hand the tool the references, every time.** If it accepts images, attach the character's reference shots, the location plate and one or two style images with each panel request. `python3 tools/generate.py --story <slug> "<scene line>" --dry-run` prints the prompt Kav would send and the reference files it would bind: use them. If the tool takes no images, put the cast file's physical description and the style's medium line in the prompt.
6. **Save every take through `tools/add_candidate.py`**, never straight into a page:

   ```
   python3 tools/add_candidate.py chapters/chNN/panels/batch-<name>.json <panel-id> take1.png take2.png take3.png --source "codex image generation"
   ```

   It files each image as the panel's next take, records it in the story's ledger (with no price) and rebuilds the contact sheet. From there the chapter runs as written: review on the author's surface (`/kav-review`), picks recorded, lettering, pages, readers.

The batch JSON, the scene list and `plan.md` are written exactly as for any lane. Only the step that calls `tools/panel_batch.py` is replaced by the tool's own generation plus `add_candidate.py`.

## Checking the takes

The checks in `/kav-panel` and `/kav-chapter` still apply before anything is shown: each face against its reference shots, no generated lettering, the scene's time and weather. A tool Kav has not tested fails in its own ways, so look harder, not less.

**Never report a visual fix as done on your own say-so.** Counting legs, fingers or people in a generated image is exactly where an agent's eye is unreliable. Say what you asked the tool to change, show the result, and let the author confirm. "I asked for the extra leg to be removed; please check panel 2" is honest. "Corrected" is a claim only the author can make.

## When the author asks about switching models

Don't answer with one provider. Ask which image tools or accounts they already have, then list every route: the agent's own generator (nothing to set up), and each provider in `python3 tools/check_setup.py`, with its price and what it is good at. A model reached through two providers (Nano Banana Pro is on fal.ai and on Google's own key) gets both mentioned. The author chooses; `/kav-start` has the full table.
