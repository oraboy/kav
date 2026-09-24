---
name: kav-coldread
description: Read a chapter (or the book so far) the way a first-time reader does — with no access to the brief, the storyboard or the pitch — and report what they can reconstruct, what confused them and where they disengaged, without fixing anything. Produces the diff against the chapter card, updates the reader ledger, and proposes one named revision pass. Use when the author types /kav-coldread [NN], says "cold read chapter 3", "is this clear", "read it like a reader", "what's confusing here", or when a chapter's scene list or lettering is done and its mandatory cold read is due.
argument-hint: "[NN | NN-MM | book]"
---

# /kav-coldread [NN] — read it like someone who hasn't read the brief

The method and the rules are in `docs/know-how/cold-read.md`; read it in full before running this. This command is the loop: **diagnose → diff → one named pass → verify.** It never diagnoses and rewrites in the same breath.

Default target: the chapter the author is in. `NN-MM` reads a range in order; `book` reads every published chapter.

## Step 1 — Pick what the reader sees

| The chapter is at | Read |
|---|---|
| lettered or published | `chapters/chNN/panels/pNN-panelK.png`, in page order |
| scene list approved, no images | each scene's description and its **exact** proposed text from `panels/plan.md`, stripped of writer's notes |
| outline only | say so and stop. There is nothing a reader could hold yet. |

For a range or the book, read every chapter's panels in order, in one pass, with no resets in between. Cross-chapter antecedents only show up that way.

## Step 2 — Run it cold (the whole point)

Run the read in a **fresh context** that gets the file paths above and nothing else. Claude Code: the Agent tool, with the allow-list in the prompt. Codex and others: a sub-agent where the tool has one.

The reader **must not** see `story.md`, `storyboard/`, `package/brief.md`, `reader-ledger.md`, `chapter-state.md`, the writer's notes in `plan.md`, or this conversation. Not summarised, not quoted, not "for context".

Where the tool genuinely has no sub-context, say so to the author in one line — *"no fresh context here, so this read is self-administered and weaker"* — then read the panels in order and answer before opening anything else. Never present it as equivalent.

The prompt to the cold reader, in substance:

> You are reading a comic for the first time. You know nothing about it. Read these files in this order and answer in this exact shape. Do not fix anything, do not guess at what was intended, do not be generous. If you cannot tell who someone is, say you cannot tell.
>
> For the questions section: list every question you are still carrying at the end, in your own words, including the ones you *enjoyed* having. Not knowing something is not a complaint, and a book is supposed to leave you asking things. For each one say which panel opened it, and one factual thing: **did you turn back up the page to look for an answer, yes or no?** Report the backtrack honestly even when the question felt pleasant.

Output shape, verbatim (`cold-read.md` §2):

```
## Reconstruction
## Who's who
## Questions I'm carrying     ← question · opened at · did you turn back?
## Where I stopped caring
```

Two things about that third section. **Ask what they are still asking, not what confused them** — a confusion prompt is a complaint prompt, and it hides the questions the book planted on purpose, which look identical from inside the reader's head. And **do not ask the reader to judge the question's worth**; ask only whether they turned back. Curiosity carries a reader forward, confusion sends them backwards up the page. That is behaviour, not opinion, and it is the most reliable single thing a cold reader can give you. You do the classifying, in step 3.

**Language.** Tell the cold reader which language to answer in. It is the one thing about the project it may be told, because it is a fact about the room and not about the story. The reconstruction and the confusions are meta commentary, so they come back in the language the author is talking to you in; every quotation from the book stays **verbatim in the story's language**, never translated — a translated line is a line nobody can check. The four section headers stay English; they are schema labels the rest of Kav reads.

Save a single-chapter read to `chapters/chNN/cold-reads/<date>-<stage>.md` (`stage` = `scenes` or `pages`). A range or `book` read is one continuous pass across chapters and belongs to the story, not to any chapter: save it to `stories/<slug>/cold-reads/<date>-<range>.md` (`ch02-ch04`, `book`) and link it from each covered chapter's `chapter-state.md`.

Record how isolation was achieved at the top of the file, and what the reader could see without being told — the story slug sits in every path and is part of the book's presentation, not a leak, but say what it gave away so the result can be read honestly.

## Step 3 — The diff, and the ledger

Now, with the card open, do two things:

1. **Put every question on the ladder** (`cold-read.md` §3, axis 1): rung 1 with the protagonist, rung 2 about the world, rung 3 about the protagonist, rung 4 about the page. The rung is set by *whose* understanding is missing. A backtracked question behaves like rung 4 whatever it is nominally about; a question carried forward behaves like rung 2. Anything already listed under **Declared unknowns** in `story.md` drops out here and is not reported.
2. **Carry the register forward** (axis 2). Add new questions to the **Open questions** table in `reader-ledger.md` with the chapter that opened them; close the ones this chapter answered; age the rest. Rungs 1 and 2 open three chapters or more get raised once as a composition question. Rungs 3 and 4 open past the chapter that raised them are compounding and get raised every time.
3. **Diff** the reconstruction against `storyboard/chNN.md`. Axis 3: an author question, not a defect. Say explicitly which diff items appear in no question and no disengagement, because those are choices, not repairs.
4. **Update the facts table in `reader-ledger.md`.** Every *Who's who* row the reader couldn't fill is an unpaid fact: mark it OPEN with the panel that teased it. Every row the reader filled correctly gets its Paid panel recorded. A ledger row nobody teased and nobody paid is a fact the plot is silently assuming. OPEN is a neutral state; a book with no OPEN rows has no questions in it.

## Step 4 — Report (GATE)

Open with the progress header. Then, short:

> **A reader got:** <the reconstruction, 3–5 lines, verbatim enough to sting>
>
> **Broken (rung 4 · about the page):** <who spoke, where we are, what just happened — fix these, no discussion needed>
> **Costly (rung 3 · about the protagonist):** <locked out of the one thing they came for, and how long it has been open>
> **Pulling (rungs 1–2 · with the protagonist, about the world):** <what they're still asking and carried forward — named so you can protect it, not fix it. Flag any open three chapters or more.>
> **Against the card:** <the diff — say which items no reader noticed, because those are yours to keep or spend>
>
> **I'd run one pass: `<goal>`** — <the assignment in one line> · <what it costs>
> Or: <the one other pass worth considering, and why I didn't pick it>
> Or: **nothing.** Say so when that's the answer.

Name defaults and choices (`cold-read.md` §8). **Then stop.**

The author decides. A good story leaves the reader asking for a long time; it just doesn't leave them confused for a long time, and the two look identical until you know which rung the question sits on. When the read comes back with a clean reconstruction and nothing above rung 2, the correct report is *"a reader follows this and is still carrying three questions"*, and the correct recommendation is none.

## Step 5 — One pass, then verify

On the author's yes, run **exactly one** goal from the taxonomy (`cold-read.md` §4). Not two. Not "and while I'm in there".

- Fix at the altitude the bug lives at. A beat that can't be written without explaining it is a scene-list problem; a chapter question that doesn't follow is a storyboard problem. Escalate rather than papering over (`cold-read.md` §6). Say which altitude you're working at before you touch a file.
- Adding a beat after images exist marks the affected panels stale, and the new beat needs its own panels. Say what that costs in images before the author agrees.
- Text the author has written stays verbatim. A revision pass rewrites your proposals, never their lines.

Then **verify with a second cold read**, same isolation, and do not tell the reader what was fixed. Compare the new Confusions with the old. Report: gone, still there, or new.

If the pass didn't land, say so plainly and propose either a second attempt at the same goal or an escalation. Never declare a goal met because the work was done.

## Hard rules

- **One call never both diagnoses and rewrites.** Step 2 produces no edits; step 5 reads no diagnosis it wrote in the same breath.
- **The cold reader is context-starved or it is not a cold read.** If isolation failed, say so instead of reporting the result as clean.
- The verifier is never told the assignment.
- **A gap is a hook until the reader turns back.** Report questions; never quietly close one, and never recommend closing one the reader carried forward. Over-explaining is this command's own failure mode and it produces a duller book than the one it was pointed at.
- **The rung is set by whose understanding is missing.** Confusion the reader shares with the protagonist is the book working. Confusion *about* the protagonist is the expensive kind, and it has to be declared in `story.md` to stop being reported.
- **The diff against the card is an author question, not a defect.** Items no reader noticed get reported, never repaired on your initiative.
- No craft vocabulary in the report. "A reader can't tell who David is" — not "the antecedent is unresolved".
- Persist every read under `chapters/chNN/cold-reads/`; update the ledger and `chapter-state.md` immediately.
