"""Yield opportunity ingest from DeFiLlama and internal yield scanner."""
from __future__ import annotations

from typing import Optional

from src.yield_scanner import scan


def ingest_yields(db_path: Optional[str] = None) -> dict:
    result = scan(db_path)
    return {
        "inserted": 0,
        "anomalies": len(result.get("anomalies", [])),
        "new_vaults": len(result.get("new_vaults", [])),
        "note": "yield data scanned; anomalies logged to stdout",
    }
