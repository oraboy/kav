# The telling grammar — how the story reaches the reader

`intention-obstacle.md` says why things happen; `cast-dna.md` says who they happen to. This document is about **how it is told** on the page: whose voice carries which text, and how the page itself characterises.

## 1 · Two voices, never blurred

Every graphic novel made with Kav runs on two registers:

**A. The character's voice** — speech balloons, thought bubbles, sound bursts. In-world, subjective, present-tense, possibly wrong. A character knows only their own life.

**B. The narrator's voice** — captions. The storyteller's hand: it can frame, compress time, name what no single character can see. Calm and knowing.

**Caption = narrator register. Balloon = character register.** A caption that starts talking like a character, or a balloon that starts explaining the plot, is the most common way a page goes soft.

## 2 · Declare the telling register at kickoff

How does interiority reach the reader? Pick one explicitly and write it in `story.md` CONCEPT:

| Register | How it works | Good for |
|---|---|---|
| **Thought balloons** | The protagonist's inner voice in thought bubbles; captions are a third-person narrator | Intimate, comic, character-led stories |
| **Caption voice** | The protagonist narrates in first person in captions; balloons only for speech heard in the panel | Memoir, noir, retrospective tellings |
| **Pure observation** | No interiority in text; faces and staging carry it | Quiet, visual, ambiguous stories |

Kav's lettering defaults (third person about the protagonist = caption; protagonist thinking = thought bubble; other characters speak little; sounds = bursts) implement the first register. A story that declares another register overrides them in `story.md`.

## 3 · POV rules

Decide what the reader knows versus what the protagonist knows, and write it down. Useful patterns:

- **Limited POV:** everything is what the protagonist sees and understands. Others speak in short balloons with a small vocabulary, because that's what the protagonist catches.
- **The readable misread:** the reader understands a balloon the protagonist gets wrong. A cheap, strong source of dramatic irony.
- **Non-speaking characters** (animals, infants, the silent type) never get speech balloons; sounds are bursts, feelings are faces or thoughts.

### What the reader has actually been given

POV decides what the reader is *allowed* to know. This decides what they have *been told*, and it is the easier one to get wrong, because everyone writing the book can see the brief and the reader can't.

Before a line ships, resolve every noun in it against the panels alone. *"Finish it."* is a fine line if the reader saw what was started. *"I won't send you out there"* is a fine line if the reader knows where out there is and why anyone would go. Neither is a fine line otherwise, and neither *sounds* wrong: compressed dialogue over missing antecedents has the exact surface texture of good comics writing. That's what makes it hard to catch from the inside.

**The tease is the hook, and the hook is the product.** Ending a chapter on a name nobody has explained is a strong move, and it stays strong for as long as the reader keeps turning pages on it. Some of those names should never be explained at all. Track both ends in `stories/<slug>/reader-ledger.md` so you know what the reader is carrying; `docs/know-how/cold-read.md` §3 is what tells a hook from a hole, and the test is not whether the reader knows, it is whether not knowing pulls them forward or pushes them out.

A comic's bandwidth is narrow, so exposition delivered plainly is not the sin it is in prose. A clumsy line that lands a fact beats an elegant one that assumes it. Fix the clumsiness on a later pass; a reader who is lost has already closed the chapter.

## 4 · Form is characterisation

The *shape* of a character's text characterises before the words do. Give each principal a Voice line in their DNA and let it govern:

| A character who… | …might speak in |
|---|---|
| avoids feelings | fragments; nouns and places, no verbs of feeling |
| performs confidence | exclamations, never questions |
| is anxious | questions, trailing ellipses |
| holds power | one sentence, always exactly one |

Keep it consistent: a reader should be able to tell who's talking with the tails cropped off.

## 5 · Page rules that serve the telling

- **One drawable moment per panel.** A panel is a frozen instant, not a summary.
- **Balloons are short** — two tight lines. Longer means split, or it belongs in a caption.
- **A balloon never ends on a period.** Speech isn't prose.
- **Reading order is vertical order** within a panel.
- **Silence is a beat.** A panel with no text, after a noisy one, is a pause the reader feels.
- **Cliffs at strip and page boundaries.** Place scene breaks and turns where the reader's eye (or thumb) has to move.
- **Stakes on the page.** Captions may frame; they never carry the want or the obstacle alone.
