# Kav — Your AI co-writer for graphic novels

Kav turns an agentic coding tool into a graphic-novel studio. You bring the story and make the calls; Kav helps you shape it (character DNA, intention and obstacle, story shape, a chapter-by-chapter storyboard), then draws it with you: panel images generated against your own character, location and style references, a local review page where you pick every image, lettering in any language including right-to-left, and assembled pages with two web readers per chapter. It grew out of a finished five-chapter book, and every rule in it was earned making that book.

## Install

Open Claude Code or Codex CLI in an empty folder and paste:

```
Please read github.com/oraboy/kav, install it and help me get started.
```

Kav works in **agentic coding tools** that can run commands on your machine: Claude Code and OpenAI Codex CLI are supported; Cursor, Gemini CLI and other agents that read `AGENTS.md` should work. It does **not** work in chat-only apps, because Kav runs a local image, lettering and page-assembly pipeline. Manual steps are in [INSTALL.md](INSTALL.md).

## The process

1. **Kickoff** — a slug and a one-line pitch
2. **Characters, locations, key events** — collected one at a time, with reference images
3. **Visual style** — pick or build a style pack, test it cheaply, lock it
4. **Storyboard & brief** — story shape, intention/obstacle per character, a card per chapter, a one-page brief
5. **Chapter by chapter** — an outline, the scene breakdown, image review on a local page
6. **Lettering & pages** — captions, balloons and sound bursts; pages, a phone reader and a page reader
7. **Final draft & publish** — linked readers, Instagram-ready carousel images, a trailer deck

Every step writes a file, so you can stop anywhere and pick up later. Nothing is generated past a decision that's yours. Details: [docs/process.md](docs/process.md).

## Commands

| Claude Code | Codex CLI | What it does |
|---|---|---|
| `/kav-start` | `/prompts:kav-start` | welcome, install health check, image setup with a test panel |
| `/kav-kickoff <slug>` | `/prompts:kav-kickoff <slug>` | scaffold a story: concept, cast, locations, style, pitch, storyboard, brief |
| `/kav-character <name>` | `/prompts:kav-character <name>` | build a character's reference mug shots |
| `/kav-style <pack>` | `/prompts:kav-style <pack>` | register reference images as a named style |
| `/kav-visual-style-lock <pack>` | `/prompts:kav-visual-style-lock <pack>` | test the style on cheap samples, then bake production references |
| `/kav-note <note>` | `/prompts:kav-note <note>` | jot down any idea — a scene, a visual, an object — for Kav to pick up when it fits |
| `/kav-view [ideas]` | `/prompts:kav-view [ideas]` | pull up the story board, fresh |
| `/kav-chapter <NN>` | `/prompts:kav-chapter <NN>` | write and draw one chapter |
| `/kav-location <name>` | `/prompts:kav-location <name>` | bring a place into the story from its photos |
| `/kav-object <name>` | `/prompts:kav-object <name>` | bring a thing that must always look the same (a can, a car, a dress) into the story |
| `/kav-coldread [NN]` | `/prompts:kav-coldread [NN]` | read it back the way a first-time reader does, and say what isn't landing |
| `/kav-panel` | `/prompts:kav-panel` | one scene plus its text into a lettered panel |
| `/kav-review <batch.json>` | `/prompts:kav-review <batch.json>` | open the image review page and apply your picks |
| `/kav-trailer` | `/prompts:kav-trailer` | build the story's swipeable trailer deck |
| `/kav-publish` | `/prompts:kav-publish` | build and link readers for every chapter; where to post them |

In Codex, custom prompts are invoked with the `/prompts:` prefix. In any other agent, ask for the step in plain words ("start a kickoff for my story") — the agent routes it through `AGENTS.md`.

## Requirements

- **Python 3.10+** and the packages in `requirements.txt`
- **Google Chrome or Chromium** — lettering, pages and readers are rendered headless
- **A fal.ai API key** (`FAL_KEY`) — Seedream 4.5, the main image lane
- **A Google AI Studio API key** (`GEMINI_API_KEY`) — Nano Banana Pro, for text in frame, real places and identity-critical mug shots

**Rough image costs** (2026 prices, check the providers): Seedream about $0.04 per image, Nano Banana Pro about $0.15. A character's mug-shot set is about $0.60. A chapter of ~25 panels at 3 takes each, plus rerolls, is roughly 100 images, around $4 on Seedream. Story writing itself costs nothing beyond your agent subscription.

## Folder layout

```
AGENTS.md              operating contract for any agent
kav/commands/          the canonical commands (tool-agnostic markdown)
.claude/skills/        Claude Code adapters (generated)
adapters/codex/        Codex CLI prompts and skills (generated)
docs/                  process, craft, know-how, templates, publishing
tools/                 image generation, review page, lettering, pages, readers, trailer
styles/                shared style packs
stories/<slug>/        your stories: cast, locations, style, storyboard, chapters, package
```

## Sample story

Coming soon.

## License

MIT — see [LICENSE](LICENSE).
