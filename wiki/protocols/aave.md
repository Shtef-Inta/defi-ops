---
type: protocol
chain: ethereum
tier: critical
last_updated: 2026-04-20
---

# Aave

Lending/borrowing протокол, флагман DeFi. В нашем watchlist — `critical`.

## Что важно сейчас

- **V4 запущен на Ethereum mainnet** ([[events/2026-04-aave-v4-deposits]]). Crossed $30M deposits в апреле 2026.
- Используется как infrastructure для других протоколов — например, [[protocols/ethena]] листит свои PT на Aave/Plasma instance с caps $30M (USDe) и $150M (sUSDe).
- **2026-04-20**: V4 launch теперь имеет **cross_family_confirmed** cluster — к Aave official (X + YouTube Aave Labs) добавлена research семья (The Rollup interview Стани Кулечова). Это первый маршрут в системе с независимым подтверждением через разные семьи.

## Открытые вопросы

- Реальная liquidity и depth на V4 vs V3 — не проверено через DeFiLlama.
- Risk parameters новых listings (USDe/sUSDe PT) — нужны docs ссылки.
- Governance подтверждение из форума aave.com/governance ещё не пересекается с V4 launch по времени — pub_date из RSS не сохраняется (fetcher пишет fetch_time вместо article pub_date). Это будет править в Sprint 2.5.

## Cross-refs

- [[assets/aave]] (токен)
- [[protocols/ethena]] (как distribution channel)
- [[events/2026-04-aave-v4-deposits]]
- [[concepts/governance]]

## Источники

- @aave (X) — официальный, single_source
- Aave Labs (YouTube, @aavelabs) — официальный, video "Aave V4 deep dive and risk controls"
- The Rollup (YouTube) — research, интервью со Стани Кулечовым про V4
- Aave Governance Forum (RSS) — парсится, но pub_date не сохраняется ⇒ не попадает в window
- DeFiLlama TVL (пока не подключён)
