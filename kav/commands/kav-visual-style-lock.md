---
name: kav-visual-style-lock
description: Lock the book's visual identity once cast references, location references and a style pack exist — a staged sample-and-approve flow (summary sheet → cheap samples with lettering → draft styled mugs → production styled mugs → sample gallery → shareable style sheet) producing the styled reference sets every panel binds. Use when the author types /kav-visual-style-lock <pack>, says "lock the style", "bake the style", "styled mug shots", or when kickoff's STYLE block locks and production mugs don't exist yet. Every stage gates on the author.
argument-hint: "<pack> [--story <slug>]"
---

# /kav-visual-style-lock <pack> — bake and lock the look

Runs **after** kickoff has collected cast references, location references and a chosen style pack with a lettering theme. Output: production styled mug sets in `stories/<slug>/cast/<name>/<pack>/` — the references every panel binds automatically — plus an approved sample gallery proving the look works *with text on it*.

**Cheap lane first, expensive lane only after approval.** The author gates every stage and may iterate the style at any gate (swap reference images, reword `medium.txt`, retune the lettering theme). Iterating restarts from step 2, which is the point of doing it cheap.

## Inputs (all story-local)

Before step 1, `stories/<slug>/` must hold:
- `briefs.json` with `characters` (one description line each), `locations` (photos + description), `location_words`
- `cast/<name>/source*` per character
- `locations/<name>/` photos
- `styles/<pack>/` (linked) with `medium.txt`

The roster is `stories/<slug>/cast/*.md` — use that explicit list for every step. Background characters get mug sets only if the author wants them drawn consistently; ask. If something is missing, that's a kickoff block to finish, not a lookup elsewhere.

**Worksheets are the paper trail.** Every board or contact sheet you show is also saved as `stories/<slug>/style/worksheets/step<N>-<name>_iter<M>.png` the moment it's shown. Every board carries a **`Visual Style: <pack>`** marker in its header. Boards are self-contained: images embedded (or rendered to a PNG), never `file://` links that break when the file moves.

**How boards reach the author:** their `KAV_REVIEW` surface (`docs/know-how/review-surfaces.md`) — inline in the conversation, a published page, or the local server. A localhost page is never the only route to a gate.

**Three rules for every gate here:**
- **Show it, don't describe it.** A lettering theme, a palette, a border treatment, a page device, a style: render a sample and put it in front of the author. Anything described in prose and not shown is provisional, never approved.
- **Label every option inside the image** — a large `A` / `B` / `C` burned onto each candidate, repeated in the text. The author answers "B" from a phone. In elimination rounds the survivors keep their letters; never renumber.
- **Comparisons carry cast faces.** A board of locations proves nothing about a book with people in it. Early rounds show the protagonist plus one contrasting cast member; finalist rounds show every principal you can fit. (The pack's own images may show faces — a pack with no close-up face never teaches the model how to render one — but they must not resemble the cast, or they compete with identity.)

## Step 1 — Summary sheet (GATE)

One sheet showing everything collected: every character's reference (front shot or source) + name · every location's primary photo + name · the pack's images, the `medium.txt` line verbatim, and the lettering theme rendered (a sample caption and balloon). The author confirms the input set is complete.

## Step 1b — Quick scan (GATE · the reliability test)

**Before any styled mugs are baked, find out whether this cast, these locations and this pack can actually be rendered together.** A book's look is not locked by agreeing it is pretty; it is locked by proving it comes out the same twice. This stage exists so that failures surface here, cheaply, against the *sources* — not in chapter three against a deadline.

**1 · Generate a 9-image scan.** Nine different combinations — no duplicates — spread across the cast and the locations, on the pack: a couple of single-character shots, several two-handers, at least one crowded panel, each location at least once, a mix of interior and exterior and of close and wide. About $0.36.

**Location plates come with it.** The scan draws a plate for every location shot it touches — the place redrawn once in the pack's style, which is what panels bind from then on (`docs/know-how/image-prompting.md`). **Show the plates beside the scan** and treat them as their own small gate: a plate built from the wrong photograph is wrong in every panel that takes that view, so this is the moment the author picks the view. A place whose identifying feature is missing from its plate — the sign, the mural, the frontage — needs a second shot declared, not a reworded prompt.

**2 · Review it yourself first, and say what you flagged.** Compare every face to its mug shot, every place to its reference photos, every panel to the pack. Flag identity drift, location drift, style drift, invented people, invented signage. **Never present a scan you have not judged** — that is the author's second opinion, not their first.

**3 · Show the grid with your flags on it**, each image numbered, and for each one **the exact prompt and the reference list that produced it, available to read**. The author can overrule any flag, add flags you missed, and say why. A flag you cannot explain in one line is not a flag.

**4 · Then, depending on what the scan shows:**

- **Clean** — say so and move on. Do not invent problems to look diligent.
- **Isolated misses** (a character wrong in one image of nine) — that is variance. Note it, move on.
- **Something failing consistently** — roughly one or two bad in every three attempts at the same character, place or combination — **is not a prompt problem and must not be treated as one.** Work the loop yourself first: better reference crops, a reworded description, an added reference image, the chaining method. Ask for more source photographs when they would settle it. Then re-scan.
  - **For a character, the first move is to rebuild their mug set with the reading pushed the other way** — if they keep rendering as a girl, write the mug-shot direction unmistakably male and overshoot; the direction never reaches a panel prompt, so overshooting costs nothing in the book. Retest on the panel that was failing, at three seeds. Then bring it to the author: a rebuilt set changes how a real person looks on every page they appear on, and they may know a better lever. Worked example in `docs/know-how/image-prompting.md`.
- **Impasse** — when the loop stops improving, **stop.** Do not keep spending.

**5 · At an impasse, escalate to a book-level decision and walk the author through it.** Say it plainly: *the image generator, with this story's current material, cannot render X reliably.* Then give concrete options, each with its cost:

| The failure | The book-level options |
|---|---|
| A character keeps coming out wrong | new source photographs · a different/stronger signature feature · demote them to background · write them out |
| A location keeps breaking | new photographs covering the surfaces panels need · restrict it to the shots that do work · replace it with another place · cut it |
| The style keeps drifting | swap the pack · change the register · simplify the palette |
| A combination fails (these two together, this place at night) | stage it differently · split across panels · avoid the combination in the storyboard |

This is a **story** decision, not a technical one, so it belongs to the author — including the option to accept the flaw and carry on. Log whichever they choose in `kickoff-state.md`, and mark the storyboard stale if a place or a character left the book.

**6 · Re-scan with another nine** after any change, to prove the fix rather than assume it. **7 · The author approves the scan, and only then does anything expensive get baked.**

**Write the outcome into `style/style.md`** — what was scanned, what failed, what was changed, and the **capability envelope** the book now operates under: how many faces a panel can hold, which combinations need staging, and what this book has decided it will not attempt. `/kav-chapter` and `/kav-panel` read that envelope and refuse to spend past it.

## Step 2 — Cheap samples with text (GATE · iterate here)

On Seedream (~$0.04/image):
1. **One styled front portrait per character** — draft into `cast/<name>/<pack>/draft/`:
   `python3 tools/build_mugshots.py --story <slug> --char <name> --style-pack <pack> --lane seedream --shots front` *(flags per `--help`)*
2. **Three simple scenes** — one character in one of the story's locations each:
   `python3 tools/generate.py --story <slug> "<character> in <location words>, <pack>" --lane seedream --ar 4:5`
   Letter each with `python3 tools/letter.py <spec.json> <out.png>` using the story's lettering theme: a caption naming the lane (`sample · Seedream`), and a speech balloon **in the story language**: *"Hi, I'm <NAME>. Nice to meet you"* (no final period).
3. Show portraits **and** lettered scenes together. The author judges drawing style and lettering style as one unit. Iterate until it's a yes. **Inconsistency across samples almost always means `medium.txt` is ambiguous** — fix the language per `/kav-style`, not the seeds.

## Step 3 — Full draft mugs (GATE)

Full sets (front, three-quarter, smile, full-body) on Seedream into `cast/<name>/<pack>/draft/` for each character in the roster. Contact sheet → show it **together with the latest lettered sample scenes** (a mug set is judged against how the character reads in a scene) → approve. (~$0.16 per character.)

## Step 4 — Production mugs (GATE)

Production sets on Nano Banana Pro into `cast/<name>/<pack>/`:
`python3 tools/build_mugshots.py --story <slug> --char <name> --style-pack <pack>` *(flags per `--help`)*
Contact sheet + sample scenes → approve. Rebuild bad shots individually — a full-body with a cropped head is a broken reference. Fix a single detail with `python3 tools/touch_up.py --story <slug> --char <name> --shot <shot> --instruction "<one detail>"`. (~$0.60 per character.)

**If the author picks Seedream as the single production lane** (the simple default), skip step 4 and **promote** the step-3 drafts: copy `cast/<name>/<pack>/draft/*.png` → `cast/<name>/<pack>/`. Record the promotion in `style/style.md`. Generation must never bind a `draft/` folder directly.

## Step 5 — Concept scenes, both lanes

Five varied scenes (different characters, locations, times of day, group sizes), each on **both** lanes, production mugs now binding automatically. **Letter them** — a caption and a balloon per scene, in the story language, through `tools/letter.py`. This is the author's first real look at the book: art, type and language together, not a gallery of untexted pictures. Show them **side by side per scene**, one lane against the other, labelled `A` / `B` — the author decides the lane by comparison, not assertion.

These are concept art for the brief and the trailer. They never become page art: a page image is only one the author picked in a chapter review.

## Step 6 — Save the samples

Approved samples are story artifacts: `stories/<slug>/style/samples/<scene-slug>_<lane>_iter<N>.png`, each with its lettering spec beside it. This folder is the look's living portfolio — later sessions (and `/kav-trailer`) read it.

## Step 7 — Confirm and close

Verify every roster character has four production shots in `cast/<name>/<pack>/`.

**Bind the pack for real.** Write `defaults.style_pack: "<pack>"` into `stories/<slug>/briefs.json`. Without it, every later scene line that doesn't happen to name the pack generates unstyled — a locked `style.md` and a linked `styles/<pack>/` bind nothing on their own. Confirm with `python3 tools/generate.py --story <slug> "<a line that does not name the pack>" --dry-run`: the output must name the pack and list style references.

**Say how many faces a panel can now hold, and write the number into `style/style.md`.** The lane's image cap fixes it for the whole book — *faces ≤ cap − location slots − style slots − object slots* — so an uncapped lane gives about four (quality-limited, and needing 3–4 takes at that end), an 8-cap gives three, a 5-cap gives two. Say it as a constraint on the **story**, not on the drawing: scenes with more people than that must be staged across panels, and the storyboard has to know before it writes them. Working through it, and what a cap does to the style pack: `docs/know-how/image-prompting.md`.

**Lock the lane as a production decision.** Record in `style/style.md`: the lane and provider, **the faces-per-panel number it implies**, the evidence (which samples, which comparison board), and the date. **Switching lanes later re-renders the whole book** — two models never agree on a face — so this is a book-level decision, never a per-panel one. A model that wins on one image can still lose a book — identity drift across scenes is what matters, and that only shows in a multi-scene comparison. Once locked, the lane is not switched panel by panel; reopening it is a gate of this command, not a passing choice. Keep the bake-off boards in `style/worksheets/`, and keep the losing model's images out of the story brief: the brief carries the chosen look as concept art, not an argument about models.

Append to `style/style.md`'s lock log: date, lanes tested, samples path. Update `kickoff-state.md` (visual lock: locked).

## Step 8 — The style sheet

Build one self-contained HTML page (`stories/<slug>/style/style-sheet.html`, images embedded as downscaled JPEG data URIs, well under 16 MB), designed in the pack's own palette and lettering fonts, with a `Visual Style: <pack>` badge:
1. **Cast** — per character: the reference first, then the production shots; each image chipped **reference** or **generated · <lane>**.
2. **Locations** — the reference library.
3. **Style** — the pack images, the `medium.txt` line (labelled as the line injected into every prompt), the lettering theme rendered live.
4. **Samples** — lettered look-tests and the dual-lane pairs, lane-labelled.

Open it for the author. Share or host it only if the author asks.

## Hard rules

- Cheap lane before expensive lane, always; nothing generates on the expensive lane before the cheap gate passes.
- **Always show the scene samples at every stage that has any — never only the mug shots.**
- Sample text goes through the lettering tool, never generation-time text.
- Story-local in and out.
- The author approves every gate; a style iteration reruns from step 2.
- A 403 from fal usually means the balance is locked — the author tops up; re-run to fill gaps, never skip.
