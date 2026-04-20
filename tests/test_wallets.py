"""Tests for wallets.py — tx classification and divergence."""
from __future__ import annotations

import pytest

from src import wallets
from src.db import init_db


def test_classify_wallet_txs(tmp_path):
    db_file = tmp_path / "test.sqlite"
    conn = init_db(str(db_file))
    conn.execute(
        """
        INSERT INTO wallet_tx (address, wallet_group, tx_hash, tx_from, tx_to, tx_input, block_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        ("0xabc", "reference", "0x1", "0xdef", "0xabc", "0x", "2025-04-21T10:00:00+00:00"),
    )
    conn.execute(
        """
        INSERT INTO wallet_tx (address, wallet_group, tx_hash, tx_from, tx_to, tx_input, block_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        ("0xabc", "reference", "0x2", "0xabc", "0xdef", "0x", "2025-04-21T10:00:00+00:00"),
    )
    conn.execute(
        """
        INSERT INTO wallet_tx (address, wallet_group, tx_hash, tx_from, tx_to, tx_input, block_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        ("0xabc", "reference", "0x3", "0xabc", "0xdef", "0xa9059cbb", "2025-04-21T10:00:00+00:00"),
    )
    conn.commit()
    conn.close()

    res = wallets.classify_wallet_txs(str(db_file))
    assert res["classified"] == 3

    conn = init_db(str(db_file))
    rows = conn.execute("SELECT tx_type FROM wallet_tx ORDER BY id").fetchall()
    assert rows[0][0] == "inflow"
    assert rows[1][0] == "outflow"
    assert rows[2][0] == "contract_interaction"
    conn.close()


def test_detect_divergence_empty(tmp_path):
    db_file = tmp_path / "test.sqlite"
    init_db(str(db_file)).close()
    div = wallets.detect_divergence(str(db_file))
    assert div == []
