"""Paper trading — virtual position tracking."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Optional

from src.db import get_conn


def open_position(cluster_id, protocol, decision, entry_price, size_usd, source_families, signals_count, voice_weight, db_path=None, strategy="conservative"):
    conn = get_conn(db_path)
    cur = conn.execute(
        """INSERT INTO paper_positions
        (cluster_id, protocol, decision, entry_price, size_usd, source_families, signals_count, voice_weight, strategy)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cluster_id, protocol, decision, entry_price, size_usd, source_families, signals_count, voice_weight, strategy),
    )
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid


def snapshot_positions(db_path=None):
    conn = get_conn(db_path)
    positions = conn.execute("SELECT id, protocol, entry_price FROM paper_positions WHERE status = 'open'").fetchall()
    for pos in positions:
        # Placeholder: update with latest price if available
        conn.execute(
            "INSERT INTO position_snapshots (position_id, price_usd, pnl_pct, captured_at) VALUES (?, ?, ?, ?)",
            (pos["id"], pos["entry_price"], 0.0, datetime.now(timezone.utc).isoformat()),
        )
    conn.commit()
    conn.close()


def get_open_positions(db_path=None, strategy=None):
    conn = get_conn(db_path)
    sql = """
        SELECT pp.*, ps.price_usd as latest_price, ps.pnl_pct as latest_pnl_pct
        FROM paper_positions pp
        LEFT JOIN position_snapshots ps ON ps.position_id = pp.id
        WHERE pp.status = 'open'
    """
    params = []
    if strategy:
        sql += " AND pp.strategy = ?"
        params.append(strategy)
    sql += " ORDER BY ps.captured_at DESC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def close_position(pos_id, exit_price, reason, db_path=None):
    conn = get_conn(db_path)
    row = conn.execute("SELECT entry_price FROM paper_positions WHERE id = ?", (pos_id,)).fetchone()
    if not row:
        conn.close()
        return
    entry = row["entry_price"]
    pnl = (exit_price - entry) / entry if entry else 0
    conn.execute(
        "UPDATE paper_positions SET status = 'closed', exit_price = ?, exit_at = ?, pnl_pct = ?, closed_reason = ? WHERE id = ?",
        (exit_price, datetime.now(timezone.utc).isoformat(), pnl, reason, pos_id),
    )
    conn.commit()
    conn.close()
