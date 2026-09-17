# Kav roadmap

Planned work that is agreed but not built yet.

## More image providers

Today Kav's tools call two providers directly: fal.ai (Seedream 4.5, Nano Banana Pro) and Google Gemini (Nano Banana Pro). Next, in this order of interest:

- **Magnific**
- **Higgsfield**
- **OpenAI image models** (DALL·E / GPT Image)

Each needs a lane client in `tools/lanes/`, a key entry in `tools/kav_env.py` (`KEY_HELP`, `KEY_ALIASES`), detection and cost in `tools/check_setup.py`, and a row in the key table of `/kav-start` and `INSTALL.md`.

## Agent-side image tools

An image tool the agent already has (an MCP server, a built-in tool) can't drive the pipeline today, because every panel needs the character, location and style references assembled by `tools/kav_refs.py`. `/kav-start` says so when it sees one. A future "agent lane" could hand the assembled prompt and reference paths to the agent's tool and collect the file back.
