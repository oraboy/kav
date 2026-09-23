# Kav tools

Python scripts that do the image, lettering and page work. Run them from the repo root with Python 3.10+ after `pip install -r requirements.txt`. Every tool prints full usage with `--help`.

Paths used below:

- `<repo>`: the repo root (or `$KAV_HOME`)
- `S` = `<repo>/stories/<slug>/`
- `CH` = `S/chapters/<chNN>/`

API keys come from the environment or `<repo>/.env` (see `.env.example`). Every tool that makes an image goes through `tools/lanes/`, which keeps two choices apart: the **lane** (the model) and the **provider** (who runs it, `--provider`, or `KAV_PROVIDER` in `.env`).

**`tools/lanes/models.json` is the registry** — every provider and model with its endpoints, key names, reference cap, how it takes an aspect ratio, rough price, how far it has been tested (`recommended` · `tested` · `untested` · `not-recommended`) and the date that was last checked. The clients read it, so adding or refreshing a model is an edit there plus a bake-off run, not a code change. `python3 tools/check_setup.py` prints the table and flags entries older than 120 days.

Today: `fal` (`seedream` recommended, `nanobanana` tested) · `magnific` (`seedream` tested, 5 refs max, no 4:5) · `higgsfield` (`popcorn`, `soul` — wired up but untested) · `gemini` (`nanobanana` tested).

**The reference budget is the quality limit.** Characters, then the location photo, then objects, then the style pack. On a capped provider, a panel with four subjects leaves the style pack nothing and the look drifts — keep panels to three named subjects (see `/kav-panel`). `generate.py` and `panel_batch.py` report this as a `warning` in their output.

Browser renders use Chrome, Chromium or Edge, found automatically or set with `KAV_CHROME`. No tool calls an image API unless it says so below.

## Story layout the tools read

```
stories/<slug>/
  story.json                 optional: {"title", "lang", "dir"}
  briefs.json                characters, locations, objects, word maps, defaults.style_pack (the
                             story's locked style; without it a line that doesn't name a pack
                             generates unstyled) — tools/examples/briefs.example.json
  scenes.md                  optional extra briefs
  cast/<name>/source*.jpg    seed photos
  cast/<name>/front.png ...  mug shots: front, three-quarter, smile, full-body
  cast/<name>/<pack>/...     mug shots rendered in a style pack
  locations/<loc>/*.jpg      paths listed in briefs.json
  objects/<obj>.png
  playground/                generate.py output
  ledger.jsonl               one row per image request (tools/ledger.py)
  chapters/chNN/panels/      batch-*.json, candidates/, reviews/, lettering specs, lettered pNN-panelK.png
  chapters/chNN/pages/       layout.json, pNN.png, carousel/
  storyboard/chNN.md         first "# heading" = chapter title
  package/                   trailer.json, trailer.html, slides/, cover.png, readers
styles/<pack>/*.png + medium.txt   shared style packs
```

## check_setup.py

One-command health check: Python, Pillow, Chrome, `.env`, each API key (set or not, and whether it came from the shell or `.env`; values are never printed) and the cheapest configured image lane with its rough cost.

```
python3 tools/check_setup.py [--json]
python3 tools/check_setup.py --import <other/.env> [--overwrite]
```

- **`--import`** copies only Kav's key names (and their aliases) from another env file into `<repo>/.env`, reporting names only. Keys already set are kept unless `--overwrite`.

## welcome_panel.py (calls the API)

The setup test image. Generates one cartoon panel (an author and a robot over a notepad in a workshop, no text in the image) on the cheapest configured lane, then letters the robot's welcome balloon through `letter.py`. No story, no references.

```
python3 tools/welcome_panel.py [--lane seedream|nanobanana] [--dry-run]
python3 tools/welcome_panel.py --letter-only
```

- **Output:** `<repo>/setup/` (gitignored): `welcome-panel.png` (raw), `welcome.lettering.json` (balloon spec), `welcome.png` (lettered). Edit the spec and run `--letter-only` to move the balloon without a new generation.

## ledger.py

What a story cost. Every tool that calls an image API appends a row to `S/ledger.jsonl` at request time — model, stage, price, outcome, output path — so rerolls, rejected takes and charged failures are counted, which a file count never does.

```
python3 tools/ledger.py --story <slug> [--detail] [--json]
```

- **Output:** totals by model and by stage, failed requests, rows with no price. The total is a **documented minimum**: what Kav generated for this story through its own tools. A provider dashboard covers the whole account and is not this book's cost.

## generate.py (calls the API)

Makes one image from a plain-English scene line. The tool finds the cast, location, objects and style pack named in the line, using briefs.json, the pack folder names and the word maps.

```
python3 tools/generate.py --story <slug> "<scene line>" [--lane seedream|nanobanana] [--ar 4:5|8:5|12:5|9:16] [--seed N] [--style <pack>|none] [--dry-run]
```

- **Rules:** the line must name at least one character. `--ar` also accepts 16:9, 1:1, 3:4, 4:3, 2:3 and 3:2, and defaults to 9:16. `--dry-run` prints the brief, the reference list and the prompt without calling the API.
- **Output:** `S/playground/<ts>-<lane>-<slug>.png` plus a `.png.json` sidecar with the prompt, seed, refs, cast and location. The result JSON goes to stdout and includes `ok` and `path`. The exit code is 1 on failure.

## build_mugshots.py (calls the API)

Builds a character's reference set.

```
python3 tools/build_mugshots.py --story <slug> --char <name> [--char <name2>] [--seed N] [--shots front,three-quarter,smile,full-body] [--style-pack <pack>] [--lane nanobanana|seedream] [--from <image>] [--describe "<text>"] [--force]
```

- **Inputs:** `S/cast/<name>/source*` plus `--from`, and the character's description from briefs.json (or `--describe`).
- **Output:** `S/cast/<name>/<shot>.png`, or `S/cast/<name>/<pack>/<shot>.png` with `--style-pack`.
- **Lanes:** `--lane seedream` writes cheap drafts to `.../draft/`, which the pipeline never uses. The default seed is 7. Existing shots are skipped unless you pass `--force`. Needs FAL_KEY.

## touch_up.py (calls the API)

Makes a single-detail edit pass on a finished mug shot.

```
python3 tools/touch_up.py --story <slug> --char <name> --shot front --instruction "<one detail to change>" [--pack <pack>] [--seed N]
```

- **Arguments:** `--shot` takes a comma list and defaults to front.
- **Input:** `S/cast/<name>/[<pack>/]<shot>.png`.
- **Output:** `.../touch/<shot>.png`. It is never used automatically: copy it over the original once approved. Needs FAL_KEY.

## panel_batch.py (calls the API)

Generates candidates for a batch of panels in parallel.

```
python3 tools/panel_batch.py <batch.json> [--sheet-only]
```

- **Batch format:** `{story, chapter, lane, n, workers?, only?: [ids], panels: [{id, ar, line, text?, n?, seed?, style?, picked?}]}`. See `examples/batch.example.json`.
- **Output:** `CH/panels/candidates/<id>-<k>.png` and `<id>-<k>.json`, plus the contact sheet `CH/panels/candidates/<batch-stem>_sheet.png`.
- **Selection:** panels with `picked` are skipped. `only` reruns just those ids. Each candidate gets its own seed. `--sheet-only` rebuilds the contact sheet without generating.

## review.py

Opens a local review page where the author picks candidates.

```
python3 tools/review.py <batch.json> [--port 8765] [--host 127.0.0.1] [--no-open] [--title "..."] [--static out.html]
```

- **Page:** shows panels in batch order. Each panel has its candidates, a pick or reroll toggle, an editable text box (pre-filled from the batch `text`) and a notes box. A panel with `picked` shows only that image, marked locked. A wide panel (`ar` wider than 4:5) shows the full image and its centre 4:5 phone crop side by side.
- **Server:** serves images from `CH/panels/candidates/` as 1000px JPEGs. Submit POSTs to `/submit`, which writes `CH/panels/reviews/<batch-stem>.json`:
  `{"batch", "story", "chapter", "submittedAt", "panels": {"<id>": {"pick": "2"|null, "reroll": bool, "comment": str, "text": str}}}`
  The page then shows "Saved — tell your AI 'picks in'". If a review file already exists, it pre-fills the page. Stop the server with Ctrl+C.
- **`--static out.html`:** writes a standalone page instead, with images linked by relative path. Its Submit button shows the JSON to copy.

## cell_crop.py

Crops an image to a page-cell shape: 4:5, 8:5 or 12:5.

```
python3 tools/cell_crop.py <image> --cells 1|2|3 [<out.png>] [--dx N] [--dy N] [--in-place]
```

- **Output:** `<out.png>`. Without it, the tool writes `<image-stem>.cells<N>.png` next to the input, or overwrites the input with `--in-place`.
- **Crop:** centred, and `--dx`/`--dy` shift the window. The tool prints the phone safe zone (the x range of the centre 4:5).

## letter.py

Letters a panel: speech, thought and shout balloons, captions and free text. The page is rendered as HTML and screenshotted in headless Chrome.

```
python3 tools/letter.py <spec.json> <out.png> [--phone]
```

- **Spec:** `{story?, panel, size: [w, h], style?: {speech|thought|shout|caption: {fill, stroke, stroke_w, font, color, size, weight, slant}}, fonts?: [css urls], overlays: [...]}`. See `examples/lettering.example.json`. `panel` is relative to `S` when `story` is set, otherwise to the repo; it can also be absolute.
- **Balloon:** `{type:"balloon", kind:"speech"|"thought"|"shout", cx, cy, rx, ry, tail?: [x, y], lang, lines, size?}`. Leave out `tail` for a continuation balloon. The tail stops 12% short of the point it aims at.
- **Caption:** `{type:"caption", y, lang, lines}`. The band spans the full panel width with a 40px margin, the text is 1.5x the theme size, and Hebrew is right-aligned.
- **Text:** `{type:"text", x, y, w, h, lang, lines, color?, weight?, font?:"balloon"}` places free text with no box, for title cards.
- **`--phone`:** on a wide panel, captions fit the centre 4:5 crop. Save that render as `pNN-panelK.phone.png`.
- **Output:** `<out.png>` plus `<out>.html` next to it. Default fonts are Varela Round for balloons and Karantina for captions, loaded from Google Fonts, so the render needs network access.

## assemble.py

Builds classic pages and a phone carousel from lettered panels.

```
python3 tools/assemble.py <layout.json>
```

- **Layout:** `{story, chapter, dir?: "rtl"|"ltr" (default rtl), page_width?: 2400, gutter?: 36, background?: [r,g,b], pages: [{id, rows: [[[panel-id, cells], ...], ...]}]}`. See `examples/layout.example.json`.
- **Input:** `CH/panels/<panel-id>.png`. For the carousel, `<panel-id>.phone.png` is used instead when it exists.
- **Output:** `CH/pages/<page-id>.png` and `CH/pages/carousel/<seq>-<panel-id>.jpg` at 1080x1350. Old carousel JPEGs are deleted first.

## build_readers.py

Builds two self-contained reader pages with images embedded.

```
python3 tools/build_readers.py --story <slug> --chapters chNN [chNN ...] --title "..." --out <dir> [--next "..."] [--next-story-url U] [--next-pages-url U] [--home-url U] [--next-label "Next chapter →"] [--home-label "Home"] [--brand "..."] [--chapter-label "..."] [--end-mark "..."] [--dir rtl|ltr] [--footer "..."] [--page-px 1500] [--slide-px 1080] [--slide-q 82]
```

- **Input:** `CH/pages/pNN.png` and `CH/pages/carousel/*.jpg` for each chapter. Chapter titles come from `S/storyboard/chNN.md`.
- **Output:** `<out>/reader-comic.html` (pages stacked) and `<out>/reader-story.html` (one panel per slide, a divider before each chapter, and an end slide when `--next` or `--next-story-url` is given). `--out` is relative to the repo or absolute.
- **Links:** every link uses `target="_top"`. The home link has a house icon and appears only when `--home-url` is set.
- **Defaults:** `--brand` comes from `story.json` `title`. `--dir` comes from `story.json` `dir`, or from `lang`, falling back to ltr.

## build_trailer.py

Builds the story's trailer deck.

```
python3 tools/build_trailer.py --story <slug> [--statics] [--config <trailer.json>] [--out <html>]
```

- **Config:** `S/package/trailer.json`, `{title, lang?, dir?, portrait_pack?, opener: {image, sub}, sections: [...], labels?, fonts?: {urls, heading, body}}`. See `examples/trailer.example.json`. A newline in `title` becomes a line break. Image paths are relative to `S`.
- **Sections:**
  - `{type:"divider", title, sub?}`
  - `{type:"cast", items: [{char, name, line, image?, pack?}]}`
  - `{type:"also", image, title, sub}`
  - `{type:"chapters", items: [{num, title, image, synopsis, readers?: {story, comic}}]}`
  - `{type:"closer", chapter:"01", title?}`
- **Labels:** defaults are `{story:"Story", comic:"Comic", wip:"In progress", chapter:"Chapter", prev:"Previous", next:"Next"}`.
- **Navigation:** tap zones (right two-thirds forward, left third back), swipe, arrow keys and dots. A chapter slide with no reader links shows the `wip` label.
- **Output:** `S/package/trailer.html`. `--statics` also writes `S/package/slides/slide-NN.png` at 1080x1920, which needs Chrome.

## build_cover.py

Builds the link-preview cover: a round portrait on one half, a scene image on the other.

```
python3 tools/build_cover.py --story <slug> --portrait-char <name> --scene-image <path> [--pack <pack>] [--portrait-side left|right] [--scene-focus 0.42] [--out <png>]
```

- **Portrait:** `S/cast/<name>/[<pack>/]front.png`. Without a pack, the tool takes the first `*/front.png` it finds, then `source*`.
- **Scene image:** a path relative to the cwd, the repo or `S`.
- **Output:** `S/package/cover.png` at 1200x630.

## Support modules (not run directly)

- `kav_env.py`: repo root, story paths, `.env` key loading with friendly missing-key messages, Pillow JPEG helpers.
- `kav_refs.py`: reference assembly (`set_story`, `parse_quick_line`, `build_refs`, `build_prompt`, `char_budget`, `style_budget`, `mugshots`, `portrait_path`).
- `chrome.py`: `find_chrome()` and `screenshot()`. `python3 tools/chrome.py` prints the browser it found.
- `lanes/fal.py`: fal.ai queue client (`run(endpoint, payload, key)`).
- `lanes/gemini.py`: direct Gemini image client (`run(prompt, refs, key, ar)`). Its model comes from `KAV_GEMINI_MODEL`.
