# Changelog

Kav's version is in `VERSION`, and `/kav-start` prints it. Tell us which version you were on when something goes wrong — it's the fastest way to work out what happened.

## Unreleased

**The story board.** One page that opens beside the chat the moment a story's first piece lands, and stays current after every change (`docs/know-how/story-board.md`, `tools/build_map.py`).
- **Map:** cast, locations, objects, styles (every available pack), the story (concept, storyboard) and chapters. Each square is its image with two counts — reference images the author gave and images Kav made. Green check when ready; grey otherwise, and hovering says why in one of three plain reasons: reference images missing, description missing, Kav processing pending. Click for what's needed, every image labelled (REF01, GEN01, P01) so the author can say "remove GEN02 from Oren", and links to published chapters and the brief. Each row says how to add to it.
- **Ideas:** the notes from `pitch-inbox.md`, and a box to pin a thought any time. In Claude the drop goes straight onto the board; Kav files it at the next gate and brings it up when it touches what's being worked on. Used notes show where they went.
- After each piece, Kav offers the fork: another, or move on.

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
