# Image models: what each is like to work with in Kav

What we know about each image model **as it behaves inside Kav**: with a character's reference shots, a location and a style pack bound to every panel. This is not a general ranking. A model that makes the most beautiful single picture can still lose a book, because a book needs the same face on page 1 and page 40.

Every line says where it comes from. "Bake-off" means the same ten picked panels of a finished book were redrawn on that model and judged by eye. "One book" means a single author's session. "Untested" means the client works and nothing it made has been judged.

Prices and reference caps change: `python3 tools/check_setup.py` prints the current ones from `tools/lanes/models.json`. When this page and the registry disagree, the registry wins and this page needs an edit.

## How to use this with an author

Ask what they already have an account with, then show the options that fit, with the trade-offs in plain words. **A tool they already use and like is the natural choice**; say what it costs them in Kav and respect the decision. If they name something that isn't here, say it is new to us, try it through the author's-own-tool route (`own-image-tool.md`) on two or three panels, and judge it together. Then add what you learned to this page.

## Works through Kav's own lanes

| Model, and where | Good at | Costs you | Evidence |
|---|---|---|---|
| **Seedream 4.5 on fal.ai** · about $0.04 | Holding faces and a style pack together across scenes. Takes up to 10 reference images, the biggest stack of any lane. Kav's default | Past 10 references it silently drops some, so a very crowded panel loses a character. A fourth named face still drifts first | Bake-off: matched the book |
| **Seedream 4.5 on Magnific** · about $0.05 | Same model, similar quality, its own slightly different look. A good choice for someone who already pays for Magnific | **5 reference images at most.** In practice a panel holds three named subjects (characters and bound objects) before the style stops binding, so scenes are planned around that. No 4:5 output: page cells come back 3:4 and need cropping | Bake-off: passed |
| **Nano Banana Pro on fal.ai or Google's own key** · about $0.15 | Overall image quality and a strong look of its own. Reliable for text inside the frame, real places, and a single character's reference shots | About four times Seedream's price. Faces hold less well from scene to scene. It tends to paint in its own style over the style pack: in our rotoscope test it ignored the pack. Refuses the wide panel shapes (8:5, 12:5), which come back 16:9 and 21:9 | Bake-off (one style) |
| **Popcorn on Higgsfield** · about $0.05 | Takes 8 references, the closest in shape to how Kav works | Unknown. API credits are bought separately from the app plan | Untested |
| **Soul on Higgsfield** · about $0.05 | Higgsfield's own look | One style reference only, so it cannot hold a character's face across panels | Untested |

## Works through the author's own tool

No key and nothing to set up. Kav cannot bind its reference stack or see the cost; the agent passes the references and files the results as takes (`own-image-tool.md`).

| Tool | Good at | Costs you | Evidence |
|---|---|---|---|
| **ChatGPT / Codex built-in image generation** | Attractive painterly pages straight away, and it follows a rough layout sketch well. The author called the first full set "beautiful" | Precise anatomy on unusual subjects (an ant's six legs) failed repeatedly, and a local fix tends to redraw its neighbours. Much easier to live with one panel per image and three takes to choose from. Cost is not visible to Kav | One book |
| **Midjourney** | The most artistic, stylised output of anything here | **Kav cannot drive it: it has no API.** Images an author makes there by hand can still be brought in as takes with `tools/add_candidate.py`, but every panel is a manual round trip, and keeping a character consistent is on the author | Not used in Kav |
| **Anything else** (Krea, Leonardo, Ideogram, a local model…) | Unknown to us | Unknown to us. Try two or three panels and judge | Untested |

## What decides it for most books

- **A cast of recurring faces:** Seedream, on fal.ai if there is no account yet. Reference capacity matters more than polish.
- **Three or fewer subjects per panel and a Magnific account:** Magnific is fine. Plan the fourth character into the next panel.
- **A look that matters more than the same face twice** (a poem, a mood piece, single images): Nano Banana Pro, or the author's own tool.
- **No key, wants to start now:** the AI tool's own generator. Say that consistency is on that tool, and move on.

## Adding to this page

When a model is tried on a real story, add or correct its row: what it was good at, what it cost, and the evidence in two or three words. One author's experience is worth writing down as "one book". Don't promote it to a recommendation until it has been through a bake-off.
