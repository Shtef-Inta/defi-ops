"""SQLite schema and helpers for defi-ops."""
import sqlite3
from pathlib import Path
from typing import Optional

SCHEMA_SQL = """
-- Signals: raw ingest from all 5 source families
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_family TEXT NOT NULL,
    source_handle TEXT,
    protocol TEXT,
    event_key TEXT,
    content TEXT,
    url TEXT,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    asset_symbols TEXT,
    sentiment TEXT CHECK(sentiment IN ('bullish','bearish','neutral')),
    raw_payload TEXT
);

CREATE INDEX IF NOT EXISTS idx_signals_captured ON signals(captured_at);
CREATE INDEX IF NOT EXISTS idx_signals_protocol ON signals(protocol);
CREATE INDEX IF NOT EXISTS idx_signals_family ON signals(source_family);
CREATE INDEX IF NOT EXISTS idx_signals_asset ON signals(asset_symbols);

-- Clusters: event-unit (protocol, event_key, 48h window)
CREATE TABLE IF NOT EXISTS clusters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    protocol TEXT NOT NULL,
    event_key TEXT NOT NULL,
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    aspects TEXT, -- JSON array of families present
    voice_weight REAL DEFAULT 0.0,
    confidence TEXT CHECK(confidence IN ('high','medium','single')),
    contradiction_flag INTEGER DEFAULT 0,
    contradiction_reason TEXT,
    status TEXT DEFAULT 'open' CHECK(status IN ('open','closed','blocked','delivered')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_clusters_protocol ON clusters(protocol);
CREATE INDEX IF NOT EXISTS idx_clusters_event ON clusters(event_key);
CREATE INDEX IF NOT EXISTS idx_clusters_status ON clusters(status);
CREATE INDEX IF NOT EXISTS idx_clusters_created ON clusters(created_at);

-- Cluster-to-signal linkage
CREATE TABLE IF NOT EXISTS cluster_signals (
    cluster_id INTEGER NOT NULL,
    signal_id INTEGER NOT NULL,
    PRIMARY KEY (cluster_id, signal_id)
);

-- Wallet raw transactions
CREATE TABLE IF NOT EXISTS wallet_tx (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    address TEXT NOT NULL,
    wallet_group TEXT NOT NULL,
    tx_hash TEXT UNIQUE,
    chain TEXT,
    tx_type TEXT CHECK(tx_type IN ('inflow','outflow','swap','bridge','contract_interaction')),
    counterparties TEXT,
    value_usd REAL,
    token_symbols TEXT,
    block_time TIMESTAMP,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_wallet_tx_addr ON wallet_tx(address);
CREATE INDEX IF NOT EXISTS idx_wallet_tx_time ON wallet_tx(block_time);
CREATE INDEX IF NOT EXISTS idx_wallet_tx_group ON wallet_tx(wallet_group);

-- Normalized wallet flows
CREATE TABLE IF NOT EXISTS wallet_flows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tx_id INTEGER REFERENCES wallet_tx(id),
    protocol TEXT,
    direction TEXT CHECK(direction IN ('in','out')),
    amount_token REAL,
    token_symbol TEXT,
    normalized_type TEXT CHECK(normalized_type IN ('accumulation','drain','positioning','bridge_surge')),
    pattern_flags TEXT,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Decision cards
CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_id INTEGER REFERENCES clusters(id),
    card_id TEXT UNIQUE,
    verdict TEXT CHECK(verdict IN ('BUY_PROBE','WATCH','SKIP','BLOCKED')),
    size_usd REAL,
    trigger_entry TEXT,
    trigger_exit TEXT,
    liquidity_verified INTEGER DEFAULT 0,
    tvl_at_decision REAL,
    risk_flags TEXT,
    card_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    message_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_decisions_card ON decisions(card_id);
CREATE INDEX IF NOT EXISTS idx_decisions_cluster ON decisions(cluster_id);
CREATE INDEX IF NOT EXISTS idx_decisions_created ON decisions(created_at);

-- Outcomes: operator replies / CLI records
CREATE TABLE IF NOT EXISTS outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id INTEGER REFERENCES decisions(id),
    decision TEXT CHECK(decision IN ('entered','ignored','exited','deferred')),
    entry_price REAL,
    exit_price REAL,
    pnl_pct REAL,
    notes TEXT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_outcomes_decision ON outcomes(decision_id);

-- Source reliability (voice-weight denominator)
CREATE TABLE IF NOT EXISTS source_reliability (
    source_family TEXT NOT NULL,
    source_handle TEXT NOT NULL,
    reliability REAL DEFAULT 1.0,
    outcomes_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (source_family, source_handle)
);

CREATE INDEX IF NOT EXISTS idx_reliability_score ON source_reliability(reliability DESC);

-- API daily budget counters
CREATE TABLE IF NOT EXISTS api_budget (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT UNIQUE NOT NULL,
    calls_today INTEGER DEFAULT 0,
    calls_max INTEGER DEFAULT 1000,
    reset_date TEXT,
    last_call_at TIMESTAMP
);
"""


def init_db(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else Path(__file__).parent.parent / "state" / "ops.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn


def get_conn(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else Path(__file__).parent.parent / "state" / "ops.sqlite"
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn
