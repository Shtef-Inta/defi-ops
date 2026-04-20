# Spec: Liquidity Gate (DeFiLlama)

## Goal
Before any decision card is sent to Telegram, verify that the protocol has fresh TVL data from DeFiLlama. If not — block the card and mark it `liquidity_unverified`.

## Requirements
- MUST: Fetch protocol TVL from `api.llama.fi/protocol/<slug>`
- MUST: Cache response in `state/liquidity-cache.json` with 1-hour TTL
- MUST: If cache stale/missing and API fails → block card
- SHOULD: Support 12 protocols from `config/watchlist.yaml`
- NICE: Show TVL delta (24h) in decision card

## Interface
```python
def fetch_protocol_tvl(protocol: str) -> dict | None:
    """Return {tvl, tvl_24h_delta, timestamp} or None on failure."""
    ...

def is_liquidity_verified(protocol: str, min_tvl_usd: float = 1_000_000) -> bool:
    """Check fresh TVL >= threshold."""
    ...
```

## Open Questions
- What slug mapping for each protocol? (Aave → "aave", Uniswap → "uniswap-v3"?)
- Do we need pool-level liquidity or protocol-level is enough?
