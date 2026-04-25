"""Telegram delivery with real trade cards and strategy routing."""
from __future__ import annotations

import json
import os
import urllib.request
import ssl
from typing import Optional

import certifi

from src.config import load_delivery

_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
_SSL_CTX = ssl.create_default_context(cafile=certifi.where())


def send_card(text: str, topic_id: Optional[str] = None) -> dict:
    """Send a card to Telegram."""
    if not _BOT_TOKEN:
        return {"ok": False, "error": "no TELEGRAM_BOT_TOKEN"}
    cfg = load_delivery()
    chat_id = cfg.get("telegram_chat_id") or os.environ.get("TELEGRAM_GROUP_ID", "-1003981168546")
    url = f"https://api.telegram.org/bot{_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
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


def deliver(cards: list[dict], topic_id: Optional[str] = None, dry_run: bool = True, card_type: str = "decisions") -> list[dict]:
    """Deliver cards. If dry_run, print to stdout instead of sending."""
    cfg = load_delivery()
    if topic_id is None and card_type:
        topic_id = cfg.get(f"topic_{card_type}_id")

    results = []
    for card in cards:
        text = card if isinstance(card, str) else format_card(card)
        if dry_run:
            print("=" * 40)
            print(text)
            print("=" * 40)
            results.append({"cluster_id": card.get("cluster_id", 0), "status": "dry_run"})
        else:
            try:
                send_card(text, topic_id=topic_id)
                results.append({"cluster_id": card.get("cluster_id", 0), "status": "sent"})
            except Exception as exc:
                results.append({"cluster_id": card.get("cluster_id", 0), "status": "error", "error": str(exc)})
    return results


def format_card(card: dict) -> str:
    """Format a decision card. Accepts both legacy card dicts and analysis dicts."""
    protocol = card.get("protocol", "unknown")
    event_key = card.get("event_key") or card.get("title") or "Unknown"
    title = card.get("title") or card.get("event_key") or ""
    stance = card.get("stance") or card.get("capital_stance") or "neutral"
    weight = card.get("weight", card.get("voice_weight", 0))
    families = card.get("families") or card.get("source_families") or ""
    cluster_id = card.get("cluster_id", 0)
    created_at = card.get("created_at", "")
    action = card.get("action_now", "")
    deploy = 0
    if isinstance(stance, dict):
        deploy = stance.get("deploy_now_usd", 0)
        stance_str = stance.get("reason", "neutral")
    else:
        stance_str = stance

    lines = [
        f"🚨 {protocol.upper()} — {event_key}",
        f"Title: {title}",
        f"Action: {action}" if action else f"Stance: {stance_str}",
        f"Weight: {weight} | Families: {families}",
    ]
    if deploy > 0:
        lines.append(f"Deploy: ${deploy:,.0f}")
    if card.get("url"):
        lines.append(f"Link: {card['url']}")
    tvl_data = card.get("tvl") or card.get("liquidity")
    if tvl_data:
        tvl_usd = tvl_data.get("tvl") or 0
        tvl_b = tvl_usd / 1_000_000_000
        delta = tvl_data.get("tvl_24h_delta") or 0
        prev_tvl = tvl_usd - delta
        pct = (delta / prev_tvl) * 100 if prev_tvl else 0.0
        lines.append(f"TVL: ${tvl_b:.2f}B (Δ24h: {pct:+.2f}%)")
    created_snippet = created_at[:19] if isinstance(created_at, str) else ""
    lines.append(f"ID: {cluster_id} | {created_snippet}")
    return "\n".join(lines)


def deliver_briefs(analyses, topic_id=None, dry_run=False):
    """Deliver trade recommendation briefs for each analysis."""
    from src.brief import format_trade_card
    from src.telegram_alerts import send_trade_card

    if dry_run:
        for a in analyses:
            print("=" * 40)
            print(format_trade_card(a))
            print("=" * 40)
        return [{"cluster_id": a.get("cluster_id", 0), "status": "dry_run"} for a in analyses]

    results = []
    for a in analyses:
        if a.get("action_now") not in ("готовить вход", "наблюдать"):
            continue
        try:
            send_trade_card(a, topic_id=topic_id)
            results.append({"cluster_id": a.get("cluster_id", 0), "status": "sent"})
        except Exception as exc:
            results.append({"cluster_id": a.get("cluster_id", 0), "status": "error", "error": str(exc)})
    return results
