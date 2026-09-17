# Kav roadmap

Planned work that is agreed but not built yet.

## More image providers

Today Kav's tools call two providers directly: fal.ai (Seedream 4.5, Nano Banana Pro) and Google Gemini (Nano Banana Pro). Next, in this order of interest:

- **Magnific**
- **Higgsfield**
- **OpenAI image models** (DALL·E / GPT Image)

Each needs a lane client in `tools/lanes/`, a key entry in `tools/kav_env.py` (`KEY_HELP`, `KEY_ALIASES`), detection and cost in `tools/check_setup.py`, and a row in the key table of `/kav-start` and `INSTALL.md`.

## Keeping the provider/model list current

Providers ship new models constantly, and Kav's list is hand-written in `tools/lanes/<provider>.py`. Nothing discovers them. Neither Magnific nor Higgsfield exposes a "list models" endpoint that carries what Kav needs (reference-image support, caps, aspect ratios, price), so the list cannot be refreshed from the API today. Planned instead:

- **One registry file** (`tools/lanes/models.json`): per provider and model — endpoint, reference cap, aspect ratios, rough price, `verified_on` date and a link to the docs. The clients read it instead of holding their own constants; adding a model becomes a data edit and one bake-off run.
- **A staleness nudge:** `check_setup.py` says when a provider's entry was last verified, and `/kav-start` mentions it when the date is old.
- **A bake-off command** (`stories/<slug>/bakeoff/replay_book.py`, generalised): point it at any set of picked panels and a new model, get the comparison board. That is how a new model earns a place on the menu, since only the author's eye can say whether it passes.
- **Higgsfield's catalogue** is per account (its CLI lists 23 image models), so its client should read the account's own model list where the API allows it.

## Per-story model choice at visual lock

Setup records a default provider and model order (recommended: fal.ai, Seedream first, Nano Banana Pro second). During `/kav-visual-style-lock` the author may compare models on their own look and lock a different one for this story ("Nano Banana holds this style better, worth the extra cost"). Kav recommends and warns about cost or quality; the author decides. The lock lives in the story (e.g. `style/style.md` backend block, read by the tools) and overrides the setup default.

## Cost ledger per story

Every generation appends a row to a story-local ledger (e.g. `stories/<slug>/ledger.jsonl`): timestamp, tool, provider, model, prompt, reference list, output path, approximate cost, and later whether the image made it into published work. Kav surfaces running totals as the story progresses (per block, per chapter, spent vs. used) so the author sees what the book costs and how much generation was discarded.

## Agent-side image tools

An image tool the agent already has (an MCP server, a built-in tool) can't drive the pipeline today, because every panel needs the character, location and style references assembled by `tools/kav_refs.py`. `/kav-start` says so when it sees one. A future "agent lane" could hand the assembled prompt and reference paths to the agent's tool and collect the file back.
