---
name: kav-view
description: Pull up the Story Tool — rebuild it from the story's files, file any ideas pinned on it, and put it in front of the author beside the chat. Use when the author types /kav-view, says "show me the Story Tool", "show me the board", "open the map", "where are we", "refresh the board", or "check the board". /kav-view ideas opens it on the Ideas tab.
argument-hint: "[ideas]"
---

# /kav-view — the Story Tool, fresh, in front of the author

The Story Tool opens by itself once a story's first piece lands and stays current on its own (`docs/know-how/story-tool.md`). This is the manual version: open it, or refresh it, any time.

1. **Identify the story** (from context or the most recent `stories/<slug>/kickoff-state.md`; ask if ambiguous).
2. **File pinned ideas.** In Claude, read the Story Tool's `drops` collection and file each unfiled one into `pitch-inbox.md` exactly as `/kav-note` does. Say what you filed in one line, if anything.
3. **Rebuild.** `python3 tools/build_map.py --story <slug>` — add `--standalone` when it's going to a ChatGPT Site. Refresh `package/idea-suggestion.txt` if the old suggestion was used.
4. **Put it in front of the author**, at the same link as always (`kickoff-state.md` → Links → Story Tool; stories started before the rename say *Story board*):
   - **Claude:** republish `story-map.html` over the existing artifact (`capabilities: {"db": {}}`) and show it. A Story Tool that's already open updates itself in place.
   - **ChatGPT / Codex:** there are no artifacts, so the Story Tool lives on its own small ChatGPT Site — the Story Tool's, never the book's (`/kav-publish` owns that one). Build with `--standalone` into `stories/<slug>/board-site/dist/index.html`, register the Site once with the `sites-building` and `sites-hosting` skills, deploy **owner-only**, and keep its link in `kickoff-state.md`. Every refresh redeploys the same Site; the author reloads the page.
   - **Local only:** serve it and give the address, and say it only opens on this machine.
5. With `ideas`, link straight to the Ideas tab: the Story Tool's link with `#ideas` on the end.

No story yet? Say so in one line and offer `/kav-kickoff`.
