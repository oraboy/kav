# Showing work for approval

Every creative gate ends with the author looking at something. How they look depends on where Kav is running and what device they are on, so the surface is a setting, not a guess.

## The setting

`KAV_REVIEW` in `.env`, asked once by `/kav-start`:

| Value | What it means | Good default for |
|---|---|---|
| `inline` | composite boards posted straight into the conversation | ChatGPT / Codex, and anyone working from a phone |
| `artifact` | a published interactive page (Claude Artifacts), link shared in the conversation | Claude Code, desktop or phone |
| `local` | the local review server, `tools/review.py`, at `http://127.0.0.1:<port>` | desktop only, when the author wants the click-to-pick page |

Unset: use `artifact` when Artifacts are available, otherwise `inline`. Ask the author to confirm the first time it matters, then stop asking.

## Rules that hold on every surface

- **A localhost page is never the only route to a gate.** It cannot be opened from a phone, from a remote session, or from a chat-hosted agent. Whenever `local` is used, post the same content as a composite board as well.
- **A raw `file://` link is not a review surface.** Some hosts render such a page as source. Serve HTML through the local server, or publish it.
- **Few boards, not many links.** One composite sheet with every take beats twelve separate image links, especially on a phone.
- **Every option carries its label inside the image**: `<panel-id> A`, `<panel-id> B`. Repeat the label in the text. Never rely on order, column, filename or caption — the author replies "s2p1 B" from their phone. `panel_batch.py` burns these in.
- **Letters survive elimination.** If B and D go through to a second round, they stay B and D. Never renumber survivors.
- **Show, don't describe.** Lettering themes, palettes, borders, page furniture, a style: render a sample and show it. Anything described but not shown is provisional, never approved.
- **Discussion art is not page art.** Moodboards, style samples and storyboard concept visuals are for talking. Page artwork is only what the author picked in the chapter review. Approving a board never promotes a concept image into a page.
