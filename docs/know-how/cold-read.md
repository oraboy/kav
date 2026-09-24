# Cold reads — what the reader actually gets

`story-craft.md` Check 6 already says a chapter must be legible to someone opening it cold. Nothing enforced it, because every agent that writes a scene can see `story.md`, the chapter card and the brief. **A writer who can see the brief writes for a reader who can see the brief.** The reader can't. They get panels and balloons, in order, and nothing else.

This is not a style failure and it does not look like one. *"Finish it."* and *"I won't send you out there"* read as confident, compressed comics dialogue. They are unparseable if the reader was never told what *it* is or where *out there* is. Compression only works over information the reader already holds — laconic writing over missing antecedents is just noise that sounds like craft.

Two mechanisms catch it: a **ledger** that tracks what the reader knows, and a **cold read** by something that hasn't seen the brief.

**Read the rest of this document against its opposite failure.** Withholding is most of what makes a story worth continuing. A reader who is unsure and still thinking is a reader the book has, and half of what looks like a gap is the hook doing its job. The instinct these two mechanisms create — close the gap, name the thing, make it clear — is wrong more often than it is right, and applied bluntly it returns a chapter that opens with a character announcing the premise out loud. That is duller than any confusion and no later pass repairs it. The question is never *does the reader know this*. It is **does not knowing it pull them forward or push them out.**

---

## 1 · The reader ledger → `stories/<slug>/reader-ledger.md`

One row per fact the plot leans on, tracking where the reader can first *know* it.

```markdown
| Fact | Teased | Paid | Gap | How it's paid |
|---|---|---|---|---|
| David is the boy Ruth loved | ch01 s8p3 | ch01 s9p1 | 1 panel | flashback: the two of them at the wall, named |
| David vanished at sea | ch01 s8p3 | ch02 s1p2 | 1 chapter | Imi says it to Babz in front of Ruth |
| Ruth and David had a private light signal | ch01 s7p1 | — | OPEN | — |
```

What gets a row: every named character (*who is this*), every pre-story event the plot depends on, every rule of the world the reader has to accept, every relationship a beat leans on, every object whose meaning is not its appearance.

**An unpaid fact is not a bug.** Withholding is most of what makes a story worth continuing: a reader who is unsure and still thinking is a reader the book has. Spelling everything out is its own failure, and a worse one, because it is boring and boring is unfixable by a later pass.

So the ledger does not grade gaps. **It records them so that the author can see, in one table, what the reader is carrying unresolved.** That is a composition tool, not a defect list. A book with no OPEN rows has no questions in it.

| Gap | What it means |
|---|---|
| Paid in the same scene | plain exposition. Fine, and cheap. Nothing to decide. |
| Paid later | a hook with a landing. Note which chapter lands it. |
| Never paid, reader carried it forward | **the book working.** Declare it and stop reporting it. |
| Never paid, reader turned back | the only version that is a bug. See §3. |

The last two rows are the same ledger state and opposite verdicts, so the ledger alone cannot tell them apart. The cold read can.

**The ledger's second table is the Open questions register** — what the reader is *asking*, as opposed to what they have been *told*. It carries forward chapter to chapter, because the age of a question is half of what it means (§3, axis 2).

**Paid means on the page.** A panel, a line, a flashback the reader can read with no other document open. The blurb is not payment. The chapter card is not payment. "It's clear from context" is not payment — if it were, the cold read would have got it.

Seeded at STORYBOARD from the locked pitch (every name and pre-story fact the arc depends on, all rows OPEN), then filled chapter by chapter. Every chapter's scene-list gate updates it. A chapter never locks with an OPEN row the author hasn't seen.

---

## 2 · The cold read

**Context isolation is the entire mechanism.** A cold read done by something that has the story in its head is theatre.

**Reads, in reading order, and nothing else:**
- After images and lettering: the rendered panels, `chapters/chNN/panels/pNN-panelK.png`.
- Before images exist: the scene list's per-scene description and its exact proposed text, and nothing from the writer's notes.
- Any earlier chapter's rendered panels, when the read covers more than one chapter.

**Must not read:** `story.md`, `storyboard/`, `package/brief.md`, `reader-ledger.md`, `chapter-state.md`, the writer's notes in `plan.md`, or this conversation.

**Run it in a fresh context.** Claude Code: the Agent tool with an explicit allow-list of paths. Codex and others: a sub-agent where the tool has one. Where none exists, say so plainly to the author in one line, then do the next best thing — read the panels in order and answer before consulting anything else. A self-administered cold read is weaker evidence. Never present it as equivalent.

**Output, verbatim shape:**

```
## Reconstruction
<what happened, 5-10 lines, in a reader's own words>

## Who's who
<every named entity, and what the reader can actually say about it —
 "David: a name Ruth says. No idea who he is." is a valid and useful row>

## Questions I'm carrying
<the question, in the reader's own words> — opened at <panel id> — <did you turn back? yes/no>

## Where I stopped caring
<panel id> — <why>
```

**Ask what they are still asking, not what confused them.** "What confused you" is a complaint prompt: it biases toward fault and it hides the good questions, which look identical from inside the reader's head. "What are you still carrying at the end of this chapter" gets the same list, plus the ones the book put there on purpose.

**Do not ask the reader to judge the questions.** Readers are poor at introspecting on their own engagement, and a reader asked whether they *needed* to know something will do the editor's job badly. Ask instead for one observable fact: **did you turn back?** Curiosity carries a reader forward; confusion sends them backwards up the page looking for the bit they must have missed. That backtrack is behaviour, not opinion, and it is the single most reliable thing a cold reader can report.

Classification happens on your side, against §3. Never outsource it.

**No fixes.** The cold read never proposes a rewrite, never edits a line, never explains what was probably meant. One call does not both diagnose and repair: generation drowns critique every time, and you get a polished chapter with the same hole in it.

---

## 3 · Sorting the questions: what it's about, and how long it's been open

Every question the reader is carrying gets two marks. Neither alone decides anything.

### Axis 1 — what the question is about

A ladder, from free to never acceptable. **The rung is set by whose understanding is missing, not by how big the question is.**

| Rung | The reader is asking | Cost |
|---|---|---|
| **1 · With the protagonist** | something the protagonist doesn't understand either | **Free, and usually the point.** In a limited-POV book this *is* the reading experience. *ברקו doesn't follow what the adults are saying, so neither do I.* |
| **2 · About the world** | what that place is, who that person is, what happens next | **The engine.** This is suspense. A book with none of these has nothing pulling the reader through. |
| **3 · About the protagonist** | why he said that, what she just did, what he wants | **Expensive.** The reader is locked out of the one thing they came for. Tolerable in small doses and only on purpose. |
| **4 · About the page** | who spoke, where we are, what physically just happened | **Always a bug.** Craft, not story. Nobody ever enjoyed not knowing who was talking. |

Rung 4 is fixed, always, without asking. Rung 1 is left alone, always. Rungs 2 and 3 are where the author's judgement actually lives, and rung 3 is the one to raise out loud, because a reader locked out of the protagonist usually stops reading before they can tell you why.

**The backtrack overrides the rung.** A question the reader turned back to re-read for is behaving like rung 4 whatever it is nominally about. A question they carried forward is behaving like rung 2.

### Axis 2 — how long it has been open

Carry every open question forward from chapter to chapter in the **Open questions** register (`reader-ledger.md`). Age is a signal on its own, and it cuts in opposite directions per rung:

- **Rungs 1 and 2:** duration is composition. A question open since chapter 1 may be the spine of the book. Surface it once it has been open for three chapters — *"the reader has been asking this since ch01, still deliberate?"* — and otherwise leave it.
- **Rungs 3 and 4:** duration is rot. These compound. A reader who has not understood the protagonist for two chapters is not intrigued, they are gone, and every later beat lands on a foundation they don't have.

A good story leaves the reader asking for a long time. It does not leave them **confused** for a long time, and the register is what makes the difference visible instead of arguable.

### Axis 3, which is not about the reader at all

**The diff against the card is an author question, never a defect.** Put the reconstruction beside `storyboard/chNN.md`. Where they disagree, the card says what was designed and the read says what shipped. That is real and worth knowing, and it is *not* evidence anything is wrong: a beat can go missing without a single reader noticing its absence. **A diff item that appears in no question and no disengagement is not a reader problem.** Report it, say plainly that no reader flagged it, and let the author keep it or spend on it. Proposing a repair for one of these as if it were a defect is the most likely way this tool damages a book.

### Declared confusion

A story may deliberately keep the reader in the dark about a named subject, including at rung 3. That is a legitimate and sometimes excellent choice, and it is **a `story.md` decision, not a per-chapter excuse.** Declared in CONCEPT beside the telling register and the POV rules:

> **Declared unknowns:** the reader never learns why אורן and אפרת fell out (Part 1). Rung 1 by design — ברקו cannot know, so neither can the reader.

Once declared, cold reads stop reporting it. Undeclared, a rung-3 question is raised every time, however confident anyone is that it was intentional. The difference between a withhold and an oversight is whether it was written down before the chapter was drawn.

### When it is a bug, it is one of

- **Missing antecedent** — the reader can't resolve a name, a place, a task, a pronoun, *and* it cost them the page.
- **Missing stake** — the reader follows the events and doesn't know why they matter. Fix at the beat, not the caption.
- **Missing causality** — the reader can retell it as "and then, and then". Escalate to the outline.

---

## 4 · One fix per pass

"Improve this chapter" returns mush. Each revision pass takes exactly one goal from the taxonomy, with its own acceptance check.

| Goal | The assignment | Passes when |
|---|---|---|
| **antecedents** | Pay only the rows where the reader was **lost**, never every OPEN row. Add beats; don't add explanation to existing balloons. | the confusion is gone *and* no new row appeared under *Where I stopped caring* |
| **show, don't tell** | No caption or balloon in this chapter states what anyone feels. Emotion reaches the reader through action, gesture, framing or what a character does instead. | no *Confusions* row about motive, and the removed captions aren't missed |
| **causal chaining** | Every beat connects to the last with *therefore* or *but*, never *and then*. | the reconstruction retells it with therefores |
| **stakes** | The want and the cost are visible in what characters do, in this chapter, without a caption carrying either. | a cold reader can say what she loses if she fails |
| **pacing** | No two scenes run the same loop. Cut or merge the second. | the reconstruction doesn't repeat itself |
| **voice** | Each principal's balloons match their DNA Voice line with the tails cropped off. | a cold reader can attribute unlabelled lines |

**Therefore/but is sharp and narrow.** It catches a chapter that repeats a loop or drifts, and it will happily pass a chapter whose causality is perfect and whose nouns mean nothing to the reader. Run it alongside the antecedent check, never instead of it.

---

## 5 · Verification is a second cold read

The thing that checks a fix must not be the thing that made it, and must not be told what was being fixed. A verifier that knows the assignment grades its own homework and always passes.

Re-run the cold read, same isolation, same output shape. Compare the new *Confusions* against the old. The pass succeeded when the targeted rows are gone and no new ones appeared.

---

## 6 · Escalation — errors travel upstream

Fixing a structural problem at the wrong altitude is how a chapter gets nicer and stays broken. No lettering pass saves a weak outline.

| Found at | Kind of problem | Goes back to |
|---|---|---|
| lettering | the balloon can't be written without explaining | the scene list — the beat is missing |
| scene list | a beat only connects with *and then* | the outline |
| outline | the chapter question doesn't follow from the last chapter | `/kav-kickoff` STORYBOARD |
| any stage | a contradiction with `story.md` | `/kav-kickoff` PITCH, logged |

Kick it up. Never paper over it at the stage that found it.

---

## 7 · Where cold reads run

Two are mandatory per chapter, placed where the cost of being wrong changes by an order of magnitude.

| When | Reads | Why here |
|---|---|---|
| **After the scene list, before any image is generated** | the scene descriptions + exact proposed text | catches it before a hundred images exist. The cheapest gate in the process. |
| **After lettering, before the author's read-through** | the rendered lettered panels | catches what survived contact with images and picks |
| After chapter 1 locks *(also mandatory)* | ch01's rendered panels alone | ch01 owes almost every antecedent in the book. If it's opaque, nothing downstream recovers. |
| On request, `/kav-coldread` | whatever the author points at | |

---

## 8 · Gates for an author who approves by default

Assume the author will say yes without reading. Design the gate so that a yes is still informed.

- **Present decisions, not documents.** Under the content, name the two or three places where it could genuinely have gone another way, each with its trade-off in one line. A tired reviewer can react to a choice; nobody reacts to six pages.
- **Name what is a default.** Anything you chose because it was the obvious option gets marked. *"Ch3 opens on the radio room because ch2 closed there — no other reason."*
- **A silent yes is recorded as a silent yes.** When the author approves with no comment, write it into `chapter-state.md` as passed-on-inertia, listing which parts were defaults. It stays approved; the note just means a later cold read knows where to look first.
- **Lead with the diff.** One decision-free item at every gate: the cold read's reconstruction. If it doesn't match what the author meant, they'll know in ten seconds, and being diligent is not a prerequisite.
