"""Paper trading engine with strategy tagging, PnL tracking, and snapshots."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Optional

from src.db import get_conn


def open_position(
    cluster_id: int,
    protocol: str,
    decision: str,
    entry_price: float,
    size_usd: float,
    source_families: str,
    signals_count: int,
    voice_weight: float,
    db_path: Optional[str] = None,
    strategy: str = "conservative",
    leverage: int = 1,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
) -> int:
    conn = get_conn(db_path)
    cur = conn.execute(
        """
        INSERT INTO paper_positions
            (cluster_id, protocol, decision, entry_price, size_usd,
             source_families, signals_count, voice_weight, strategy,
             leverage, stop_loss, take_profit, status, opened_at, pnl_usd)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, 0)
        """,
        (cluster_id, protocol, decision, entry_price, size_usd,
         source_families, signals_count, voice_weight, strategy,
         leverage, stop_loss, take_profit,
         datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    return cur.lastrowid


def snapshot_positions(db_path: Optional[str] = None) -> dict:
    conn = get_conn(db_path)
    cur = conn.execute(
        """
        SELECT COUNT(*), SUM(size_usd), SUM(pnl_usd)
        FROM paper_positions WHERE status = 'open'
        """
    )
    total, exposure, pnl = cur.fetchone()
    conn.close()
    return {
        "open_count": total or 0,
        "total_exposure": exposure or 0,
        "unrealized_pnl": pnl or 0,
    }


def get_open_positions(db_path: Optional[str] = None, strategy: Optional[str] = None) -> list[dict]:
    conn = get_conn(db_path)
    sql = "SELECT * FROM paper_positions WHERE status = 'open'"
    params = ()
    if strategy:
        sql += " AND strategy = ?"
        params = (strategy,)
    cur = conn.execute(sql, params)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    conn.close()
    return [dict(zip(cols, row)) for row in rows]


def close_position(pos_id: int, exit_price: float, reason: str, db_path: Optional[str] = None) -> dict:
    conn = get_conn(db_path)
    row = conn.execute(
        "SELECT entry_price, size_usd, leverage FROM paper_positions WHERE id = ?",
        (pos_id,),
    ).fetchone()
    if not row:
        conn.close()
        return {"error": "position not found"}
    entry_price, size_usd, leverage = row
    pnl = (exit_price - entry_price) / entry_price * size_usd * leverage if entry_price else 0
    conn.execute(
        """
        UPDATE paper_positions
        SET status = 'closed', exit_price = ?, closed_at = ?, close_reason = ?, pnl_usd = ?
        WHERE id = ?
        """,
        (exit_price, datetime.now(timezone.utc).isoformat(), reason, pnl, pos_id),
    )
    conn.commit()
    conn.close()
    return {"id": pos_id, "pnl_usd": pnl, "reason": reason}


def update_position_pnl(pos_id: int, current_price: float, db_path: Optional[str] = None) -> float:
    conn = get_conn(db_path)
    row = conn.execute(
        "SELECT entry_price, size_usd, leverage FROM paper_positions WHERE id = ? AND status = 'open'",
        (pos_id,),
    ).fetchone()
    if not row:
        conn.close()
        return 0.0
    entry_price, size_usd, leverage = row
    pnl = (current_price - entry_price) / entry_price * size_usd * leverage if entry_price else 0
    conn.execute("UPDATE paper_positions SET pnl_usd = ? WHERE id = ?", (pnl, pos_id))
    conn.commit()
    conn.close()
    return pnl
