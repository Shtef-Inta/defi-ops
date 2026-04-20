# Telegram Topics Schema

> **Source of truth** for `defi-ops` Telegram delivery layer.  
> Verified by live sends 2026-04-13 → 2026-04-21.

## Group

| Property | Value |
|---|---|
| Group ID | `-1003981168546` |
| Internal `t.me/c` ID | `3981168546` |
| Bot | `@OpenClawMacBook_ConductorBot` |
| Bot display name | `OpenClawMacBook` |
| Owner ID | `365840120` |

## Topics

| Topic | Purpose | Thread ID |
|---|---|---:|
| `twitter` | Twitter/X parser, recommendations from X | `199` |
| `youtube` | YouTube / Ask Chat source | `200` |
| `web` | Web/RSS sources | `201` |
| `telegram` | Telegram source/input | `202` |
| `schema` | **Main DeFi/operator/autopilot topic** | `203` |
| `document` | Documents | `204` |
| `media` | Media | `205` |
| `alerts` | Alerts | `206` |
| `storage` | Storage/archive | `207` |
| `signals` | Signals | `208` |
| `tests` | Tests | `209` |

## Verified Send Log

| Date | Topic | Thread ID | Message ID | Payload |
|---|---|---|---|---|
| 2026-04-13 | all topics | `199-209` | various | `проверка связи` |
| 2026-04-20 | `schema` | `203` | `1266` | pipeline test |
| 2026-04-20 | `schema` | `203` | various | first 4 decision cards |
| prior | `twitter` | `199` | `913` | Twitter recommendations |
| 2026-04-21 | `schema` | `203` | various | first 4 decision cards (live pipeline) |
| prior | `schema` | `203` | `1147` | DeFi operator cycle |

## Delivery Rules

- **Decision cards** → `schema / 203`
- **Risk/alerts** → `alerts / 206`
- **Raw signals digest** → `signals / 208`
- **Test messages** → `tests / 209`

## Hard Constraints (from previous bridge)

- No trades, transfers, swaps, signing, onchain actions, private keys, or arbitrary shell from Telegram.
- Read-only control commands only (`/status`, `/tail`, `/monitor`).
