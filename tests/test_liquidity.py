"""Tests for src/liquidity.py with stubbed HTTP."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src import liquidity


class _FakeResponse:
    def __init__(self, payload: dict[str, Any] | str, status: int = 200):
        if isinstance(payload, dict):
            self._body = json.dumps(payload).encode("utf-8")
        else:
            self._body = payload.encode("utf-8")
        self.status = status

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def _make_tvl_series(base_tvl: float = 10_000_000, delta: float = 500_000) -> list[dict]:
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    return [
        {"date": int(yesterday.timestamp()), "totalLiquidityUSD": base_tvl - delta},
        {"date": int(today.timestamp()), "totalLiquidityUSD": base_tvl},
    ]


def test_fetch_protocol_tvl_hits_api_and_caches(monkeypatch, tmp_path):
    cache_file = tmp_path / "liquidity-cache.json"
    monkeypatch.setattr(liquidity, "_cache_path", lambda: cache_file)

    calls = []

    def fake_urlopen(req, **kwargs):
        calls.append(req.full_url)
        return _FakeResponse({"tvl": _make_tvl_series()})

    monkeypatch.setattr(liquidity.urllib.request, "urlopen", fake_urlopen)

    result = liquidity.fetch_protocol_tvl("aave")
    assert result is not None
    assert result["tvl"] == 10_000_000
    assert result["tvl_24h_delta"] == 500_000
    assert "timestamp" in result
    assert len(calls) == 1

    # second call should use cache
    result2 = liquidity.fetch_protocol_tvl("aave")
    assert result2 is not None
    assert result2["tvl"] == 10_000_000
    assert len(calls) == 1


def test_fetch_protocol_tvl_refreshes_stale_cache(monkeypatch, tmp_path):
    cache_file = tmp_path / "liquidity-cache.json"
    monkeypatch.setattr(liquidity, "_cache_path", lambda: cache_file)

    stale_ts = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    cache_file.write_text(
        json.dumps({"aave": {"tvl": 1_000_000, "tvl_24h_delta": 0, "timestamp": stale_ts}})
    )

    calls = []

    def fake_urlopen(req, **kwargs):
        calls.append(req.full_url)
        return _FakeResponse({"tvl": _make_tvl_series(base_tvl=20_000_000)})

    monkeypatch.setattr(liquidity.urllib.request, "urlopen", fake_urlopen)

    result = liquidity.fetch_protocol_tvl("aave")
    assert result is not None
    assert result["tvl"] == 20_000_000
    assert len(calls) == 1


def test_fetch_protocol_tvl_api_error_returns_none(monkeypatch, tmp_path):
    cache_file = tmp_path / "liquidity-cache.json"
    monkeypatch.setattr(liquidity, "_cache_path", lambda: cache_file)

    def fake_urlopen(req, **kwargs):
        raise Exception("network down")

    monkeypatch.setattr(liquidity.urllib.request, "urlopen", fake_urlopen)

    assert liquidity.fetch_protocol_tvl("aave") is None


def test_fetch_protocol_tvl_malformed_response_returns_none(monkeypatch, tmp_path):
    cache_file = tmp_path / "liquidity-cache.json"
    monkeypatch.setattr(liquidity, "_cache_path", lambda: cache_file)

    def fake_urlopen(req, **kwargs):
        return _FakeResponse({"name": "no tvl key"})

    monkeypatch.setattr(liquidity.urllib.request, "urlopen", fake_urlopen)

    assert liquidity.fetch_protocol_tvl("aave") is None


def test_fetch_protocol_tvl_empty_tvl_returns_none(monkeypatch, tmp_path):
    cache_file = tmp_path / "liquidity-cache.json"
    monkeypatch.setattr(liquidity, "_cache_path", lambda: cache_file)

    def fake_urlopen(req, **kwargs):
        return _FakeResponse({"tvl": []})

    monkeypatch.setattr(liquidity.urllib.request, "urlopen", fake_urlopen)

    assert liquidity.fetch_protocol_tvl("aave") is None


def test_is_liquidity_verified_true_when_above_threshold(monkeypatch, tmp_path):
    cache_file = tmp_path / "liquidity-cache.json"
    monkeypatch.setattr(liquidity, "_cache_path", lambda: cache_file)

    def fake_urlopen(req, **kwargs):
        return _FakeResponse({"tvl": _make_tvl_series(base_tvl=5_000_000)})

    monkeypatch.setattr(liquidity.urllib.request, "urlopen", fake_urlopen)

    assert liquidity.is_liquidity_verified("aave", min_tvl_usd=1_000_000) is True


def test_is_liquidity_verified_false_when_below_threshold(monkeypatch, tmp_path):
    cache_file = tmp_path / "liquidity-cache.json"
    monkeypatch.setattr(liquidity, "_cache_path", lambda: cache_file)

    def fake_urlopen(req, **kwargs):
        return _FakeResponse({"tvl": _make_tvl_series(base_tvl=500_000)})

    monkeypatch.setattr(liquidity.urllib.request, "urlopen", fake_urlopen)

    assert liquidity.is_liquidity_verified("aave", min_tvl_usd=1_000_000) is False


def test_is_liquidity_verified_false_on_api_failure(monkeypatch, tmp_path):
    cache_file = tmp_path / "liquidity-cache.json"
    monkeypatch.setattr(liquidity, "_cache_path", lambda: cache_file)

    def fake_urlopen(req, **kwargs):
        raise Exception("timeout")

    monkeypatch.setattr(liquidity.urllib.request, "urlopen", fake_urlopen)

    assert liquidity.is_liquidity_verified("aave") is False


def test_cache_file_created_and_reused(monkeypatch, tmp_path):
    cache_file = tmp_path / "liquidity-cache.json"
    monkeypatch.setattr(liquidity, "_cache_path", lambda: cache_file)

    def fake_urlopen(req, **kwargs):
        return _FakeResponse({"tvl": _make_tvl_series(base_tvl=15_000_000)})

    monkeypatch.setattr(liquidity.urllib.request, "urlopen", fake_urlopen)

    liquidity.fetch_protocol_tvl("uniswap")
    assert cache_file.exists()
    data = json.loads(cache_file.read_text())
    assert "uniswap" in data
    assert data["uniswap"]["tvl"] == 15_000_000
