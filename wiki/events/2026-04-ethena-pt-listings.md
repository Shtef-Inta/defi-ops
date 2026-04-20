---
type: event
date: 2026-04
protocol: ethena
assets: [USDe, sUSDe, ENA]
host_protocol: aave
chain: plasma
confirmation: single_source
last_updated: 2026-04-20
---

# Ethena PT listings on Aave/Plasma (April 2026)

## Что произошло

Ethena объявила листинг новых Principal Tokens (PT) на инстансе Aave, развёрнутом на Plasma:

- June USDe PT — borrow cap **$30M**
- June sUSDe PT — borrow cap **$150M**
- Caps будут подняты по scaling demand

## Источники

- @ethena (X) — официальный пост
- **Cross-family confirmation: ОТСУТСТВУЕТ** — пока нет governance post, нет docs link, нет DeFiLlama подтверждения активных pools

## Что не подтверждено

- Конкретные Aave governance proposal id / дата активации
- Реальный uptake vs cap — заполнены ли caps или остаются свободными
- Risk parameters для этих PT (liquidation thresholds, oracle)
- Какой именно инстанс Aave на Plasma (это fork? licensed deployment?)
- Implications для [[protocols/aave]] main deployment

## Значение для route decisions

- Route sheet: `Ethena` tier=important, action=ждать
- Триггер для пересмотра: Aave governance post → верификация caps → DeFiLlama показывает realизованный supply/borrow
- Без этого — не входим

## Связанное

Недавнее governance proposal у Ethena про tokenized gold backing — отдельное событие, нужен ingest через @KairosRes или governance forum. TBD.

## Cross-refs

- [[protocols/ethena]]
- [[protocols/aave]] (host)
- [[assets/usde]], [[assets/susde]]
- [[concepts/stablecoin-rotation]]
