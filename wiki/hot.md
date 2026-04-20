---
type: cache
last_updated: 2026-04-21T02:04Z
purpose: Recent context cache for defi-ops sessions
---

# Hot Cache

Это первое, что читается при старте сессии. Если недостаточно — открыть `wiki/index.md`.

## Где мы сейчас

- **Sprint 0 — DONE**: scaffold, git, venv, deps, wiki copy, old services disabled.
- **Sprint 1 — IN PROGRESS**:
  - Task 1.1 `src/db.py` — DONE (schema + tests green)
  - Next: Task 1.2 `src/ingest.py:fetch_twitter` via syndication.twitter.com
- **Active code**: `src/db.py`, `tests/test_db.py`, `tests/test_sanity.py`
- **Active config**: `config/sources.yaml`, `config/watchlist.yaml`, `config/delivery.yaml`

## Стек

- Python 3.14, stdlib-first
- SQLite `state/ops.sqlite`
- deps: certifi, Telethon, tenacity, pytest
- 9 модулей максимум (`src/db.py`, `src/ingest.py`, `src/classify.py`, `src/wallets.py`, `src/liquidity.py`, `src/decide.py`, `src/deliver.py`, `src/record.py`, `src/learn.py`)

## Жёсткие правила

- Никаких новых scoring/attribution layers вне PLAN.md
- Telegram send только с `--send --approve-send=approve-send`
- TDD для classify, decide, wallets group_divergence, learn
- Integration tests для ingest, deliver
- Credentials chmod 600, никогда в git

## Архивные проекты (frozen)

- Research-v2 (`/Users/shtef/Research-v2/`) — frozen archive, LaunchAgent выключен
- openclaw TS pipeline (`~/.openclaw/workspace/`) — cron jobs disabled, gateway оставлен для klava-supervisor

## Watchlist (текущий)

| Protocol | Tier | Последнее событие |
|--|--|--|
| Aave | critical | V4 $30M deposits (апрель) |
| Uniswap | critical | CCA auctions context |
| Ethena | important | PT caps $30M/$150M на Aave/Plasma |

## Открытые блокеры

- `src/ingest.py` — не написан (5 fetchers: twitter, youtube, rss, telegram, wallets)
- `src/classify.py` — не написан (event-unit clustering, voice-weighted confirmation)
- DeFiLlama не подключён — Sprint 4
- Telegram delivery не интегрирована — Sprint 6

## Последнее изменение wiki

- `2026-04-21 02:04Z` — unified wiki migration: переписаны index, hot, overview; обновлены protocols/events/concepts для defi-ops taxonomy.
- Если эта строка старше 24 часов и были новые ingest — обновить hot.md обязательно.
