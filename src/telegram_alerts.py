"""Telegram alerting: one daily brief + optional immediate trade alerts."""
from __future__ import annotations

import json
import os
import ssl
import urllib.request
from typing import Optional

import certifi

_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
_GROUP_ID = os.environ.get("TELEGRAM_GROUP_ID", "-1003981168546")
_TOPIC_SCHEMA = "203"
_TOPIC_ALERTS = "206"

_SSL_CTX = ssl.create_default_context(cafile=certifi.where())


def _send(text: str, topic_id: Optional[str] = None, parse_mode: str = "HTML") -> dict:
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


def send_daily_brief(analyses: list[dict], positions: dict) -> dict:
    """Send one consolidated daily brief."""
    from src.brief import format_daily_brief
    text = format_daily_brief(analyses, positions)
    return _send(text, topic_id=_TOPIC_SCHEMA)


def send_trade_alert(analysis: dict) -> dict:
    """Send a compact alert for an immediate trade opportunity."""
    from src.brief import format_trade_alert
    text = format_trade_alert(analysis)
    return _send(text, topic_id=_TOPIC_SCHEMA)


def send_error_alert(message: str) -> dict:
    text = f"🚨 <b>Ошибка системы</b>\n<pre>{message[:400]}</pre>"
    return _send(text, topic_id=_TOPIC_ALERTS)


def send_risk_alert(protocol: str, risk_flags: list[str]) -> dict:
    text = f"⚠️ <b>Риск: {protocol.upper()}</b>\n" + "\n".join(f"• {f}" for f in risk_flags)
    return _send(text, topic_id=_TOPIC_ALERTS)
