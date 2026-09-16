---
name: kav-review
description: Open the local image review page for a panel batch, wait for the author to pick, reroll and edit text, then read the saved review JSON and apply it (picks recorded, rerolls regenerated with a changed line, text replaced verbatim). Use when the author types /kav-review <batch.json>, says "open the review page", "show me the takes", or "picks are in".
argument-hint: "<batch.json>"
---

# /kav-review <batch.json> — the author picks

The author chooses every image that lands in a page. This is where that happens: a local page, not a chat thread.

## 1 · Open the page

```
python3 tools/review.py <batch.json> [--port 8765]
```

Run it in the background (it serves until stopped) and give the author the local URL it prints. If the port is busy, pick another with `--port`.

What the author sees: **the whole chapter in reading order** — every scene's panels; already-picked panels shown locked as their chosen image; open panels showing every take, **full image and phone crop side by side**. Per panel: pick a take, mark reroll (with a note on why), edit the caption/balloon text. Plus a notes box. One save writes:

```
stories/<slug>/chapters/<ch>/panels/reviews/<batch-stem>.json
```

Say, briefly: the page is open, pick / reroll / edit text, press save, then tell me "picks in". **Then wait.** Don't poll the author, don't pre-pick.

## 2 · Picks in

When the author says so (or asks you to check), read `reviews/<batch-stem>.json`. If it doesn't exist yet, say so — the save didn't happen — and wait again. If it exists, apply it:

- **Picks** — for each picked panel: record in `panels/manifest.md` (panel id → scene → line → chosen candidate file); mark it `"picked": "<take>"` in the batch so the next review renders it locked.
- **Rerolls** — rewrite the panel's `line` **for the reason the author gave**, then regenerate just those panels (a new batch `batch-<stem>-reroll.json` with only the reroll panels plus the locked ones for context, or `tools/generate.py` per panel). Never resend an unchanged line. Common fixes: move the camera for a wrong direction; "in the foreground centre, face clear" plus repeated identity words for a lost character; bind an approved earlier panel as a location reference when a room drifted (see `/kav-chapter`, continuity).
- **Text** — the author's text replaces the proposal **verbatim**; fix only obvious typos and flag them. Update `plan.md` and the lettering specs.
- **Notes** — act on each, or ask one question if unclear.

Report back in a few lines: N picked, N rerolling (with the changed reason per panel), text changes applied. Then either run the reroll batch and reopen the review page, or, when every panel is picked, move on to lettering.

## Hard rules

- Never pick for the author unless they explicitly say "you pick" — then say which and why.
- Never letter a panel that isn't picked in a saved review.
- The review JSON is the record of the author's decisions; don't edit it by hand.
