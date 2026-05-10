from datetime import datetime, timezone
from pathlib import Path
import hashlib
import os
import re
import tempfile
import xml.etree.ElementTree as ET

from feedgen.feed import FeedGenerator
from yt_dlp import YoutubeDL

PLAYLIST_URL = (
    "https://www.youtube.com/playlist"
    "?list=PLBG6UuYpOcTvg9ALz7cJelclMi1oc7TQp"
)

OUTPUT = Path("docs/feed.xml")

SITE_URL = (
    "https://animesh.github.io/"
    "mann-ki-baat-hindi-rss/feed.xml"
)

cookiefile_path = os.environ.get("YTDLP_COOKIES_PATH")
cookiefile_content = os.environ.get("YTDLP_COOKIES")
created_cookiefile = None

if cookiefile_content and not cookiefile_path:
    cookiefile_content = cookiefile_content.replace("\r\n", "\n").replace("\r", "\n")
    cookiefile_content = cookiefile_content.strip() + "\n"
    temp_cookie = tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8")
    temp_cookie.write(cookiefile_content)
    temp_cookie.close()
    cookiefile_path = temp_cookie.name
    created_cookiefile = temp_cookie.name

if not cookiefile_path:
    print(
        "WARNING: YTDLP_COOKIES is not set. YouTube extraction may fail due to sign-in/bot checks."
    )

playlist_opts = {
    "quiet": True,
    "extract_flat": True,
    "skip_download": True,
    "js_runtimes": {"deno": {}},
}

if cookiefile_path:
    playlist_opts["cookiefile"] = cookiefile_path

with YoutubeDL(playlist_opts) as ydl:
    playlist = ydl.extract_info(
        PLAYLIST_URL,
        download=False
    )

entries = playlist.get("entries", [])

fg = FeedGenerator()

fg.load_extension("podcast")

fg.id(SITE_URL)
fg.title("Mann Ki Baat Hindi")
fg.author({"name": "PMO India"})
fg.link(href=SITE_URL, rel="self")
fg.language("hi")
fg.description(
    "Unofficial Hindi podcast feed for Mann Ki Baat"
)

fg.podcast.itunes_author("PMO India")
fg.podcast.itunes_category("Government")
fg.podcast.itunes_explicit("no")
fg.podcast.itunes_summary(
    "Hindi editions of Mann Ki Baat"
)

video_opts = {
    "quiet": True,
    "skip_download": True,
    "js_runtimes": {"deno": {}},
}

if cookiefile_path:
    video_opts["cookiefile"] = cookiefile_path

count = 0

for entry in entries:

    video_id = entry.get("id")

    if not video_id:
        continue

    video_url = (
        f"https://www.youtube.com/watch?v={video_id}"
    )

    try:

        with YoutubeDL(video_opts) as ydl:
            info = ydl.extract_info(
                video_url,
                download=False
            )

        title = info.get("title", "Mann Ki Baat")

        formats = info.get("formats", [])

        media_url = None
        media_type = "audio/mp4"
        media_length = None

        for f in formats:
            ext = f.get("ext")
            acodec = f.get("acodec")
            vcodec = f.get("vcodec")

            if (
                ext in ("m4a", "mp4")
                and acodec != "none"
                and vcodec == "none"
            ):
                media_url = f.get("url")
                media_length = f.get("filesize") or f.get("filesize_approx")
                if ext == "m4a":
                    media_type = "audio/mp4"
                else:
                    media_type = "video/mp4"
                break

        if not media_url:
            for f in formats:
                ext = f.get("ext")

                if ext == "mp4":
                    media_url = f.get("url")
                    media_length = f.get("filesize") or f.get("filesize_approx")
                    media_type = "video/mp4"
                    break

        if not media_url:
            continue

        if not media_length:
            continue

        count += 1

        fe = fg.add_entry()

        guid = hashlib.md5(
            video_url.encode()
        ).hexdigest()

        fe.id(guid)
        fe.guid(guid, permalink=False)

        fe.title(title)

        fe.link(href=video_url)

        description = (
            info.get("description", "")[:4000]
        )

        fe.description(description)

        fe.enclosure(
            media_url,
            media_length,
            media_type
        )

        upload_date = info.get("upload_date")

        if upload_date:

            dt = datetime.strptime(
                upload_date,
                "%Y%m%d"
            ).replace(tzinfo=timezone.utc)

            fe.pubDate(dt)

    except Exception as e:
        print("ERROR:", e)

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

temp_output = OUTPUT.with_suffix(".tmp.xml")
fg.rss_file(str(temp_output))

xml_text = temp_output.read_text(encoding="utf-8")
xml_text = re.sub(r"<lastBuildDate>.*?</lastBuildDate>", "", xml_text, flags=re.DOTALL).strip()


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

new_items = feed_items(xml_text)
old_items = []
if OUTPUT.exists():
    old_text = OUTPUT.read_text(encoding="utf-8")
    old_text = re.sub(r"<lastBuildDate>.*?</lastBuildDate>", "", old_text, flags=re.DOTALL).strip()
    old_items = feed_items(old_text)

if old_items == new_items:
    temp_output.unlink()
    print("No feed entry changes detected; docs/feed.xml not updated.")
else:
    OUTPUT.write_text(xml_text, encoding="utf-8")
    temp_output.unlink()
    print(f"Generated RSS with {count} podcast episodes")

if created_cookiefile:
    os.remove(created_cookiefile)
