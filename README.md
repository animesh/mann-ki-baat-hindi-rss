# Mann Ki Baat Hindi RSS

Automatically generates a Hindi-only RSS feed for Mann Ki Baat using the official YouTube RSS feed.

## Features

- Uses official YouTube RSS source
- Filters Hindi editions only
- Publishes via GitHub Pages
- Auto-updates:
  - on every push
  - manually
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

Your feed will be available at:

```text
https://animesh.github.io/mann-ki-baat-hindi-rss/feed.xml
```

## Local testing

```bash
pip install -r requirements.txt
python scripts/generate_feed.py
```
