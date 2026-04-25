"""Scalper strategy: tight stops, quick exits, high frequency."""
from __future__ import annotations

from typing import Optional


def should_enter(analysis: dict) -> bool:
    """Scalper enters on any actionable signal with high liquidity."""
    action = analysis.get("action_now")
    if action != "готовить вход":
        return False
    liquidity = analysis.get("liquidity") or {}
    tvl = liquidity.get("tvl", 0)
    return tvl > 10_000_000  # $10M min TVL


def sizing(analysis: dict) -> dict:
    """Aggressive sizing for scalper."""
    stance = analysis.get("capital_stance", {}) or {}
    base = stance.get("deploy_now_usd", 5000)
    return {
        "size_usd": base * 1.5,
        "leverage": 5,
        "stop_loss_pct": -2.0,
        "take_profit_pct": 4.0,
        "max_hold_hours": 4,
    }


def should_exit(position: dict, current_price: float) -> Optional[str]:
    """Exit if stop or target hit, or hold time exceeded."""
    entry = position.get("entry_price", 0)
    if entry <= 0:
        return None
    pct = (current_price - entry) / entry * 100
    if pct <= -2.0:
        return "stop_loss"
    if pct >= 4.0:
        return "take_profit"
    return None
