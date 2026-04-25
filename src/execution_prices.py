"""Price fetcher for execution: current prices with caching."""
from __future__ import annotations

import json
import os
import sqlite3
import time
import urllib.request
import ssl
import certifi
from typing import Optional

from src.db import get_conn

_SSL_CTX = ssl.create_default_context(cafile=certifi.where())
_CG_BASE = "https://api.coingecko.com/api/v3"
_CACHE_TABLE = """
CREATE TABLE IF NOT EXISTS price_cache (
    coin_id TEXT PRIMARY KEY,
    usd REAL,
    updated_at REAL
)
"""


def _ensure_cache(db_path: Optional[str] = None):
    conn = get_conn(db_path)
    conn.execute(_CACHE_TABLE)
    conn.commit()
    conn.close()


def fetch_price(coin_id: str, max_age_seconds: int = 60) -> Optional[float]:
    """Fetch USD price from CoinGecko with in-memory fallback."""
    try:
        url = f"{_CG_BASE}/simple/price?ids={coin_id}&vs_currencies=usd"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, context=_SSL_CTX, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        return data.get(coin_id, {}).get("usd")
    except Exception:
        return None


def snapshot_prices(coin_ids: list[str], max_age_minutes: int = 5, db_path: Optional[str] = None) -> dict[str, dict]:
    """Return cached prices for coin_ids."""
    _ensure_cache(db_path)
    conn = get_conn(db_path)
    now = time.time()
    result = {}
    to_fetch = []
    for cid in coin_ids:
        row = conn.execute("SELECT usd, updated_at FROM price_cache WHERE coin_id = ?", (cid,)).fetchone()
        if row and (now - row[1]) < max_age_minutes * 60:
            result[cid] = {"usd": row[0], "cached": True}
        else:
            to_fetch.append(cid)
    for cid in to_fetch:
        price = fetch_price(cid)
        if price is not None:
            conn.execute(
                "INSERT OR REPLACE INTO price_cache (coin_id, usd, updated_at) VALUES (?, ?, ?)",
                (cid, price, now),
            )
            result[cid] = {"usd": price, "cached": False}
    conn.commit()
    conn.close()
    return result


# Protocol mapping
PROTOCOL_TO_COIN = {
    "aave": "aave",
    "uniswap": "uniswap",
    "ethena": "ethena",
    "morpho": "morpho",
    "compound": "compound-governance-token",
    "lido": "lido-dao",
    "curve": "curve-dao-token",
    "balancer": "balancer",
    "gmx": "gmx",
    "dydx": "dydx",
    "jupiter": "jupiter-exchange-solana",
    "hyperliquid": "hyperliquid",
    "eigenlayer": "eigenlayer",
    "sky": "sky",
    "spark": "spark",
    "gearbox": "gearbox",
    "fluid": "fluid",
}
