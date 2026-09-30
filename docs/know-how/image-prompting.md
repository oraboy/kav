# Image prompting — the operating manual

How Kav builds image-generation calls: reference ordering, style packs, prompt wording, model choice, and the failure modes measured in real production (several hundred generations across a bake-off and a finished book). Where a claim comes from vendor docs rather than our own runs, it says so.

## Story scope

Every reference in a call — cast, location, object, style — belongs to the story being drawn. Resolve the roster from `stories/<slug>/cast/*.md` and places from that story's `locations/`. If a scene needs something the story doesn't have, say so and offer to create it.

## The call shape

One call carries every reference, in this order:

1. **Cast** — mug shots per character (styled set when it exists)
2. **Location** — the real photograph(s) or approved earlier panels
3. **Objects** — the photograph of a thing that must be identical every time
4. **Style pack** — the images in the linked `styles/<pack>/`

The prompt names each by index *and* role: *"Image 1 shows <name>: …"*, *"Image 3 shows the real location the scene takes place in"*, *"Images 4 to 6 are the rendering target."* Indices disambiguate for the model; roles make the log readable.

**Everything is an image.** No written styles, no described-only locations: photographs are what make a place recognisable, and word-defined styles drift.

## Prompt rules that measurably changed output

- **Name the medium in prose.** The pack's `medium.txt` line goes into every prompt. The single most effective lever found: it turned failed style transfers into correct ones and made seeds agree stylistically. Its wording rules are in `/kav-style`.
- **Frame positively; assign every slot.** Negative commands underperform (Google documents this for Gemini; our runs agree). Instead of "take nothing of their subject matter", write "the final image shows only the scene described above; its subject, composition and setting come entirely from images 1 to 2."
- **Say "including the background."** Style drift shows up in backgrounds first.
- **Set the aspect ratio explicitly** (`--ar`). On Nano Banana the model otherwise takes it from the *last* image — the style pack's shape would decide the framing.
- **Give the subject a position.** A character lost in a crowd comes back with "in the foreground centre, close to the camera, face clear" plus their identity words repeated.
- **Name the expression, always.** A line that carries the action and not the face returns the model's default: a mild, pleasant, camera-aware smile, on a character dangling off a railing in a storm. Nothing in the reference stack corrects it, because mug shots are neutral by design. Write the face as an instruction — "jaw set, eyes narrowed against the rain, not looking at the camera" — and write it even when it seems obvious from the beat. It is never obvious to the model. A panel spec without an expression is an incomplete spec.
- **Carry the scene state into every panel of the scene.** Time of day, weather, light source, wet or dry, hurt or whole, and what each character is wearing. Panels are generated independently; anything the line doesn't say gets re-invented per panel, so a midnight storm turns into a blue afternoon three panels later and a jacket becomes a summer top. See below.
- **Keep real place names out of the line** once the photo binds — the name becomes invented signage.
- **Wide panels:** put the subject in the centre third; the phone crop keeps only the middle.
- **Never put story dialogue in the line.** Lettering is post-process.

## Choosing a model

**A locked lane overrides the recommendations below.** These are capabilities to consider before the author locks a lane, not an escalation ladder. “Production” does not name a model: a more expensive or generally stronger model is not a transparent upgrade. Because models reinterpret identity and style, changing lanes requires an explicit author gate and a labelled side-by-side comparison.

| Need | Use | Why |
|---|---|---|
| Non-Latin text in frame (e.g. Hebrew signage) | **Nano Banana Pro** | The only model tested that spells it correctly; others render convincing nonsense — worse than no text |
| A real place must be recognisable | **Nano Banana Pro** | Rebuilds a location and re-stages the camera within it |
| A precise emotional beat or body language | **Nano Banana Pro** | Best at turning a written moment into that moment |
| Style-heavy work, volume, exploration | **Seedream 4.5** | Transfers a pack's visual language more faithfully, looks better, costs ~$0.04 vs $0.15 |

Nano Banana at "2K" costs the same as "1K" — never run below it.

## Style packs

- **2–5 images, three is the default** (matches documented vendor caps and practitioner experience; convention, not proof).
- **No faces that resemble the cast** — a look-alike competes with the character's own references for identity. But **include one unrelated face**: a pack of empty rooms and objects teaches the model nothing about how this style renders a face, which is most of what a book is made of. A faceless pack is a common cause of a session of face drift. (`/kav-style` says the same; the short form "no faces in the pack" used to appear here and read as the opposite.)
- **Plates carry content, not only rendering.** A plate that is an interior with a counter and stools will donate counters and stools to scenes that already have their own, and a shopfront plate will push a shopfront into a scene set indoors. Choose subjects that carry light, colour relationships, line and texture with as little furniture as possible.
- **Internally coherent** — same artist, same day. Disagreeing images average into mush.
- **No text in references** — it bleeds into output.
- **Test on bright daylight exteriors.** Both models hold stylised looks in dim interiors and drift toward ordinary colour illustration outdoors, where the location photo's light fights the pack.

## Objects — putting a specific thing in frame

The wording decides whether it works, by a wide margin. "An object to place in the scene, reproduce its lettering" transferred only the object's *shape* and invented the text. This transferred the text correctly on the same model and seed:

> Image N is a photograph of a real physical object. Place this exact object into the scene unchanged, as though it were photographed there. Any lettering on it is copied verbatim, glyph for glyph, in the same script and spelling — it is never re-typeset, translated, or replaced with different words.

- This is how the cheap lane gets correct non-Latin text: it can't spell from a prompt, but it carries text off an object photo. Treat signage as pick-from-two, not one-shot.
- **Photograph objects alone.** A dress photographed on a model gave the character wearing it the model's haircut; the flat-lay dress came through exactly.
- **Making a sign:** render it with PIL and a font that covers the script. PIL applies bidi itself — pass the logical string, don't pre-reverse it. Verify by checking the first glyph sits on the correct edge.

## Every reference tends to become a thing in the frame

The most useful mental model: a reference exerts pressure to appear *as an object in the picture*.
- Two mug shots of one character can produce two of that character in one frame. **One mug shot per character in multi-character scenes.**
- An object reference can produce a second copy of the object. Word objects as belonging to the scene ("the car they are riding in").
- A style line that names a noun (clouds, foliage) paints that noun into every frame.

## The reference budget — how many, and which

**References must agree with each other.** What looks like a fixed budget running out is usually two references arguing about what the panel is. A scene at a pizzeria's interior counter came back as a generic rooftop and was blamed on reference count — but the set included a photograph of the *outside of the building*. Remove that one contradiction and the same scene rendered correctly on **seven** references, beating the eight-reference version it replaced. Fewer references that agree beat more that don't. And never pass two photos of the same angle: a duplicate spends a slot and says nothing the first one didn't.

**The three kinds behave differently, and this is the part that gets missed.**

| Kind | How many | Which ones |
|---|---|---|
| **Style plates** | **Constant across the book.** Pick the number once — three is a good default — and never vary it panel to panel. | May vary by **shot type**, never by panel: a crowd scene, a close-up and a wide interior may each take a different trio, as long as the mapping is fixed, so every close-up in the book takes the same trio as every other close-up. An ad-hoc per-panel choice optimises one panel and costs the book its consistency, which is the one thing a pack exists to protect. |
| **Location photos** | **One — a plate, not a photograph.** See below. | The plate for the view this panel takes. An interior scene gets the interior plate; the shopfront stays out of it. |
| **Mug shots** | 2–3 per character. | The views the shot needs — full-body for a standing wide, the smile shot for a laughing close-up, front always as the anchor. Taking the first two in a fixed order wastes both: a head-to-foot panel given `front` + `three-quarter` came back cropped at mid-thigh, and came back near full length given `full-body` + `front`. |

### Locations get mug shots too

A photograph of a real place and a stylised drawing of a character are two different kinds of picture, and a panel that binds both has to reconcile them — silently, and differently on every take. Move that reconciliation out of the panel: redraw the location once in the pack's style, look at it, and from then on bind the drawing. A **plate** is to a location what a mug shot is to a character.

Measured on nero-pizza (2026-09-27), the same two-hander at the same three seeds, changing nothing but the location reference:

| Location reference | Character read correctly | Place recognisable |
|---|---|---|
| Three photographs | 2/3 | Partly — the mural and the red stools went missing, the street outside turned American |
| One photograph | 2/3 | **Worse.** La Tigre lost its neon disc and its tiger mural on every take; one had no sign at all |
| **One plate** | **3/3** | Yes — concertina frames, red stools, tiled counter base, an Israeli bus outside |

Cutting to one photograph is the obvious move and it is the wrong one: it costs the place its signature without buying identity back. The kind of picture is what matters, not the count.

**Plates are per shot, not per location.** A scene at the window counter and a scene arriving from the street are two different views of the same pizzeria and want two different plates, exactly as a character wants `front` and `full-body`. Declare the shots the way mug shots are declared — the photograph each comes from, the words in a scene line that call for it, and what it shows.

**Build them on demand and cache them.** The first panel that needs a view draws it (one cheap call); every later panel in that view is free. Nothing is generated up front, so a location the book never enters never costs anything, and a book that grows a new kind of scene grows a new plate without a ceremony.

**Whatever is in the plate arrives in the panel, faithfully.** In testing the Tigre panels reproduced their plate's terrace down to the air-conditioning unit and the shop sign across the street — which is the argument for plates and the warning about them in one observation. If the plate is built from the wrong photograph, the panel is wrong in exactly that way, every time, instead of rolling the dice across three photos. That makes plate choice an author decision, made once and visibly, which is where it belongs. Show new plates at the next gate.

**Word the shot cues as viewpoints, not as scene dressing.** A first pass matched `"from the street"` as a cue for Brooklyn's shopfront and pulled the exterior into an interior scene whose line happened to read *"warm light from the street."* Cues name where the camera stands — `window counter`, `shopfront`, `order counter` — never what the light or the weather is doing.

**A place erodes the same way a face does, and for the same reason: nothing told the model to keep it.** The character block has always carried an explicit *must remain recognisably the same* sentence; the location block had none. With a correct plate bound and no such clause, a pizzeria came back as a generic late-night kiosk and an al taglio counter as an American slice joint, while the characters in the same panels held. Say it for the place too: *the setting is that same place and no other — keep its architecture, frontage, signage and the wording on it, fittings, furniture, colours and light; the camera may move within it and the people are new, but the place itself is never redesigned, generalised, or replaced with a similar-looking venue.*

**The seating is a shot, and most books need it.** A story set in cafés, bars or restaurants is mostly people sitting outside, and a frontage plate does not contain the furniture — so every seated scene borrows a frontage view and the model invents the tables. It reads as *the place is wrong* in four different panels and is one missing shot. Declare the seating as its own view wherever characters sit, and make it the location's `default_shot`.

**But keep the seating cues narrow.** Making seating the default is right; giving it cues like `table` or `at a table` is not, because those appear in scenes whose real subject is the sign or the frontage — a La Tigre panel asking for the red neon got the terrace and lost the mural. The default already catches a plain seated scene; the cues only need to name the seating itself.

**Two things a plate prompt must forbid, because both are wrong on every page set there.** *Invented lettering:* a plate built from a photograph with a sign cut off filled it with nonsense in the right script, and every panel copied it faithfully. Tell it to copy lettering glyph for glyph and to leave unreadable signs blank. *Inverted geometry:* a wide downward view of round café tables came back with the tables hanging from the sky, on four seeds and three prompt variants — the model reads tabletops seen from above as ceiling lamps. Stating the orientation did not fix it and neither did stating the camera; **a different photograph did.** When a plate fails the same way twice, change the source, not the words.

**Bind a location's signature object rather than describing it.** ARTZIELI's Roman al taglio — rectangular trays cut into rectangles on baking paper — came back as round American pizza every time, because *pizza* has a strong prior and the description was fighting it. The tray was already a registered object with a photograph and nothing was binding it. Objects need to be scoped to the places they belong to (`"at": ["artzieli"]`), so ordinary words like `tray` or `slice` can trigger them there without dragging a Roman pizza into a Neapolitan pizzeria.

**And keep generic words out of cue lists entirely.** `pavement`, `table`, `sitting`, `outside`, `sunset` appear in nearly every line at an outdoor location, so they win by accident and decide the plate for scenes they say nothing about: a La Tigre panel asking for red neon got the terrace, which has neither the neon disc nor the mural, because `pavement` is a longer string than `neon`. Rank cues by specificity rather than length, and let a line that only says "at a table" fall through to the location's `default_shot` — that is what a default is for.

### How many faces a panel can carry

**The lane sets the book's face budget, once.** The lane is locked for the whole book — switching it mid-book means re-rendering every panel, because two models never agree on a face — so a provider's image cap is not a caveat about crowded panels. It is a property of the book, fixed the moment the lane is chosen, and it decides which scenes the story can stage at all.

**The arithmetic.** Per panel, the reference stack is *faces + location + style + objects*, and `plan_refs` sacrifices in that order when a cap bites: characters drop to one shot each, the location to one photo, and the style pack takes whatever is left. So the budget is:

> **faces ≤ cap − location slots − style slots − object slots**

with a style pack that needs at least two or three slots to hold a look, and at least one location photo in any scene that has a place. Worked through:

| Lane cap | Faces a panel can carry | What happens past it |
|---|---|---|
| **Uncapped** (fal) | ~4, limited by quality rather than arithmetic | Reliability drops: a four-face panel at twelve references collapsed one of two dark-haired women into the other on one seed and got all four right on the next. It works at **three or four takes instead of one or two** — three to four times the cost of a two-face panel. |
| **8** | 3, at one or two shots each | Style or location starts losing slots. |
| **5** (Magnific) | **2** | At four characters plus a location, the style pack gets **zero** slots — and a style block with no images means `medium.txt` never enters the prompt either, so the panel returns **completely unstyled**. A different-looking page mid-book, not a slightly worse one. Bind an object and it is over cap before style is considered. |

**Tell the author the number, twice.** Once when the lane is chosen or installed — *"on this lane a panel holds N faces; scenes with more have to be staged across panels"* — because it constrains the storyboard, not just the drawing. And again the moment a planned panel exceeds it, at scene-list time, while the fix is still a sentence rather than a re-render.

**At the top of the budget the location is what pays.** Eight face references against one location photo, and a pizzeria at a city square became a seafront promenade in both takes. You can hold the people or the place, not both. The answer is craft, not budget: **establish the place in a one- or two-character panel where the location has slots, then let the group panel run loose on its background.** The reader has already been told where they are and does not need the set re-proved while four people talk.

## What working comics people actually do

Kav's design — character mugs, location photographs and style plates in one undifferentiated reference stack, each panel generated independently — is **not** what the practitioners with finished work do. Worth knowing where we stand on a path and where we are doing original work.

**Chain each panel from the last, rather than re-deriving it from references.** The strongest technique found, from the most credible source: [K.M. Carroll](https://kmcarroll.substack.com/p/i-made-a-comic-with-ai-tools), a comics artist with a published hand-drawn graphic novel, on her own AI comic — *"I could feed the AI the last image I had generated and tell it 'draw the next moment, where the character is doing X'. This would keep the character **and background** consistent."* Identity and place travel through the chain instead of through a stack. Every working method in that survey introduces a dependency between panels; Kav's independent per-panel stacks do not. Kav already documents "continuity by reference" for fixing drift — this is the same move used *by default* rather than as a repair.

**Keep identity and style apart.** Nobody credible puts both into one flat stack. They run identity and style as two sequential passes, or generate characters and backgrounds in separate calls and composite ([Rootport's *Cyberpunk: Peach John*](https://www.cnn.com/style/article/japan-first-ai-generated-manga-art-intl-hnk/index.html), 100+ pages), or at minimum fence the style refs in words — *"use the attached images strictly as stylistic references only."* The cheap version of this costs one sentence.

**References should be boring.** The best-documented character-consistency write-up ([Pratibimbh](https://medium.com/@jjmayank98/my-attempts-at-making-consistent-images-for-a-comic-book-with-ai-471a2a1402e1)) found that a reference's *background and atmosphere are read as part of the identity signal* — dramatic dark references forced every scene dark regardless of the prompt. The fix was regenerating every reference on pure white with flat even lighting: *"the white ones looked like passport photos"*, and contamination "disappeared completely." The principle: **references are data, not art.** This sits in real tension with `/kav-visual-style-lock` producing deliberately *styled* mugs, and is worth an A/B before anyone trusts either.

**Nobody passes photographs of locations.** Not one practitioner in the survey. The documented approaches are chaining, or generating a background once and reusing it. Kav's location-photo binding is genuinely unexplored — which is a differentiator if it works, but means its failures have no prior art to consult.

**The ceiling is about two identity-locked characters**, confirmed independently: past that, practitioners stop trying to lock identity and carry it on silhouette and clothing instead. Which is why a **signature feature** — one thing extreme enough that the model cannot quietly drop it — is the standard remedy, and why it reads at panel size when a face does not.

**Manual correction is structural, not a fallback.** Every finished work in the survey involved hand-drawn panels, composited figures, or per-page retouching. Carroll hand-drew one character on every page because the model could never learn him. Budget for it.

**Two things Kav already gets right**, per the same sources: panel-at-a-time rather than whole-page generation (*"NEVER an entire page. AI commits laughably horrible crimes"*), and lettering as a post-process — generated lettering is the instant giveaway of an amateur AI comic.

**So design panels to the lane's number instead of discovering it at generation time:**

- A wide establishing panel where nobody is individually legible, then the conversation in two-shots.
- **Split a crowded table across panels with an overlapping anchor** — half the faces in one, half in the next, one or two people appearing in both. The shared figures stitch the halves into a single table in the reader's head, and no panel ever exceeds the lane's number.
- Backs, shoulders, a hand reaching in, a figure cut by the frame edge. A comic never needed every face legible in every frame.

Write chapter cards to the lane's number: planning a two-panel table is cheaper than fighting one crowded panel, and it is the difference between a story that can be told on this lane and one that cannot.

**Where this goes eventually:** a crowded panel is a compositing problem, not a prompting one — a background pass, figure passes at one or two faces each, merged. That removes the ceiling entirely and is the right long-term shape. Nothing in Kav does it today; the staging rules above are what works now.

## Continuity by reference

When a place drifts across panels, bind an **approved earlier panel** of it as an extra location reference (copy it into `locations/<name>/`, add it to `photos` in `briefs.json`). The next generation binds the drawn place, not only the photo. Adjectives in the prompt don't fix drift; references do.

## Scene state — what drifts when nobody names it

References hold identity. They hold nothing about the moment. Every panel is an independent call, so whatever the line leaves out, the model invents fresh — and it invents toward the pleasant and the well-lit.

Five things drift, in rough order of how badly they break a reader:

| Drifts | Looks like | Carry it in the line |
|---|---|---|
| **Expression** | the same mild smile through terror, exhaustion and fury | the face, as an instruction, in every panel |
| **Time and weather** | a midnight storm rendered as a blue afternoon at the climax | the hour, the sky, the sea state, the light source, every panel |
| **Wardrobe** | a zipped jacket becomes a summer top mid-scene | the character's clothes for *this chapter*, from their cast file |
| **Condition** | soaked and bleeding in one panel, dry and neat in the next | wet, torn, bruised, carrying-something |
| **Identity of the second and third character** | two supporting characters become interchangeable | one distinguishing feature per supporting character, named every time |
| **Apparent age** | a mother drawn as a teenager in some panels and an adult in others | the age, in years, in every line that names them. Measured: two independent readers of one book both took the mother for the protagonist's *sister*. Age drift doesn't just blur a character — it changes the relationship the reader infers, and they build the rest of the book on it |

A **scene-state line** written once at the top of a scene and pasted into every panel of it costs nothing and fixes most of this. Put it in `panels/plan.md` at the scene header so the author can see it and change it.

Two notes on where this bites hardest. Supporting characters drift far more than the protagonist, because the protagonist usually has one loud visual anchor (a signature jacket, a braid) doing the identity work — which means the moment that anchor is out of frame, they drift too; give every principal a feature that survives a costume change. And the climax is the most likely scene in a book to be rendered in daylight, because it tends to be planned last, at the end of a long batch, when scene state has quietly stopped being repeated.

## Debugging a wrong image

**Print the whole prompt before theorising.** `--dry-run` shows every reference in order and the assembled prompt; read it once, because most "the model is drifting" turns out to be something sitting in plain sight. Two real examples from one book, each invisible for a whole session:

- A `medium.txt` that itself began *"Render the entire final image as…"*, while `build_prompt` wraps it in *"Render the entire final image as a {medium}"* — so every prompt carried the stem twice. Write `medium.txt` as a noun phrase (*"A clear-line comic drawing: …"*), never as its own instruction.
- An object registered with triggers as broad as "pizza" and "slice", which bound a *Roman rectangular* pizza — and its shouted "NEVER round, NEVER a wedge" — into a Neapolitan pizzeria that serves round pizza. An object's triggers must be as specific as the object.

Then, in order:

1. Read the candidate's `.json` sidecar: which cast, location, objects and style actually bound?
2. Location triggers are first-match. A generic word ("apartment", "room", "street") in one location's triggers steals scenes meant for another. Put specific places first; drop generic words.
3. **Generate three takes before diagnosing anything.** One bad image is not evidence: identity at two mug shots per character lands most of the time and misses sometimes, so a single miss looks exactly like a broken pipeline. Diagnosing off one generation produced three wrong diagnoses in a row on one book — a systemic identity failure, then the style pack, then the seed — when the truth was one wrong word in each of two character descriptions, plus ordinary variance. **Wrong in one take of three is variance; wrong in all three is a cause.**
4. When it is wrong in all three, suspect **a word in the character description before anything else.** Descriptions have overwhelmed mug shots repeatedly: *"tousled"* gave a cropped-haired man wavy hair; *"wavy and a little unruly"* gave a boy ringlets; and *"soft full cheeks · slender undeveloped jaw · a delicate jaw · full lips · narrow shoulders"* stacked onto a blunt fringe rendered an eighteen-year-old boy as a girl in every take. Read the description aloud and ask what it would conjure with no photograph attached — that is most of what the model is doing with it.
5. Only then rewrite the scene line — for a named reason.

**When one cast member keeps failing, rebuild their references pushed the other way.** Rewording the panel prompt is arguing with the model at the wrong end: the reading the panel inherits was baked into the mug shots. Rebuild the set with the mug-shot direction pushed *past* the target, so the drawing has to travel back through the panel's variance rather than start at the edge of it. An eighteen-year-old boy who rendered as a girl in every take — pale, slight, a heavy blunt fringe that kept resolving to a bob — got a direction written in the opposite direction: squarer jaw, visible Adam's apple, flat broad chest, the fringe cut short and above the brows, the sides cropped close, *"so the head reads as a boy's crop and never as a bob."* The same panel at the same seeds went from 0 to 2 of 3.

Three notes on doing it:

- **Push the reading, not the likeness.** The direction steers the mug build only; it never reaches a panel prompt. Overshooting there costs nothing in the book and buys margin in every panel.
- **Retest on the panel that was failing, at three seeds, before believing it.** Two of three is progress, not a fix, and says to keep going.
- **Then ask the author.** A rebuilt set changes how a real person's character looks on every page they appear on. That is theirs to accept, and they may know a better lever — a different haircut in the book, a signature prop, or a better photograph. (Invented features carry well: a character given large glasses and an orange shirt at touch-up time, neither in any photograph of him, kept both across panels.)

## Cost and speed

**References are posted on every call, so their size is most of the wall-clock.** Sending files as they sit on disk is the obvious thing and it is very expensive: styled mug shots are 2048-square PNGs and style plates are larger, so a four-face panel posted **13 MB** of base64 per generation. Measured on one panel: 17.7s uploading 1.9 MB against ~110 KB/s upstream, which at 13 MB is over two minutes before the model starts. Downscale references to **1024px JPEG** on the wire — the same stack becomes 1.7 MB, eight times less — and cache the encoding per file so a batch sending the same mug shots nine times encodes them once. Nothing is lost: the model resizes them anyway, and identity is carried by structure. A/B'd at 1024, 1600 and 2048 against a location that was failing: **no difference in fidelity**, so the small one is free.

**The rest of the wall-clock is the provider's queue, so generate concurrently.** A single Seedream panel is ~100s and ~80s of it is waiting on their side. Nine in sequence is a quarter of an hour of nothing; three at a time is about five minutes. Draw any missing location plates serially first — two scenes at one place would otherwise race to draw the same plate, paying twice — then fan out.

**Retry upload failures.** `write operation timed out` happens, and a nine-image run that dies on the second image wastes everything already paid for.

## Known failure modes

- **Invented lettering in frame.** Any surface that could carry text — a control panel, a sign, a schematic, a map, a notebook — comes back with confident nonsense ("FINKTESSTATICK CHECK"). It reads as a typo to the author and as a broken world to a reader. Either keep text surfaces out of the framing, or promote the thing to an object and bind its photograph (see above).
- **Hallucinated artist signatures.** A scrawl in a bottom corner that looks like a signature, because the style pack's references have them. It is a made-up human name signed on the author's page. Check every corner of every picked candidate; crop or reroll.
- **Three-plus characters** get less reliable as the count rises.
- **Seed-to-seed style drift** — first suspect an ambiguous `medium.txt`.
- **Interiors losing their ceiling** — the location photo doesn't show it; get a photo that does.
- **fal 403** — balance locked, not rate limiting. Top up; known cases stay locked briefly after top-up.
- **fal CDN files expire in 7 days and are public URLs** — the tools download immediately.

## Things that are not real

- **Seedream "reference weights"** (Character 1.0, Style 0.9…) described in popular guides don't exist in any API surface.
- **Locked seeds as a consistency mechanism** — seeds are a variation knob, not identity control.

## Cost shape

Use the story's approved lane from exploration through publication. Before lock, Seedream is an economical candidate for broad exploration (~$0.04/image), while Nano Banana Pro (~$0.15 at 2K) may be worth comparing for specific capabilities. Neither is inherently the production model. A chapter of ~25 panels at 3 takes each plus rerolls is roughly 100 images: about $4 on Seedream at these example prices. Prices as of 2026; check fal.ai and Google AI Studio for current rates.
