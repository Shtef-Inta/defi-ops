# Wiki Index

Семантический слой Research-v2 по методу Карпати. Между `raw/` (сырые захваты) и `digests/` (route sheets для оператора).

LLM поддерживает страницы при каждом ingest нового сигнала. Хозяин читает wiki когда нужен полный bird's-eye view.

## Структура

```
wiki/
├── index.md          ← этот файл (каталог)
├── log.md            ← append-only chronology действий
├── protocols/        ← одна страница на DeFi-протокол
├── assets/           ← одна страница на тикер
├── concepts/         ← механики (governance, liquidity, depeg, etc.)
├── wallets/          ← watched whales / treasuries / risk wallets
├── signals/          ← интересные одиночные сигналы (с cross-refs)
└── events/           ← конкретные события (Aave V4 launch, USDe depeg risk, etc.)
```

## Правила maintenance

- **При импорте сигнала про X** — обновить соответствующую `protocols/<name>.md` и `assets/<symbol>.md`, добавить запись в `log.md`
- **Каждая страница** содержит: краткое описание, последние ключевые события, открытые вопросы, cross-references (`[[Aave]]`, `[[ENA]]`)
- **Добавить только если есть свежее изменение** — не плодить пустые страницы
- **Не переписывать историю** — append + датированный header

## Каталог страниц

### Audit / meta
- [[machine-audit-2026-04-20]] — полное сканирование машины Хозяина: все проекты, cron jobs, секреты, дубликаты, нарушения

### Protocols
- [[protocols/aave]] — lending/borrowing, critical, V4 live
- [[protocols/ethena]] — synthetic dollar (USDe/sUSDe), important
- [[protocols/uniswap]] — DEX, critical

### Assets
*(пусто — при следующем ingest)*

### Concepts
- [[concepts/risk-overlay-peckshield]] — negative-evidence gate

### Wallets
*(пусто — наполнится после Sprint 2.5 wallet intelligence)*

### Signals
*(пусто)*

### Events
- [[events/2026-04-aave-v4-deposits]] — $30M crossed, single source
- [[events/2026-04-ethena-pt-listings]] — caps $30M/$150M на Aave/Plasma, single source

## Operations

| Команда | Когда | Что делает |
|--|--|--|
| **Ingest** | новый источник в `raw/` | прочитать → summary → обновить relevant pages → log |
| **Query** | вопрос Хозяина типа "что мы знаем про X" | поиск по wiki → синтез с цитатами → опц. сохранить как новую страницу |
| **Lint** | по запросу или раз в неделю | проверить contradictions, stale claims, orphan pages, missing cross-refs |

## Связь с проектом

- `obsidian/` (project notes по фазам) ≠ `wiki/` (знания по DeFi-домену)
- `wiki/` читается при работе над route sheets (D.1) — даёт контекст для `whyMoneyMoves`, `confirmed`, `unconfirmed`
- При ingest сигнала из Twitter — Python pipeline пишет в `signals.sqlite`, я (LLM) пишу в `wiki/`
