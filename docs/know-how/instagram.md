# Instagram: posting and reading the numbers

Kav posts lettered panels to the author's own Instagram account and reads back how each post did. Both go through `tools/instagram.py`, which talks to the Instagram API with Instagram Login (`graph.instagram.com`). The commands are `/kav-post` and `/kav-readers`.

## 1 · What it needs

- **A professional Instagram account**: Creator or Business. A personal account cannot use the API. The switch is free and takes a minute in the app: Settings → Account type and tools → Switch to professional account.
- **A Meta developer app** that the author owns. It stays in Development mode. An app in Development mode can post to and read the accounts of the people who have a role on it, which is all Kav needs, so there is no App Review.
- **A long-lived access token** for that account, in `.env`. It lasts 60 days and Kav renews it.
- **A public address for each image.** Instagram does not accept an upload: it fetches the image from a URL. See section 5.

No Facebook Page is needed.

## 2 · One-time setup: walk the author through it

The author does every step that needs a login. Never ask for a password, and never ask the author to paste the token into the chat. Meta moves the labels in this dashboard often, so describe what to look for, and ask the author what is on the screen when a label does not match.

1. **Make the account professional** (section 1), signed in as the account that will post.
2. **Open the developer dashboard**: https://developers.facebook.com/apps, signed in with the author's Facebook account. An author who already has a Meta app for another Instagram account can reuse it and skip to step 4.
3. **Create an app.** Any name ("Kav posts" is fine). When asked for a use case, pick the Instagram one, or "Other" and then app type "Business". On the app's dashboard, add the **Instagram** product and open **API setup with Instagram login**.
4. **Generate the token.** In that screen, the section named "Generate access tokens": **Add account**, log in to Instagram as the posting account, and allow these permissions:
   - `instagram_business_basic`
   - `instagram_business_content_publish` (posting)
   - `instagram_business_manage_insights` (views, reach, saves, shares)
   - `instagram_business_manage_comments` (only for reading comment text)

   Then **Generate token** next to the account and copy it. If the dashboard refuses the account, add it under App roles → Roles as an **Instagram Tester**, accept the invitation in the Instagram app (Settings → Apps and websites → Tester invites), and try again.
5. **Put it in `.env`**, which the author edits themselves:

   ```
   INSTAGRAM_ACCESS_TOKEN=<the token>
   INSTAGRAM_USERNAME=<the handle, without @>
   ```

   For this token the repo's `.env` wins over the shell environment, the reverse of Kav's other keys: a token exported for another project would post to that project's account. `auth` says where the token came from.

   `INSTAGRAM_USERNAME` is a guard: Kav refuses to post when the token belongs to a different account. A story can name its own account in `story.json` as `"instagram": {"account": "handle"}`.
6. **Check it:**

   ```
   python3 tools/instagram.py auth
   ```

   It prints the account, its type and how many posts are left in the 24-hour quota. It never prints the token.

## 3 · The token's life

A token from the dashboard lasts 60 days. A token that is at least a day old can be traded for a fresh 60 days:

```
python3 tools/instagram.py auth --refresh
```

Kav also does this by itself after every successful post, so an author who posts at least once in two months never sees it expire. The expiry date is kept in `.env` as `INSTAGRAM_TOKEN_EXPIRES`. An expired token cannot be refreshed: generate a new one (step 4).

## 4 · What the API allows

| | |
|---|---|
| Image format | JPEG only. `draft` converts. |
| Shape | 4:5 portrait to 1.91:1 landscape. Kav's 4:5 panels and 1080×1350 carousel images fit. Wide panels use their phone crop. |
| Carousel | 2 to 10 images through the API (the app allows more). `draft` splits a longer chapter into parts. Instagram crops every image to the first one's shape. |
| Caption | 2,200 characters, 30 hashtags, 20 @mentions. Links in a caption are plain text, not clickable. |
| Tags | An @handle in the caption is a mention. A photo tag is separate: `user_tags` on the image, with a position. |
| Quota | Posts per 24 hours are limited per account; `auth` shows what is left. A carousel counts as one. |
| Stories and Reels | Not built. This posts feed images and carousels. |

## 5 · Where the images are hosted

Instagram fetches each image from a public URL at the moment of posting. Two ways:

- **The plan already has a URL.** An image entry with `"url"` is used as it is. Use this when the panels are already public, for example in a reader the author published.
- **`--host fal`** (the default). The JPEG is uploaded to fal.ai storage with the author's `FAL_KEY`, and Instagram fetches that link. The dry run says how many images will go there, so the author's yes covers it.

## 6 · When Instagram refuses

- **An error with a message** (bad token, missing permission, wrong shape): fix what it says and try again.
- **A refusal with no reason.** The upload stays in ERROR and Instagram gives no detail. This is the sign of a temporary spam block, which Meta applies to accounts that create many uploads quickly. It clears in one to three days, and each retry extends it. The tool starts a one-hour cooldown (`.instagram-cooldown` at the repo root) and stops. Tell the author to post that one by hand and to wait. Do not delete the cooldown file to try again.
- **One post at a time.** Never loop over a backlog of posts in one go. Post, confirm with the author, then the next.

## 7 · The numbers

`stats` reads, for every post in `stories/<slug>/instagram/posts.jsonl`: likes, comments, views, reach, saves and shares. It groups them by chapter (or by post, for a story made of single posts).

- The API returns **organic numbers only**. A boosted post shows more in the app than here.
- A metric that Instagram does not give for a post is left empty and named in a note. It is not a zero.
- Numbers settle slowly. Each run appends to `stats-history.jsonl`, so two runs a few days apart show how a post grew.
- A post made by hand is not in the list until it is registered: `python3 tools/instagram.py link --story <slug> --unit chNN --permalink <url>`.
