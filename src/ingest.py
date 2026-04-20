"""Raw ingest from 5 source families. Sprint 1: twitter + youtube."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.config import load_env
from src.ingest_rss import fetch_rss as _fetch_rss

load_env()
from src.ingest_telegram import fetch_telegram as _fetch_telegram
from src.ingest_twitter import fetch_twitter as _fetch_twitter
from src.ingest_wallets import fetch_wallets as _fetch_wallets
from src.ingest_youtube import fetch_youtube as _fetch_youtube


def _write_raw(source: str, handle: str, payload: dict) -> Path:
    """Persist raw payload to state/raw/<source>/ for wiki-base workflow."""
    raw_dir = Path(__file__).parent.parent / "state" / "raw" / source
    raw_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    safe_handle = re.sub(r"[^a-z0-9]+", "-", handle.lower()).strip("-") or "unknown"
    path = raw_dir / f"{safe_handle}-{stamp}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    return path


def fetch_twitter(
    db_path: Optional[str] = None,
    max_per_handle: int = 20,
    sleep: float = 2.0,
    timeout: int = 15,
) -> dict:
    """Fetch twitter handles from sources.yaml and insert into signals (deduped by tweet_id)."""
    return _fetch_twitter(
        db_path=db_path,
        max_per_handle=max_per_handle,
        sleep=sleep,
        timeout=timeout,
        _write_raw=_write_raw,
    )


def fetch_youtube(
    db_path: Optional[str] = None,
    max_per_channel: int = 10,
    timeout: int = 15,
) -> dict:
    """Fetch YouTube channels from sources.yaml via RSS and insert into signals."""
    return _fetch_youtube(
        db_path=db_path,
        max_per_channel=max_per_channel,
        timeout=timeout,
        _write_raw=_write_raw,
    )


def fetch_rss(
    db_path: Optional[str] = None,
    max_per_source: int = 10,
    timeout: int = 15,
) -> dict:
    """Fetch RSS feeds from sources.yaml and insert into signals."""
    return _fetch_rss(
        db_path=db_path,
        max_per_source=max_per_source,
        timeout=timeout,
        _write_raw=_write_raw,
    )


def fetch_wallets(
    db_path: Optional[str] = None,
    max_per_wallet: int = 50,
    timeout: int = 15,
) -> dict:
    """Fetch watched wallet transactions via Etherscan v2 and insert into wallet_tx."""
    return _fetch_wallets(
        db_path=db_path,
        max_per_wallet=max_per_wallet,
        timeout=timeout,
        _write_raw=_write_raw,
    )


def fetch_telegram(
    db_path: Optional[str] = None,
    max_per_channel: int = 20,
    lookback_hours: int = 24,
    _client_factory=None,
) -> dict:
    """Fetch Telegram channels via Telethon and insert into signals."""
    return _fetch_telegram(
        db_path=db_path,
        max_per_channel=max_per_channel,
        lookback_hours=lookback_hours,
        _write_raw=_write_raw,
        _client_factory=_client_factory,
    )


def ingest_all(db_path: Optional[str] = None) -> dict:
    """Run all ingest sources. Sprint 1: twitter + youtube + rss + wallets + telegram."""
    results: dict = {}
    results["twitter"] = fetch_twitter(db_path)
    results["youtube"] = fetch_youtube(db_path)
    results["rss"] = fetch_rss(db_path)
    results["wallets"] = fetch_wallets(db_path)
    results["telegram"] = fetch_telegram(db_path)
    return results
