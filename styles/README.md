# Style packs

A **style pack** is a folder that defines a visual language by example:

```
styles/<pack>/
  01.jpg  02.jpg  03.jpg     2–5 reference images (three is the default), sent in filename order
  medium.txt                 one line of prose describing how images are rendered
```

The images are passed to the image model alongside a story's character and location references; `medium.txt` is injected into every prompt. Together they steer the rendering without a pile of style adjectives.

## Making one

Run `/kav-style <pack>` (Codex: `/prompts:kav-style <pack>`) and point it at your reference images. The agent copies them here, looks at each one, writes `medium.txt` with you, and links the pack into your story at `stories/<slug>/styles/<pack>`. Then `/kav-visual-style-lock <pack>` tests it on cheap lettered samples and bakes the styled character references the book draws from.

Good packs:
- look like the same artist on the same day — different subjects, one rendering
- contain **one unrelated face**, and no look-alike of your cast — a face teaches the pack how this style renders a face, while a look-alike competes with the character's own references. A pack of only empty rooms and objects teaches faces nothing, and faces are most of a book
- carry as little furniture as they can: a plate that is an interior with a counter and stools donates counters and stools to scenes that already have their own
- contain no text (it bleeds into panels)
- have a `medium.txt` that names light, colour relationships, line and texture — never objects, sky, weather or props, which get painted into every frame

Full rules: `kav/commands/kav-style.md` and `docs/know-how/image-prompting.md`.

## Sharing

Packs are the one asset stories may share. A story uses only the pack its `style/style.md` names.

## Registered packs

*(Each pack gets a short entry here: name · what it looks like · the medium line.)*

- **`ligne-tlv`** — clear line and flat warm colour. Even-weight contour on every form, no hatching and no
  rendered shadow; light is a hard-edged warm/cool split between two flat fills of the same surface; a cool
  violet carries the shadow pole against ochre, terracotta and amber. Faces get black ink on eyes and brows
  and colour-matched line everywhere else, so line and colour integrate. Plates: `01` a close portrait of an
  older East Asian woman (an unrelated face, so the pack teaches face rendering without competing with any
  cast), `02` an empty plastered corner cut by a wedge of sun (the light logic, nothing else), `03` three
  tomatoes on a folded cloth. Deliberately content-light — the v1 plates were an interior with a counter and
  a shopfront, and they donated furniture to scenes that had their own; kept in `ligne-tlv/_v1/`.
  Built for `nero-pizza`; shareable. Medium line in `ligne-tlv/medium.txt`.
