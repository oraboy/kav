# Changelog

Kav's version is in `VERSION`, and `/kav-start` prints it. Tell us which version you were on when something goes wrong — it's the fastest way to work out what happened.

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

**Known limits**
- Higgsfield is wired up but untested; no image it made has been judged.
- Magnific takes five reference images, so panels stay at three named subjects, and it returns 3:4 rather than 4:5.
- Nano Banana Pro is not recommended for rotoscope-style looks: it drifts faces and ignores the style pack.
- There is no cost ledger yet. Spend has to be read off the provider's dashboard, which mixes in unrelated work.
