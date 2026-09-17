# Installing Kav — instructions for the AI agent

You are an agent (Claude Code, Codex CLI, or similar) installing Kav for an author who may not be technical. Follow these steps in order. Explain each step in one plain sentence as you go, report problems clearly, and don't skip the checks.

## 1 · Get the repo

- If the current directory already contains `AGENTS.md` and `kav/commands/`, you are in Kav. Skip to step 2.
- Otherwise clone it: `git clone https://github.com/oraboy/kav.git` and work inside `kav/` from now on. If the author wants it somewhere specific, ask where first.

## 2 · Python 3.10+

Run `python3 --version`. If it's older than 3.10 or missing, stop and tell the author how to install it for their OS (python.org, or Homebrew `brew install python` on macOS). Don't continue without it.

## 3 · Dependencies

Recommended: a virtual environment.

```
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

If you create a venv, remember to use `.venv/bin/python3` (or activate it) for every later `tools/` command, and tell the author it exists.

## 4 · Chrome

Run `python3 tools/chrome.py`. It prints the Chrome/Chromium path it found, or an error. If none is found, ask the author to install Google Chrome (https://www.google.com/chrome/) or Chromium, then run the check again. Lettering, pages and readers don't work without it.

## 5 · API keys

Create the env file: `cp .env.example .env` (skip if `.env` exists). `.env` is gitignored.

**Ask first: "Set up image generation now, or later?"** Later is fine: writing works without keys, and `/kav-start` offers this again. If now:

1. Run `python3 tools/check_setup.py`. It reports keys already set in the shell or in `.env` (never their values). If one is there, offer to use it.
2. If the author has a key in another project's `.env`, ask for the path and run `python3 tools/check_setup.py --import <path>`. It copies only Kav's key names and reports names only. Don't open that file yourself.
3. Otherwise walk the author through getting a key, one at a time (fal.ai alone is enough):

| Variable | What it powers | Where to get it |
|---|---|---|
| `FAL_KEY` | Seedream 4.5 — the main image lane | Sign in at https://fal.ai, open https://fal.ai/dashboard/keys, create a key. Add a little credit under Billing: generation stops with a 403 when the balance runs low |
| `GEMINI_API_KEY` | Nano Banana Pro — text in frame, real places, mug shots | Sign in at https://aistudio.google.com/apikey and create a key. Nano Banana Pro needs billing enabled on the Google Cloud project behind the key |

**Handling keys safely:**
- Best: ask the author to open `.env` in their editor and paste each key after the `=` themselves. Offer to open the file for them.
- If the author pastes a key into the chat anyway: write it into `.env` yourself, **don't repeat it back**, don't print `.env`, and suggest they rotate it later if the chat is logged anywhere they don't control.
- Never put keys in any other file, a commit, a command line argument or a URL.
- To verify, check the variables are non-empty without printing them.

The author can start writing (kickoff, characters' DNA, pitch, storyboard) without keys; images need them.

## 6 · Wire up the commands

**Claude Code:** nothing to copy. The commands are already in `.claude/skills/kav-*/`. Tell the author to restart Claude Code in this folder (exit, then run `claude` here) so the skills load. Commands: `/kav-start`, `/kav-kickoff <slug>`, …

**Codex CLI:** custom prompts are read from `~/.codex/prompts/` (top-level `.md` files only):

```
mkdir -p ~/.codex/prompts
cp adapters/codex/prompts/kav-*.md ~/.codex/prompts/
```

Tell the author to restart Codex in the Kav folder. Commands are invoked as **`/prompts:kav-start`**, **`/prompts:kav-kickoff <slug>`**, etc. (type `/prompts:` to see the list). Each prompt tells Codex to read the canonical command file in `kav/commands/`, so Codex must be started from the Kav folder.

Codex also supports skills (OpenAI now recommends skills over custom prompts). They ship ready in `.agents/skills/`, so inside the Kav folder the commands are also available as `$kav-start` etc., and via `/skills` — no copy needed.

**Other agents** (Cursor, Gemini CLI, …): nothing to install. They read `AGENTS.md`; the author asks for a step by name ("run kav-start").

After pulling Kav updates, re-copy the Codex prompts. Maintainers who edit `kav/commands/` run `python3 scripts/sync_adapters.py` to regenerate all adapters.

## 7 · Smoke test

Run the lettering tool on the bundled example — it needs Python, the dependencies and Chrome, but no API keys:

```
python3 tools/letter.py tools/examples/lettering.example.json /tmp/kav-smoke.png
```

Look at the output image to confirm a caption and balloon were drawn. If it fails, read the error: usually Chrome (step 4) or a missing package (step 3).

If a key is set, **ask before spending** (the *image lane* line of `check_setup.py` gives the cheapest lane and its cost, about $0.04 on Seedream), then run `python3 tools/welcome_panel.py`. It generates one cartoon panel of an author and a robot in a workshop and letters the robot's welcome balloon, proving the key, the lane, Chrome and lettering in one go. Look at `setup/welcome.png` and show it to the author; to move the balloon, edit `setup/welcome.lettering.json` and run it again with `--letter-only`.

## 8 · Hand over

Tell the author, in two or three sentences, that Kav is installed and what worked. Then tell them to run:

- Claude Code: **`/kav-start`** (after restarting)
- Codex CLI: **`/prompts:kav-start`** (after restarting)
- Other agents: "run kav-start"

It welcomes them, checks the install again, offers image setup if it was left for later, explains the process, and offers to start their first story.
