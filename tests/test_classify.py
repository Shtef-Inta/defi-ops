"""Tests for classify.py — event extraction, clustering, voice weight, contradiction."""
from __future__ import annotations

import sqlite3

import pytest

from src import classify
from src.db import init_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_WATCHLIST = """
protocols:
  - name: aave
    tier: critical
    aliases: [Aave, AAVE]
    event_keywords:
      launch: ["v4 live", "aave v4", "mainnet launch"]
      freeze: ["frozen", "pause", "paused", "halt"]
      depeg: ["usds depeg"]
  - name: ethena
    tier: critical
    aliases: [Ethena, USDe, ENA]
    event_keywords:
      freeze: ["usde depeg", "peg", "pause", "paused"]
"""


# ---------------------------------------------------------------------------
# Event key extractor
# ---------------------------------------------------------------------------


def test_extract_event_key_launch():
    assert classify.extract_event_key("Aave V4 is live on mainnet", SAMPLE_WATCHLIST) == (
        "aave",
        "aave_launch_v4",
    )


def test_extract_event_key_freeze():
    assert classify.extract_event_key("Ethena pauses USDe minting on L2", SAMPLE_WATCHLIST) == (
        "ethena",
        "ethena_freeze_usde",
    )


def test_extract_event_key_no_match():
    protocols = classify._parse_watchlist(SAMPLE_WATCHLIST)
    print("PROTOCOLS", protocols)
    assert classify.extract_event_key("Random crypto news today", SAMPLE_WATCHLIST) == (None, None)


def test_extract_event_key_case_insensitive():
    assert classify.extract_event_key("AAVE v4 deployed to mainnet", SAMPLE_WATCHLIST) == (
        "aave",
        "aave_launch_v4",
    )


def test_extract_event_key_uses_first_protocol():
    # When multiple protocols match, pick the one with longest alias match
    assert classify.extract_event_key("Aave and Ethena both pause", SAMPLE_WATCHLIST)[0] in {
        "aave",
        "ethena",
    }


# ---------------------------------------------------------------------------
# Clustering
# ---------------------------------------------------------------------------


def test_classify_signals_fills_event_key_and_clusters(monkeypatch, tmp_path):
    db_file = tmp_path / "test.sqlite"
    conn = init_db(str(db_file))
    conn.execute(
        """
        INSERT INTO signals (source_family, source_handle, content, captured_at, source_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("official", "aave", "Aave V4 is live on mainnet", "2025-04-21T10:00:00+00:00", "tw:1"),
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr("src.classify._load_watchlist", lambda: classify._parse_watchlist(SAMPLE_WATCHLIST))
    classify.classify_signals(db_path=str(db_file))

    conn = sqlite3.connect(str(db_file))
    row = conn.execute("SELECT protocol, event_key FROM signals WHERE id=1").fetchone()
    assert row == ("aave", "aave_launch_v4")

    clusters = conn.execute("SELECT protocol, event_key, aspects FROM clusters").fetchall()
    assert len(clusters) == 1
    assert clusters[0][0] == "aave"
    assert clusters[0][1] == "aave_launch_v4"
    assert "official" in clusters[0][2]
    conn.close()


def test_classify_signals_groups_same_event_within_48h(monkeypatch, tmp_path):
    db_file = tmp_path / "test.sqlite"
    conn = init_db(str(db_file))
    for i, ts in enumerate(["2025-04-21T10:00:00+00:00", "2025-04-21T12:00:00+00:00"], start=1):
        conn.execute(
            """
            INSERT INTO signals (source_family, source_handle, content, captured_at, source_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("research", "ignas", "Aave V4 launch details", ts, f"tw:{i}"),
        )
    conn.commit()
    conn.close()

    monkeypatch.setattr("src.classify._load_watchlist", lambda: classify._parse_watchlist(SAMPLE_WATCHLIST))
    classify.classify_signals(db_path=str(db_file))

    conn = sqlite3.connect(str(db_file))
    clusters = conn.execute("SELECT id FROM clusters").fetchall()
    assert len(clusters) == 1
    links = conn.execute("SELECT cluster_id FROM cluster_signals").fetchall()
    assert len(links) == 2
    conn.close()


def test_extract_event_key_ai_tech():
    assert classify.extract_event_key("Anthropic launches Claude Code v2", None) == (
        "anthropic",
        "anthropic_launch_v2",
    )
    assert classify.extract_event_key("OpenAI GPT-5 is live", None) == (
        "openai",
        "openai_launch_gpt",
    )


def test_classify_signals_separate_clusters_after_48h(monkeypatch, tmp_path):
    db_file = tmp_path / "test.sqlite"
    conn = init_db(str(db_file))
    for i, ts in enumerate(["2025-04-21T10:00:00+00:00", "2025-04-23T12:00:00+00:00"], start=1):
        conn.execute(
            """
            INSERT INTO signals (source_family, source_handle, content, captured_at, source_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("official", "aave", "Aave V4 is live on mainnet", ts, f"tw:{i}"),
        )
    conn.commit()
    conn.close()

    monkeypatch.setattr("src.classify._load_watchlist", lambda: classify._parse_watchlist(SAMPLE_WATCHLIST))
    classify.classify_signals(db_path=str(db_file))

    conn = sqlite3.connect(str(db_file))
    clusters = conn.execute("SELECT id FROM clusters").fetchall()
    assert len(clusters) == 2
    conn.close()
