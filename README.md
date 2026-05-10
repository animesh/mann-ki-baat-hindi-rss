# Mann Ki Baat Hindi RSS

Automatically generates a Hindi-only RSS feed for Mann Ki Baat and publishes it through GitHub Pages.

## Features

- Extracts Hindi Mann Ki Baat episodes from YouTube search results
- Filters out unrelated language editions
- Deduplicates episodes by number
- Generates `docs/feed.xml`
- Publishes via GitHub Pages
- Auto-updates on:
  - every push
  - manual workflow dispatch
  - every hour on the last Sunday of every month

## Setup

1. Create a GitHub repository.
2. Upload all files from this project.
3. Enable GitHub Pages:
   - Settings
   - Pages
   - Deploy from branch
   - Branch: `main`
   - Folder: `/docs`

### GitHub Actions auth

The workflow may need YouTube login cookies to extract episode metadata.

Set a repository secret named `YTDLP_COOKIES` with raw YouTube cookies in Netscape `cookies.txt` format. The secret should contain multiline cookie content, not a JSON object or `Set-Cookie` header string.

If you export cookies from your browser, use a tool that produces a standard `cookies.txt` file and paste the exact contents into the secret value.

## Published URLs

- Feed: `https://animesh.github.io/mann-ki-baat-hindi-rss/feed.xml`
- Site root: `https://animesh.github.io/mann-ki-baat-hindi-rss/`

## What changed

- Updated `scripts/generate_feed.py` to use the actual GitHub Pages URL
- Regenerated `docs/feed.xml`
- Added `docs/index.html` so the root URL resolves
- Left the official-channel filter in place as commented-out code for later use
- Confirmed workflow `.github/workflows/update.yml` runs on push, manual dispatch, and schedule

## Local testing

```bash
pip install -r requirements.txt
python scripts/generate_feed.py
```

## Original feed 

https://www.youtube.com/playlist?list=PLBG6UuYpOcTvg9ALz7cJelclMi1oc7TQp

## Feed testing
https://www.castfeedvalidator.com/validate.php?url=https://animesh.github.io/mann-ki-baat-hindi-rss/feed.xml