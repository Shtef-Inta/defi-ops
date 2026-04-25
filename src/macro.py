"""Macro regime tracker: funding rates, BTC.D, regime classification."""
from __future__ import annotations

import json
import urllib.request
import ssl
import certifi
from typing import Optional

_SSL_CTX = ssl.create_default_context(cafile=certifi.where())


def fetch_funding_rates() -> dict[str, float]:
    """Fetch funding rates from CoinGlass or similar. Stub using CoinGecko for BTC/ETH."""
    try:
        url = "https://api.coingecko.com/api/v3/coins/bitcoin?localization=false&tickers=false&market_data=true"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, context=_SSL_CTX, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        return {"btc_funding": data.get("market_data", {}).get("price_change_percentage_24h", 0) / 100}
    except Exception:
        return {}


def fetch_btc_dominance() -> float:
    """Fetch BTC dominance from CoinGecko."""
    try:
        url = "https://api.coingecko.com/api/v3/global"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, context=_SSL_CTX, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        return data.get("data", {}).get("market_cap_percentage", {}).get("btc", 50.0)
    except Exception:
        return 50.0


def classify_regime(funding: dict, btc_d: float, btc_change_24h: float) -> str:
    """Classify macro regime."""
    if btc_change_24h > 5 and btc_d > 55:
        return "degen"
    if btc_change_24h > 2 and btc_d > 50:
        return "risk_on"
    if btc_change_24h < -3 or btc_d < 40:
        return "risk_off"
    return "neutral"


def macro_summary() -> dict:
    """Return full macro snapshot."""
    funding = fetch_funding_rates()
    btc_d = fetch_btc_dominance()
    btc_change = (funding.get("btc_funding") or 0) * 100
    regime = classify_regime(funding, btc_d, btc_change)
    return {
        "regime": regime,
        "btc_dominance": btc_d,
        "btc_change_24h_pct": btc_change,
        "funding_rates": funding,
        "size_adjustment": {"degen": 1.5, "risk_on": 1.0, "neutral": 0.75, "risk_off": 0.5}.get(regime, 1.0),
    }
