---
type: index
last_updated: 2026-04-21
---

# Wiki Index

Семантический слой defi-ops по методу Карпати. Между `raw/` (сырые захваты) и `digests/` (daily summaries).

LLM поддерживает страницы при каждом ingest нового сигнала. Хозяин читает wiki когда нужен полный bird's-eye view.

## Структура

```
wiki/
├── index.md          ← этот файл (каталог)
├── hot.md            ← оперативный контекст текущего спринта
├── overview.md       ← pipeline-диаграмма + watchlist
├── log.md            ← append-only chronology (archive + новые)
├── protocols/        ← одна страница на DeFi-протокол
├── assets/           ← одна страница на тикер
├── concepts/         ← механики (governance, liquidity, depeg, risk overlay, etc.)
├── wallets/          ← watched whales / treasuries / risk wallets
├── signals/          ← интересные одиночные сигналы (с cross-refs)
└── events/           ← конкретные события (launch, freeze, depeg, etc.)
```

## Правила maintenance

- **При импорте сигнала про X** — обновить соответствующую `protocols/<name>.md` и `assets/<symbol>.md`, добавить запись в `log.md`
- **Каждая страница** содержит: краткое описание, последние ключевые события, открытые вопросы, cross-refs
- **Добавить только если есть свежее изменение** — не плодить пустые страницы
- **Не переписывать историю** — append + датированный header

## Каталог страниц

### Audit / meta
- [[machine-audit-2026-04-20]] — полное сканирование машины: проекты, cron jobs, секреты, дубликаты (archive, 2026-04-20)

### Protocols
- [[protocols/aave]] — lending/borrowing, critical tier, V4 live
- [[protocols/ethena]] — synthetic dollar (USDe/sUSDe), important tier
- [[protocols/uniswap]] — DEX, critical tier

### Assets
- [[assets/aave]] — AAVE token
- [[assets/ena]] — ENA token
- [[assets/susde]] — sUSDe synthetic dollar
- [[assets/usde]] — USDe synthetic dollar
- [[assets/uni]] — UNI token

### Concepts
- [[concepts/dex-liquidity]] — DEX liquidity mechanics
- [[concepts/governance]] — on-chain/off-chain governance
- [[concepts/risk-overlay-peckshield]] — negative-evidence gate
- [[concepts/stablecoin-rotation]] — yield-driven stablecoin flows

### Wallets
*(пусто — наполнится после Sprint 3 wallet intelligence)*

### Signals
*(пусто)*

### Events
- [[events/2026-04-aave-v4-deposits]] — $30M crossed, April 2026
- [[events/2026-04-ethena-pt-listings]] — caps $30M/$150M на Aave/Plasma

## Operations

| Команда | Когда | Что делает |
|--|--|--|
| **Ingest** | новый сигнал в `raw/` | прочитать → summary → обновить relevant pages → log |
| **Query** | вопрос Хозяина типа "что мы знаем про X" | поиск по wiki → синтез с цитатами → опц. сохранить как новую страницу |
| **Lint** | по запросу или раз в неделю | проверить contradictions, stale claims, orphan pages, missing cross-refs |

## Связь с проектом

- `CLAUDE.md` — Level 1 context (stack, rules, commands)
- `PLAN.md` — sprint roadmap (Sprint 0–7)
- `wiki/` — знания по DeFi-домену, обновляются при ingest
- `src/classify.py` читает wiki при enrichment для `event_key` validation

## Backlinks

- [[2026-04-aave-v4-deposits]]
- [[2026-04-ethena-pt-listings]]
- [[Aave]]
- [[Aave V4 deposits crossed $30M]]
- [[Ethena]]
- [[Ethena PT listings on Aave/Plasma (April 2026)]]
- [[Machine Audit — 2026-04-20]]
- [[Risk Overlay — PeckShield]]
- [[Uniswap]]
- [[aave]]
- [[concepts/risk-overlay-peckshield]]
- [[ethena]]
- [[events/2026-04-aave-v4-deposits]]
- [[events/2026-04-ethena-pt-listings]]
- [[machine-audit-2026-04-20]]
- [[protocols/aave]]
- [[protocols/ethena]]
- [[protocols/uniswap]]
- [[risk-overlay-peckshield]]
- [[uniswap]]

