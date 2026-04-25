"""Price fetching with caching."""
from __future__ import annotations
from typing import Optional

PROTOCOL_TO_COIN = {
    "jupiter": "jupiter-exchange-solana",
    "aave": "aave",
    "uniswap": "uniswap",
    "ethena": "ethena",
    "pendle": "pendle",
    "morpho": "morpho",
    "lido": "lido-dao",
    "hyperliquid": "hyperliquid",
    "fluid": "fluid",
    "compound": "compound-governance-token",
    "curve": "curve-dao-token",
    "sky": "sky",
    "spark": "spark",
    "eigenlayer": "eigenlayer",
    "gearbox": "gearbox",
    "balancer": "balancer",
    "gmx": "gmx",
    "dydx": "dydx",
}

def snapshot_prices(db_path=None, coin_ids=None, max_age_minutes=5):
    """Placeholder: returns empty dict. Implement with CoinGecko cache."""
    return {}
