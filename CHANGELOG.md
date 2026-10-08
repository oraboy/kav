# Changelog

Kav's version is in `VERSION`, and `/kav-start` prints it. Tell us which version you were on when something goes wrong — it's the fastest way to work out what happened.

## Unreleased

**An author's style pack stays out of Kav's files.** `/kav-style` used to add every new pack to the tracked `styles/README.md`, so registering a look left an edit to Kav itself in the author's folder. Notes now go in the pack's own `README.md`. Kav's `styles/README.md` no longer lists an author's pack, and says how packs ship: `/kav-style <pack> propose` opens a pull request with only the pack in it, for the maintainer to accept or decline.

From the author's own run of the new welcome, photos first:

**Kav talks less.** A reply at a gate is the progress line, the picture, one question and up to three next steps, in about 60 words of Simplified Technical English. No description of a picture the author can see, no report of Kav's own work, no notes about Kav's files in the chat (`AGENTS.md`, "How Kav talks to the author").

**The review surface the author chose is used every time.** Takes go through `/kav-review` from every command. In the chat they are one labelled sheet, never loose images, with a one-time offer of a click-to-pick page.

**Playgrounds.** A photos-first story is a playground (`"kind": "playground"` in `story.json`): no pitch, storyboard or chapters. The Story Tool says what it is under Concept, hides Storyboard and Chapters, and gains a **Playground** row with every panel made in `chapters/play/panels/`.

**The author's approval locks the style.** "Go ahead" on the look, or on a set of portraits in it, is recorded as `**Locked:**` in `style.md`, and the style turns green on the Story Tool. Without a clear approval, Kav says the look is not locked and that `/kav-visual-style-lock` comes next. `/kav-style <pack> approved` does it by hand.

**The review page can be published.** An author who chose `artifact` as their review surface used to get the takes posted in the chat anyway, because the click-to-pick page only ran on `127.0.0.1`. `tools/review.py --artifact` now writes the same page as one self-contained file to publish as an artifact; Submit saves the picks to the artifact's store, and Kav reads them back.

**Reference shots wait for the style.** `/kav-character` used to draw a plain photographic set the moment a photo arrived, before the story had a look. It now registers the photos and the description and stops: the author is offered another character, a place, or the look. The set is drawn once a style is chosen, in that style, straight from the author's photos. The Story Tool says so on a character that is waiting.

From the first author outside the team, who finished an 18-page book the day after Kav was shared: he arrived with the story already written, drew with his AI tool's own image generator, and never touched a provider key. The book got made, but most of Kav's pipeline was bypassed on the way.

**Any image tool is welcome, and its output goes through the pipeline.** Kav used to say its pipeline couldn't use the agent's own image generator. It now says yes: one panel per image, a few takes each, saved with the new `tools/add_candidate.py`, then review, picks, lettering and pages as for any lane (`docs/know-how/own-image-tool.md`). Kav's tested providers are a head start, not a fence. Asked about models, Kav lists every option and asks what the author already has.

**One image is one panel**, in every lane. Pages drawn as a single image can't be lettered, re-rolled or fixed a panel at a time. Now a hard rule.

**A few takes per panel, said and shown up front.** `/kav-start` tells the author before their first story that every panel comes as takes to pick from or re-roll, and shows it with a bundled demo of the review page: a picture of it mid-use (two picks, one re-roll with a note) and the live page on ready-made *Last Light* takes, `python3 tools/review.py --demo`. No story, no key, no cost. The review page now labels takes A, B, C like the contact sheet, and counts picks and re-rolls beside the submit button.

**`docs/know-how/image-models.md`** — a short table of what each image model is like to work with in Kav: Seedream on fal.ai and on Magnific, Nano Banana Pro, Higgsfield, and Midjourney (no API, so only by hand). Asked about a tool that isn't listed, Kav says it knows of no specific limits and offers to try a few examples.

**Starting points.** Before the first story, Kav asks where the author is starting from: a finished story to adapt, a few photos to play with, an idea to develop, or a look around. A finished story gets its own way into `/kav-kickoff`: the text is saved untouched and Kav asks how to adapt it, not what it is about.

**However the author works, these hold** — a short frame in `AGENTS.md` that survives any route: the story in Kav's files and shapes, the Story Tool from the first piece, single panels, takes and picks, Kav's own lettering and page tools, show instead of describe (fonts as the story's sentence set in each one, never links), and only the author can call a picture fixed.

**`/kav-update`** — the latest Kav in one command. Pulls the new version, refreshes dependencies and the Codex prompts, re-runs the health check and says what changed in a few plain lines. It never touches `stories/`, `styles/` or `.env`, and it sets local changes to Kav aside rather than discarding them.

**`/kav-report`** — how it's going, in one message the author sends. `tools/report.py` reads the version, the setup and how far each story has got; the command opens by saying what it is (a way to prepare feedback for the Kav team, nothing sent directly) and asks the author for one comment. Nothing from the story is included, story names are hidden unless asked for, and Kav sends nothing itself.

**The story board is now the Story Tool.** One name for the page beside the chat, so it stops being confused with the storyboard, which is the chapter outline. `docs/know-how/story-board.md` moved to `story-tool.md`. "Show me the board" still works. A tour with screenshots is in `docs/tour.md`.

**The Story Tool.** One page that opens beside the chat the moment a story's first piece lands, and stays current after every change (`docs/know-how/story-tool.md`, `tools/build_map.py`).
- **Overview:** cast, locations, objects, styles (the one in use, every custom pack, any that ship with Kav), the story (concept, storyboard) and chapters, each named under its square. A square shows the piece with two counts — reference images the author gave and images Kav made. Green check when ready; grey otherwise, and hovering says why in one of three plain reasons: reference images missing, description missing, Kav processing pending. Click for a short description (read more for the rest), what to do next as commands to copy — including *complete as is* to skip a step and *build a dna* to go deeper — the images, links to published chapters and the brief, and the source file by its full path. Each row says how to add to it.
- **Ideas:** the notes from `pitch-inbox.md`, and a box to pin a thought any time. In Claude the drop goes straight onto the Story Tool; Kav files it at the next gate and brings it up when it touches what's being worked on. Used notes show where they went.
- After each piece, Kav offers the fork: another, or move on.

**`/kav-note`** replaces `/kav-plot-note`: notes are about anything — a scene, a visual, an object, a line — not only plot. A note that's an instruction ("add a Coke can as an object") gets done; Kav stops only for something it needs from the author, for work that would go stale, or for real generation spend. The Ideas tab opens with an invitation, a copyable `/kav-note <jot your note>`, and one example note Kav wrote from what it knows of the story.

**`/kav-view [ideas]`** pulls the Story Tool up by hand: files any pinned ideas, rebuilds, republishes to the same link. In Claude an open Story Tool also updates itself whenever Kav republishes it.

**On ChatGPT / Codex** there are no artifacts, so the Story Tool lives on its own owner-only ChatGPT Site, built with `build_map.py --standalone`. `/kav-publish` stays for the book.

**Everything copyable copies.** Every command on the Story Tool is a small panel with a copy button, section hints included, and a chapter with a published reader has a copy-link button on its square and its links at the top of its detail.

**`/kav-object <name>`** — a thing that must always look the same (a can, a car, a dress) gets its own intake: one photo of the thing alone, a line on what it is, trigger words, a test scene.

**The intro** (`/kav-start`, kickoff's first message) now tells the author about the Story Tool and where ideas go before the first one arrives, and says the order is a suggestion: start from a story, or from one character in one place.

**`/kav-location <name>`** — a place gets the same intake a character does: photos under one name for sheet, folder and registry, a written line, trigger words, and a test scene to prove it binds.

From reading *Last Light* end to end as a reader rather than as its authors. The story's dialogue was compressed and confident and, in several chapters, unparseable: nobody is told who David is, that he vanished, or why anyone has to go outside, because every agent that wrote a scene could see the brief and the reader never can. The visuals drifted the same way, in the things a reference set doesn't hold.

**Cold reads** — a diagnostic stage that runs on a context-starved reader, `docs/know-how/cold-read.md` and `/kav-coldread`.
- Two are mandatory per chapter, both before the author sees what they're judging: on the scene list before any image money is spent, and on the lettered pages before the read-through gate. Chapter 1 gets a third, alone, once it locks.
- One call never both diagnoses and rewrites. A revision pass takes exactly one named goal from a taxonomy; a second cold read that wasn't told the goal verifies it.
- Errors escalate upstream. A beat that only joins with *and then* is an outline problem.

**The reader ledger** — `stories/<slug>/reader-ledger.md`: every name, pre-story event, world rule and relationship the plot leans on, with where it was teased and where it was paid. Seeded at STORYBOARD, closed chapter by chapter. The brief is not payment. **OPEN is a neutral state:** a book with no open rows has no questions in it.

**A gap is a hook until the reader turns back.** Over-explaining is this tool's own failure mode and it produces a duller book than the one it was pointed at, so `cold-read.md` §3 is built to resist it.

- The reader is asked **what questions they are still carrying**, not what confused them. A confusion prompt is a complaint prompt and it hides the questions the book planted on purpose. They are never asked to judge a question's worth, only for one observable fact: **did you turn back up the page?** Curiosity carries a reader forward, confusion sends them backwards.
- Questions are sorted on a ladder by **whose understanding is missing**: with the protagonist (free, and usually the point), about the world (the engine), about the protagonist (expensive), about the page (always a bug). Same amount of not-knowing, opposite cost.
- The **Open questions register** in the ledger carries every question chapter to chapter, because age is half of what a question means. On the bottom two rungs duration is composition; on the top two it is rot.
- `story.md` CONCEPT gains **Declared unknowns**: what the reader deliberately never learns, and whose understanding is missing. Declared, a cold read leaves it alone. Undeclared, it is raised every time, however obviously intentional it looks.
- The diff against the chapter card is a third thing entirely, an author question rather than a defect: a beat can go missing without a single reader noticing.

**What a two-reader cold read of *Last Light* taught the method.** Both readers retold all six chapters correctly: the plot reached them. What didn't was **who the family were** and **what the central choice cost**. The mother is named once in the whole book and the father never, and both readers took the mother for a sister who doesn't exist. The story's key price, "the handover", was only ever announced by a system voice in capitals, and both readers stopped caring on that page.
- The ledger seeds **every principal's name and relationship on the page**, and **every term the story coins**, first. A principal's first appearance names them or their role in a balloon or caption; a coined term is paid in plain words before the chapter that spends it. Enforced at the outline gate and in Check 7.
- **Apparent age is a hard trait**, written in years. Age drift doesn't only blur a character: it changes the relationship a reader infers.
- The reader gets the book title and chapter titles as text, the assembled pages, and **not the blurb**. The book has to stand without it.
- **A canary fact** — in the brief, not on the page — checks that isolation held.
- The diff against the storyboard runs **heaviest first**: fortune-curve turns, then key events, then the price. *Last Light*'s curve low point was missing from both reconstructions and nobody complained, because nobody misses a turn they never saw.
- Questions both readers carry that the pitch itself can't answer are routed to PITCH, not patched in lettering.
- **Landing** joins the report: callbacks both readers recognised, so no revision pass breaks them.
- `/kav-publish` offers a whole-book cold read when the last chapter is out.
- `cold-read.md` §9 records what is measured and what is still judgement.

**Scene state and faces** — a line without an expression returns the model's default pleasant smile, on a character hanging off a railing in a storm. Every panel line now carries the scene's state clause (hour, sky, light, wardrobe, condition) and that panel's expression. Cast files gain a Wardrobe line and must hold one identity trait that survives a costume change.

**Picked-candidate checks** — invented lettering on any text surface, hallucinated artist signatures in the corners, scene state against the scene, faces against the beat, supporting cast against their mug sets. Checked before lettering, not after publishing.

**Gates for an author who approves by default** — decisions instead of documents, defaults named as defaults, and a silent yes recorded as a silent yes in `chapter-state.md` so a later cold read knows where to look first. At PITCH, 2–3 genuinely different engines rather than one outline to rubber-stamp.

## 1.0.0-rc1 — 2026-09-22

The first build shared with beta authors. It grew out of two finished books: *ברקוביץ ואוליב*, five chapters in Hebrew, and *Last Light*, six chapters written in ChatGPT with Codex. Nearly every rule in here was earned making one of them.

**Writing and drawing**
- Kickoff: concept, cast, locations, objects, style, visual lock, pitch, storyboard, package.
- Characters at two depths: a quick sketch from a one-liner and 2–3 questions, or the full DNA interview.
- Style packs, then a gated visual lock: cheap samples with lettering, draft mug shots, production mug shots, a sample gallery and a style sheet.
- Chapters: outline, scene plan, batched panel generation, the author's picks, lettering in any language including right-to-left, assembled pages, two readers and an Instagram carousel.
- A trailer deck, and publishing per chapter.

**Images**
- Providers behind one layer: fal.ai (Seedream 4.5, Nano Banana Pro), Magnific (Seedream 4.5), Higgsfield (Popcorn, Soul — untested), Google Gemini (Nano Banana Pro).
- `tools/lanes/models.json` is the registry: endpoints, reference caps, prices, how far each model was tested and when it was last checked.
- The reference budget is planned once and shared by prompt and references, capped per provider, with a plain warning when a panel's cast crowds out the style pack.

**Setup**
- `tools/check_setup.py`: one health check, the provider table, and importing keys from another project's `.env` without ever printing one.
- `tools/welcome_panel.py`: one test image, lettered, proving key, model, Chrome and lettering together.
- `KAV_REVIEW` chooses how work is shown for approval: inline boards, a published page, or the local review server.

**Costs**
- `tools/ledger.py`: a row per request in `stories/<slug>/ledger.jsonl`, written when the request is made, so rerolls, rejects and charged failures all count. Totals by model and stage, reported as a documented minimum.

**Known limits**
- Higgsfield is wired up but untested; no image it made has been judged.
- Magnific takes five reference images, so panels stay at three named subjects, and it returns 3:4 rather than 4:5.
- Nano Banana Pro is not recommended for rotoscope-style looks: it drifts faces and ignores the style pack.
- The ledger counts what Kav generated from the day it was added; earlier work in an existing story isn't in it, and it can't yet say which images reached the finished pages.
