"""Wallet flow classification and divergence detection."""
from __future__ import annotations

import os
import sqlite3
from typing import Optional

from src.db import get_conn


def classify_wallet_txs(db_path: Optional[str] = None) -> dict:
    """Classify raw wallet_tx rows into inflow/outflow/contract_interaction."""
    conn = get_conn(db_path)
    rows = conn.execute(
        "SELECT id, address, tx_from, tx_to, tx_input FROM wallet_tx WHERE tx_type IS NULL"
    ).fetchall()

    updated = 0
    for row in rows:
        tx_id, address, tx_from, tx_to, tx_input = row
        address = (address or "").lower()
        tx_from = (tx_from or "").lower()
        tx_to = (tx_to or "").lower()
        tx_input = (tx_input or "")

        if tx_input and tx_input != "0x":
            tx_type = "contract_interaction"
        elif tx_to == address and tx_from != address:
            tx_type = "inflow"
        elif tx_from == address and tx_to != address:
            tx_type = "outflow"
        else:
            tx_type = "contract_interaction"

        conn.execute(
            "UPDATE wallet_tx SET tx_type = ? WHERE id = ?",
            (tx_type, tx_id),
        )
        updated += 1

    conn.commit()
    conn.close()
    return {"classified": updated}


def enrich_wallet_labels(db_path: Optional[str] = None, max_lookups: int = 50) -> dict:
    """Fetch Arkham labels for counterparties and update counterparties column."""
    from src.ingest_wallets import _fetch_arkham_labels

    conn = get_conn(db_path)
    api_key = os.environ.get("ARKHAM_API_KEY")
    if not api_key:
        conn.close()
        return {"lookups": 0}

    rows = conn.execute(
        "SELECT id, tx_from, tx_to FROM wallet_tx WHERE counterparties IS NULL LIMIT ?",
        (max_lookups,),
    ).fetchall()

    labels: dict[str, str] = {}
    updated = 0

    for row in rows:
        tx_id, tx_from, tx_to = row
        addrs = {a.lower() for a in (tx_from, tx_to) if a}
        names: list[str] = []
        for addr in addrs:
            if addr not in labels:
                data = _fetch_arkham_labels(addr, api_key)
                label = data.get("arkhamLabel", {}).get("name") or data.get("arkhamEntity", {}).get("name")
                labels[addr] = label or ""
            if labels[addr]:
                names.append(labels[addr])

        if names:
            conn.execute(
                "UPDATE wallet_tx SET counterparties = ? WHERE id = ?",
                (", ".join(names), tx_id),
            )
            updated += 1

    conn.commit()
    conn.close()
    return {"lookups": len(labels), "updated": updated}


def detect_divergence(db_path: Optional[str] = None, hours: int = 24) -> list[dict]:
    """Detect if watched wallets show unusual activity vs recent clusters."""
    conn = get_conn(db_path)
    rows = conn.execute(
        f"""
        SELECT wallet_group, COUNT(*) as cnt
        FROM wallet_tx
        WHERE tx_type = 'outflow'
          AND datetime(block_time) >= datetime('now', '-{hours} hours')
        GROUP BY wallet_group
        """
    ).fetchall()
    conn.close()
    return [{"wallet_group": r[0], "outflows": r[1]} for r in rows]
