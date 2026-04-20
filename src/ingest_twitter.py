"""Twitter fetcher via syndication.twitter.com."""
from __future__ import annotations

import json
import re
import ssl
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Optional

try:
    import certifi

    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CTX = ssl.create_default_context()

from src.db import get_conn

SYND_URL = "https://syndication.twitter.com/srv/timeline-profile/screen-name/{handle}"
NEXT_DATA_RE = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

GROUP_TO_FAMILY = {
    "defi_core": "official",
    "researchers": "research",
    "risk_overlay": "risk_overlay",
    "analytics": "aggregator",
    "infra": "official",
}


def _parse_twitter_handles(text: str) -> list[tuple[str, str]]:
    """Extract (handle, source_family) from the twitter section of sources.yaml."""
    handles: list[tuple[str, str]] = []
    in_twitter = False
    current_group: str | None = None

    for raw in text.splitlines():
        line = raw.rstrip("\n")
        stripped = line.lstrip(" ")
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))

        if stripped == "twitter:":
            in_twitter = True
            continue

        if in_twitter and indent == 0 and stripped:
            break

        if not in_twitter:
            continue

        if indent == 2 and stripped.split()[0].endswith(":"):
            current_group = stripped.split("#")[0].strip().rstrip(":").strip()
            continue

        if indent == 4 and stripped.startswith("- "):
            h = stripped[2:].strip().lstrip("@").strip('"').strip("'")
            if h:
                handles.append((h, GROUP_TO_FAMILY.get(current_group, "social")))

    return handles


def _fetch_syndication(handle: str, timeout: int = 15) -> bytes | None:
    url = SYND_URL.format(handle=handle)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,*/*",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
            return resp.read()
    except urllib.error.HTTPError:
        return None
    except urllib.error.URLError:
        return None
    except TimeoutError:
        return None
    except Exception:
        return None


def _extract_tweets(body: bytes) -> list[dict]:
    html = body.decode("utf-8", errors="replace")
    m = NEXT_DATA_RE.search(html)
    if not m:
        return []
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return []
    entries = (
        data.get("props", {})
        .get("pageProps", {})
        .get("timeline", {})
        .get("entries", [])
    )
    tweets: list[dict] = []
    for e in entries:
        if e.get("type") != "tweet":
            continue
        t = (e.get("content") or {}).get("tweet")
        if isinstance(t, dict):
            tweets.append(t)
    return tweets


def _twitter_date_to_iso(s: str | None) -> str | None:
    if not s:
        return None
    try:
        dt = parsedate_to_datetime(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return None


def _normalize_tweet(t: dict, handle: str, source_family: str) -> dict | None:
    full_text = t.get("full_text") or t.get("text") or ""
    if not full_text.strip():
        return None

    user = t.get("user") or {}
    screen = user.get("screen_name") or handle
    id_str = t.get("id_str") or str(t.get("id") or "")
    status_url = t.get("permalink") or f"https://x.com/{screen}/status/{id_str}"
    if status_url.startswith("/"):
        status_url = "https://twitter.com" + status_url

    text_lower = full_text.lower()
    if any(
        w in text_lower
        for w in ("launch", "live", "rewards", "integration", "partnership")
    ):
        sentiment = "bullish"
    elif any(
        w in text_lower
        for w in ("freeze", "halt", "pause", "exploit", "drain", "depeg", "hack")
    ):
        sentiment = "bearish"
    else:
        sentiment = "neutral"

    return {
        "source_family": source_family,
        "source_handle": screen.lower(),
        "protocol": None,
        "event_key": None,
        "content": full_text,
        "url": status_url,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "asset_symbols": None,
        "sentiment": sentiment,
        "raw_payload": json.dumps(t, ensure_ascii=False),
        "source_id": id_str,
    }


def fetch_twitter(
    db_path: Optional[str] = None,
    max_per_handle: int = 20,
    sleep: float = 2.0,
    timeout: int = 15,
    _write_raw=None,
) -> dict:
    """Fetch twitter handles from sources.yaml and insert into signals (deduped by tweet_id)."""
    sources_path = Path(__file__).parent.parent / "config" / "sources.yaml"
    handles = _parse_twitter_handles(sources_path.read_text()) if sources_path.exists() else []

    conn = get_conn(db_path)
    inserted = 0
    skipped = 0
    failed = 0

    for idx, (handle, family) in enumerate(handles):
        if idx > 0:
            time.sleep(sleep)
        body = _fetch_syndication(handle, timeout=timeout)
        if body is None:
            failed += 1
            continue
        tweets = _extract_tweets(body)
        if not tweets:
            failed += 1
            continue

        if _write_raw:
            _write_raw(
                "x",
                handle,
                {
                    "source_family": family,
                    "handle": handle,
                    "captured_at": datetime.now(timezone.utc).isoformat(),
                    "tweets": tweets[:max_per_handle],
                },
            )

        for t in tweets[:max_per_handle]:
            norm = _normalize_tweet(t, handle, family)
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
        "handles_attempted": len(handles),
        "inserted": inserted,
        "skipped": skipped,
        "failed": failed,
    }
