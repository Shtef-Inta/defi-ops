---
type: overview
last_updated: 2026-04-20
---

# Research-v2 Overview

Локальный DeFi research pipeline для $100k капитала. Цель: от сигналов (X/YouTube/Telegram/Web/Wallets) → cross-source confirmation + wallet flow → financial recommendation в Telegram → outcome tracking → learning loop.

## В одном взгляде

```
  Sources                         Analysis                    Delivery
  ───────                         ────────                    ────────
  X/Twitter        ──┐
  YouTube          ──┤
  Telegram         ──┼→ signals.sqlite ─→ clusters ─→ route sheets ─→ Telegram card
  Web/RSS          ──┤                                                     │
  Profile sites    ──┘                                                     ↓
                                                                    operator decision
  Wallet/onchain   ─→ wallet-flows ─→ patterns+anomalies               │
                                  ↘                                     ↓
                                   correlation with signals        outcome + PnL
                                                                        │
                                                                        ↓
                                                        source reliability adjust
```

## Текущий статус

- **Phase 1 (сбор)** ✅ — X работает через bridge из browser-observed captures
- **Phase 2 (оценка)** ✅ — scoring/triage/dedupe в Python pipeline
- **Phase 3 (feedback)** 🔄 — 10 manual confirmations, top-3 prompt не достроен
- **Phase 4 (route execution)** 🔄 — Task 1 (`generate_route_sheet.py`) готов, 3 задачи впереди
- **Phase 5 (learning)** ❌ — зависит от Phase 4

## Ключевые артефакты

- `signals.sqlite` — единое хранилище сигналов (в .gitignore)
- `digests/YYYY-MM-DD-route-sheets.{json,md}` — готовые маршруты для оператора
- `digests/YYYY-MM-DD-defi-summary.md` — ежедневный DeFi-summary
- `wiki/` — семантический слой (Karpathy method)

## Watchlist

| Protocol | Tier | Chain | Последнее событие |
|--|--|--|--|
| [[protocols/aave]] | critical | ethereum | V4 crossed $30M (April) |
| [[protocols/uniswap]] | critical | ethereum | CCA context |
| [[protocols/ethena]] | important | multi | PT listings на Aave/Plasma |
| Pendle | critical | ethereum | (нет новых данных) |
| Morpho | important | ethereum | (нет новых данных) |
| Gearbox | critical | ethereum | (нет новых данных) |

## Ключевые правила

1. Local-only. No live trading APIs. No signing. No wallets.
2. Telegram send только с явным approval от Хозяина.
3. Не строить новые scoring layers до реального outcome.
4. Safety flags в каждом артефакте (`researchOnly=true`).
5. Financial recommendation только после ≥2 cross-family confirmation + liquidity verified + no active risk overlay.

## Глубже

- Полный план: [[../PHASE_4_PLAN]] (в корне проекта)
- Текущие задачи: [[../tasks/todo]]
- Проектные правила: [[../obsidian/projects/research/PROJECT_STATE]]
- Живая хронология wiki: [[log]]
