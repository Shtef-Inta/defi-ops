"""Risk-adjusted sizing: Kelly criterion, volatility regime, portfolio heat."""
from __future__ import annotations

import math
from typing import Optional


def kelly_criterion(win_rate: float, avg_win: float, avg_loss: float) -> float:
    """Full Kelly fraction. Returns 0 if edge is negative."""
    b = avg_win / avg_loss if avg_loss > 0 else 1.0
    q = 1 - win_rate
    kelly = (b * win_rate - q) / b if b > 0 else 0.0
    return max(0.0, min(kelly, 1.0))


def kelly_size(
    bankroll: float,
    win_rate: float,
    avg_win: float,
    avg_loss: float,
    conviction: str = "MEDIUM",
) -> dict:
    """Return position size with Kelly scaling by conviction."""
    full_kelly = kelly_criterion(win_rate, avg_win, avg_loss)
    # Scale by conviction
    scale = {"SINGLE": 0.25, "MEDIUM": 0.5, "HIGH": 0.75, "SPECULATIVE": 0.125, "DEGEN": 1.0}.get(conviction, 0.25)
    fraction = full_kelly * scale
    deploy = bankroll * fraction
    return {
        "full_kelly": full_kelly,
        "scaled_fraction": fraction,
        "deploy_usd": deploy,
        "conviction_scale": scale,
    }


def portfolio_heat(positions: list[dict], max_heat: float = 0.5) -> dict:
    """Calculate portfolio heat map and warn if overexposed."""
    total_exposure = sum(p.get("size_usd", 0) for p in positions)
    by_protocol = {}
    for p in positions:
        proto = p.get("protocol", "unknown").lower()
        by_protocol[proto] = by_protocol.get(proto, 0) + p.get("size_usd", 0)
    heat = {proto: exp / total_exposure if total_exposure else 0 for proto, exp in by_protocol.items()}
    max_proto = max(heat, key=heat.get) if heat else None
    return {
        "total_exposure": total_exposure,
        "protocol_heat": heat,
        "max_protocol": max_proto,
        "max_protocol_pct": heat.get(max_proto, 0) if max_proto else 0,
        "overheated": any(h > max_heat for h in heat.values()),
    }


def suggest_size(analysis: dict, bankroll: float = 100_000, current_positions: Optional[list] = None) -> dict:
    """Suggest position size for an analysis."""
    conviction = analysis.get("conviction", "MEDIUM")
    # Default win/loss assumptions by conviction
    defaults = {
        "SINGLE": (0.45, 0.15, 0.05),
        "MEDIUM": (0.50, 0.18, 0.05),
        "HIGH": (0.60, 0.25, 0.04),
        "SPECULATIVE": (0.35, 0.30, 0.08),
        "DEGEN": (0.30, 0.50, 0.10),
    }
    win_rate, avg_win, avg_loss = defaults.get(conviction, (0.50, 0.15, 0.05))
    kelly = kelly_size(bankroll, win_rate, avg_win, avg_loss, conviction)
    # Reduce if portfolio heat is high
    if current_positions:
        heat = portfolio_heat(current_positions)
        if heat["overheated"]:
            kelly["deploy_usd"] *= 0.5
            kelly["heat_reduction"] = True
    return kelly
