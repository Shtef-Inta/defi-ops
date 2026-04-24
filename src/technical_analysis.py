"""Technical analysis layer: price data + indicators → signals.

Fetches OHLCV-like price history from CoinGecko (free tier),
calculates RSI / EMA / MACD, and generates signals into the DB.
Also supports TradingView webhook alerts as external signals.
"""
from __future__ import annotations

import json
import sqlite3
import ssl
import time
import urllib.request
from datetime import datetime, timezone
from typing import Optional

from src.db import get_conn

# macOS/Homebrew Python sometimes lacks system certs
try:
    import certifi
    _SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except Exception:
    _SSL_CONTEXT = ssl.create_default_context()

# Protocol → CoinGecko coin id
_CG_ID_MAP: dict[str, str] = {
    "aave": "aave",
    "uniswap": "uniswap",
    "ethena": "ethena",
    "pendle": "pendle",
    "morpho": "morpho",
    "lido": "lido-dao",
    "hyperliquid": "hyperliquid",
    "fluid": "fluid",
    "compound": "compound-governance-token",
    "curve": "curve-dao-token",
    "sky": "sky",
    "spark": "spark",
    "eigenlayer": "eigenlayer",
    "gearbox": "gearbox",
    "balancer": "balancer",
    "gmx": "gmx",
    "dydx": "dydx",
    "jupiter": "jupiter-exchange-solana",
    "solana": "solana",
    "ethereum": "ethereum",
}


def _ema(values: list[float], period: int) -> list[float | None]:
    k = 2.0 / (period + 1)
    result: list[float | None] = [None] * (period - 1)
    sma = sum(values[:period]) / period
    result.append(sma)
    prev = sma
    for v in values[period:]:
        ema = v * k + prev * (1 - k)
        result.append(ema)
        prev = ema
    return result


def _rsi(values: list[float], period: int = 14) -> list[float | None]:
    if len(values) <= period:
        return [None] * len(values)
    gains = []
    losses = []
    for i in range(1, len(values)):
        diff = values[i] - values[i - 1]
        gains.append(max(diff, 0.0))
        losses.append(max(-diff, 0.0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    rsis: list[float | None] = [None] * (period + 1)
    rsis.append(_calc_rsi(avg_gain, avg_loss))
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        rsis.append(_calc_rsi(avg_gain, avg_loss))
    return rsis


def _calc_rsi(avg_gain: float, avg_loss: float) -> float:
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _fetch_market_chart(cg_id: str, days: int = 14) -> list[list[float]]:
    url = (
        f"https://api.coingecko.com/api/v3/coins/{cg_id}/market_chart"
        f"?vs_currency=usd&days={days}"
    )
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30, context=_SSL_CONTEXT) as resp:
        data = json.loads(resp.read().decode())
    return data.get("prices", [])


def _ensure_ta_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS technical_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            protocol TEXT NOT NULL,
            indicator TEXT NOT NULL,
            signal TEXT NOT NULL,
            value REAL,
            price REAL,
            timeframe TEXT DEFAULT '1d',
            captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ta_protocol_time
        ON technical_signals(protocol, captured_at)
        """
    )


def generate_ta_signals(protocol: str, db_path: Optional[str] = None) -> list[dict]:
    cg_id = _CG_ID_MAP.get(protocol.lower())
    if not cg_id:
        return []

    prices_raw = _fetch_market_chart(cg_id, days=30)
    if len(prices_raw) < 30:
        return []

    prices = [p[1] for p in prices_raw]
    latest_price = prices[-1]

    ema12 = _ema(prices, 12)
    ema26 = _ema(prices, 26)
    rsi_vals = _rsi(prices, 14)

    signals: list[dict] = []

    if ema12[-1] is not None and ema26[-1] is not None:
        prev12 = ema12[-2]
        prev26 = ema26[-2]
        curr12 = ema12[-1]
        curr26 = ema26[-1]
        if prev12 is not None and prev26 is not None:
            if prev12 <= prev26 and curr12 > curr26:
                signals.append({
                    "indicator": "EMA12/26",
                    "signal": "bullish_cross",
                    "value": curr12 - curr26,
                    "price": latest_price,
                })
            elif prev12 >= prev26 and curr12 < curr26:
                signals.append({
                    "indicator": "EMA12/26",
                    "signal": "bearish_cross",
                    "value": curr12 - curr26,
                    "price": latest_price,
                })

    latest_rsi = rsi_vals[-1]
    if latest_rsi is not None:
        if latest_rsi < 30:
            signals.append({
                "indicator": "RSI14",
                "signal": "oversold",
                "value": latest_rsi,
                "price": latest_price,
            })
        elif latest_rsi > 70:
            signals.append({
                "indicator": "RSI14",
                "signal": "overbought",
                "value": latest_rsi,
                "price": latest_price,
            })

    if len(prices) >= 2:
        change_24h = (prices[-1] - prices[-2]) / prices[-2] * 100
        if abs(change_24h) >= 5:
            signals.append({
                "indicator": "price_change_24h",
                "signal": "bullish_spike" if change_24h > 0 else "bearish_spike",
                "value": change_24h,
                "price": latest_price,
            })

    conn = get_conn(db_path)
    _ensure_ta_table(conn)
    for sig in signals:
        conn.execute(
            """
            INSERT INTO technical_signals (protocol, indicator, signal, value, price, captured_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                protocol,
                sig["indicator"],
                sig["signal"],
                sig["value"],
                sig["price"],
                datetime.now(timezone.utc).isoformat(),
            ),
        )
    conn.commit()
    conn.close()
    return signals


def run_ta_for_all(db_path: Optional[str] = None) -> dict[str, list[dict]]:
    results: dict[str, list[dict]] = {}
    for protocol in _CG_ID_MAP:
        if protocol in ("solana", "ethereum"):
            continue
        try:
            sigs = generate_ta_signals(protocol, db_path)
            if sigs:
                results[protocol] = sigs
            time.sleep(2.5)
        except Exception as exc:
            print(f"TA failed for {protocol}: {exc}")
    return results


def get_latest_ta_summary(db_path: Optional[str] = None, hours: int = 24) -> list[dict]:
    conn = get_conn(db_path)
    rows = conn.execute(
        """
        SELECT protocol, indicator, signal, value, price, captured_at
        FROM technical_signals
        WHERE captured_at >= datetime('now', '-{} hours')
        ORDER BY captured_at DESC
        """.format(hours)
    ).fetchall()
    conn.close()
    return [
        {
            "protocol": r[0],
            "indicator": r[1],
            "signal": r[2],
            "value": r[3],
            "price": r[4],
            "captured_at": r[5],
        }
        for r in rows
    ]


def ingest_ta_as_signals(db_path: Optional[str] = None) -> int:
    conn = get_conn(db_path)
    rows = conn.execute(
        """
        SELECT protocol, indicator, signal, value, price, captured_at
        FROM technical_signals
        WHERE captured_at >= datetime('now', '-1 hour')
          AND NOT EXISTS (
              SELECT 1 FROM signals s
              WHERE s.source_family = 'technical'
                AND s.protocol = technical_signals.protocol
                AND s.content LIKE '%' || technical_signals.indicator || '%'
                AND s.captured_at >= datetime('now', '-1 hour')
          )
        """
    ).fetchall()
    inserted = 0
    for r in rows:
        protocol, indicator, sig, value, price, captured_at = r
        sentiment = "bullish" if sig in ("bullish_cross", "oversold", "bullish_spike") else "bearish"
        content = f"[{indicator}] {sig} @ ${price:.4f} (value={value:.2f})"
        conn.execute(
            """
            INSERT INTO signals (protocol, source_family, source_handle, content, sentiment, asset_symbols, captured_at, url)
            VALUES (?, 'technical', ?, ?, ?, ?, ?, ?)
            """,
            (protocol, indicator, content, sentiment, protocol.upper(), captured_at, ""),
        )
        inserted += 1
    conn.commit()
    conn.close()
    return inserted
