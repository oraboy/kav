# Character DNA — the model

A character's DNA is a set of **instructions to the co-writer**, not a prose bio. It says who the character is anywhere, in any story; the story-specific situation lives in one clearly marked section. Kickoff writes one file per character at `stories/<slug>/cast/<name>.md` (template in `docs/templates.md`).

## The schema

| Field | What it holds |
|---|---|
| **Bio** | Two lines in narrator voice |
| **Bio (self-written)** | Two lines in the character's own voice — how they'd introduce themselves |
| **Appearance (ref canon)** | 1–2 sentences + the path to the reference set. The images are canon; the sentence describes them |
| **Hard traits** | The few details that carry identity and must never drift (eye colour, a scar, an ear shape). Mirrored in `briefs.json`; when one changes, the whole approved reference set is corrected, never a single shot |
| **Identity** | Passion / true calling · Profession · Character — what they care about, what they do day to day, what governs their actions |
| **Desires** | What they want |
| **Skills** | What they're good at |
| **Tendencies** | Their comfort zone — what they do when nothing pushes them |
| **Shadows** | Fears and hidden truths |
| **Don't** | Hard constraints. Never crossed, by the character or the writing |
| **Relationships** | Per other character: history · current charge · carried unsaid · who knows what |
| **Story state** | The only home for story-specific facts: situation entering the story, active secrets |
| **Voice** | How they speak in balloons — register, tics, what they never say |
| **Background** | Fixed facts |

## The drama formula

> **Drama = pushing a character out of their Tendencies toward their Desires, through a Shadow, without ever violating a Don't.**

Everything in the storyboard leans on this. An intent (see `intention-obstacle.md`) is legitimate when it traces to a Desire; an obstacle bites hardest when it runs through a Shadow; a Don't limits the tactics available and is never itself the obstacle.

## A generic example

**MIRA OKAFOR — principal**

**Bio:** The harbour's night-shift crane operator. Can lift a container onto a ship in a gale; can't lift the phone to call her brother.
**Bio (self-written):** I move heavy things carefully. Nights, mostly.
**Identity:** Builder | Crane operator | Loyal to a fault

**Desires:**
- Keep the family house her father built
- Be forgiven by her brother for leaving
- Be the best operator on the pier, and be seen as it

**Skills:**
- Precise under pressure
- Reads weather before the forecast
- Fixes anything mechanical

**Tendencies:**
- Works extra shifts instead of having conversations
- Keeps promises to strangers more easily than to family
- Makes tea for whoever is awake at 4 a.m.

**Shadows:**
- Believes she caused her father's accident by being late that night
- Afraid that asking for help means she's failed

**Don't:**
- Lie to her brother
- Abandon a shift mid-lift
- Sell the crane her father trained her on

**Relationships:**
| With | History | Current charge | Carried unsaid | Who knows what |
|---|---|---|---|---|
| Tomas (brother) | Raised him after their father's accident; left for the harbour job at 22 | Cold, polite | She thinks he blames her; he thinks she blames him | Only Mira knows she was late that night |

**Story state:** The bank's letter about the house arrived this week. She hasn't opened it.

**Voice:** Short sentences. Mechanical metaphors. Never says "sorry" out loud; brings food instead.

With this DNA, a legitimate story intent is *"Mira intends to raise the money to keep the house before the auction, but the only way is a job that means leaving the pier for a month"* — a Desire (the house), pushed through a Shadow (asking for help = failure), constrained by a Don't (she won't lie to Tomas about why she's leaving).

## Principal vs. background

- **Principal** — for anyone the story turns on, at one of two depths:
  - **Full** — the full schema.
  - **Sketch** — the author's one-liner and look, plus 2–3 answers (what they want most · what trips them up · how they act when nothing pushes them). Kav drafts one or two lines each for Desires, Tendencies, Shadows, Don't and Voice from those answers and marks every drafted line `(draft)`. That is the minimum the drama formula needs, so PITCH can work from a sketch; it presses the `(draft)` lines first. A sketch deepens into full DNA whenever the author wants, or when PITCH needs more.
- **Background** — four fields only: *character class · what they are* (the author's line) *· appearance + references · where they appear* (a standing instruction for panels). The DNA sections are omitted on purpose and the file says so. A chorus of market stallholders doesn't need Shadows; inventing them makes them read as guns that never fire.

A background character can be promoted to principal later; that marks downstream artifacts stale.

## Rules

- Everything above *Story state* must be true of the character in any story.
- DNA is written in the story's language; the field labels stay in English so every command can read them.
- Appearance is grounded in the reference images, not guessed from the name.
