# Kav — Claude Code instructions

Read and follow `AGENTS.md` — it is the operating contract for this repo (process, command router, tools, hard rules).

In Claude Code the commands are installed as skills in `.claude/skills/kav-*/SKILL.md`, invoked as `/kav-start`, `/kav-kickoff <slug>`, `/kav-chapter <NN>` and so on. Those skill files are generated from `kav/commands/*.md` by `python3 scripts/sync_adapters.py`; edit the canonical command, then re-run the script. Never edit the generated skills by hand.
