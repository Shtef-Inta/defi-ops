---
type: cache
last_updated: 2026-04-21T03:00Z
purpose: Recent context cache for defi-ops sessions
---

# Hot Cache

Это первое, что читается при старте сессии. Если недостаточно — открыть `wiki/index.md`.

## Где мы сейчас

- **Sprint 0 — DONE**: scaffold, git, venv, deps, wiki copy, old services disabled.
- **Sprint 1 — IN PROGRESS**:
  - Task 1.1 `src/db.py` — DONE
  - Task 1.2 `src/ingest.py:fetch_twitter` — DONE (syndication + dedupe + tests)
  - Task 1.3 `src/ingest.py:fetch_youtube` — DONE (RSS + channel_id resolve + tests)
  - Task 1.4 `src/ingest.py:fetch_rss` — DONE (RSS 2.0 + Atom + dedupe + tests)
  - Next: Task 1.5 `src/ingest.py:fetch_wallets`
- **Active code**: `src/db.py`, `src/ingest.py`, `tests/test_db.py`, `tests/test_ingest.py`
- **Active config**: `config/sources.yaml`, `config/watchlist.yaml`, `config/delivery.yaml`

## Стек

- Python 3.14, stdlib-first
- SQLite `state/ops.sqlite`
- deps: certifi, Telethon, tenacity, pytest
- 9 модулей максимум (`src/db.py`, `src/ingest.py`, `src/classify.py`, `src/wallets.py`, `src/liquidity.py`, `src/decide.py`, `src/deliver.py`, `src/record.py`, `src/learn.py`)

## Session Handoff

- **Start:** `python scripts/session_start.py` — восстанавливает контекст из summaries/memory
- **End:** `python scripts/session_close.py --tasks="..." --next="..."` — сохраняет состояние
- **Memory:** `state/memory/preferences.jsonl` + `state/memory/incidents.jsonl`

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

- `src/ingest.py` — twitter + youtube DONE; остались rss, telegram, wallets
- `src/classify.py` — не написан (event-unit clustering, voice-weighted confirmation)
- DeFiLlama не подключён — Sprint 4
- Telegram delivery не интегрирована — Sprint 6

## Wiki Base — новый skill

- Skill `wiki-base` создан в `.claude/skills/wiki-base/`
- Workflow: `state/raw/<source>/` → инкрементальное обновление `wiki/`
- Скрипт: `scripts/rebuild_backlinks.py` — перестраивает бэклинки по всей вики
- `src/ingest.py` теперь сохраняет raw payloads в `state/raw/`
## Session State (auto-updated 2026-04-20 22:12Z)

- **Done:** Task 1.2+1.3 done, wiki-base skill, memory system
- **Blockers:** none
- **Next:** Task 1.4 fetch_rss

## Backlinks

- [[Machine Audit — 2026-04-20]]
- [[Wiki Log]]
- [[log]]
- [[machine-audit-2026-04-20]]

