#!/usr/bin/env python3
"""Telegram bot for interactive control and status queries."""
from __future__ import annotations

import json
import os
import signal
import sys
import threading
import time
from pathlib import Path

from telethon.sync import TelegramClient, events  # type: ignore[import-untyped]

API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
OWNER_ID = int(os.environ.get("TELEGRAM_OWNER_ID", "365840120"))
SESSION_PATH = str(Path(__file__).parent.parent / "state" / "telegram_bot.session")

client = TelegramClient(SESSION_PATH, API_ID, API_HASH)


def _status_reply() -> str:
    from src.db import get_conn
    from src.quality import open_positions_summary
    from src.paper_trading import snapshot_positions
    try:
        snap = snapshot_positions()
        summary = open_positions_summary()
        conn = get_conn()
        signals_24h = conn.execute(
            "SELECT COUNT(*) FROM signals WHERE captured_at >= datetime('now', '-24 hours')"
        ).fetchone()[0]
        clusters = conn.execute(
            "SELECT COUNT(*) FROM clusters WHERE status = 'open'"
        ).fetchone()[0]
        conn.close()
        return (
            f"📊 <b>Status</b>\n"
            f"Open positions: {snap['open_count']}\n"
            f"Exposure: ${snap['total_exposure']:,.0f}\n"
            f"Unrealized PnL: ${snap['unrealized_pnl']:,.0f}\n"
            f"Signals 24h: {signals_24h}\n"
            f"Open clusters: {clusters}"
        )
    except Exception as exc:
        return f"❌ Error getting status: {exc}"


@client.on(events.NewMessage(pattern=r"/status"))
def handle_status(event):
    if event.sender_id != OWNER_ID:
        return
    event.reply(_status_reply(), parse_mode="html")


@client.on(events.NewMessage(pattern=r"/tail"))
def handle_tail(event):
    if event.sender_id != OWNER_ID:
        return
    log_path = Path(__file__).parent.parent / "state" / "daemon.log"
    if not log_path.exists():
        event.reply("No daemon.log found")
        return
    lines = log_path.read_text().splitlines()[-20:]
    text = "\n".join(lines)
    event.reply(f"<pre>{text[-4000:]}</pre>", parse_mode="html")


@client.on(events.NewMessage(pattern=r"/monitor"))
def handle_monitor(event):
    if event.sender_id != OWNER_ID:
        return
    event.reply("🟢 Daemon is running. Dashboard: http://0.0.0.0:8765")


def main():
    client.start(bot_token=BOT_TOKEN)
    print("[telegram_bot] Started")
    client.run_until_disconnected()


if __name__ == "__main__":
    main()
