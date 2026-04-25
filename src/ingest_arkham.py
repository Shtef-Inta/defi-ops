"""Arkham intelligence ingest: whale alerts, entity labels, smart money flows."""
from __future__ import annotations

import json
import os
import urllib.request
import ssl
from datetime import datetime, timezone
from typing import Optional

from src.db import get_conn

_API_KEY = os.environ.get("ARKHAM_API_KEY", "")
_SSL_CTX = ssl.create_default_context()
_BASE = "https://api.arkhamintelligence.com"


def _req(path: str) -> dict:
    if not _API_KEY:
        return {}
    url = f"{_BASE}{path}"
    req = urllib.request.Request(url, headers={"Accept": "application/json", "API-Key": _API_KEY})
    try:
        with urllib.request.urlopen(req, context=_SSL_CTX, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return {}


def fetch_entity_transfers(entity: str, limit: int = 20) -> list[dict]:
    data = _req(f"/v1/transfers?entity={entity}&limit={limit}")
    return data.get("transfers", [])


def ingest_whale_alerts(db_path: Optional[str] = None) -> dict:
    """Ingest recent large transfers for watched entities."""
    conn = get_conn(db_path)
    inserted = 0
    entities = ["vitalik.eth", "binance", "aave", "uniswap"]
    for entity in entities:
        for tx in fetch_entity_transfers(entity, limit=10):
            usd = tx.get("usdValue", 0)
            if usd < 100_000:
                continue
            source_id = f"arkham:{tx.get('hash', '')}"
            existing = conn.execute("SELECT 1 FROM signals WHERE source_id = ?", (source_id,)).fetchone()
            if existing:
                continue
            conn.execute(
                """
                INSERT INTO signals (source_family, source_handle, protocol, event_key, content, url,
                                     captured_at, asset_symbols, sentiment, raw_payload, source_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "onchain_analytics",
                    entity,
                    tx.get("tokenSymbol", "").lower(),
                    f"whale_transfer_{entity}",
                    f"Transfer {tx.get('value', 0)} {tx.get('tokenSymbol', '')} (${usd:,.0f}) from {tx.get('from', '?')} to {tx.get('to', '?')}",
                    f"https://arkhamintelligence.com/tx/{tx.get('hash', '')}",
                    datetime.now(timezone.utc).isoformat(),
                    tx.get("tokenSymbol", ""),
                    "neutral",
                    json.dumps(tx, ensure_ascii=False),
                    source_id,
                ),
            )
            inserted += 1
    conn.commit()
    conn.close()
    return {"inserted": inserted}
