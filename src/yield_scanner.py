"""Yield anomaly scanner: APY deviations, new vaults, points farming."""
from __future__ import annotations

import json
import urllib.request
import ssl
from typing import Optional

_SSL_CTX = ssl.create_default_context()
_DEFILLAMA_POOLS = "https://yields.llama.fi/pools"


def fetch_pools() -> list[dict]:
    """Fetch yield pools from DeFiLlama."""
    try:
        req = urllib.request.Request(_DEFILLAMA_POOLS, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, context=_SSL_CTX, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        return data.get("data", [])[:200]
    except Exception:
        return []


def detect_anomalies(pools: list[dict], z_threshold: float = 2.0) -> list[dict]:
    """Detect pools with APY > z_threshold standard deviations above mean for their chain."""
    from statistics import mean, stdev
    by_chain = {}
    for p in pools:
        chain = p.get("chain", "Unknown")
        by_chain.setdefault(chain, []).append(p.get("apy", 0))

    chain_stats = {}
    for chain, apys in by_chain.items():
        if len(apys) < 3:
            continue
        try:
            chain_stats[chain] = {"mean": mean(apys), "stdev": stdev(apys)}
        except Exception:
            pass

    anomalies = []
    for p in pools:
        chain = p.get("chain", "Unknown")
        apy = p.get("apy", 0)
        stats = chain_stats.get(chain)
        if not stats or stats["stdev"] == 0:
            continue
        z = (apy - stats["mean"]) / stats["stdev"]
        if z > z_threshold and apy > 0.10:  # >10% APY and >2σ
            anomalies.append({
                "pool": p.get("pool", "unknown"),
                "protocol": p.get("project", "unknown"),
                "chain": chain,
                "apy": apy,
                "tvl_usd": p.get("tvlUsd", 0),
                "z_score": round(z, 2),
                "mean_apy": round(stats["mean"] * 100, 2),
                "url": p.get("url", ""),
            })
    return sorted(anomalies, key=lambda x: x["z_score"], reverse=True)


def scan(db_path: Optional[str] = None) -> dict:
    """Full yield scan."""
    pools = fetch_pools()
    anomalies = detect_anomalies(pools)
    new_vaults = [p for p in pools if p.get("tvlUsd", 0) > 1_000_000 and p.get("apy", 0) > 0.20][:10]
    return {
        "pools_checked": len(pools),
        "anomalies": anomalies[:10],
        "new_vaults": [{"pool": p.get("pool"), "protocol": p.get("project"), "apy": p.get("apy"), "tvl": p.get("tvlUsd")} for p in new_vaults],
    }
