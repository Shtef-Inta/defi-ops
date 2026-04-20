"""Decision card builder: cluster + wallets + liquidity → brief."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.db import get_conn


def _fetch_open_clusters(conn) -> list[dict]:
    rows = conn.execute(
        """
        SELECT id, protocol, event_key, aspects, voice_weight, contradiction_flag, contradiction_reason
        FROM clusters
        WHERE status = 'open'
        ORDER BY voice_weight DESC, created_at DESC
        """
    ).fetchall()
    clusters = []
    for row in rows:
        clusters.append({
            "id": row[0],
            "protocol": row[1],
            "event_key": row[2],
            "aspects": json.loads(row[3]) if row[3] else [],
            "voice_weight": row[4] or 0.0,
            "contradiction_flag": row[5],
            "contradiction_reason": row[6],
        })
    return clusters


def _fetch_latest_signal(conn, cluster_id: int) -> dict | None:
    row = conn.execute(
        """
        SELECT s.content, s.url, s.sentiment
        FROM signals s
        JOIN cluster_signals cs ON cs.signal_id = s.id
        WHERE cs.cluster_id = ?
        ORDER BY s.captured_at DESC
        LIMIT 1
        """,
        (cluster_id,),
    ).fetchone()
    if not row:
        return None
    return {"content": row[0], "url": row[1], "sentiment": row[2]}


def _has_risk_wallet_activity(conn, hours: int = 24) -> bool:
    """Check if any risk_wallet had a tx in last N hours."""
    row = conn.execute(
        """
        SELECT 1 FROM wallet_tx
        WHERE wallet_group = 'risk_wallets'
          AND datetime(block_time) >= datetime('now', '-{} hours')
        LIMIT 1
        """.format(hours)
    ).fetchone()
    return bool(row)


def build_cards(db_path: Optional[str] = None, max_cards: int = 5) -> list[dict]:
    """Build decision cards from open clusters."""
    conn = get_conn(db_path)
    clusters = _fetch_open_clusters(conn)
    cards: list[dict] = []

    risk_active = _has_risk_wallet_activity(conn)

    for c in clusters:
        if len(cards) >= max_cards:
            break

        signal = _fetch_latest_signal(conn, c["id"])
        text = (signal["content"] if signal else "").strip()
        title = text.split("\n")[0][:80] if text else c["event_key"]

        # Simple stance heuristic
        if c["contradiction_flag"]:
            stance = "⚠️ CONTRADICTION"
        elif risk_active and c["protocol"] in ("aave", "ethena", "uniswap"):
            stance = "⛔ BLOCK (risk wallet active)"
        elif c["voice_weight"] >= 2.0:
            stance = "📊 WATCH closely"
        else:
            stance = "📋 WATCH"

        card = {
            "cluster_id": c["id"],
            "protocol": c["protocol"],
            "event_key": c["event_key"],
            "title": title,
            "stance": stance,
            "weight": round(c["voice_weight"], 2),
            "families": ", ".join(c["aspects"]),
            "url": signal["url"] if signal else None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        cards.append(card)

    conn.close()
    return cards


def format_card(card: dict) -> str:
    lines = [
        f"🚨 {card['protocol'].upper()} — {card['event_key']}",
        f"Title: {card['title']}",
        f"Stance: {card['stance']}",
        f"Weight: {card['weight']} | Families: {card['families']}",
    ]
    if card.get("url"):
        lines.append(f"Link: {card['url']}")
    lines.append(f"ID: {card['cluster_id']} | {card['created_at'][:19]}")
    return "\n".join(lines)
