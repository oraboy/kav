# Image models in Kav

What each image model is like when you make a book with it in Kav. This is not a general ranking. A book needs the same face on every page, so consistency counts more than one beautiful picture.

Prices and reference limits change. `python3 tools/check_setup.py` prints the current values.

## Models Kav can run

| Model | Strong points | Limits |
|---|---|---|
| **Seedream 4.5 on fal.ai** · about $0.04 | Best consistency. It keeps faces and style across scenes. It takes 10 reference images. Kav's default | A fourth named character in one panel can drift |
| **Seedream 4.5 on Magnific** · about $0.05 | Good consistency. The same model as on fal.ai | It takes 5 reference images. Keep to 3 characters in a panel. It does not make 4:5 images, so Kav crops them |
| **Nano Banana Pro** on fal.ai or a Google key · about $0.15 | Strong styling and image quality | It struggles with consistency. It costs about 4 times more than Seedream |
| **Higgsfield** (Popcorn, Soul) · about $0.05 | Popcorn takes 8 reference images | Not tested. Soul takes 1 reference image, so it cannot keep a face |

## Models Kav cannot run

| Model | Strong points | Limits |
|---|---|---|
| **Midjourney** | The most artistic output | It has no API, so Kav cannot use it. You can make images there by hand, and Kav can add them as takes (`tools/add_candidate.py`) |

## The image generator in the author's AI tool

It needs no key and no setup. The agent makes one panel for each image and adds the results as takes (`own-image-tool.md`). Kav cannot see the cost.

## When the author asks about a tool that is not here

Say that Kav knows of no specific limits or problems with it. Offer to try a few examples together and judge the results. Do not start a test before the author says yes.

## How to use this page with an author

1. Ask which image tools or accounts the author already has.
2. Show the options that fit, with the strong points and the limits.
3. Let the author choose. A tool the author already uses is a good choice.

## Add what you learn

When a model is tested on a real story, change its row. Keep each cell to one or two short sentences.
