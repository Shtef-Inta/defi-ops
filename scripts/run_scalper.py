#!/usr/bin/env python3
"""Run scalper strategy loop."""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.analyze import analyze_clusters
from src.paper_trading import get_open_positions, close_position, update_position_pnl
from src.prices import snapshot_prices, PROTOCOL_TO_COIN
from src.strategy_scalper import should_enter, sizing, should_exit


def main():
    print("[run_scalper] Started")
    while True:
        analyses = analyze_clusters(max_items=10, contradiction_threshold=1, ignore_contradiction=True)
        open_pos = get_open_positions(strategy="scalper")
        open_protocols = {p["protocol"].lower(): p for p in open_pos}

        # Check exits
        for pos in open_pos:
            proto = pos["protocol"].lower()
            coin_id = PROTOCOL_TO_COIN.get(proto)
            if not coin_id:
                continue
            prices = snapshot_prices(max_age_minutes=5) or {}
            price_data = prices.get(coin_id, {})
            current = float(price_data.get("usd", 0))
            if current > 0:
                update_position_pnl(pos["id"], current)
                reason = should_exit(pos, current)
                if reason:
                    close_position(pos["id"], current, f"scalper_{reason}")
                    print(f"[scalper] Closed {proto} at {current} ({reason})")

        # Check entries
        for a in analyses:
            proto = a.get("protocol", "").lower()
            if not proto or proto in open_protocols:
                continue
            if should_enter(a):
                cfg = sizing(a)
                coin_id = PROTOCOL_TO_COIN.get(proto)
                prices = snapshot_prices(max_age_minutes=5) or {}
                price_data = prices.get(coin_id, {})
                current = float(price_data.get("usd", 0))
                if current > 0:
                    from src.paper_trading import open_position
                    pos_id = open_position(
                        cluster_id=a["cluster_id"],
                        protocol=a["protocol"],
                        decision="entered",
                        entry_price=current,
                        size_usd=cfg["size_usd"],
                        source_families=",".join(a.get("source_families", [])),
                        signals_count=a.get("signals_count", 0),
                        voice_weight=a.get("voice_weight", 0),
                        strategy="scalper",
                        leverage=cfg["leverage"],
                        stop_loss=current * (1 + cfg["stop_loss_pct"] / 100),
                        take_profit=current * (1 + cfg["take_profit_pct"] / 100),
                    )
                    print(f"[scalper] Opened {proto} at {current} (id={pos_id})")

        time.sleep(300)  # 5 min


if __name__ == "__main__":
    main()
