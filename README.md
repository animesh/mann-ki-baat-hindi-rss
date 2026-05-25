# Mann Ki Baat Hindi RSS

Automatically generates a Hindi-only RSS feed for Mann Ki Baat and publishes at https://animesh.github.io/mann-ki-baat-hindi-rss/feed.xml.

## Features

- Generates a Hindi-only RSS feed from a public YouTube playlist
- Filters out AI-generated and reupload entries from the playlist
- Includes podcast enclosures so feed validators detect episodes
- Writes `docs/feed.xml` for GitHub Pages publication
- Auto-updates on:
  - every push
  - manual workflow dispatch
  - daily at 12:00 GMT via GitHub Actions schedule

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

No login cookies are required for this feed. The generator uses YouTube's public playlist RSS feed and works without secrets.

## Published URLs

- Feed: `https://animesh.github.io/mann-ki-baat-hindi-rss/feed.xml`
- Site root: `https://animesh.github.io/mann-ki-baat-hindi-rss/`

## Local testing

```bash
pip install -r requirements.txt
python scripts/generate_feed.py
```

Verified locally:

- generator compiles cleanly
- feed generation completes successfully
- `docs/feed.xml` contains the latest playlist items

## Feed source

Public playlist: https://www.youtube.com/playlist?list=PLBG6UuYpOcTvg9ALz7cJelclMi1oc7TQp

## Feed testing

https://www.castfeedvalidator.com/validate.php?url=https://animesh.github.io/mann-ki-baat-hindi-rss/feed.xml