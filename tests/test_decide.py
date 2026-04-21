"""Tests for decide.py — card building and formatting."""
from __future__ import annotations

import pytest

from src import decide
from src.db import init_db


def test_build_cards_empty_db(tmp_path):
    db_file = tmp_path / "test.sqlite"
    init_db(str(db_file)).close()
    cards = decide.build_cards(db_path=str(db_file))
    assert cards == []


def test_build_cards_with_cluster(monkeypatch, tmp_path):
    db_file = tmp_path / "test.sqlite"
    conn = init_db(str(db_file))
    conn.execute(
        """
        INSERT INTO signals (source_family, source_handle, protocol, event_key, content, url, captured_at, source_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("official", "aave", "aave", "aave_launch_v4", "Aave V4 is live", "https://example.com", "2025-04-21T10:00:00+00:00", "s:1"),
    )
    conn.execute(
        """
        INSERT INTO clusters (protocol, event_key, window_start, window_end, aspects, status, voice_weight)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        ("aave", "aave_launch_v4", "2025-04-21T10:00:00+00:00", "2025-04-21T10:00:00+00:00", '["official"]', "open", 2.5),
    )
    conn.execute("INSERT INTO cluster_signals (cluster_id, signal_id) VALUES (1, 1)")
    conn.commit()
    conn.close()

    monkeypatch.setattr(decide, "is_liquidity_verified", lambda protocol: True)
    monkeypatch.setattr(
        decide,
        "fetch_protocol_tvl",
        lambda protocol: {
            "tvl": 5_000_000_000,
            "tvl_24h_delta": 100_000_000,
            "timestamp": "2025-04-21T10:00:00+00:00",
        },
    )

    cards = decide.build_cards(db_path=str(db_file))
    assert len(cards) == 1
    assert cards[0]["protocol"] == "aave"
    assert cards[0]["event_key"] == "aave_launch_v4"
    assert cards[0]["stance"] == "📊 WATCH closely"
    assert cards[0]["weight"] == 2.5
    assert cards[0]["tvl"]["tvl"] == 5_000_000_000


def test_build_cards_skips_when_liquidity_missing(monkeypatch, tmp_path):
    db_file = tmp_path / "test.sqlite"
    conn = init_db(str(db_file))
    conn.execute(
        """
        INSERT INTO signals (source_family, source_handle, protocol, event_key, content, url, captured_at, source_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("official", "aave", "aave", "aave_launch_v4", "Aave V4 is live", "https://example.com", "2025-04-21T10:00:00+00:00", "s:1"),
    )
    conn.execute(
        """
        INSERT INTO clusters (protocol, event_key, window_start, window_end, aspects, status, voice_weight)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        ("aave", "aave_launch_v4", "2025-04-21T10:00:00+00:00", "2025-04-21T10:00:00+00:00", '["official"]', "open", 2.5),
    )
    conn.execute("INSERT INTO cluster_signals (cluster_id, signal_id) VALUES (1, 1)")
    conn.commit()
    conn.close()

    monkeypatch.setattr(decide, "is_liquidity_verified", lambda protocol: False)
    monkeypatch.setattr(decide, "fetch_protocol_tvl", lambda protocol: None)

    cards = decide.build_cards(db_path=str(db_file))
    assert cards == []


def test_build_cards_passes_when_liquidity_present(monkeypatch, tmp_path):
    db_file = tmp_path / "test.sqlite"
    conn = init_db(str(db_file))
    conn.execute(
        """
        INSERT INTO signals (source_family, source_handle, protocol, event_key, content, url, captured_at, source_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("official", "aave", "aave", "aave_launch_v4", "Aave V4 is live", "https://example.com", "2025-04-21T10:00:00+00:00", "s:1"),
    )
    conn.execute(
        """
        INSERT INTO clusters (protocol, event_key, window_start, window_end, aspects, status, voice_weight)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        ("aave", "aave_launch_v4", "2025-04-21T10:00:00+00:00", "2025-04-21T10:00:00+00:00", '["official"]', "open", 2.5),
    )
    conn.execute("INSERT INTO cluster_signals (cluster_id, signal_id) VALUES (1, 1)")
    conn.commit()
    conn.close()

    monkeypatch.setattr(decide, "is_liquidity_verified", lambda protocol: True)
    monkeypatch.setattr(
        decide,
        "fetch_protocol_tvl",
        lambda protocol: {
            "tvl": 3_000_000_000,
            "tvl_24h_delta": -50_000_000,
            "timestamp": "2025-04-21T10:00:00+00:00",
        },
    )

    cards = decide.build_cards(db_path=str(db_file))
    assert len(cards) == 1
    assert cards[0]["protocol"] == "aave"
    assert cards[0]["tvl"]["tvl"] == 3_000_000_000


def test_format_card():
    card = {
        "cluster_id": 1,
        "protocol": "aave",
        "event_key": "aave_launch_v4",
        "title": "Aave V4 live",
        "stance": "📊 WATCH closely",
        "weight": 2.5,
        "families": "official",
        "url": "https://example.com",
        "created_at": "2025-04-21T10:00:00",
    }
    text = decide.format_card(card)
    assert "AAVE" in text
    assert "Aave V4 live" in text
    assert "https://example.com" in text


def test_format_card_includes_tvl():
    card = {
        "cluster_id": 1,
        "protocol": "aave",
        "event_key": "aave_launch_v4",
        "title": "Aave V4 live",
        "stance": "📊 WATCH closely",
        "weight": 2.5,
        "families": "official",
        "url": "https://example.com",
        "created_at": "2025-04-21T10:00:00",
        "tvl": {
            "tvl": 5_000_000_000,
            "tvl_24h_delta": 100_000_000,
            "timestamp": "2025-04-21T10:00:00+00:00",
        },
    }
    text = decide.format_card(card)
    assert "TVL: $5.00B (Δ24h: +2.04%)" in text
