"""Swing strategy: medium hold, trend following, lower leverage."""
from __future__ import annotations

from typing import Optional


def should_enter(analysis: dict) -> bool:
    """Swing enters on confirmed signals with good conviction."""
    action = analysis.get("action_now")
    if action not in ("готовить вход", "наблюдать"):
        return False
    conviction = analysis.get("conviction", "SINGLE")
    return conviction in ("HIGH", "MEDIUM")


def sizing(analysis: dict) -> dict:
    """Moderate sizing for swing."""
    stance = analysis.get("capital_stance", {}) or {}
    base = stance.get("deploy_now_usd", 10000)
    return {
        "size_usd": base,
        "leverage": 3,
        "stop_loss_pct": -5.0,
        "take_profit_pct": 15.0,
        "max_hold_hours": 72,
    }


def should_exit(position: dict, current_price: float) -> Optional[str]:
    """Exit on wider stops or trend reversal signals."""
    entry = position.get("entry_price", 0)
    if entry <= 0:
        return None
    pct = (current_price - entry) / entry * 100
    if pct <= -5.0:
        return "stop_loss"
    if pct >= 15.0:
        return "take_profit"
    return None
