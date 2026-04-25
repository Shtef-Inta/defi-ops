"""Telegram channel ingest via Telethon (read-only, user session)."""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.db import get_conn


def _env_key(name: str) -> str | None:
    return os.environ.get(name) or None


def _parse_telegram_channels(text: str) -> list[dict]:
    """Extract enabled telegram channels from sources.yaml."""
    channels: list[dict] = []
    in_telegram = False
    current_item: dict | None = None

    for raw in text.splitlines():
        line = raw.rstrip("\n")
        stripped = line.lstrip(" ")
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))

        if stripped == "telegram:":
            in_telegram = True
            continue

        if in_telegram and indent == 0 and stripped:
            break

        if not in_telegram:
            continue

        if indent == 4 and stripped.startswith("- "):
            current_item = {}
            rest = stripped[2:].strip()
            if ":" in rest:
                k, _, v = rest.partition(":")
                current_item[k.strip()] = v.strip().strip('"').strip("'")
            if current_item:
                channels.append(current_item)
            continue

        if indent == 6 and current_item is not None and ":" in stripped:
            k, _, v = stripped.partition(":")
            current_item[k.strip()] = v.strip().strip('"').strip("'")

    return [c for c in channels if c.get("enabled", "").lower() == "true"]


def _normalize_message(msg: dict, channel: dict) -> dict | None:
    text = (msg.get("text") or "").strip()
    if not text:
        return None
    msg_id = str(msg.get("id", ""))
    handle = channel.get("handle", "")
    return {
        "source_family": channel.get("source_family", "social_community"),
        "source_handle": handle,
        "protocol": channel.get("protocol"),
        "event_key": None,
        "content": text,
        "url": f"https://t.me/{handle}/{msg_id}",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "asset_symbols": None,
        "sentiment": None,
        "raw_payload": json.dumps(msg, ensure_ascii=False),
        "source_id": f"{handle}:{msg_id}",
    }


def fetch_telegram(
    db_path: Optional[str] = None,
    max_per_channel: int = 20,
    lookback_hours: int = 24,
    _write_raw=None,
    _client_factory=None,
) -> dict:
    """Fetch messages from enabled Telegram channels and insert into signals."""
    sources_path = Path(__file__).parent.parent / "config" / "sources.yaml"
    channels = _parse_telegram_channels(sources_path.read_text()) if sources_path.exists() else []
    if not channels:
        return {"channels": 0, "inserted": 0, "skipped": 0, "failed": 0}

    api_id = _env_key("TELEGRAM_API_ID")
    api_hash = _env_key("TELEGRAM_API_HASH")
    if not api_id or not api_hash:
        return {"channels": len(channels), "inserted": 0, "skipped": 0, "failed": len(channels)}

    session_path = Path(__file__).parent.parent / "state" / "telegram.session"
    bot_token = _env_key("TELEGRAM_BOT_TOKEN")
    conn = get_conn(db_path)
    inserted = 0
    skipped = 0
    failed = 0

    try:
        from telethon.sync import TelegramClient  # type: ignore[import-untyped]
    except ImportError:
        conn.close()
        return {"channels": len(channels), "inserted": 0, "skipped": 0, "failed": len(channels)}

    client = (
        _client_factory(str(session_path), int(api_id), api_hash)
        if _client_factory
        else TelegramClient(str(session_path), int(api_id), api_hash)
    )

    try:
        client.connect()
        if not client.is_user_authorized():
            if bot_token:
                client.start(bot_token=bot_token)
            else:
                client.disconnect()
                return {"channels": len(channels), "inserted": 0, "skipped": 0, "failed": len(channels)}
        for ch in channels:
            handle = ch.get("handle", "")
            if not handle:
                failed += 1
                continue
            try:
                entity = client.get_entity(handle)
                msgs: list[dict] = []
                for message in client.iter_messages(entity, limit=max_per_channel):
                    if message.date is None:
                        continue
                    age_hours = (datetime.now(timezone.utc) - message.date.replace(tzinfo=timezone.utc)).total_seconds() / 3600
                    if age_hours > lookback_hours:
                        break
                    msgs.append({
                        "id": str(message.id),
                        "text": message.text or "",
                        "date": message.date.isoformat(),
                    })

                if _write_raw:
                    _write_raw(
                        "telegram",
                        handle,
                        {
                            "channel": handle,
                            "captured_at": datetime.now(timezone.utc).isoformat(),
                            "messages": msgs,
                        },
                    )

                for m in msgs:
                    norm = _normalize_message(m, ch)
                    if not norm:
                        continue
                    existing = conn.execute(
                        "SELECT 1 FROM signals WHERE source_family = ? AND source_id = ?",
                        (norm["source_family"], norm["source_id"]),
                    ).fetchone()
                    if existing:
                        skipped += 1
                        continue

                    conn.execute(
                        """
                        INSERT INTO signals
                            (source_family, source_handle, protocol, event_key, content, url,
                             captured_at, asset_symbols, sentiment, raw_payload, source_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            norm["source_family"],
                            norm["source_handle"],
                            norm["protocol"],
                            norm["event_key"],
                            norm["content"],
                            norm["url"],
                            norm["captured_at"],
                            norm["asset_symbols"],
                            norm["sentiment"],
                            norm["raw_payload"],
                            norm["source_id"],
                        ),
                    )
                    inserted += 1
            except Exception:
                failed += 1
                continue
    finally:
        if client.is_connected():
            client.disconnect()

    conn.commit()
    conn.close()
    return {
        "channels": len(channels),
        "inserted": inserted,
        "skipped": skipped,
        "failed": failed,
    }
