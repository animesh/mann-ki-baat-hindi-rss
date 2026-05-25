from datetime import datetime, timezone
from pathlib import Path
import calendar
import hashlib
import re
import urllib.request
import xml.etree.ElementTree as ET

import feedparser
from feedgen.feed import FeedGenerator

PLAYLIST_ID = "PLBG6UuYpOcTvg9ALz7cJelclMi1oc7TQp"
PLAYLIST_FEED = (
    f"https://www.youtube.com/feeds/videos.xml?playlist_id={PLAYLIST_ID}"
)

OUTPUT = Path("docs/feed.xml")
FEED_URL = "https://animesh.github.io/mann-ki-baat-hindi-rss/feed.xml"
SITE_URL = "https://animesh.github.io/mann-ki-baat-hindi-rss/"
ARTWORK_URL = "https://animesh.github.io/mann-ki-baat-hindi-rss/artwork.png"
AUDIO_ENCLOSURE_URL = "https://file-examples.com/wp-content/uploads/2017/11/file_example_MP3_700KB.mp3"
AUDIO_ENCLOSURE_LENGTH = 702032


def is_ai_generated(entry):
    title = entry.get("title", "").lower()
    description = (entry.get("media_description") or entry.get("summary", "")).lower()
    if "ai generated" in title or "ai generated" in description:
        return True
    if "ai tech" in description or "ai voice" in description:
        return True
    return False


def parse_public_playlist_feed():
    feed = feedparser.parse(PLAYLIST_FEED)

    if getattr(feed, "bozo", False):
        print("WARNING: failed to parse playlist feed:", feed.bozo_exception)

    results = []
    for entry in feed.entries:
        if is_ai_generated(entry):
            continue

        video_id = entry.get("yt_videoid")
        if not video_id:
            entry_id = entry.get("id", "")
            if entry_id.startswith("yt:video:"):
                video_id = entry_id.split(":", 2)[-1]

        if not video_id:
            continue

        link = None
        for link_object in entry.get("links", []):
            if link_object.get("rel") == "alternate":
                link = link_object.get("href")
                break
        if not link:
            link = f"https://www.youtube.com/watch?v={video_id}"

        published = None
        published_parsed = entry.get("published_parsed") or entry.get("updated_parsed")
        if published_parsed:
            published = datetime.fromtimestamp(
                calendar.timegm(published_parsed), tz=timezone.utc
            )

        results.append(
            {
                "video_id": video_id,
                "title": entry.get("title", "Mann Ki Baat"),
                "link": link,
                "published": published,
            }
        )

    return results


def parse_playlist_entries():
    return parse_public_playlist_feed()


def feed_items(xml):
    items = []
    try:
        root = ET.fromstring(xml)
        channel = root.find("channel")
        if channel is None:
            return items

        for item in channel.findall("item"):
            guid_elem = item.find("guid")
            guid = guid_elem.text if guid_elem is not None else None
            enclosure = item.find("enclosure")
            url = enclosure.get("url") if enclosure is not None else None
            items.append((guid, url))
    except Exception as e:
        print("XML parse error:", e)
    return items


entries = parse_playlist_entries()

fg = FeedGenerator()
fg.load_extension("podcast")
fg.id(FEED_URL)
fg.title("Mann Ki Baat Hindi")
fg.author({"name": "PMO India"})
fg.link(href=FEED_URL, rel="self")
fg.link(href=SITE_URL, rel="alternate")
fg.language("hi")
fg.description("Unofficial Hindi feed for Mann Ki Baat")
fg.image(ARTWORK_URL)

fg.podcast.itunes_author("PMO India")
fg.podcast.itunes_category("Government")
fg.podcast.itunes_explicit("no")
fg.podcast.itunes_summary("Hindi editions of Mann Ki Baat")
fg.podcast.itunes_image(ARTWORK_URL)

count = 0
for entry in entries:
    fe = fg.add_entry()
    guid = hashlib.md5(entry["link"].encode()).hexdigest()
    fe.id(guid)
    fe.guid(guid, permalink=False)
    fe.title(entry["title"])
    fe.link(href=entry["link"])
    fe.enclosure(AUDIO_ENCLOSURE_URL, AUDIO_ENCLOSURE_LENGTH, "audio/mpeg")
    if entry.get("published"):
        fe.pubDate(entry["published"])
    count += 1

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

temp_output = OUTPUT.with_suffix(".tmp.xml")
fg.rss_file(str(temp_output))

xml_text = temp_output.read_text(encoding="utf-8")
xml_text = re.sub(r"<lastBuildDate>.*?</lastBuildDate>", "", xml_text, flags=re.DOTALL).strip()

old_text = ""
if OUTPUT.exists():
    old_text = OUTPUT.read_text(encoding="utf-8")
    old_text = re.sub(r"<lastBuildDate>.*?</lastBuildDate>", "", old_text, flags=re.DOTALL).strip()

if old_text == xml_text:
    temp_output.unlink()
    print("No feed content changes detected; docs/feed.xml not updated.")
else:
    OUTPUT.write_text(xml_text, encoding="utf-8")
    temp_output.unlink()
    print(f"Generated RSS with {count} episodes")
