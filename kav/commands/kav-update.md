---
name: kav-update
description: Update this Kav install to the latest version without touching the author's stories — pull the new version, refresh dependencies and the Codex prompts if needed, re-run the health check, and say in a few plain lines what changed. Use when the author types /kav-update, says "update Kav", "get the latest version", "is there a new version", or was told a fix has been released.
---

# /kav-update — the latest Kav, stories untouched

Kav changes often. This brings the install up to date in one go. **The author's work is safe by design:** `stories/`, `styles/` and `.env` are not part of what gets updated, and this command never deletes or overwrites them.

## Steps

1. **Where we are.** Confirm the current folder is Kav (`AGENTS.md` and `kav/commands/` exist). Read `VERSION` and keep it as *before*.
2. **Is this install a git clone?** Run `git status --short`.
   - **Not a git repository** (Kav was downloaded as a zip): say so, and give the way through: download the new version into a new folder, then move `stories/`, `styles/` and `.env` across. Offer to do the move once they have the new folder. Stop here.
   - **Changed Kav files listed:** the author, or an agent, has edited Kav itself. List the files in plain words and ask which they want: keep the changes aside and update (`git stash`, and say how to get them back with `git stash pop`), or leave the update for now. Never discard them.
   - **Clean:** go on.
3. **Not on `main`?** `git branch --show-current`. On another branch, say which, and ask before doing anything. Don't switch branches on your own.
4. **Update.** `git pull --ff-only`. If it fails:
   - no network: say so, nothing has changed, try again later;
   - cannot fast-forward: this copy has commits of its own. Say that plainly and stop. Never force, reset or rebase.
5. **Already up to date?** Say so with the version and stop. No need for the rest.
6. **Refresh what the update can't reach.**
   - Dependencies, if `requirements.txt` changed: `pip install -r requirements.txt` (inside the venv if the install uses one).
   - **Codex only:** copy the prompts again, `cp adapters/codex/prompts/kav-*.md ~/.codex/prompts/`.
7. **Check.** `python3 tools/check_setup.py`. Report anything that isn't OK with its fix.
8. **Say what changed**, in three to five plain lines, from the top of `CHANGELOG.md` down to the *before* version: what the author can now do, new commands by name, anything that works differently. No file names, no internals.
9. **Tell them to restart** the agent in this folder so new and changed commands load (Claude Code: exit and run `claude` here; Codex: restart it here). Name the version they are now on.

## Hard rules

- **Never touch `stories/`, `styles/` or `.env`.** If a pull would overwrite something there, stop and say so.
- **Never throw away local changes** to Kav. Set aside or leave alone; the author decides.
- Nothing is pushed or published by this command.
