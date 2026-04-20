# Plan: Liquidity Gate (DeFiLlama)

## Task 1 — Core fetcher + cache
- **Files**: `src/liquidity.py`, `tests/test_liquidity.py`
- **Tests**: stubbed HTTP for DeFiLlama, cache TTL logic
- **Deps**: none

## Task 2 — Protocol slug mapping
- **Files**: `config/watchlist.yaml` (add `defillama_slug`), `src/liquidity.py`
- **Tests**: mapping lookup tests
- **Deps**: Task 1

## Task 3 — Integrate into decide.py
- **Files**: `src/decide.py`
- **Tests**: card blocked when liquidity missing, passed when present
- **Deps**: Task 1, Task 2

## Task 4 — Update delivery format
- **Files**: `src/decide.py` (show TVL in card), `src/deliver.py`
- **Tests**: format_card includes TVL line
- **Deps**: Task 3
