"""Whale alert aggregator: Arkham + Etherscan large transfers."""
from __future__ import annotations

from typing import Optional

from src.ingest_arkham import ingest_whale_alerts


def check_whale_alerts(db_path: Optional[str] = None) -> dict:
    """Run all whale alert sources."""
    arkham = ingest_whale_alerts(db_path)
    return {
        "arkham_inserted": arkham.get("inserted", 0),
        "total_inserted": arkham.get("inserted", 0),
    }
