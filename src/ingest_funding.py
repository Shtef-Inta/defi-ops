"""Funding rate ingest: perp funding from CoinGlass or exchange APIs."""
from __future__ import annotations

import json
import urllib.request
import ssl
import certifi
from typing import Optional

_SSL_CTX = ssl.create_default_context(cafile=certifi.where())


def fetch_funding_coinbase() -> list[dict]:
    """Fetch funding rates from Coinbase Advanced (placeholder)."""
    return []


def ingest_funding(db_path: Optional[str] = None) -> dict:
    """Stub: funding rate ingestion."""
    return {"inserted": 0, "note": "stub: implement funding rate API"}
