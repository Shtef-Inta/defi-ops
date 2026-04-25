"""Portfolio tracker: PnL, rebalancing suggestions, heat map."""
from __future__ import annotations

from typing import Optional

from src.db import get_conn


def get_portfolio(db_path: Optional[str] = None) -> dict:
    conn = get_conn(db_path)
    open_pos = conn.execute(
        "SELECT * FROM paper_positions WHERE status = 'open'"
    ).fetchall()
    cols = [d[0] for d in conn.execute("SELECT * FROM paper_positions WHERE 1=0").description]
    closed = conn.execute(
        "SELECT * FROM paper_positions WHERE status = 'closed' ORDER BY closed_at DESC LIMIT 20"
    ).fetchall()
    conn.close()

    open_list = [dict(zip(cols, row)) for row in open_pos]
    closed_list = [dict(zip(cols, row)) for row in closed]

    total_pnl = sum(p.get("pnl_usd", 0) for p in open_list)
    total_exposure = sum(p.get("size_usd", 0) for p in open_list)
    closed_pnl = sum(p.get("pnl_usd", 0) for p in closed_list)

    by_protocol = {}
    for p in open_list:
        proto = p.get("protocol", "unknown").lower()
        by_protocol[proto] = by_protocol.get(proto, {"count": 0, "exposure": 0, "pnl": 0})
        by_protocol[proto]["count"] += 1
        by_protocol[proto]["exposure"] += p.get("size_usd", 0)
        by_protocol[proto]["pnl"] += p.get("pnl_usd", 0)

    return {
        "open_positions": open_list,
        "closed_positions": closed_list,
        "total_open_pnl": total_pnl,
        "total_exposure": total_exposure,
        "closed_pnl_20": closed_pnl,
        "by_protocol": by_protocol,
    }


def rebalance_suggestions(portfolio: dict, max_protocol_pct: float = 0.3) -> list[dict]:
    """Suggest rebalancing if any protocol is overweight."""
    total = portfolio.get("total_exposure", 0)
    if total <= 0:
        return []
    suggestions = []
    for proto, data in portfolio.get("by_protocol", {}).items():
        pct = data["exposure"] / total
        if pct > max_protocol_pct:
            suggestions.append({
                "protocol": proto,
                "current_pct": pct,
                "target_pct": max_protocol_pct,
                "reduce_by_usd": data["exposure"] - total * max_protocol_pct,
                "reason": f"Overweight {proto}: {pct:.1%} > {max_protocol_pct:.1%}",
            })
    return suggestions
