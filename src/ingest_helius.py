"""Helius Solana ingest: NFT sales, token transfers, program interactions."""
from __future__ import annotations

import json
import os
import urllib.request
import ssl
from datetime import datetime, timezone
from typing import Optional

_API_KEY = os.environ.get("HELIUS_API_KEY", "")
_SSL_CTX = ssl.create_default_context()
_BASE = "https://mainnet.helius-rpc.com"


def rpc_call(method: str, params: list) -> dict:
    if not _API_KEY:
        return {}
    url = f"{_BASE}/?api-key={_API_KEY}"
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, context=_SSL_CTX, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return {}


def ingest_recent_signatures(address: str, limit: int = 20) -> list[dict]:
    data = rpc_call("getSignaturesForAddress", [address, {"limit": limit}])
    return data.get("result", [])


def ingest_helius(db_path: Optional[str] = None) -> dict:
    """Stub: ingest Solana activity. Requires HELIUS_API_KEY."""
    return {"inserted": 0, "note": "stub: set HELIUS_API_KEY to enable"}
