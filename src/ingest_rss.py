"""RSS fetcher for web and governance feeds."""
from __future__ import annotations

import json
import ssl
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Optional

try:
    import certifi

    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())

from src.db import get_conn

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


def _parse_rss_sources(text: str) -> list[dict]:
    """Extract RSS source dicts from the rss section of sources.yaml."""
    sources: list[dict] = []
    in_rss = False
    current_item: dict | None = None

    for raw in text.splitlines():
        line = raw.rstrip("\n")
        stripped = line.lstrip(" ")
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))

        if stripped == "rss:":
            in_rss = True
            continue

        if in_rss and indent == 0 and stripped:
            break

        if not in_rss:
            continue

        if indent == 2 and stripped.split()[0].endswith(":"):
            continue

        if indent == 4 and stripped.startswith("- "):
            current_item = {}
            rest = stripped[2:].strip()
            if ":" in rest:
                k, _, v = rest.partition(":")
                current_item[k.strip()] = v.strip().strip('"').strip("'")
            sources.append(current_item)
            continue

        if indent == 6 and current_item is not None and ":" in stripped:
            k, _, v = stripped.partition(":")
            current_item[k.strip()] = v.strip().strip('"').strip("'")

    return sources


def _fetch_rss(url: str, timeout: int = 15) -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
            return resp.read()
    except Exception:
        return None


def _rss_date_to_iso(s: str | None) -> str | None:
    if not s:
        return None
    try:
        dt = parsedate_to_datetime(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return None


def _parse_rss_feed(xml_bytes: bytes) -> list[dict]:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return []

    tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag

    # Atom feed
    if tag == "feed":
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = []
        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns)
            link = entry.find("atom:link[@rel='alternate']", ns)
            if link is None:
                link = entry.find("atom:link", ns)
            published = entry.find("atom:published", ns)
            if published is None:
                published = entry.find("atom:updated", ns)
            summary = entry.find("atom:summary", ns)
            if summary is None:
                summary = entry.find("atom:content", ns)
            id_el = entry.find("atom:id", ns)

            entries.append(
                {
                    "title": title.text if title is not None else "",
                    "url": link.get("href") if link is not None else "",
                    "published": published.text if published is not None else "",
                    "description": summary.text if summary is not None else "",
                    "guid": id_el.text if id_el is not None else "",
                }
            )
        return entries

    # RSS 2.0
    if tag == "rss":
        entries = []
        for item in root.iter("item"):
            title = item.find("title")
            link = item.find("link")
            pub_date = item.find("pubDate")
            desc = item.find("description")
            guid = item.find("guid")

            entries.append(
                {
                    "title": title.text if title is not None else "",
                    "url": link.text if link is not None else "",
                    "published": pub_date.text if pub_date is not None else "",
                    "description": desc.text if desc is not None else "",
                    "guid": guid.text if guid is not None else "",
                }
            )
        return entries

    return []


def _normalize_rss_entry(entry: dict, source: dict) -> dict | None:
    title = entry.get("title", "")
    if not title.strip():
        return None

    text = f"{title}\n{entry.get('description', '')}"[:1200]
    text_lower = text.lower()
    if any(w in text_lower for w in ("launch", "live", "rewards", "integration", "partnership")):
        sentiment = "bullish"
    elif any(w in text_lower for w in ("freeze", "halt", "pause", "exploit", "drain", "depeg", "hack")):
        sentiment = "bearish"
    else:
        sentiment = "neutral"

    source_id = entry.get("guid") or entry.get("url") or title
    return {
        "source_family": source.get("source_family", "aggregator"),
        "source_handle": source.get("name", "").lower().replace(" ", "-"),
        "protocol": source.get("protocol"),
        "event_key": None,
        "content": text,
        "url": entry.get("url", ""),
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "asset_symbols": None,
        "sentiment": sentiment,
        "raw_payload": json.dumps(entry, ensure_ascii=False),
        "source_id": source_id,
    }


def fetch_rss(
    db_path: Optional[str] = None,
    max_per_source: int = 10,
    timeout: int = 15,
    _write_raw=None,
) -> dict:
    """Fetch RSS feeds from sources.yaml and insert into signals."""
    sources_path = Path(__file__).parent.parent / "config" / "sources.yaml"
    sources = (
        _parse_rss_sources(sources_path.read_text())
        if sources_path.exists()
        else []
    )

    conn = get_conn(db_path)
    inserted = 0
    skipped = 0
    failed = 0
    total_sources = 0

    for src in sources:
        if src.get("enabled", "true").lower() == "false":
            continue
        url = src.get("url", "")
        if not url:
            continue
        total_sources += 1

        xml = _fetch_rss(url, timeout=timeout)
        if xml is None:
            failed += 1
            continue

        entries = _parse_rss_feed(xml)
        if not entries:
            failed += 1
            continue

        if _write_raw:
            _write_raw(
                "rss",
                src.get("name", "unknown"),
                {
                    "source": src,
                    "captured_at": datetime.now(timezone.utc).isoformat(),
                    "entries": entries[:max_per_source],
                },
            )

        for e in entries[:max_per_source]:
            norm = _normalize_rss_entry(e, src)
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
        "sources_attempted": total_sources,
        "inserted": inserted,
        "skipped": skipped,
        "failed": failed,
    }
