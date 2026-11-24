# Publishing surfaces

The author decides how a story goes out; Kav renders the same lettered panels into each surface. Every surface is fed by what a finished chapter already contains, so none needs new art:

- `chapters/chNN/pages/pNN.png` — assembled pages (2400 px wide)
- `chapters/chNN/pages/carousel/NN-*.jpg` — one 1080×1350 image per panel, in reading order
- `chapters/chNN/pages/reader-story.html` / `reader-comic.html` — the two readers
- `package/trailer.html` + `package/slides/slide-NN.png` — the trailer deck and its 1080×1920 statics

| Surface | What goes | Status |
|---|---|---|
| **Static website** (any host, Netlify, GitHub Pages) | the readers + trailer as a folder with relative links | ready — `/kav-publish` builds and links it |
| **Instagram** | carousel JPEGs per chapter; trailer slide PNGs | ready: `/kav-post` posts a panel or a carousel of up to 10 to the author's account, `/kav-readers` reads likes, comments and views back. One-time setup in `docs/know-how/instagram.md`. Posting by hand still works (20 per carousel in the app) |
| **PDF / print** | page PNGs in order (reversed for RTL books), optional cover and dividers | not built yet; `tools/build_cover.py` makes a cover |
| **EPUB** | fixed-layout is the honest fit for comics | later |

## Hosting the readers

- **Netlify:** drag the site folder onto app.netlify.com/drop for a quick link, or connect a repo for deploys on push.
- **GitHub Pages:** put the folder in a repo, enable Pages for that branch and folder.
- **Anything else:** it's static HTML and images; upload it.

Chapter by chapter works well: each chapter is small, links forward to the next, and the trailer is the doorway that links into whichever chapters exist.

## Ask the author once per story

- Which surfaces this story goes to.
- For a site: where it's hosted, which repo and folder, whether a push deploys.
- For Instagram: the account, whether captions are written per chapter, and whether people and places are tagged on the image.

Record the answers under Links in `kickoff-state.md`. **Never publish, push or post without an explicit yes for that action.**
