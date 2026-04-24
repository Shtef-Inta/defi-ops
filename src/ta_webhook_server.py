"""TradingView webhook server — receives alerts and stores them as signals.

Run standalone:
    python -m src.ta_webhook_server

Or integrate into daemon.
"""
from __future__ import annotations

import json
import os
import sys
import threading
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional

_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from src.db import get_conn

DB_PATH: Optional[str] = os.getenv("DB_PATH")
PORT = int(os.getenv("WEBHOOK_PORT", "8080"))


class _WebhookHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        pass

    def do_POST(self) -> None:
        if self.path != "/webhook/tradingview":
            self.send_error(404)
            return

        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0:
            self.send_error(400)
            return

        body = self.rfile.read(content_length).decode("utf-8", errors="replace")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {"raw": body}

        self._handle_tradingview_alert(payload)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

    def _handle_tradingview_alert(self, payload: dict) -> None:
        ticker = payload.get("ticker", "")
        price = payload.get("price", 0.0)
        message = payload.get("message", payload.get("raw", ""))
        strategy = payload.get("strategy", "TradingView")

        protocol = _ticker_to_protocol(ticker)
        sentiment = _infer_sentiment(message)

        content = f"[TradingView] {strategy}: {message} @ ${price}"
        if not protocol:
            content = f"[TradingView/{ticker}] {strategy}: {message} @ ${price}"

        try:
            conn = get_conn(DB_PATH)
            conn.execute(
                """
                INSERT INTO signals (protocol, source_family, source_handle, content, sentiment, asset_symbols, captured_at, url)
                VALUES (?, 'technical', ?, ?, ?, ?, ?, ?)
                """,
                (
                    protocol or "",
                    strategy,
                    content,
                    sentiment,
                    ticker.replace("USD", "").replace("USDC", "").replace("USDT", ""),
                    datetime.now(timezone.utc).isoformat(),
                    "",
                ),
            )
            conn.commit()
            conn.close()
            print(f"[WEBHOOK] {ticker}: {message} ({sentiment})")
        except Exception as exc:
            print(f"[WEBHOOK ERROR] {exc}")


def _ticker_to_protocol(ticker: str) -> str:
    mapping = {
        "JUPUSD": "jupiter",
        "JUPUSDC": "jupiter",
        "JUPUSDT": "jupiter",
        "AAVEUSD": "aave",
        "UNIUSD": "uniswap",
        "ENAUSD": "ethena",
        "PENDLEUSD": "pendle",
        "CRVUSD": "curve",
        "COMPUSD": "compound",
        "BALUSD": "balancer",
        "GMXUSD": "gmx",
        "DYDXUSD": "dydx",
        "LDOUSD": "lido",
        "MORPHOUSD": "morpho",
        "HYPEUSD": "hyperliquid",
        "SOLUSD": "solana",
        "ETHUSD": "ethereum",
    }
    return mapping.get(ticker.upper(), "")


def _infer_sentiment(message: str) -> str:
    m = message.lower()
    if any(w in m for w in ("buy", "long", "bullish", "oversold", "breakout", "cross up")):
        return "bullish"
    if any(w in m for w in ("sell", "short", "bearish", "overbought", "breakdown", "cross down")):
        return "bearish"
    return "neutral"


def start_webhook_server(port: Optional[int] = None, db_path: Optional[str] = None) -> threading.Thread:
    global DB_PATH
    if db_path:
        DB_PATH = db_path
    p = port or PORT
    server = HTTPServer(("0.0.0.0", p), _WebhookHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"[TA Webhook] Listening on http://0.0.0.0:{p}/webhook/tradingview")
    return thread


def main() -> None:
    start_webhook_server()
    print("Press Ctrl+C to stop")
    try:
        while True:
            threading.Event().wait(3600)
    except KeyboardInterrupt:
        print("\nStopped")


if __name__ == "__main__":
    main()
