---
type: protocol
chain: ethereum
tier: critical
last_updated: 2026-04-21
---

# Aave

Lending/borrowing протокол, флагман DeFi. В нашем watchlist — `critical`.

## Что важно сейчас

- **V4 запущен на Ethereum mainnet** ([[events/2026-04-aave-v4-deposits]]). Crossed $30M deposits в апреле 2026.
- Используется как infrastructure для других протоколов — например, [[protocols/ethena]] листит свои PT на Aave/Plasma instance с caps $30M (USDe) и $150M (sUSDe).
- **Voice confirmation:** Aave official (X + YouTube Aave Labs) + research семья (The Rollup interview Стани Кулечова). В defi-ops taxonomy это попадает под `high` confidence (≥2 families, weight ≥3.0).

## Открытые вопросы

- Реальная liquidity и depth на V4 vs V3 — не проверено через DeFiLlama (Sprint 4).
- Risk parameters новых listings (USDe/sUSDe PT) — нужны docs ссылки.
- Governance подтверждение из форума aave.com/governance ещё не пересекается с V4 launch по времени — pub_date из RSS vs fetch_time mismatch (Sprint 1).

## Cross-refs

- [[assets/aave]] (токен)
- [[protocols/ethena]] (как distribution channel)
- [[events/2026-04-aave-v4-deposits]]
- [[concepts/governance]]

## Источники

- @aave (X) — official
- Aave Labs (YouTube, @aavelabs) — official, video "Aave V4 deep dive and risk controls"
- The Rollup (YouTube) — research, интервью со Стани Кулечовым про V4
- Aave Governance Forum (RSS) — парсится, но pub_date propagation в Sprint 1
- DeFiLlama TVL (пока не подключён — Sprint 4)
