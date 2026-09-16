# Scenes — from a line of English to candidate images

The drawing loop every command uses: a scene line goes in, candidate images come out, the author looks. Use it directly for quick tests ("show me the two sisters on the pier at dawn in the noir pack") and through `panel_batch.py` for chapter work.

## Story scope

A scene may only draw on its own story's cast, locations, objects and style. Before running, check every name in the line belongs to `stories/<slug>/cast/*.md`. A name the story doesn't have is a missing character to create (`/kav-character`), not a lookup to satisfy elsewhere.

## One scene

```
python3 tools/generate.py --story <slug> "<scene line>" [--lane seedream|nanobanana] [--ar 4:5|8:5|12:5|9:16] [--seed N]
```

- **Cast** binds from character names in the line (as spelled in `briefs.json` `characters`).
- **Location** binds from the first matching `location_words` trigger.
- **Objects** bind from `object_words` triggers.
- **Style** binds when the line names a pack linked under the story's `styles/` (or the default in `style/style.md`).
- Each run writes the image and a `.json` sidecar naming what actually bound. **Read the sidecar** when something looks wrong — the answer is usually a wrong binding, not a weak model.

Run 2–4 takes with different seeds when the author will choose.

## Many scenes

Write a batch (see `/kav-chapter` Stage C for the shape) and run `python3 tools/panel_batch.py <batch.json>`; review with `/kav-review`.

## Keep the author's words

When the author gives scene ideas, keep their phrasing in the line — especially emotional direction ("he's exhausted, she's furious"), which is the part worth testing. Add only what generation needs: names, location words, framing, position.

## Reading failures

- **403 from fal** — the balance is locked (it locks above zero). The author tops up; re-run to fill gaps.
- **A refusal reported as success** — some endpoints return COMPLETED with a content-policy refusal in the body. Report it as a finding.
- **Scattered errors when running many requests** — fal's default concurrency is low; run fewer workers.

## As an instrument

This is an artistic tool as much as a production one. If a scene is worth seeing in more than one style, location or lane, offer the variants rather than quietly picking one — and let the author look.
