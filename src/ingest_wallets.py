"""Wallet fetcher via Etherscan v2 + optional Arkham labels."""
from __future__ import annotations

import json
import os
import ssl
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import certifi

    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL_CTX = ssl.create_default_context()

from src.db import get_conn

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

ETHERSCAN_V2_URL = "https://api.etherscan.io/v2/api"
ARKHAM_URL = "https://api.arkhamintelligence.com/intelligence/address"


def _env_key(name: str) -> str | None:
    return os.environ.get(name) or None


def _parse_wallets(text: str) -> list[dict]:
    """Extract wallet dicts from the wallets section of sources.yaml."""
    wallets: list[dict] = []
    in_wallets = False
    current_group: str | None = None
    current_item: dict | None = None

    for raw in text.splitlines():
        line = raw.rstrip("\n")
        stripped = line.lstrip(" ")
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))

        if stripped == "wallets:":
            in_wallets = True
            continue

        if in_wallets and indent == 0 and stripped:
            break

        if not in_wallets:
            continue

        if indent == 2 and stripped.split()[0].endswith(":"):
            current_group = stripped.split("#")[0].strip().rstrip(":").strip()
            current_item = None
            continue

        if indent == 4 and stripped.startswith("- "):
            current_item = {}
            rest = stripped[2:].strip()
            if ":" in rest:
                k, _, v = rest.partition(":")
                current_item[k.strip()] = v.strip().strip('"').strip("'")
            if current_item and current_group and current_group != "autodiscover":
                current_item["_group"] = current_group
                wallets.append(current_item)
            continue

        if indent == 6 and current_item is not None and ":" in stripped:
            k, _, v = stripped.partition(":")
            current_item[k.strip()] = v.strip().strip('"').strip("'")

    return wallets


def _fetch_etherscan_txs(address: str, api_key: str | None, chain: str = "ethereum", timeout: int = 15) -> list[dict]:
    if not api_key:
        return []
    chainid = 1 if chain == "ethereum" else 1
    url = (
        f"{ETHERSCAN_V2_URL}?chainid={chainid}&module=account&action=txlist"
        f"&address={address}&sort=desc&apikey={api_key}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception:
        return []

    if data.get("status") != "1" or not isinstance(data.get("result"), list):
        return []
    return data["result"]


def _fetch_arkham_labels(address: str, api_key: str | None, timeout: int = 15) -> dict:
    if not api_key:
        return {}
    url = f"{ARKHAM_URL}/{address}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "API-Key": api_key})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception:
        return {}


def _normalize_tx(tx: dict, wallet: dict) -> dict | None:
    tx_hash = tx.get("hash") or tx.get("txHash")
    if not tx_hash:
        return None
    ts = tx.get("timeStamp")
    try:
        block_time = datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat() if ts else None
    except Exception:
        block_time = None

    return {
        "address": wallet.get("address", "").lower(),
        "wallet_group": wallet.get("_group", "unknown"),
        "tx_hash": tx_hash.lower(),
        "chain": wallet.get("chain", "ethereum"),
        "tx_type": None,
        "counterparties": None,
        "value_usd": None,
        "token_symbols": None,
        "block_time": block_time,
        "tx_from": tx.get("from", "").lower() or None,
        "tx_to": tx.get("to", "").lower() or None,
        "tx_input": tx.get("input") or None,
        "tx_value": tx.get("value") or None,
    }


def fetch_wallets(
    db_path: Optional[str] = None,
    max_per_wallet: int = 50,
    timeout: int = 15,
    _write_raw=None,
) -> dict:
    """Fetch watched wallet transactions via Etherscan v2 and insert into wallet_tx."""
    sources_path = Path(__file__).parent.parent / "config" / "sources.yaml"
    wallets = _parse_wallets(sources_path.read_text()) if sources_path.exists() else []

    api_key = _env_key("ETHERSCAN_API_KEY")
    arkham_key = _env_key("ARKHAM_API_KEY")

    conn = get_conn(db_path)
    inserted = 0
    skipped = 0
    failed = 0
    total_wallets = 0

    for w in wallets:
        addr = w.get("address", "")
        if not addr or w.get("enabled", "true").lower() == "false":
            continue
        total_wallets += 1

        txs = _fetch_etherscan_txs(addr, api_key, w.get("chain", "ethereum"), timeout=timeout)
        if not txs:
            failed += 1
            continue

        if _write_raw:
            _write_raw(
                "wallets",
                w.get("name", addr),
                {
                    "address": addr,
                    "group": w.get("_group", "unknown"),
                    "captured_at": datetime.now(timezone.utc).isoformat(),
                    "txs": txs[:max_per_wallet],
                },
            )

        for tx in txs[:max_per_wallet]:
            norm = _normalize_tx(tx, w)
            if not norm:
                continue

            existing = conn.execute(
                "SELECT 1 FROM wallet_tx WHERE tx_hash = ?",
                (norm["tx_hash"],),
            ).fetchone()
            if existing:
                skipped += 1
                continue

            conn.execute(
                """
                INSERT INTO wallet_tx
                    (address, wallet_group, tx_hash, chain, tx_type, counterparties,
                     value_usd, token_symbols, block_time, tx_from, tx_to, tx_input, tx_value)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    norm["address"],
                    norm["wallet_group"],
                    norm["tx_hash"],
                    norm["chain"],
                    norm["tx_type"],
                    norm["counterparties"],
                    norm["value_usd"],
                    norm["token_symbols"],
                    norm["block_time"],
                    norm["tx_from"],
                    norm["tx_to"],
                    norm["tx_input"],
                    norm["tx_value"],
                ),
            )
            inserted += 1

    conn.commit()
    conn.close()
    return {
        "wallets_attempted": total_wallets,
        "inserted": inserted,
        "skipped": skipped,
        "failed": failed,
    }
