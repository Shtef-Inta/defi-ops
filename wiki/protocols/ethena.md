---
type: protocol
chain: multi
tier: important
last_updated: 2026-04-21
---

# Ethena

Synthetic dollar протокол. Выпускает USDe (delta-neutral stablecoin) и sUSDe (yield-bearing версия). В watchlist — `important`.

## Что важно сейчас

- **Новые PT (Principal Tokens) листятся на Aave/Plasma** ([[events/2026-04-ethena-pt-listings]]):
  - June USDe PT — cap $30M
  - June sUSDe PT — cap $150M
  - Caps будут подняты по demand
- **Tokenized gold backing proposal** (governance) — обсуждается через Kairos Research (TBD при следующем ingest полного текста)
- BitGo и Kraken — custody/yield distribution context

## Открытые вопросы

- Backing risk для tokenized gold proposal — нужен governance text + kairos research polls
- USDe peg history и behavior во время market stress — не проверено
- Implications $150M cap на sUSDe — это много или мало относительно текущего sUSDe supply? Без DeFiLlama не определить (Sprint 4).
- Independent sources за пределами @ethena handle — пока только @KairosRes и @krakenfx как secondary

## Cross-refs

- [[assets/usde]], [[assets/susde]], [[assets/ena]]
- [[protocols/aave]] (host для PT listings)
- [[concepts/stablecoin-rotation]]
- [[concepts/governance]]
- [[events/2026-04-ethena-pt-listings]]

## Источники

- @ethena (X) — official
- @KairosRes (X) — independent research, governance commentary
- @krakenfx (X) — custody/yield distribution
