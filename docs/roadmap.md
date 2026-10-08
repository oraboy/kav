# Kav roadmap

Planned work that is agreed but not built yet.

## More image providers

Today Kav's tools call two providers directly: fal.ai (Seedream 4.5, Nano Banana Pro) and Google Gemini (Nano Banana Pro). Next, in this order of interest:

- **Magnific**
- **Higgsfield**
- **OpenAI image models** (DALL·E / GPT Image)

Each needs a lane client in `tools/lanes/`, a key entry in `tools/kav_env.py` (`KEY_HELP`, `KEY_ALIASES`), detection and cost in `tools/check_setup.py`, and a row in the key table of `/kav-start` and `INSTALL.md`.

## Keeping the provider/model list current

The registry exists: `tools/lanes/models.json` holds every provider and model with endpoints, key names, reference cap, aspect handling, rough price, status and `verified_on`; the clients read it, and `check_setup.py` prints it and flags anything older than 120 days. No API offers a "list models" endpoint carrying what Kav needs (reference support, caps, price), so entries are verified by hand. Still to do:

- **A bake-off command:** generalise `stories/<slug>/bakeoff/replay_book.py` — point it at any set of picked panels and a new model, get the comparison board. That is how a new model earns a place on the menu, since only the author's eye can say whether it passes.
- **Higgsfield's catalogue** is per account (its CLI lists 23 image models), so its client should read the account's own list where the API allows it.
- **Parked: Higgsfield.** The client works (key accepted, references upload) but nothing it makes has ever been judged, because the test account had no credits. Left `untested` in the registry until an author who uses Higgsfield wants it; then run the replay and set its status.

## Per-story model choice at visual lock

Setup records a default provider and model order (recommended: fal.ai, Seedream first, Nano Banana Pro second). During `/kav-visual-style-lock` the author may compare models on their own look and lock a different one for this story ("Nano Banana holds this style better, worth the extra cost"). Kav recommends and warns about cost or quality; the author decides. The lock lives in the story (e.g. `style/style.md` backend block, read by the tools) and overrides the setup default.

## Cost ledger per story

Built: `tools/ledger.py` writes a row per request to `stories/<slug>/ledger.jsonl` (time, stage, tool, provider, model, aspect, seed, outcome, price, file), including failures, and reports totals by model and stage as a documented minimum. `/kav-chapter` quotes the running total; `/kav-publish` reports it when the book closes.

Still open: marking which generations actually reached the published pages, so the report can separate spent from used, and a rough per-chapter forecast before a batch runs.

## Agent-side image tools

First version built: an author can draw with the image generator in their AI tool, or any other tool, and the takes enter Kav's pipeline through `tools/add_candidate.py` (`docs/know-how/own-image-tool.md`). The agent generates one panel per image and passes the references itself; `tools/generate.py --dry-run` prints the prompt and the reference files Kav would have sent.

Still open:

- **Binding is on the agent's honour.** Kav cannot verify that the other tool received the character, location and style references. A sidecar field recording which reference files were attached would let the picked-candidate checks name what bound.
- **Cost is unknown.** Rows are written to the ledger with no price. A per-tool price the author can declare once would close the gap.
- **A lane entry per tool.** Once a tool has been judged on a real book (the bake-off above), it can earn a row in `tools/lanes/models.json` with a reference cap and a status, instead of "untested by us".
