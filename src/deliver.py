"""Telegram delivery: send decision cards via bot API."""
from __future__ import annotations

import json
import os
import ssl
import urllib.request
from pathlib import Path
from typing import Optional

try:
    import certifi

    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CTX = ssl.create_default_context()

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def _env_key(name: str) -> str | None:
    return os.environ.get(name) or None


def send_card(text: str, topic_id: Optional[str] = None) -> dict:
    """Send a single card to Telegram."""
    token = _env_key("TELEGRAM_BOT_TOKEN")
    chat_id = _env_key("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing")

    url = TELEGRAM_API.format(token=token)
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if topic_id:
        payload["message_thread_id"] = int(topic_id)

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, context=_SSL_CTX, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def deliver(
    cards: list[dict],
    topic_id: Optional[str] = None,
    dry_run: bool = True,
    card_type: str = "decisions",
) -> list[dict]:
    """Deliver cards. If dry_run, print to stdout instead of sending."""
    from src.config import load_delivery
    from src.decide import format_card

    cfg = load_delivery()
    if topic_id is None and card_type:
        topic_id = cfg.get(f"topic_{card_type}_id")

    results = []
    for card in cards:
        text = format_card(card)
        if dry_run:
            print("=" * 40)
            print(text)
            print("=" * 40)
            results.append({"cluster_id": card["cluster_id"], "status": "dry_run"})
        else:
            try:
                send_card(text, topic_id=topic_id)
                results.append({"cluster_id": card["cluster_id"], "status": "sent"})
            except Exception as exc:
                results.append({"cluster_id": card["cluster_id"], "status": "error", "error": str(exc)})
    return results
