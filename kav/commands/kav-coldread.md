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

Output shape, verbatim (`cold-read.md` §2):

```
## Reconstruction
## Who's who
## Confusions
## Where I stopped caring
```

**Language.** Tell the cold reader which language to answer in. It is the one thing about the project it may be told, because it is a fact about the room and not about the story. The reconstruction and the confusions are meta commentary, so they come back in the language the author is talking to you in; every quotation from the book stays **verbatim in the story's language**, never translated — a translated line is a line nobody can check. The four section headers stay English; they are schema labels the rest of Kav reads.

Save it to `chapters/chNN/cold-reads/<date>-<stage>.md` (`stage` = `scenes` or `pages`).

## Step 3 — The diff, and the ledger

Now, with the card open, do two things:

1. **Diff** the reconstruction against `storyboard/chNN.md`. Each disagreement is a bug of one kind: missing antecedent, missing stake, missing causality (`cold-read.md` §3).
2. **Update `stories/<slug>/reader-ledger.md`.** Every *Who's who* row the reader couldn't fill is an unpaid fact: mark it OPEN with the panel that teased it. Every row the reader filled correctly gets its Paid panel recorded. A ledger row nobody teased and nobody paid is a fact the plot is silently assuming.

## Step 4 — Report (GATE)

Open with the progress header. Then, short:

> **A reader got:** <the reconstruction, 3–5 lines, verbatim enough to sting>
> **They couldn't tell:** <the confusions, as a list, panel ids>
> **Against the card, that means:** <the diff in a line or two>
> **Unpaid in the ledger:** <OPEN rows this chapter was meant to pay>
>
> **I'd run one pass: `<goal>`** — <the assignment in one line> · <what it costs>
> Or: <the one other pass worth considering, and why I didn't pick it>

Name defaults and choices (`cold-read.md` §8). **Then stop.** The author decides whether to run a pass, which one, and whether a gap is deliberate — a chapter that withholds on purpose is a good chapter, and only the author knows which it is.

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
- The author decides whether a gap is a bug or a hook. Report gaps; never quietly close one.
- No craft vocabulary in the report. "A reader can't tell who David is" — not "the antecedent is unresolved".
- Persist every read under `chapters/chNN/cold-reads/`; update the ledger and `chapter-state.md` immediately.
