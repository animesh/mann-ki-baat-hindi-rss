from datetime import datetime, timezone
from pathlib import Path
import hashlib
import re

from feedgen.feed import FeedGenerator
from yt_dlp import YoutubeDL

OUTPUT = Path("docs/feed.xml")

SITE_URL = "https://animesh.github.io/mann-ki-baat-hindi-rss/feed.xml"

SEARCH_QUERY = "Mann Ki Baat Hindi"

# yt-dlp search
ydl_opts = {
    "quiet": True,
    "extract_flat": True,
    "skip_download": True,
}

episode_patterns = [
    r"\bEpisode\s*[:\-]?\s*(\d+)\b",
    r"\b(\d+)(?:st|nd|rd|th)?\s+Episode\b",
    r"\b(\d+)(?:st|nd|rd|th)?\s+Edition\b",
    r"\bMann\s*Ki\s*Baat\s*(\d+)\b",
    r"\bMannKiBaat\s*(\d+)\b",
]

excluded_keywords = [
    "english",
    "tamil",
    "telugu",
    "malayalam",
    "bengali",
    "kannada",
    "dogri",
    "mizo",
    "garo",
    "kashmiri",
    "nepali",
    "sindhi",
    "sign language",
]

# OFFICIAL_UPLOADER_IDS = {"@OfficialMannKiBaat"}
# OFFICIAL_CHANNEL_IDS = {"UCEKXNa0XpMKDkRatg58PGmg"}


def extract_episode_number(title: str):
    for pattern in episode_patterns:
        match = re.search(pattern, title, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


with YoutubeDL(ydl_opts) as ydl:
    result = ydl.extract_info(
        f"ytsearch20:{SEARCH_QUERY}",
        download=False
    )

entries = result.get("entries", [])

clean_items = []
seen_episodes = set()

for entry in entries:
    title = entry.get("title", "")
    title_lower = title.lower()

    if "mann ki baat" not in title_lower:
        continue

    if any(x in title_lower for x in excluded_keywords):
        continue

    # uploader_id = entry.get("uploader_id")
    # channel_id = entry.get("channel_id")
    # if uploader_id not in OFFICIAL_UPLOADER_IDS and channel_id not in OFFICIAL_CHANNEL_IDS:
    #     continue

    episode = extract_episode_number(title)
    if episode is None:
        continue

    if episode in seen_episodes:
        continue

    video_id = entry.get("id")
    if not video_id:
        continue

    seen_episodes.add(episode)
    clean_items.append({
        "episode": episode,
        "title": title,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "description": entry.get("description", ""),
        "timestamp": entry.get("timestamp"),
    })

clean_items.sort(
    key=lambda item: item["episode"],
)

fg = FeedGenerator()
fg.id(SITE_URL)
fg.title("Mann Ki Baat Hindi RSS")
fg.author({"name": "GitHub Actions"})
fg.link(href=SITE_URL, rel="self")
fg.language("hi")
fg.description("Hindi RSS feed for Mann Ki Baat")

for item in clean_items:
    fe = fg.add_entry()
    guid = hashlib.md5(item["url"].encode()).hexdigest()
    fe.id(guid)
    fe.title(item["title"])
    fe.link(href=item["url"])
    fe.description(item["description"])

    timestamp = item["timestamp"]
    if timestamp:
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        fe.pubDate(dt)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
fg.rss_file(str(OUTPUT))

print()
print(f"Generated RSS with {len(clean_items)} sequential episode entries")
print(f"Saved to: {OUTPUT}")