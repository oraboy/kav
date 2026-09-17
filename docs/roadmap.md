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

Every generation appends a row to a story-local ledger (e.g. `stories/<slug>/ledger.jsonl`): timestamp, tool, provider, model, prompt, reference list, output path, approximate cost, and later whether the image made it into published work. Kav surfaces running totals as the story progresses (per block, per chapter, spent vs. used) so the author sees what the book costs and how much generation was discarded.

## Agent-side image tools

An image tool the agent already has (an MCP server, a built-in tool) can't drive the pipeline today, because every panel needs the character, location and style references assembled by `tools/kav_refs.py`. `/kav-start` says so when it sees one. A future "agent lane" could hand the assembled prompt and reference paths to the agent's tool and collect the file back.
