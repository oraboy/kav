# Publishing surfaces

The author decides how a story goes out; Kav renders the same lettered panels into each surface. Every surface is fed by what a finished chapter already contains, so none needs new art:

- `chapters/chNN/pages/pNN.png` — assembled pages (2400 px wide)
- `chapters/chNN/pages/carousel/NN-*.jpg` — one 1080×1350 image per panel, in reading order
- `chapters/chNN/pages/reader-story.html` / `reader-comic.html` — the two readers
- `package/trailer.html` + `package/slides/slide-NN.png` — the trailer deck and its 1080×1920 statics

| Surface | What goes | Status |
|---|---|---|
| **Static website** (any host, Netlify, GitHub Pages) | the readers + trailer as a folder with relative links | ready — `/kav-publish` builds and links it |
| **Instagram** | carousel JPEGs per chapter; trailer slide PNGs | ready — posting is manual; carousels hold at most 20 items, so split long chapters |
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
- For Instagram: the account, and whether captions are written per chapter.

Record the answers under Links in `kickoff-state.md`. **Never publish, push or post without an explicit yes for that action.**
