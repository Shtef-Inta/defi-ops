"""Brief formatting with real trade recommendations."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional


def format_digest(analyses: list[dict]) -> str:
    """Return a human-readable digest of analyses."""
    if not analyses:
        return "📭 Нет активных сигналов."

    lines = [f"📊 <b>Дайджест сигналов</b> — {datetime.now(timezone.utc).strftime('%H:%M UTC')}", ""]

    for i, a in enumerate(analyses[:5], 1):
        proto = a.get("protocol", "unknown").upper()
        action = a.get("action_now", "—")
        stance = a.get("capital_stance", {}) or {}
        deploy = stance.get("deploy_now_usd", 0)
        wait = stance.get("keep_waiting_usd", 0)
        conviction = a.get("conviction", "SINGLE")
        signals = a.get("signals_count", 0)
        weight = a.get("voice_weight", 0)
        tvl_data = a.get("liquidity") or {}
        tvl_b = (tvl_data.get("tvl") or 0) / 1e9

        emoji = {
            "готовить вход": "🟢",
            "наблюдать": "🟡",
            "ждать": "🔵",
            "избегать": "🔴",
        }.get(action, "⚪")

        lines.append(f"{emoji} <b>{i}. {proto}</b> | {action.upper()}")
        lines.append(f"   Conviction: {conviction} | Signals: {signals} | Weight: {weight:.1f}")
        if deploy > 0:
            lines.append(f"   💰 Deploy: ${deploy:,.0f} | Leverage: {a.get('leverage', 1)}x")
        if wait > 0:
            lines.append(f"   ⏳ Wait: ${wait:,.0f}")
        lines.append(f"   TVL: ${tvl_b:.2f}B")
        if a.get("contradiction_reason"):
            lines.append(f"   ⚠️ Контраргумент: {a['contradiction_reason'][:80]}...")
        lines.append("")

    return "\n".join(lines)


def format_trade_card(a: dict) -> str:
    """Format a single analysis as a trade recommendation card."""
    proto = a.get("protocol", "unknown").upper()
    action = a.get("action_now", "—")
    stance = a.get("capital_stance", {}) or {}
    deploy = stance.get("deploy_now_usd", 0)
    reason = stance.get("reason", "")
    next_trigger = stance.get("next_trigger", "")
    conviction = a.get("conviction", "SINGLE")
    leverage = a.get("leverage", 1)
    expiry = a.get("expiry", "—")
    signals = a.get("signals_count", 0)
    weight = a.get("voice_weight", 0)
    families = ", ".join(a.get("source_families", []))
    confirmed = ", ".join(a.get("confirmed_by", []))
    not_confirmed = ", ".join(a.get("not_confirmed", []))
    risk_flags = a.get("risk_flags", [])
    contradiction = a.get("contradiction_reason")
    what = a.get("what_happened", "")[:200]
    why = a.get("why_moves_money", "")[:200]
    entry = a.get("trigger_for_entry", "—")
    exit_trig = a.get("trigger_for_exit", "—")
    tvl_data = a.get("liquidity") or {}
    tvl_b = (tvl_data.get("tvl") or 0) / 1e9
    tvl_delta = tvl_data.get("tvl_24h_delta") or 0
    tvl_pct = (tvl_delta / (tvl_data.get("tvl") or 1)) * 100 if tvl_data.get("tvl") else 0

    emoji_action = {
        "готовить вход": "🟢 ВХОД",
        "наблюдать": "🟡 НАБЛЮДЕНИЕ",
        "ждать": "🔵 ОЖИДАНИЕ",
        "избегать": "🔴 ИЗБЕГАТЬ",
    }.get(action, "⚪")

    lines = [
        f"<b>{emoji_action} — {proto}</b>",
        f"<i>{a.get('event_key', '')}</i>",
        "",
        f"📌 <b>Рекомендация:</b> {action}",
        f"💰 <b>Размер позиции:</b> ${deploy:,.0f}" if deploy > 0 else "💰 <b>Размер позиции:</b> $0 (ожидание)",
        f"📈 <b>Плечо:</b> {leverage}x | <b>Убеждённость:</b> {conviction}",
        f"⏳ <b>Срок:</b> до {expiry}",
        "",
        f"📊 <b>Метрики:</b>",
        f"   Сигналов: {signals} | Вес: {weight:.1f}",
        f"   TVL: ${tvl_b:.2f}B (Δ24h: {tvl_pct:+.2f}%)",
        f"   Источники: {families}",
        "",
        f"✅ <b>Подтверждено:</b> {confirmed or '—'}",
    ]
    if not_confirmed:
        lines.append(f"❌ <b>Не подтверждено:</b> {not_confirmed}")
    if risk_flags:
        lines.append(f"🚨 <b>Риски:</b> {', '.join(risk_flags)}")
    if contradiction:
        lines.append(f"⚠️ <b>Противоречие:</b> {contradiction[:120]}")
    lines.extend([
        "",
        f"🎯 <b>Триггер входа:</b> {entry}",
        f"🛑 <b>Триггер выхода:</b> {exit_trig}",
        "",
        f"📰 <b>Что произошло:</b> {what}...",
        f"💡 <b>Почему движется капитал:</b> {why}...",
    ])
    if reason:
        lines.append(f"")
        lines.append(f"📝 <b>Обоснование:</b> {reason}")
    if next_trigger:
        lines.append(f"🔔 <b>Следующий триггер:</b> {next_trigger}")

    return "\n".join(lines)
