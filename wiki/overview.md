---
type: overview
last_updated: 2026-04-21
---

# defi-ops Overview

Чистый DeFi pipeline для $100k капитала. От сигналов из 5 источников → cross-source confirmation + wallet flow + liquidity + risk + contradiction → ≤5 карточек в день в Telegram → Хозяин решает руками → outcome → learning loop.

## В одном взгляде

```
  Sources              Analysis                        Delivery
  ───────              ────────                        ────────
  X/Twitter      ──┐
  YouTube        ──┤
  Telegram       ──┼→ SQLite ─→ event-units ─→ decision cards ─→ Telegram
  Web/RSS        ──┤                                               │
  Wallets/onchain──┘                                               ↓
                                                            operator decision
                                                              │
                                                              ↓
                                                        outcome + PnL
                                                              │
                                                              ↓
                                                    source reliability adjust
```

## Pipeline stages

1. **Ingest** (`src/ingest.py`) — fetch из 5 семейств: twitter, youtube, rss, telegram, wallets
2. **Classify** (`src/classify.py`) — event-unit clustering `(protocol, event_key, 48h)`, voice-weighted confirmation, contradiction detection
3. **Wallets** (`src/wallets.py`) — normalize tx → flows → pattern detection → group_divergence
4. **Liquidity** (`src/liquidity.py`) — DeFiLlama TVL gate (без данных — карточка не уходит)
5. **Decide** (`src/decide.py`) — cluster + flows + liquidity → decision card ≤10 строк, 3 кнопки: BUY PROBE / WATCH / SKIP
6. **Deliver** (`src/deliver.py`) — Telegram send, dry-run default
7. **Record** (`src/record.py`) — outcome CLI + reply parser (`=ВХОЖУ <id>`, `=ИГНОР <id>`)
8. **Learn** (`src/learn.py`) — outcome → reliability delta по семьям

## Watchlist

| Protocol | Tier | Chain | Последнее событие |
|--|--|--|--|
| [[protocols/aave]] | critical | ethereum | V4 crossed $30M (April) |
| [[protocols/uniswap]] | critical | ethereum | CCA context |
| [[protocols/ethena]] | important | multi | PT listings на Aave/Plasma |
| Pendle | critical | ethereum | (ожидает ingest) |
| Morpho | important | ethereum | (ожидает ingest) |
| Hyperliquid | important | multi | (ожидает ingest) |
| Fluid | important | ethereum | (ожидает ingest) |

## Ключевые правила

1. Local-only. No live trading APIs. No signing. No wallets.
2. Telegram send только с `--send --approve-send=approve-send`.
3. Не строить новые scoring layers до ≥3 реальных outcomes.
4. Safety flags в каждом артефакте (`researchOnly=True`, `sendAllowed=False` по умолчанию).
5. Financial recommendation только после: voice_weight ≥3.0, ≥2 families, liquidity verified, no active risk overlay, contradiction disclosed.
6. Noise cap: максимум 5 карточек/день в Telegram.

## Глубже

- Полный план: `PLAN.md`
- Проектный контекст: `CLAUDE.md`
- Живая хронология wiki: [[log]]

## Backlinks

- [[Aave]]
- [[Ethena]]
- [[Uniswap]]
- [[Wiki Log]]
- [[aave]]
- [[ethena]]
- [[log]]
- [[protocols/aave]]
- [[protocols/ethena]]
- [[protocols/uniswap]]
- [[uniswap]]

