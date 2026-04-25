"""Telegram alerting with rich trade cards and strategy comparisons."""
from __future__ import annotations

import json
import os
import urllib.request
import ssl
from typing import Optional

_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
_GROUP_ID = os.environ.get("TELEGRAM_GROUP_ID", "-1003981168546")
_TOPIC_SCHEMA = "203"      # Main DeFi/operator topic
_TOPIC_ALERTS = "206"      # Risk/alerts
_TOPIC_SIGNALS = "208"     # Raw signals
_TOPIC_TESTS = "209"       # Test messages

_SSL_CTX = ssl.create_default_context()


def _send(text: str, topic_id: Optional[str] = None, parse_mode: str = "HTML"):
    if not _BOT_TOKEN:
        return {"ok": False, "error": "no token"}
    url = f"https://api.telegram.org/bot{_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": _GROUP_ID,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }
    if topic_id:
        payload["message_thread_id"] = int(topic_id)
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, context=_SSL_CTX, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def send_pipeline_digest(new_signals: int = 0, analyses: Optional[list] = None):
    """Send a digest of the latest pipeline run."""
    from src.brief import format_digest
    text = format_digest(analyses or [])
    return _send(text, topic_id=_TOPIC_SCHEMA)


def send_strategy_comparison(all_analyses: dict[str, list[dict]]):
    """Send a comparison of conservative vs aggressive vs ultra strategies."""
    lines = ["<b>📊 Сравнение стратегий</b>", ""]
    for name, analyses in all_analyses.items():
        buy = sum(1 for a in analyses if a.get("action_now") == "готовить вход")
        wait = sum(1 for a in analyses if a.get("action_now") == "ждать")
        watch = sum(1 for a in analyses if a.get("action_now") == "наблюдать")
        avoid = sum(1 for a in analyses if a.get("action_now") == "избегать")
        emoji = {"conservative": "🛡️", "aggressive": "⚔️", "ultra": "🔥"}.get(name, "📈")
        lines.append(f"{emoji} <b>{name.upper()}</b>: {len(analyses)} analyses | 🟢{buy} 🔵{wait} 🟡{watch} 🔴{avoid}")
        for a in analyses[:3]:
            action_emoji = {"готовить вход": "🟢", "наблюдать": "🟡", "ждать": "🔵", "избегать": "🔴"}.get(a.get("action_now"), "⚪")
            deploy = (a.get("capital_stance") or {}).get("deploy_now_usd", 0)
            lines.append(f"   {action_emoji} {a.get('protocol', '?').upper()} — ${deploy:,.0f} | {a.get('conviction', '?')} | {a.get('leverage', 1)}x")
        lines.append("")
    return _send("\n".join(lines), topic_id=_TOPIC_SCHEMA)


def send_trade_card(analysis: dict, topic_id: Optional[str] = None):
    """Send a single trade recommendation card."""
    from src.brief import format_trade_card
    text = format_trade_card(analysis)
    return _send(text, topic_id=topic_id or _TOPIC_SCHEMA)


def send_error_alert(message: str):
    """Send an error alert to the alerts topic."""
    text = f"🚨 <b>Pipeline Error</b>\n<pre>{message[:400]}</pre>"
    return _send(text, topic_id=_TOPIC_ALERTS)


def send_risk_alert(protocol: str, risk_flags: list[str]):
    """Send a risk alert."""
    text = f"⚠️ <b>Risk Alert: {protocol.upper()}</b>\n" + "\n".join(f"• {f}" for f in risk_flags)
    return _send(text, topic_id=_TOPIC_ALERTS)
