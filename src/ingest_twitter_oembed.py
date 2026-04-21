"""Fetch tweet text via Twitter oEmbed (no API key)."""
import json
import re
import sqlite3
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

OEMBED_URL = "https://publish.twitter.com/oembed?url={url}&omit_script=true"


def _extract_handle(url: str) -> str:
    m = re.search(r"twitter\.com/(\w+)/status/", url)
    if m:
        return m.group(1)
    m = re.search(r"x\.com/(\w+)/status/", url)
    if m:
        return m.group(1)
    return "unknown"


def _extract_tweet_id(url: str) -> str:
    m = re.search(r"/status/(\d+)", url)
    return m.group(1) if m else url


def _extract_text_from_html(html: str) -> str:
    # oEmbed HTML: <blockquote ...><p dir="ltr" lang="en">Tweet text</p>
    m = re.search(r'<p[^>]*>(.*?)</p>', html, re.S)
    if not m:
        return ""
    text = m.group(1)
    # Strip inline tags (links, br, etc.)
    text = re.sub(r'<a\s+[^>]*>.*?</a>', '', text, flags=re.S)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.I)
    text = re.sub(r'<[^>]+>', '', text)
    # Decode common entities
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
    return text.strip()


def _get_db_path(db_path: Optional[str]) -> Path:
    if db_path:
        return Path(db_path)
    return Path(__file__).parent.parent / "state" / "ops.sqlite"


def fetch_tweet_by_url(url: str, db_path: Optional[str] = None) -> dict:
    """Fetch a tweet via oEmbed and insert into signals table.

    Returns a dict with keys: inserted (bool), tweet_id, handle, text, error.
    """
    result = {"inserted": False, "tweet_id": None, "handle": None, "text": None, "error": None}
    tweet_id = _extract_tweet_id(url)
    handle = _extract_handle(url)
    result["tweet_id"] = tweet_id
    result["handle"] = handle

    # Dedup check
    db_file = _get_db_path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    try:
        existing = conn.execute(
            "SELECT 1 FROM signals WHERE source_family = ? AND source_id = ?",
            ("social_community", tweet_id),
        ).fetchone()
        if existing:
            return result
    except Exception as exc:
        result["error"] = f"dedup check failed: {exc}"
        conn.close()
        return result

    # Fetch oEmbed
    try:
        req = urllib.request.Request(
            OEMBED_URL.format(url=urllib.parse.quote(url, safe="")),
            headers={"User-Agent": "defi-ops/0.1 (read-only research)"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        result["error"] = f"oEmbed fetch failed: {exc}"
        conn.close()
        return result

    html = data.get("html", "")
    text = _extract_text_from_html(html)
    if not text:
        result["error"] = "could not extract tweet text from oEmbed HTML"
        conn.close()
        return result

    result["text"] = text

    # Insert
    try:
        conn.execute(
            """
            INSERT INTO signals (source_family, source_handle, content, url, source_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("social_community", handle, text, url, tweet_id),
        )
        conn.commit()
        result["inserted"] = True
    except sqlite3.IntegrityError:
        # Race or duplicate
        pass
    except Exception as exc:
        result["error"] = f"insert failed: {exc}"
    finally:
        conn.close()

    return result
