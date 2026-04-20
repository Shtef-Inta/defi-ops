import sqlite3
from pathlib import Path

from src.db import init_db, get_conn


def test_init_db_creates_schema(tmp_path):
    db_file = tmp_path / "test.sqlite"
    conn = init_db(str(db_file))

    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = {row[0] for row in cursor.fetchall()}

    expected = {
        "signals",
        "clusters",
        "cluster_signals",
        "wallet_tx",
        "wallet_flows",
        "decisions",
        "outcomes",
        "source_reliability",
        "api_budget",
    }
    assert expected.issubset(tables)
    conn.close()


def test_init_db_idempotent(tmp_path):
    db_file = tmp_path / "test.sqlite"
    init_db(str(db_file)).close()
    # second init must not raise
    conn = init_db(str(db_file))
    conn.execute("SELECT 1 FROM signals").fetchone()
    conn.close()


def test_insert_and_roundtrip(tmp_path):
    db_file = tmp_path / "test.sqlite"
    conn = init_db(str(db_file))

    conn.execute(
        "INSERT INTO signals (source_family, protocol, content) VALUES (?, ?, ?)",
        ("official", "aave", "Aave V4 is live"),
    )
    conn.commit()

    row = conn.execute("SELECT * FROM signals WHERE protocol = ?", ("aave",)).fetchone()
    assert row["source_family"] == "official"
    assert row["content"] == "Aave V4 is live"
    conn.close()


def test_get_conn(tmp_path, monkeypatch):
    db_file = tmp_path / "ops.sqlite"
    monkeypatch.setattr(
        "src.db.Path", lambda *args, **kwargs: db_file if str(args[0]).endswith("ops.sqlite") else Path(*args, **kwargs)
    )
    # get_conn expects path relative to repo; easier to init first
    init_db(str(db_file)).close()
    conn = get_conn(str(db_file))
    cur = conn.execute("SELECT 1 AS ok")
    assert cur.fetchone()["ok"] == 1
    conn.close()
