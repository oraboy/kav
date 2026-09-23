# The Kav process

Six steps from a one-line idea to a published graphic novel. The steps are ordered but the work is not linear: you can jump back to add a character in chapter 4, and the state files track what that makes stale. Every step writes a file immediately, so a session can end anywhere.

**Who carries the weight shifts as you go.** Early on, the author feeds in the story and the agent structures and presses it. By chapter production the agent generates, letters and assembles, and the author directs and selects. The author picks every image and has the last word on every line of text.

---

## 1 · Kickoff — slug and one-line pitch

**Command:** `/kav-kickoff <slug>`

The agent explains the meeting, proposes a flight plan (the block order), and asks for four things: the name and slug, the story (a one-liner plus whatever outline exists), the format (chapter count, pages, panel format, story language, telling register), and the world and era with its clock.

**Gate:** the author agrees the flight plan and answers the frame questions.
**Produces:** `stories/<slug>/` scaffold · `kickoff-state.md` · the Concept section of `story.md` · empty `briefs.json`

## 2 · Collect — characters, locations, key events

**Commands:** `/kav-kickoff` (CAST, LOCATIONS, OBJECTS blocks) · `/kav-character <name>` · `/kav-plot-note`

One character at a time: a one-liner and a look (the author's photos, a generated face the author picks, or a written description until images come), then the author picks the depth: a quick sketch (2–3 questions, the rest drafted and marked), the full DNA interview, or background (see `docs/craft/cast-dna.md`). Images and mug shots must be in place before the visual lock. Then the locations, each with photos that show every surface panels will need. Objects that must never change get registered like locations.

This step is **collection, not story**. Ideas that come up get parked in `pitch-inbox.md` with `/kav-plot-note` and raised at the pitch.

**Gates:** each character confirmed before the next · the location set confirmed
**Produces:** `cast/<name>.md` + `cast/<name>/` mug shots · `locations/<name>.md` + photos · `objects/` · `briefs.json` entries · `pitch-inbox.md`

## 3 · Visual style — pick, test, lock

**Commands:** `/kav-style <pack>` · `/kav-visual-style-lock <pack>`

Register or choose a style pack (reference images + one `medium.txt` line) and a lettering theme. Then lock it: a summary sheet of everything collected, cheap lettered samples (iterate here until it's a yes), draft styled mug shots, production mug shots, samples on both image lanes, a saved gallery and a style sheet.

**Gates:** style choice · each lock stage (summary, samples, draft mugs, production mugs)
**Produces:** `styles/<pack>/` · `style/style.md` · `cast/<name>/<pack>/` styled mugs · `style/samples/` · `style/worksheets/` · `style/style-sheet.html`

## 4 · Storyboard & brief — shape, intention/obstacle, chapters

**Command:** `/kav-kickoff` (PITCH, STORYBOARD, PACKAGE blocks) · `/kav-trailer`

**Story shape and I/O first.** The agent proposes 1–3 readings: the main character's fortune curve (man in a hole, Cinderella…) and a pressed intention/obstacle line for each character who carries weight. The author locks one. Then the full pitch: O/I grid, topology and braid for ensembles, key events, core drama, feel line. The inbox is raised and each note adopted, kept or dropped.

**Then the storyboard:** the whole arc chapter by chapter with a writer's note each (gate), then a card per chapter — chapter question, chapter I/O, synopsis, beats, gun ledger, a concept image. The arc also seeds `reader-ledger.md`: every name, pre-story event and world rule the book leans on, as an OPEN row, with the chapter meant to pay it.

**Then the package:** a one-page brief in reader-facing language. Optionally the trailer deck.

**Gates:** the reading · the full pitch · the arc · each chapter card · the package
**Produces:** `story.md` (the contract) · `reader-ledger.md` · `storyboard/chNN.md` + concept images · `package/brief.md` · `package/trailer.json` + `trailer.html`

## 5 · Chapter by chapter — outline, scenes, cold read, images, lettering, cold read, pages

**Commands:** `/kav-chapter <NN>` · `/kav-coldread [NN]` · `/kav-review <batch.json>` · `/kav-panel`

1. **Outline in content.** "In the last chapter X; in this one Y happens; the suggested plot is 1…n" — concrete scenes. The author redirects. *(gate)*
2. **Scene list.** One scene = one strip, with panels, shapes, scene state, the expression each panel needs, and proposed text. The author cuts and rewrites. *(gate)* → `panels/plan.md`
3. **Cold read, before a cent is spent.** A context-starved reader gets the scenes and their text and nothing else, and says what it could reconstruct and what confused it. The ledger absorbs the unpaid facts; the author decides which gaps are deliberate. The cheapest gate in the process. → `cold-reads/<date>-scenes.md`
4. **Images.** Batches of 2–4 takes per panel → a local review page showing the whole chapter in reading order, full image and phone crop side by side → the author picks, rerolls with a reason, edits text → "picks in": the agent applies the saved review. Repeat until every panel is picked. *(gate per round)* → `panels/candidates/`, `panels/reviews/`, `panels/manifest.md`
5. **Lettering.** Specs written by looking at each picked image; rendered; every render checked by eye for faces, collisions and the phone-safe zone. → `panels/lettering/*.json`, `panels/pNN-panelK.png`
6. **Cold read the finished chapter**, on the rendered panels, before the author reads it. The gate opens with the diff between what a reader got and what the card intended. Chapter 1 gets a second read alone once it locks. → `cold-reads/<date>-pages.md`
7. **Pages and readers.** Layout in reading order (RTL for RTL languages) → assembled pages + Instagram carousel images → the Story reader (panel per screen) and Comic reader (full pages), linked to the next chapter in the same mode and back home. *(gate: the author reads it end to end)* → `pages/`

On lock: state files updated, locations' history and cast story state appended, unpaid guns logged, ledger rows closed.

## 6 · Final draft & publish

**Commands:** `/kav-publish` · `/kav-trailer`

Readers rebuilt for every finished chapter and linked in order; the trailer's chapter slides point at them. The folder is plain HTML and images for any static host (Netlify, GitHub Pages); carousel JPEGs and slide PNGs go to Instagram as-is; page PNGs are print-shaped for a future PDF. Nothing is published without the author's explicit yes.

---

## Standing rules

- Interactive always. Gates at every creative decision; nothing generated past one.
- **Each stage diagnoses its own output before the author sees it.** The agent can see the brief; the reader can't, so the check has to come from something context-starved. Diagnosis and repair are never the same call.
- **Errors escalate upstream.** No lettering pass saves a weak outline, and a nicer scene never fixes a missing beat.
- Every step persists to a file immediately.
- Staleness is tracked and logged, never silently absorbed.
- The author picks every image. The agent prepares, generates candidates and may suggest.
- Story-local: every reference and output lives under `stories/<slug>/` (style packs may be shared).
- Co-authors at different altitudes.
