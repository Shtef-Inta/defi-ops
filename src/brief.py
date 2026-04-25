"""Brief formatting with human-readable trade recommendations."""
from __future__ import annotations

import re
from datetime import datetime, timezone


def _clean(text: str) -> str:
    return re.sub(r'<[^>]+>', '', text)


def _dedupe_by_protocol(analyses: list[dict]) -> list[dict]:
    seen = {}
    for a in analyses:
        proto = a.get("protocol", "").lower()
        if not proto:
            continue
        # Keep the one with highest deploy_usd (most actionable)
        existing = seen.get(proto)
        if existing is None:
            seen[proto] = a
        else:
            existing_deploy = (existing.get("capital_stance") or {}).get("deploy_now_usd", 0)
            new_deploy = (a.get("capital_stance") or {}).get("deploy_now_usd", 0)
            if new_deploy > existing_deploy:
                seen[proto] = a
    return list(seen.values())


def format_daily_brief(analyses: list[dict], positions: dict) -> str:
    """One beautiful message per cycle with actionable recommendations."""
    if not analyses:
        return "📭 Сегодня нет сильных сигналов. Ждём лучших точек входа."

    analyses = _dedupe_by_protocol(analyses)
    now = datetime.now(timezone.utc).strftime("%d.%m %H:%M UTC")
    buy_signals = [a for a in analyses if a.get("action_now") == "готовить вход"]
    watch_signals = [a for a in analyses if a.get("action_now") == "наблюдать"]
    wait_signals = [a for a in analyses if a.get("action_now") == "ждать"]

    lines = [f"📊 <b>Ежедневный брифинг</b> — {now}", ""]

    # Market context
    lines.append("<b>Рынок:</b> нейтральный режим | Рекомендуемая доля капитала: 50-75%")
    lines.append("")

    # BUY signals
    if buy_signals:
        lines.append(f"🟢 <b>Готовы к входу ({len(buy_signals)})</b>")
        lines.append("   Эти протоколы показывают сильные сигналы для покупки.")
        for a in buy_signals[:5]:
            proto = a.get("protocol", "").upper()
            stance = a.get("capital_stance", {}) or {}
            size = stance.get("deploy_now_usd", 0)
            lev = a.get("leverage", 1)
            conviction = a.get("conviction", "?")
            tvl_data = a.get("liquidity") or {}
            tvl_b = (tvl_data.get("tvl") or 0) / 1e9
            why = _clean(a.get("why_moves_money", ""))[:80]
            lines.append(f"   • <b>{proto}</b> — ${size:,.0f} | {lev}x | TVL ${tvl_b:.1f}B | {conviction}")
            if why:
                lines.append(f"     💡 {why}...")
        lines.append("")

    # WATCH signals
    if watch_signals:
        lines.append(f"🟡 <b>На наблюдении ({len(watch_signals)})</b>")
        lines.append("   Есть потенциал, но пока рано входить.")
        for a in watch_signals[:3]:
            proto = a.get("protocol", "").upper()
            reason = (a.get("capital_stance") or {}).get("reason", "")
            lines.append(f"   • {proto} — {reason[:80]}")
        lines.append("")

    # WAIT signals
    if wait_signals:
        lines.append(f"🔵 <b>Рано входить ({len(wait_signals)})</b>")
        lines.append("   Сигналы слабые или противоречивые. Ждём.")
        for a in wait_signals[:3]:
            proto = a.get("protocol", "").upper()
            lines.append(f"   • {proto} — ждём подтверждения сигналов")
        lines.append("")

    # Portfolio summary
    lines.append("<b>Ваш портфель:</b>")
    for strategy, data in positions.items():
        if data.get("count", 0) > 0:
            pnl = data.get("unrealized_pnl_usd", 0)
            emoji = "🟢" if pnl >= 0 else "🔴"
            lines.append(f"   {strategy}: {data['count']} поз. | ${data['exposure_usd']:,.0f} | {emoji} ${pnl:,.0f}")
    if not any(d.get("count", 0) > 0 for d in positions.values()):
        lines.append("   Пока нет открытых позиций.")

    lines.append("")
    lines.append("<b>Как действовать:</b>")
    lines.append("   Напиши <b>=ПОДПИСАТЬ НАЗВАНИЕ</b> — открою сделку вручную.")
    lines.append("   Например: <b>=ПОДПИСАТЬ JUPITER</b>")

    return "\n".join(lines)


def format_trade_alert(a: dict) -> str:
    """Compact single-trade alert for immediate action."""
    proto = a.get("protocol", "").upper()
    action = a.get("action_now", "")
    stance = a.get("capital_stance", {}) or {}
    size = stance.get("deploy_now_usd", 0)
    lev = a.get("leverage", 1)
    conviction = a.get("conviction", "?")
    why = _clean(a.get("why_moves_money", ""))[:100]
    tvl_data = a.get("liquidity") or {}
    tvl_b = (tvl_data.get("tvl") or 0) / 1e9

    emoji = {"готовить вход": "🟢", "наблюдать": "🟡", "ждать": "🔵", "избегать": "🔴"}.get(action, "⚪")

    lines = [
        f"{emoji} <b>{proto}</b> — {action.upper()}",
        f"💰 Размер: ${size:,.0f} | Плечо: {lev}x | Уверенность: {conviction}",
        f"📊 TVL: ${tvl_b:.1f}B | Сигналов: {a.get('signals_count', 0)}",
    ]
    if why:
        lines.append(f"💡 {why}...")
    if action == "готовить вход":
        lines.append(f"👉 Ответь <b>=ПОДПИСАТЬ {proto}</b> для исполнения")
    return "\n".join(lines)


def format_digest(analyses: list[dict]) -> str:
    """Legacy: kept for compatibility."""
    return format_daily_brief(analyses, {})
