from datetime import datetime, timezone
from pathlib import Path
import calendar
import hashlib
import re
import urllib.request
import xml.etree.ElementTree as ET

import feedparser
from feedgen.feed import FeedGenerator
from yt_dlp import YoutubeDL

PLAYLIST_ID = "PLBG6UuYpOcTvg9ALz7cJelclMi1oc7TQp"
PLAYLIST_FEED = (
    f"https://www.youtube.com/feeds/videos.xml?playlist_id={PLAYLIST_ID}"
)

OUTPUT = Path("docs/feed.xml")
FEED_URL = "https://animesh.github.io/mann-ki-baat-hindi-rss/feed.xml"
SITE_URL = "https://animesh.github.io/mann-ki-baat-hindi-rss/"
ARTWORK_URL = "https://animesh.github.io/mann-ki-baat-hindi-rss/artwork.png"
AUDIO_ENCLOSURE_URL = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
AUDIO_ENCLOSURE_LENGTH = 8945229


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


def select_audio_format(formats):
    candidates = []
    for f in formats:
        url = f.get("url")
        if not url:
            continue

        acodec = f.get("acodec")
        if not acodec or acodec == "none":
            continue

        protocol = f.get("protocol")
        if protocol not in ("https", "http"):
            continue

        ext = (f.get("ext") or "").lower()
        if ext in ("mhtml", "webp"):
            continue

        if ext in ("m4a", "mp4"):
            mime = "audio/mp4"
        elif ext == "webm":
            mime = "audio/webm"
        elif ext == "opus":
            mime = "audio/opus"
        elif ext == "aac":
            mime = "audio/aac"
        elif ext == "mp3":
            mime = "audio/mpeg"
        else:
            mime = f"audio/{ext}"

        abr = f.get("abr") or f.get("tbr") or 0
        filesize = f.get("filesize") or f.get("filesize_approx") or 0
        candidates.append((abr, filesize, url, mime))

    if not candidates:
        return None, None, None

    candidates.sort(key=lambda item: (item[0] or 0, item[1] or 0), reverse=True)
    _, filesize, url, mime = candidates[0]
    return url, str(filesize or 0), mime


def extract_audio_stream(video_url):
    YDL_OPTS = {
        "quiet": True,
        "skip_download": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "ignoreerrors": True,
        "extract_flat": False,
    }

    try:
        with YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(video_url, download=False)

        if not info:
            return None, None, None

        formats = info.get("formats") or []
        if formats:
            return select_audio_format(formats)

        # Fallback to the direct info URL if no formats are returned.
        url = info.get("url")
        acodec = info.get("acodec")
        if url and acodec and acodec != "none":
            size = str(info.get("filesize") or info.get("filesize_approx") or 0)
            return url, size, "audio/mpeg"

        return None, None, None
    except Exception as e:
        print("yt-dlp failed:", video_url)
        print(e)
        return None, None, None


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
fg.podcast.itunes_owner(name="PMO India", email="contact@animesh.github.io")
fg.podcast.itunes_image(ARTWORK_URL)

count = 0
for entry in entries:
    print()
    print("Processing:", entry["title"])

    audio_url, audio_size, mime = extract_audio_stream(entry["link"])

    if audio_url:
        print(" -> actual stream selected")
    else:
        print(" -> no usable stream; falling back to sample audio")
        audio_url = AUDIO_ENCLOSURE_URL
        audio_size = AUDIO_ENCLOSURE_LENGTH
        mime = "audio/mpeg"

    fe = fg.add_entry()
    guid = hashlib.md5(entry["link"].encode()).hexdigest()
    fe.id(guid)
    fe.guid(guid, permalink=False)
    fe.title(entry["title"])
    fe.link(href=entry["link"])
    fe.enclosure(audio_url, audio_size, mime)
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
