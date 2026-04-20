---
type: event
date: 2026-04
protocol: aave
assets: [AAVE, ETH]
confirmation: single_source
last_updated: 2026-04-20
---

# Aave V4 deposits crossed $30M

## Что произошло

Aave V4 (новая версия протокола), запущенная на Ethereum mainnet, преодолела отметку $30M деposits в апреле 2026.

## Источники

- @aave — пост `Aave V4 is now live on @ethereum` (Mar 30)
- @aave — пост `Aave V4 crossed $30 million deposits` (April)
- **Cross-family confirmation: ОТСУТСТВУЕТ** — пока только X handle

## Что не подтверждено

- Independent secondary source (governance forum, DeFiLlama data, docs release notes)
- Реальный TVL breakdown — сколько из $30M это new money vs migration с V3
- Liquidity depth на V4 pools — можно ли realistically выйти с размером?
- Security audits V4 — прошли ли, кто аудитор?

## Значение для route decisions

- Route sheet: `Aave` tier=critical, action=готовить вход → не переходит к `READY_TO_PROBE` без independent confirmation (Фаза D.2 gates)
- Ждём: governance post ИЛИ DeFiLlama TVL подтверждающий цифру
- Блокер: нет cross-family confirmation

## Cross-refs

- [[protocols/aave]]
- [[assets/aave]]
- [[concepts/governance]]
