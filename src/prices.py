"""Price fetching with caching for daemon and strategies."""
from __future__ import annotations

import json
import time
import urllib.request
import ssl
import certifi
from typing import Optional

from src.db import get_conn

_SSL_CTX = ssl.create_default_context(cafile=certifi.where())
_CG_BASE = "https://api.coingecko.com/api/v3"

PROTOCOL_TO_COIN = {
    "jupiter": "jupiter-exchange-solana",
    "aave": "aave",
    "uniswap": "uniswap",
    "ethena": "ethena",
    "pendle": "pendle",
    "morpho": "morpho",
    "lido": "lido-dao",
    "hyperliquid": "hyperliquid",
    "fluid": "fluid",
    "compound": "compound-governance-token",
    "curve": "curve-dao-token",
    "sky": "sky",
    "spark": "spark",
    "eigenlayer": "eigenlayer",
    "gearbox": "gearbox",
    "balancer": "balancer",
    "gmx": "gmx",
    "dydx": "dydx",
}


def _ensure_table(db_path: Optional[str] = None):
    conn = get_conn(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS price_cache (
            coin_id TEXT PRIMARY KEY,
            usd REAL,
            updated_at REAL
        )
    """)
    conn.commit()
    conn.close()


def fetch_price(coin_id: str) -> Optional[float]:
    try:
        url = f"{_CG_BASE}/simple/price?ids={coin_id}&vs_currencies=usd"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, context=_SSL_CTX, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        return data.get(coin_id, {}).get("usd")
    except Exception:
        return None


def snapshot_prices(db_path=None, coin_ids=None, max_age_minutes=5) -> dict[str, dict]:
    _ensure_table(db_path)
    conn = get_conn(db_path)
    now = time.time()
    result = {}
    to_fetch = set(coin_ids or [])
    if not to_fetch:
        # Fetch all mapped protocols
        to_fetch = set(PROTOCOL_TO_COIN.values())
    for cid in list(to_fetch):
        row = conn.execute("SELECT usd, updated_at FROM price_cache WHERE coin_id = ?", (cid,)).fetchone()
        if row and (now - row[1]) < max_age_minutes * 60:
            result[cid] = {"usd": row[0], "cached": True}
            to_fetch.discard(cid)
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
