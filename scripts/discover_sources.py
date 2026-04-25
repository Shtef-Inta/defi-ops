#!/usr/bin/env python3
"""Source discovery: find new twitter mentions, youtube channels, telegram channels."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


def discover_twitter_mentions(db_path: Optional[str] = None, min_mentions: int = 5) -> list[dict]:
    """Discover frequently mentioned handles not yet in sources."""
    from src.db import get_conn
    conn = get_conn(db_path)
    rows = conn.execute(
        """
        SELECT source_handle, COUNT(*) as cnt
        FROM signals
        WHERE source_family = 'social'
        GROUP BY source_handle
        HAVING cnt >= ?
        ORDER BY cnt DESC
        LIMIT 10
        """,
        (min_mentions,),
    ).fetchall()
    conn.close()
    return [{"handle": r[0], "mentions": r[1], "type": "twitter"} for r in rows]


def discover_youtube_channels(db_path: Optional[str] = None) -> list[dict]:
    """Discover youtube channels from raw transcripts not yet tracked."""
    return []


def discover_telegram_channels(db_path: Optional[str] = None) -> list[dict]:
    """Discover telegram channels from signals not in config."""
    return []


def save_discoveries(discoveries: dict):
    """Save discoveries to state/discovered_sources.json"""
    path = Path(__file__).parent.parent / "state" / "discovered_sources.json"
    path.write_text(json.dumps(discoveries, indent=2, ensure_ascii=False), encoding="utf-8")


def auto_enable_top_candidates(top_n: int = 5, min_score: int = 2) -> dict:
    """Auto-enable frequently mentioned sources. Stub: returns empty dict."""
    return {}
