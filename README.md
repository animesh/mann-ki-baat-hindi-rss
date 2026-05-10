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