from datetime import datetime, timezone
from pathlib import Path
import hashlib
import os
import re
import tempfile

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

fg.rss_file(str(OUTPUT))

if created_cookiefile:
    os.remove(created_cookiefile)

print(f"Generated RSS with {count} podcast episodes")
