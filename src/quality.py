"""Position quality metrics and summaries."""
from __future__ import annotations

import sqlite3
from typing import Optional


def get_conn(db_path: Optional[str] = None):
    from src.db import get_conn as _get_conn
    return _get_conn(db_path)


def open_positions_summary(db_path: Optional[str] = None) -> dict:
    conn = get_conn(db_path)
    cur = conn.execute("SELECT COUNT(*) FROM paper_positions WHERE status = 'open'")
    total = cur.fetchone()[0]
    cur = conn.execute("SELECT SUM(pnl_usd) FROM paper_positions WHERE status = 'open'")
    pnl = cur.fetchone()[0] or 0
    cur = conn.execute("SELECT SUM(size_usd) FROM paper_positions WHERE status = 'open'")
    exposure = cur.fetchone()[0] or 0
    conn.close()
    return {"total_open": total, "unrealized_pnl_usd": pnl, "total_exposure_usd": exposure}


def open_positions_by_strategy(db_path: Optional[str] = None) -> dict[str, dict]:
    conn = get_conn(db_path)
    cur = conn.execute(
        """
        SELECT strategy, COUNT(*), SUM(pnl_usd), SUM(size_usd)
        FROM paper_positions
        WHERE status = 'open'
        GROUP BY strategy
        """
    )
    result = {}
    for row in cur.fetchall():
        strategy, count, pnl, exposure = row
        result[strategy] = {
            "count": count,
            "unrealized_pnl_usd": pnl or 0,
            "exposure_usd": exposure or 0,
        }
    conn.close()
    return result
