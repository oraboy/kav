# Kav — artifact templates

One template per story artifact. `/kav-kickoff` and `/kav-chapter` instantiate these under `stories/<slug>/`. Placeholders are in `<angle brackets>`; cut any section that is genuinely not applicable rather than leaving it empty.

---

## kickoff-state.md

```markdown
# <Story name> — Kickoff State
slug: <slug> · format: <N> chapters × ~<P> pages · panel format: <instagram-master | ...> · story language: <he/en/...> · updated: <date>

## Progress
*(docs/know-how/progress.md — read first, written last)*
Stage: <Planning | ChN · outline|picks|lettering|review|publish | Done> · <n> of <N> chapters published
Planning: <in progress | locked <date> · brief published <url>>
Chapters: <ch01 published · ch02 picks · ch03–06 not started>
Next gate: <the decision the author owes>

## Publishing
- WIP surface: <ChatGPT Sites | Claude artifact | static host | none yet>
- URL: <...> · Access: <owner-only | shared | public> · Deployed: <version/date>
- Included chapters: <ch01–chNN> · Package: `stories/<slug>/site/dist/`
- Stale when a reader, the brief, a chapter title, chapter art or a nav link changes

## Flight plan
<the block order the author agreed to>

| Block | Status | Notes / open questions |
|---|---|---|
| concept | empty · in-progress · locked · stale | |
| cast | | |
| locations | | |
| objects | | |
| style | | |
| visual lock | | |
| pitch (story.md) | | |
| storyboard | see per-chapter table | |
| package | | |

## Chapters
| Ch | Card (storyboard) | Written (chapters/) | Stale — why |
|---|---|---|---|
| 01 | empty | — | |

## Links
- Trailer deck: <path or URL>
- Readers: <per chapter, when published>

## Consent
- <date> · personal photos supplied for <characters>, for this story, generated through <provider>. Re-ask only on a scope change: publishing outside the story, a new provider, reuse in another story.

## Open questions
- <question — who owes the answer>

## Change log
- <date> · <what changed> · <what it made stale, if anything>

## Process learnings
*What this story taught us about working in Kav — not story canon. Candidates for the repo's commands and docs.*
- <date> · <what went wrong or worked> · <the rule it suggests>
```

---

## cast/<name>.md — background class (short DNA)

For characters who recur visually but drive nothing: a chorus, the regulars, a fixture. **A complete artifact, not a stub.**

```markdown
# <NAME> — background
*Status: <draft | locked> <date>.*
**Character class: background.** Short DNA by design — no Desires / Skills / Shadows / Tendencies / Relationships / Story state / Voice.

**What they are:** *(the author's own line, verbatim)*
> <one line>

**Appearance (ref canon):** <what they look like; list the distinct types if it's a group> · reference set: `cast/images/<...>`

**Where they appear:** <a standing instruction for panels — where they turn up and how often — not an event>
```

---

## cast/<name>.md — principal class

```markdown
# <NAME> — <story-slug> DNA
Seeded from: <author's file / photos / interview> on <date>
**Character class: principal.**

**Bio:** <two lines, narrator voice>
**Bio (self-written):** <two lines, their own voice — how they'd introduce themselves>
**Appearance (ref canon):** <1–2 sentences> · reference set: `cast/<name>/`
**Hard traits:** <the few things that carry identity and must never drift — eye colour, a scar, an ear shape. Canon: also in briefs.json, and fixed across the whole approved set when one changes. At least one must survive a costume change: a signature garment is not an identity>
**Wardrobe:** <what they wear by default, named in panel lines> · per-chapter overrides: `| ch | what changed | why |`
**References:** active `cast/<name>/source*` · excluded `cast/<name>/_excluded/<file>` — <why it was parked> · <target age when a reference is from another age>
**Identity:** <Passion/True Calling | Profession | Character>

**Desires:** · **Skills:** · **Tendencies:** · **Shadows:** · **Don't:** (hard constraints)
<bulleted — this governs behaviour; the drama formula pushes them out of Tendencies toward Desires through a Shadow, never across a Don't>

**Relationships:**
| With | History (one line) | Current charge | Carried unsaid | Who knows what |
|---|---|---|---|---|

**Story state** — *the ONLY home for story-specific facts (situation entering the story, active secrets).*
- <fact>

**Voice:** <how they speak in balloons — register, tics, what they never say>
**Background:** <fixed facts>
```

---

## cast/<name>.md — principal class, sketch depth

For principals the author wants to breeze through: a one-liner, a look, 2–3 answers. Lines Kav drafted from those answers carry `(draft)`; PITCH presses them first. Deepens into the full principal template on request.

```markdown
# <NAME> — <story-slug> sketch
*Status: <draft | locked> <date>.*
**Character class: principal · depth: sketch.** Drafted lines are marked (draft); deepen to full DNA any time.

**Who they are:** *(the author's one-liner, verbatim)*
> <one line>

**Appearance (ref canon):** <the author's written look, or what the images show> · reference set: `cast/<name>/` <or: images still to come — needed before VISUAL LOCK>
**Hard traits:** <anything that must never drift; at least one that survives a costume change>
**Wardrobe:** <what they wear by default, named in panel lines>

**Desires:** <1–2 bullets>
**Tendencies:** <1–2 bullets>
**Shadows:** <1 bullet>
**Don't:** <1 bullet>
**Voice:** <one line>

**Story state:** <only if the author gave one>
```

---

## locations/<name>.md

```markdown
# <Location name>
**What it is:** · **Whose turf:** <every location has an owner; power tilts toward them there>
**Dramatic affordances:** <what scenes it stages well — chance encounter / private confession / public collision / the defining event>
**Visual notes:** <light, texture, best time of day; generation guidance>
**Reference images:** `locations/<name>/...` <must include every surface panels will need — ceiling, floor, door>
**History:** <what has happened here in the story; append as chapters are written>
```

---

## objects/<name>.md

```markdown
# <Object name>
**What it is:** <one line>
**Why it's an object, not scenery:** <must stay identical / carries lettering or design>
**Binds on:** <object_words triggers>
**Used in:** <panels>
```

---

## story.md (concept + pitch → the contract)

```markdown
# <Story name> (<slug>)

## Concept
1. **Pitch line** — one sentence
2. **Synopsis** — a paragraph or two
3. **Format** — chapters × pages · panel format · story language · telling register · POV rules
4. **World & era** — where/when · the clock

## Pitch  <!-- the locked reading -->
5. **Shapes** — the main character's fortune curve, plus per-strand curves where earned, staggered
6. **Story I/O** — Intent | Obstacle for the main character and every load-bearing strand, pressed
7. **Theme** — the one question every chapter gets checked against
8. **Feel line** — what happens · what we feel · what we learn
9. **Topology** — which structure and why; braid mechanisms and cast roles for ensembles
10. **Key story events** — the few load-bearing events; each a set where intents collide
11. **O/I grid** — Intent | Obstacle | Curve | Relationship line per character
12. **Core drama** — the collisions, which levers fire
13. **Open forks** — decisions deferred to the writing
```

---

## reader-ledger.md

What the reader has actually been told, and where. Seeded at STORYBOARD from the locked pitch (every name and pre-story fact the arc leans on, all rows OPEN), filled chapter by chapter, checked by every cold read. Rules and gap tolerances: `docs/know-how/cold-read.md`.

```markdown
# <Story name> — Reader Ledger
*What a reader knows from the panels alone. The brief is not payment; the blurb is not payment.*
updated: <date>

| Fact | Teased | Paid | Gap | How it's paid |
|---|---|---|---|---|
| <who a named character is> | <chNN sKpN> | <chNN sKpN> | same scene / same chapter / <N> chapters / **OPEN** | <the panel that does it> |
| <a pre-story event the plot needs> | | | **OPEN** | |
| <a rule of the world> | | | | |
| <a relationship a beat leans on> | | | | |

## Deliberate withholds
*Gaps the author has decided to keep. Not bugs; cold reads stop reporting them.*
- <fact> — withheld until <chNN>, decided <date>
```

---

## storyboard/chNN.md (the chapter card)

```markdown
# Ch <NN> — <title>
**Position:** <N of M> · **Status:** <draft | locked | stale>
**Chapter question:** <the central question this chapter answers>
**Chapter I/O:** <as a unit: X intends to Y, but Z> — <which lever fires>

**Synopsis:** <one paragraph — what happens, whose chapter it is>
**Writer's note:** <how the machinery moves here — which curve dives or climbs, which story I/O advances, what it sets up>
**Layout:** <pages / strips per the declared format · any override + why>

## Beats (per active character)
### <CHARACTER>
- **I/O this chapter:** <intends to X, but Y>
- Beats: <each passes the one-sentence test>

## Guns
| Planted here | Pays off (ch) | · | Paid off here | Planted (ch) |
|---|---|---|---|---|

**Concept visual:** `storyboard/chNN-concept.png` — <one line>
**Checks:** theme ✓/✗ · feel line ✓/✗ · curve placement ✓/✗
```

---

## style/style.md

```markdown
# <Story name> — Visual Style
**The look:** <one line>
**Register decision:** <photo-real | painted | ink noir | ...>
**Pack:** `styles/<pack>/` · **medium.txt:** "<the line>"
**References / moodboard:** `style/moodboard/` <one line each on what to take from it>
**Palette & composition rules:** <tool-agnostic>
**Backend block:** <explore lane, publish lane, aspect ratios per panel shape>
**Lettering theme:** <caption fill/colour/font · balloon fill/colour/font · shout burst>

## Per-chapter impositions
| Ch | Imposition | Why |
|---|---|---|

## Lock log
- <date> · pack baked · lanes tested · samples in `style/samples/`
```

---

## chapters/chNN/chapter-state.md

```markdown
# Ch <NN> — Chapter State
updated: <date>

| Stage | Status | Notes |
|---|---|---|
| outline | empty · in-progress · locked · stale | |
| scenes | | |
| cold read · scenes | not run · clean · <n> confusions · passed <goal> | `cold-reads/<date>-scenes.md` |
| panels (images) | | |
| lettering | | |
| cold read · pages | not run · clean · <n> confusions · passed <goal> | `cold-reads/<date>-pages.md` |
| pages + readers | | |

## Batches
| Batch | Scenes | Review status |
|---|---|---|

## Approvals
*A silent yes is still a yes. This is only so a later cold read knows where to look first.*
| Gate | Approved | How | Defaults that rode along |
|---|---|---|---|
| <stage> | <date> | considered · **on inertia** (no comment) | <what was chosen because it was the obvious option> |

## Open questions
## Change log
```

---

## package/brief.md

Human-readable, co-author framing. The story in a page: theme, feel line, the cast and what each wants, the key events (gestured at, not spoiled), the look. Assembled last, from locked artifacts only. `package/` also holds the concept visuals, a storyboard index and `trailer.json`.

---

## pitch-inbox.md

```markdown
# <Story name> — Pitch Inbox
Ideas parked during collection, not yet agreed. Raised together at PITCH. Remove one with `/kav-plot-note remove N00N`.

- **<id> · <type>** (<date>): <note> `[not-yet-agreed]`
```
