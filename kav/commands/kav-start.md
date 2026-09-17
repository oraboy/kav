---
name: kav-start
description: Kav's welcome, health check and image-generation setup. Introduces Kav, checks the install (Python, Chrome, API keys), offers to set up image generation now or later and test it with one lettered panel, explains the process, lists the commands, and offers to start a first story or open an existing one. Use when the author types /kav-start, says "get started", "how does Kav work", "what can you do", or has just finished installing.
argument-hint: ""
---

# /kav-start — welcome, health check, image setup, first steps

This command orients a new author in a few short messages. Keep it light: a tour, not a lecture. Wait for the author at every question.

## Step 1 — Welcome

Show this, verbatim, as the first thing the author reads:

> **Kav is a co-writer for graphic novels.** You bring the story and the visual style, and you make every call. Kav brings the structure, pushes back on weak spots, draws and letters the panels, and puts together the finished book.
>
> Stories can come from real life or pure imagination. Your own photos become the cast and the places, so a book can star your street, your family or your dog, or a world nobody has seen. The look is yours to pick or invent: anime, film noir, watercolour, rotoscope, anything you can point to.
>
> **How it works:** kick off with a one-line pitch, then collect the cast, the places and the look. Lock the visual style and build the reference art. Storyboard the arc, then write and draw one chapter at a time. Kav suggests options; you pick, refine, overrule and direct.
>
> **What you get:** a phone reader for each chapter, full pages, Instagram carousels and a trailer to share.
>
> Everything is saved as files in one folder per story, so work stays organised and you can run several stories side by side.

## Step 2 — Health check

Run `python3 tools/check_setup.py` (use `.venv/bin/python3` if a venv exists) and show its table. It never prints key values. For anything MISSING other than the keys, offer to fix it now following `INSTALL.md`. Keys are Step 3.

## Step 3 — Image generation (GATE)

Writing (concept, cast, pitch, storyboard) works without keys; drawing needs one. Ask explicitly:

> **Set up image generation now, or later?**

**Later:** say that `/kav-start` runs this again any time, and go to Step 4.

**Now:**

**(a) First, look at what is already there.** `check_setup.py` lists the providers whose keys are set, in the shell or in `.env`. Say what was found in one line ("fal.ai is already set up here"). Ask whether they also keep a key in another project; if so, ask for the path and run:

```
python3 tools/check_setup.py --import <path-to-other/.env>
```

It copies only the key names Kav knows, reports names only, and keeps keys already set unless `--overwrite` is added. Never open, print or read that file yourself.

If the agent has an image-generation tool of its own (an MCP server or built-in tool), say plainly that Kav's pipeline cannot use it yet: Kav's tools call the image APIs directly so every panel carries the character, location and style references. One-off pictures only.

**(b) Then present the options, with the trade-offs, and let the author choose.** Show all four, marking what is already set up and what Kav recommends. **A provider they already use is the natural choice** — say so, and don't talk them out of it.

| Provider | Models | Trade-offs |
|---|---|---|
| **fal.ai** *(recommended when nothing is set up)* | Seedream 4.5, Nano Banana Pro | One key for both. Takes Kav's full reference stack, which holds faces best. About $0.04 an image on Seedream. Needs a little credit up front, and generation stops with a 403 when the balance runs low |
| **Magnific** *(tested, passes)* | Seedream 4.5 | Same model as fal.ai's default, similar quality, its own slightly different look. **5 reference images max**, so panels must stay at three named subjects or the style stops binding. No 4:5 output: page cells come back 3:4 and need cropping |
| **Higgsfield** | Popcorn, Soul | Popcorn takes 8 references. Soul is Higgsfield's own look and takes one style reference, so it cannot hold a character's face across panels. Untested by us; API credits are separate from the app plan |
| **Google Gemini** | Nano Banana Pro | Direct access without fal.ai. One model only, about 4× Seedream's price, and in our tests it ignored a rotoscope style pack for its own painterly look. Fine for other styles; needs billing enabled on the Google Cloud project |

Ask which they want, and what to use first and second (the default is Seedream first, Nano Banana Pro second). Record it in `.env`:

```
KAV_PROVIDER=fal      # or magnific / higgsfield / gemini
```

**Warn once, then respect the choice.** If they pick a model with a known cost (price, a reference cap, a style that resists style packs), say it in one line and move on. The author decides. The choice is not permanent: during `/kav-visual-style-lock` they can compare models on their own look and lock a different one for that story.

**(c) Getting the key.** `cp .env.example .env` if it doesn't exist, then point at the right page and ask the author to paste the key into `.env` themselves. Offer to open the file. If they paste a key into the chat anyway, follow `INSTALL.md` §5. Re-run `check_setup.py` to confirm.

| Provider | Where |
|---|---|
| fal.ai | https://fal.ai/dashboard/keys (add credit under Billing) |
| Magnific | https://www.magnific.com/api |
| Higgsfield | https://cloud.higgsfield.ai/api-keys (paste the whole key, including the `:`) |
| Google Gemini | https://aistudio.google.com/apikey |

**(d) Test it (GATE).** Ask before spending:

> I'll generate one test panel, an author and a robot at work in a workshop, with the robot welcoming you to Kav in a speech balloon. It costs about $<cost> on <lane>. OK?

Use the lane and cost from `check_setup.py`'s *image lane* line (the cheapest configured). On yes:

```
python3 tools/welcome_panel.py
```

It generates the panel with no text in it, then letters the balloon with `tools/letter.py`, so one run proves the key, the lane, Chrome and lettering. **Look at `setup/welcome.png`, then show it to the author.** If the balloon's tail doesn't point at the robot or the balloon covers a face, edit `cx`/`cy`/`tail` in `setup/welcome.lettering.json` and run `python3 tools/welcome_panel.py --letter-only` (free). If generation fails, show the error: a 401/403 is usually the key or the fal.ai balance.

## Step 4 — The process

1. **Kickoff** — a slug and a one-line pitch. `/kav-kickoff <slug>`
2. **Collect** — characters (a quick sketch or a full DNA, your pick), locations and the key events. Ideas that come up early get parked with `/kav-plot-note`.
3. **Visual style** — pick or build a style pack, then lock the look on cheap samples before spending on production references. `/kav-style`, `/kav-visual-style-lock`
4. **Storyboard & brief** — the story's shape, what each character wants and what stands in the way, then a card per chapter and a one-page brief.
5. **Chapter by chapter** — outline, scene list, panel images reviewed on a local page, lettering, assembled pages. `/kav-chapter <NN>`
6. **Publish** — readers per chapter, Instagram-ready carousel images, a trailer deck. `/kav-publish`, `/kav-trailer`

## Step 5 — The commands

| Command | What it does |
|---|---|
| `/kav-start` | this welcome, health check and image setup |
| `/kav-kickoff <slug>` | scaffold a story: concept, cast, locations, style, pitch, storyboard, brief |
| `/kav-character <name>` | build a character's reference mug shots |
| `/kav-style <pack>` | register reference images as a named visual style |
| `/kav-visual-style-lock <pack>` | test the style cheaply, then bake production references |
| `/kav-plot-note <idea>` | park a story idea without arguing it; "show the notes" renders the board |
| `/kav-chapter <NN>` | write and draw one chapter |
| `/kav-panel` | one scene plus its text into one lettered panel |
| `/kav-review <batch.json>` | open the local image review page and apply the author's picks |
| `/kav-trailer` | build the story's swipeable trailer deck |
| `/kav-publish` | build readers for every drawn chapter and explain where to post them |

In Codex CLI the same commands are invoked as `/prompts:kav-start` etc. (see `INSTALL.md`). In any other agent, just ask for the step by name — the agent reads `kav/commands/kav-<name>.md`.

## Step 6 — Offer the next move

- If `stories/` holds a story folder (anything besides `.gitkeep`): list them with their `kickoff-state.md` status line and offer to resume one — `/kav-kickoff <slug>` resumes kickoff, `/kav-chapter <NN>` resumes a chapter. If a finished chapter has `pages/reader-story.html`, offer to open it so the author sees what the end product looks like.
- Otherwise: ask for a slug and a one-line pitch and offer to run `/kav-kickoff <slug>` right away. If the author has no idea yet, offer to brainstorm three one-liners — then stop and let them pick.

Wait for the author. Do not start a kickoff unasked.

## Hard rules

- Never print, echo or read back a key, `.env`, or another project's env file.
- Nothing is generated without the author's yes to the cost.
- Text on the test panel goes through the lettering tool, never into the generation prompt.
