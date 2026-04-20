"""YouTube fetcher via RSS feeds."""
from __future__ import annotations

import json
import re
import ssl
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import certifi

    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CTX = ssl.create_default_context()

from src.db import get_conn

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


def _parse_youtube_channels(text: str) -> list[dict]:
    """Extract channel dicts from the youtube section of sources.yaml."""
    channels: list[dict] = []
    in_youtube = False
    current_item: dict | None = None

    for raw in text.splitlines():
        line = raw.rstrip("\n")
        stripped = line.lstrip(" ")
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))

        if stripped == "youtube:":
            in_youtube = True
            continue

        if in_youtube and indent == 0 and stripped:
            break

        if not in_youtube:
            continue

        if indent == 2 and stripped.split()[0].endswith(":"):
            continue

        if indent == 4 and stripped.startswith("- "):
            current_item = {}
            rest = stripped[2:].strip()
            if ":" in rest:
                k, _, v = rest.partition(":")
                current_item[k.strip()] = v.strip().strip('"').strip("'")
            channels.append(current_item)
            continue

        if indent == 6 and current_item is not None and ":" in stripped:
            k, _, v = stripped.partition(":")
            current_item[k.strip()] = v.strip().strip('"').strip("'")

    return channels


def _resolve_channel_id(handle: str, timeout: int = 15) -> str | None:
    """Resolve YouTube channel id from @handle via meta tags."""
    url = f"https://www.youtube.com/@{handle}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception:
        return None

    m = re.search(
        r'<meta[^>]*property="og:url"[^>]*content="https://www\.youtube\.com/channel/([^"]+)"',
        html,
    )
    if m:
        return m.group(1)

    m = re.search(
        r'<link[^>]*rel="canonical"[^>]*href="https://www\.youtube\.com/channel/([^"]+)"',
        html,
    )
    if m:
        return m.group(1)

    m = re.search(r'"channelId":"([^"]+)"', html)
    if m:
        return m.group(1)

    return None


def _fetch_youtube_rss(channel_id: str, timeout: int = 15) -> bytes | None:
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
            return resp.read()
    except Exception:
        return None


def _parse_youtube_rss(xml_bytes: bytes) -> list[dict]:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return []

    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "yt": "http://www.youtube.com/xml/schemas/2015",
        "media": "http://search.yahoo.com/mrss/",
    }
    entries: list[dict] = []
    for entry in root.findall("atom:entry", ns):
        video_id = entry.find("yt:videoId", ns)
        title = entry.find("atom:title", ns)
        published = entry.find("atom:published", ns)
        link = entry.find("atom:link[@rel='alternate']", ns)
        author = entry.find("atom:author/atom:name", ns)
        desc = entry.find("media:group/media:description", ns)

        entries.append(
            {
                "video_id": video_id.text if video_id is not None else "",
                "title": title.text if title is not None else "",
                "published": published.text if published is not None else "",
                "url": link.get("href") if link is not None else "",
                "author": author.text if author is not None else "",
                "description": desc.text if desc is not None else "",
            }
        )
    return entries


def _normalize_youtube_entry(
    entry: dict, handle: str, source_family: str, protocol: str | None
) -> dict | None:
    video_id = entry.get("video_id")
    if not video_id:
        return None

    text = f"{entry['title']}\n{entry.get('description', '')}"[:1200]
    text_lower = text.lower()
    if any(w in text_lower for w in ("launch", "live", "rewards", "integration", "partnership")):
        sentiment = "bullish"
    elif any(w in text_lower for w in ("freeze", "halt", "pause", "exploit", "drain", "depeg", "hack")):
        sentiment = "bearish"
    else:
        sentiment = "neutral"

    return {
        "source_family": source_family,
        "source_handle": handle.lower(),
        "protocol": protocol,
        "event_key": None,
        "content": text,
        "url": entry.get("url", ""),
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "asset_symbols": None,
        "sentiment": sentiment,
        "raw_payload": json.dumps(entry, ensure_ascii=False),
        "source_id": video_id,
    }


def _youtube_cache_path(db_path: str | None) -> Path:
    if db_path:
        return Path(db_path).parent / "youtube-channel-ids.json"
    return Path(__file__).parent.parent / "state" / "youtube-channel-ids.json"


def fetch_youtube(
    db_path: Optional[str] = None,
    max_per_channel: int = 10,
    timeout: int = 15,
    _write_raw=None,
) -> dict:
    """Fetch YouTube channels from sources.yaml via RSS and insert into signals."""
    sources_path = Path(__file__).parent.parent / "config" / "sources.yaml"
    channels = (
        _parse_youtube_channels(sources_path.read_text())
        if sources_path.exists()
        else []
    )

    cache_path = _youtube_cache_path(db_path)
    cache: dict[str, str] = {}
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text())
        except Exception:
            cache = {}

    conn = get_conn(db_path)
    inserted = 0
    skipped = 0
    failed = 0
    total_channels = 0

    for ch in channels:
        handle = ch.get("handle", "")
        if not handle:
            continue
        total_channels += 1

        channel_id = cache.get(handle)
        if not channel_id:
            channel_id = _resolve_channel_id(handle, timeout=timeout)
            if channel_id:
                cache[handle] = channel_id
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(json.dumps(cache, indent=2))
        if not channel_id:
            failed += 1
            continue

        xml = _fetch_youtube_rss(channel_id, timeout=timeout)
        if xml is None:
            failed += 1
            continue

        entries = _parse_youtube_rss(xml)
        if not entries:
            failed += 1
            continue

        if _write_raw:
            _write_raw(
                "youtube",
                handle,
                {
                    "handle": handle,
                    "channel_id": channel_id,
                    "captured_at": datetime.now(timezone.utc).isoformat(),
                    "entries": entries[:max_per_channel],
                },
            )

        for e in entries[:max_per_channel]:
            norm = _normalize_youtube_entry(
                e, handle, ch.get("source_family", "official"), ch.get("protocol")
            )
            if not norm:
                continue

            existing = conn.execute(
                "SELECT 1 FROM signals WHERE source_family = ? AND source_id = ?",
                (norm["source_family"], norm["source_id"]),
            ).fetchone()
            if existing:
                skipped += 1
                continue

            conn.execute(
                """
                INSERT INTO signals
                    (source_family, source_handle, protocol, event_key, content, url,
                     captured_at, asset_symbols, sentiment, raw_payload, source_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    norm["source_family"],
                    norm["source_handle"],
                    norm["protocol"],
                    norm["event_key"],
                    norm["content"],
                    norm["url"],
                    norm["captured_at"],
                    norm["asset_symbols"],
                    norm["sentiment"],
                    norm["raw_payload"],
                    norm["source_id"],
                ),
            )
            inserted += 1

    conn.commit()
    conn.close()
    return {
        "channels_attempted": total_channels,
        "inserted": inserted,
        "skipped": skipped,
        "failed": failed,
    }
