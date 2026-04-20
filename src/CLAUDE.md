# src/ — Level 2 Context

## Module Map

| File | Lines | Responsibility | Tests |
|--|--|--|--|
| `db.py` | ~170 | SQLite schema + migrations | `tests/test_db.py` |
| `ingest.py` | ~550 | Fetchers: twitter (syndication), youtube (RSS), soon rss/wallets/tg | `tests/test_ingest.py` |
| `classify.py` | — | Event-unit clustering, voice-weighted confirmation, contradiction | `tests/test_classify.py` (TDD) |
| `wallets.py` | — | On-chain normalize, flow patterns, group_divergence | `tests/test_wallets.py` (TDD) |
| `liquidity.py` | — | DeFiLlama TVL gate | `tests/test_liquidity.py` |
| `decide.py` | — | Decision card builder, noise cap, gates | `tests/test_decide.py` (TDD) |
| `deliver.py` | — | Telegram send + approval gate | — |
| `record.py` | — | Outcome recording + PnL | — |
| `learn.py` | — | Outcome → reliability delta | `tests/test_learn.py` (TDD) |
| `cli.py` | — | Entry point: run, send, record, audit | — |

## Hard Rules for src/

1. **≤400 lines per file.** If a module grows beyond 400 lines — split by responsibility.
2. **9 source modules maximum.** If a 10th is needed — architecture review first.
3. **TDD for classify, decide, wallets:group_divergence, learn.** Red → green → refactor.
4. **Integration tests for ingest, deliver.** Mock HTTP, mock Telegram API.
5. **No live API calls in tests.** Use fixtures and monkeypatch.
6. **No financial transactions.** Read-only ingest, manual execution only.
7. **Credentials never in code.** Read from `.env`, chmod 600.
