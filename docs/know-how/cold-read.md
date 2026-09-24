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
| Never paid, reader still leaning in | **the book working.** Move it to Deliberate withholds and stop reporting it. |
| Never paid, reader disengaged | the only version that is a bug. See §3. |

The last two rows are the same ledger state and opposite verdicts, so the ledger alone cannot tell them apart. The cold read can.

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

## Confusions
<panel id> — <what is unclear, quoting the line> — **want to know** | **need to know**

## Where I stopped caring
<panel id> — <why>
```

**Every confusion is marked want-to-know or need-to-know, and that mark is the whole point of the section.**

- **Want to know** — I don't know this, and I'm still reading. It's a question the book put in me. *"I don't know what happened between her and Oren."*
- **Need to know** — I don't know this, and I can't follow the page without it. *"I can't tell which of these people said that."*

A reader cannot always be trusted on the boundary, so ask for the mark rather than inferring it, and let the disengagement section arbitrate: a want-to-know that shows up again under *Where I stopped caring* was really a need-to-know.

**No fixes.** The cold read never proposes a rewrite, never edits a line, never explains what was probably meant. One call does not both diagnose and repair: generation drowns critique every time, and you get a polished chapter with the same hole in it.

---

## 3 · Three signals, and only one of them is a bug list

A cold read produces three different things. Keeping them apart is the difference between a tool that sharpens a book and a tool that sands it flat.

**Signal 1 · Confusion plus disengagement → a bug.** The reader didn't know something and stopped caring. The intersection is the test, not either column alone. Fix it, at the altitude it lives at.

**Signal 2 · Confusion without disengagement → the book working.** The reader didn't know something and kept reading. This is a hook, and hooks are the product. Move the row to Deliberate withholds and stop reporting it. **Never fix one of these.** Over-explaining is the failure mode of this very document: an agent that closes every open question returns a chapter where a character announces the premise in the first balloon, which is duller than any gap and cannot be repaired by a later pass.

**Signal 3 · The diff against the card → an author question, never a bug.** Put the reconstruction beside `storyboard/chNN.md`. Where they disagree, the card says what was designed and the read says what shipped. That gap is real and worth knowing, and it is **not** evidence that anything is wrong, because a beat can go missing without any reader ever noticing its absence. Often the author will look at the diff and keep the page.

The crucial asymmetry: signals 1 and 2 are about the reader's experience, signal 3 is about authorial intent. **A diff item that appears in no confusion and no disengagement is not a reader problem at all.** Report it plainly, say which it is, and let the author decide. Proposing a repair for a signal-3 item as if it were a defect is the most likely way this tool gets it wrong.

When you do classify a bug, it is one of:

- **Missing antecedent** — the reader can't resolve a name, a place, a task, a pronoun, *and* it cost them the page. Find where it should land and write the beat.
- **Missing stake** — the reader follows the events and doesn't know why they matter. Fix at the beat, not the caption.
- **Missing causality** — the reader can retell it as "and then, and then". Escalate to the outline.

Show the author the three signals separately, not the two documents. It's short and it needs no craft vocabulary.

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
