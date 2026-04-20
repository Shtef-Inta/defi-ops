---
type: event
date: 2026-04
protocol: ethena
assets: [USDe, sUSDe, ENA]
host_protocol: aave
chain: plasma
confidence: single
last_updated: 2026-04-21
---

# Ethena PT listings on Aave/Plasma (April 2026)

## Что произошло

Ethena объявила листинг новых Principal Tokens (PT) на инстансе Aave, развёрнутом на Plasma:

- June USDe PT — borrow cap **$30M**
- June sUSDe PT — borrow cap **$150M**
- Caps будут подняты по scaling demand

## Источники

- @ethena (X) — official пост
- **Cross-family confirmation: ОТСУТСТВУЕТ** — пока нет governance post, нет docs link, нет DeFiLlama подтверждения активных pools

## Что не подтверждено

- Конкретные Aave governance proposal id / дата активации
- Реальный uptake vs cap — заполнены ли caps или остаются свободными
- Risk parameters для этих PT (liquidation thresholds, oracle)
- Какой именно инстанс Aave на Plasma (это fork? licensed deployment?)
- Implications для [[protocols/aave]] main deployment

## Значение для decision cards

- Tier: important
- Триггер для пересмотра: Aave governance post → верификация caps → DeFiLlama показывает realized supply/borrow
- Без этого — verdict `SKIP`

## Связанное

Недавнее governance proposal у Ethena про tokenized gold backing — отдельное событие, нужен ingest через @KairosRes или governance forum. TBD.

## Backlinks

- [[Aave]]
- [[Ethena]]
- [[Wiki Index]]
- [[Wiki Log]]
- [[aave]]
- [[ethena]]
- [[index]]
- [[log]]
- [[protocols/aave]]
- [[protocols/ethena]]

