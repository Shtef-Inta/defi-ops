"""Telegram Web ingest: browser-based fallback for channels not accessible via MTProto."""
from __future__ import annotations

from typing import Optional


def ingest_telegram_web(db_path: Optional[str] = None) -> dict:
    """Stub: Telegram Web scraping fallback."""
    return {"inserted": 0, "note": "stub: use Telethon MTProto instead"}
