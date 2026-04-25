"""Execution helpers: pre-fill trade parameters for manual execution."""
from __future__ import annotations

from typing import Optional


def prefill_trade(
    protocol: str,
    direction: str,  # long / short
    entry_price: float,
    size_usd: float,
    leverage: int = 1,
    stop_loss_pct: float = -5.0,
    take_profit_pct: float = 15.0,
    rationale: str = "",
) -> dict:
    """Return a pre-filled trade brief for operator approval."""
    stop = entry_price * (1 + stop_loss_pct / 100) if direction == "long" else entry_price * (1 - stop_loss_pct / 100)
    target = entry_price * (1 + take_profit_pct / 100) if direction == "long" else entry_price * (1 - take_profit_pct / 100)
    liquidation = entry_price * (1 - 90 / leverage / 100) if direction == "long" else entry_price * (1 + 90 / leverage / 100)
    return {
        "protocol": protocol,
        "direction": direction,
        "entry_price": round(entry_price, 6),
        "size_usd": round(size_usd, 2),
        "leverage": leverage,
        "notional": round(size_usd * leverage, 2),
        "stop_loss": round(stop, 6),
        "take_profit": round(target, 6),
        "liquidation_estimate": round(liquidation, 6),
        "risk_reward": abs(take_profit_pct / stop_loss_pct) if stop_loss_pct != 0 else 0,
        "rationale": rationale,
        "status": "pending_approval",
    }


def format_for_telegram(trade: dict) -> str:
    """Format a pre-filled trade for Telegram."""
    return (
        f"🎯 <b>ПРЕДВАРИТЕЛЬНАЯ СДЕЛКА</b>\n"
        f"<b>{trade['protocol'].upper()}</b> — {trade['direction'].upper()}\n"
        f"\n"
        f"💰 Размер: ${trade['size_usd']:,.0f}\n"
        f"📈 Плечо: {trade['leverage']}x (notional ${trade['notional']:,.0f})\n"
        f"🚪 Вход: ${trade['entry_price']}\n"
        f"🛑 Стоп: ${trade['stop_loss']}\n"
        f"🎯 Цель: ${trade['take_profit']}\n"
        f"💀 Ликвидация ≈ ${trade['liquidation_estimate']}\n"
        f"⚖️ R:R = 1:{trade['risk_reward']:.1f}\n"
        f"\n"
        f"📝 Обоснование:\n{trade['rationale'][:300]}\n"
        f"\n"
        f"Ответь <b>=ПОДПИСАТЬ</b> для исполнения."
    )
