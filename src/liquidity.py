"""Liquidity gate via DeFiLlama protocol TVL."""
from __future__ import annotations

import json
import ssl
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import certifi

    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

DEFILLAMA_PROTOCOL_URL = "https://api.llama.fi/protocol/{slug}"
CACHE_PATH = Path(__file__).parent.parent / "state" / "liquidity-cache.json"
CACHE_TTL_SECONDS = 3600


def _cache_path() -> Path:
    return CACHE_PATH


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _load_cache() -> dict[str, Any]:
    path = _cache_path()
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_cache(cache: dict[str, Any]) -> None:
    path = _cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, default=str)


def _is_stale(entry: dict[str, Any]) -> bool:
    ts_str = entry.get("timestamp")
    if not ts_str:
        return True
    try:
        ts = datetime.fromisoformat(ts_str)
    except Exception:
        return True
    age = (_now() - ts).total_seconds()
    return age > CACHE_TTL_SECONDS


def _extract_tvl(data: dict[str, Any]) -> dict[str, Any] | None:
    """Extract current TVL and 24h delta from DeFiLlama protocol response."""
    tvl_series = data.get("tvl")
    if not isinstance(tvl_series, list) or len(tvl_series) == 0:
        return None
    try:
        current = tvl_series[-1]
        prev = tvl_series[-2] if len(tvl_series) >= 2 else current
        current_tvl = float(current.get("totalLiquidityUSD", 0))
        prev_tvl = float(prev.get("totalLiquidityUSD", 0))
        delta = current_tvl - prev_tvl
    except (TypeError, ValueError, AttributeError):
        return None
    return {
        "tvl": current_tvl,
        "tvl_24h_delta": delta,
        "timestamp": _now().isoformat(),
    }


def _fetch_raw(slug: str, timeout: int = 15) -> dict[str, Any] | None:
    url = DEFILLAMA_PROTOCOL_URL.format(slug=slug)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    return data


def fetch_protocol_tvl(protocol: str, timeout: int = 15) -> dict | None:
    """Return {tvl, tvl_24h_delta, timestamp} or None on failure."""
    slug = protocol.lower().strip()
    cache = _load_cache()
    entry = cache.get(slug)
    if entry and not _is_stale(entry):
        return {
            "tvl": entry.get("tvl"),
            "tvl_24h_delta": entry.get("tvl_24h_delta"),
            "timestamp": entry.get("timestamp"),
        }

    raw = _fetch_raw(slug, timeout=timeout)
    if raw is None:
        return None

    parsed = _extract_tvl(raw)
    if parsed is None:
        return None

    cache[slug] = parsed
    _save_cache(cache)
    return parsed


def is_liquidity_verified(protocol: str, min_tvl_usd: float = 1_000_000) -> bool:
    """Check fresh TVL >= threshold."""
    info = fetch_protocol_tvl(protocol)
    if info is None:
        return False
    tvl = info.get("tvl")
    if tvl is None:
        return False
    return tvl >= min_tvl_usd
