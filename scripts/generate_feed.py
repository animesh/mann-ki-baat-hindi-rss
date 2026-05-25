from datetime import datetime, timezone
from pathlib import Path
import hashlib
import urllib.request
import xml.etree.ElementTree as ET

PLAYLIST_ID = "PLBG6UuYpOcTvg9ALz7cJelclMi1oc7TQp"
PLAYLIST_FEED = (
    f"https://www.youtube.com/feeds/videos.xml?playlist_id={PLAYLIST_ID}"
)

OUTPUT = Path("docs/feed.xml")
FEED_URL = "https://animesh.github.io/mann-ki-baat-hindi-rss/feed.xml"
SITE_URL = "https://animesh.github.io/mann-ki-baat-hindi-rss/"

NAMESPACES = {
    "yt": "http://www.youtube.com/xml/schemas/2015",
}


def is_ai_generated(title, description):
    title = (title or "").lower()
    description = (description or "").lower()
    if "ai generated" in title or "ai generated" in description:
        return True
    if "ai tech" in description or "ai voice" in description:
        return True
    return False


def parse_playlist_entries():
    request = urllib.request.Request(
        PLAYLIST_FEED,
        headers={"User-Agent": "Mozilla/5.0 (compatible; feed-generator/1.0)"},
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        xml_data = response.read()

    root = ET.fromstring(xml_data)
    entries = []

    atom_ns = "{http://www.w3.org/2005/Atom}"
    for item in root.findall(f"{atom_ns}entry"):
        title = item.findtext(f"{atom_ns}title", "").strip()
        description = item.findtext(f"{atom_ns}summary", "").strip()
        if is_ai_generated(title, description):
            continue

        video_id = item.findtext("yt:videoId", namespaces=NAMESPACES)
        if not video_id:
            entry_id = item.findtext(f"{atom_ns}id", "")
            if entry_id.startswith("yt:video:"):
                video_id = entry_id.split(":", 2)[-1]

        if not video_id:
            continue

        link = None
        for link_elem in item.findall(f"{atom_ns}link"):
            if link_elem.get("rel") == "alternate":
                link = link_elem.get("href")
                break

        if not link:
            link = f"https://www.youtube.com/watch?v={video_id}"

        published = item.findtext(f"{atom_ns}published")
        published_dt = None
        if published:
            try:
                published_dt = datetime.fromisoformat(published.replace("Z", "+00:00")).astimezone(timezone.utc)
            except ValueError:
                published_dt = None

        entries.append(
            {
                "title": title or "Mann Ki Baat",
                "link": link,
                "published": published_dt,
            }
        )

    return entries


def build_feed(entries):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = "Mann Ki Baat Hindi"
    ET.SubElement(channel, "link").text = SITE_URL
    ET.SubElement(channel, "description").text = "Unofficial Hindi feed for Mann Ki Baat"
    ET.SubElement(channel, "atom:link", {
        "href": FEED_URL,
        "rel": "self",
        "xmlns:atom": "http://www.w3.org/2005/Atom",
    })

    for entry in entries:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = entry["title"]
        ET.SubElement(item, "link").text = entry["link"]
        guid = hashlib.md5(entry["link"].encode()).hexdigest()
        guid_elem = ET.SubElement(item, "guid", isPermaLink="false")
        guid_elem.text = guid
        if entry["published"] is not None:
            ET.SubElement(item, "pubDate").text = entry["published"].strftime("%a, %d %b %Y %H:%M:%S +0000")

    return ET.tostring(rss, encoding="utf-8", xml_declaration=True)


def main():
    entries = parse_playlist_entries()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    feed_xml = build_feed(entries)
    OUTPUT.write_bytes(feed_xml)
    print(f"Generated RSS with {len(entries)} entries")


if __name__ == "__main__":
    main()
