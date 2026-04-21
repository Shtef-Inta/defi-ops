# defi-ops — DeFi Intelligence Layer (v2)

> **Goal:** Autonomous alpha-generation system for DeFi.  
> **Output:** 0-10 trade ideas per day with entry/exit/leverage parameters. Any conviction — from degen to high-probability.  
> **Risk tolerance:** Very high. Leverage, perps, options, asymmetric bets, directional speculation — all fair game.  
> **Hard constraint:** No onchain transactions without explicit `=ПОДПИСАТЬ` from operator. Everything else is fair game.

**Architecture:** Signal-to-action pipeline with cross-signal fusion, risk-adjusted sizing, and pre-filled trade briefs.

```
Raw feeds (Twitter oEmbed, TG, RSS, onchain, yield APIs, macro)
    ↓
Signal extraction (smart money, governance, yield, arbitrage, sentiment, macro)
    ↓
Cross-signal fusion (where 2+ independent sources agree)
    ↓
Risk-adjusted sizing (Kelly criterion, volatility regime, portfolio heat)
    ↓
Pre-filled trade brief (token, entry, exit, size, leverage, rationale)
    ↓
Operator approval (Telegram reply)
    ↓
Manual execution by operator
```

---

## Sprint Roadmap (v2)

### Phase 1: Alpha Extraction (Days 1-3)

- [ ] **Task 1** — Yield Anomaly Scanner (`src/yield_scanner.py`)
  - Detect APY deviations >2σ from 7d average via DeFiLlama
  - Flag new vaults, points farming opportunities
  - Tests: `tests/test_yield_scanner.py`

- [ ] **Task 2** — Cross-Signal Fusion Engine
  - Upgrade `src/classify.py` with `fuse_signals()`: 2+ families = HIGH
  - Add `speculative` tier (1 strong signal + high volatility)
  - Upgrade `src/decide.py` to filter by `fusion_score >= 1` (no hard cap)
  - Tests: `tests/test_fusion.py`

- [ ] **Task 3** — Risk-Adjusted Sizing (`src/sizing.py`)
  - Kelly criterion (full-Kelly for high conviction, half-Kelly for medium, quarter for speculative)
  - Portfolio heat map (total exposure by protocol/token)
  - Tests: `tests/test_sizing.py`

### Phase 2: Tracking & Patterns (Days 4-6)

- [ ] **Task 4** — Portfolio Tracker (`src/portfolio.py` + `config/portfolio.yaml`)
  - Position PnL, rebalancing suggestions, heat map
  - Tests: `tests/test_portfolio.py`

- [ ] **Task 5** — Macro Regime Tracker (`src/macro.py`)
  - Funding rates, BTC.D, regime classification (risk_on/off/neutral/degen)
  - Gate: reduce size 50% in risk_off, increase in degen
  - Tests: `tests/test_macro.py`

- [ ] **Task 6** — Smart Money Patterns (upgrade `src/wallets.py`)
  - Accumulation: 3+ inflows same token within 24h
  - Drain: 3+ outflows same protocol within 24h
  - Pre-announcement positioning: smart money moves 6-48h before gov deadline
  - MEV leak detection: sandwich victim patterns
  - Tests: `tests/test_wallets.py`

### Phase 3: Delivery & Integration (Days 7-10)

- [ ] **Task 7** — Decision Card v2 (upgrade `src/decide.py` + `src/deliver.py`)
  - Format: conviction (DEGEN/SPECULATIVE/MEDIUM/HIGH), signal fusion, trade params, leverage, liquidation price, risk metrics, expiry
  - Topic routing: DEGEN/SPECULATIVE → alerts/206, MEDIUM/HIGH → schema/203
  - Tests: `tests/test_decide.py`

- [ ] **Task 8** — End-to-End Integration
  - Wire all modules in `src/cli.py`
  - First live v2 card to Telegram
  - Update docs

---

## Source Modules (max 9, ≤400 lines each)

| # | Module | Purpose | Status |
|---|--------|---------|--------|
| 1 | `src/ingest.py` | Thin router (Twitter oEmbed, RSS, Wallets) | ✅ |
| 2 | `src/classify.py` | Event extraction + cross-signal fusion | 🔄 (Task 2) |
| 3 | `src/wallets.py` | Onchain normalize + pattern detection | 🔄 (Task 6) |
| 4 | `src/yield_scanner.py` | APY anomaly detection | ⬜ (Task 1) |
| 5 | `src/macro.py` | Regime tracking | ⬜ (Task 5) |
| 6 | `src/liquidity.py` | DeFiLlama TVL gate | ✅ |
| 7 | `src/sizing.py` | Kelly criterion + portfolio heat | ⬜ (Task 3) |
| 8 | `src/decide.py` | Trade brief builder | 🔄 (Task 7) |
| 9 | `src/deliver.py` | Telegram send + topic routing | 🔄 (Task 7) |

**Extra:** `src/portfolio.py` (counts as config/tooling, not core source)

---

## Success Metrics

| Metric | Target |
|---|---|
| Raw signals/day | 100-500 |
| Fused alpha ideas/day | 0-10 |
| Hit rate (profit > 0) | ≥45% |
| Avg win | +15% |
| Avg loss | -5% |
| Operator ignore rate | < 60% |

---

## What We Do NOT Build

- No automated execution (no bots signing txs) — pre-filled txs only
- No "hold forever" — every trade has expiry or trigger
- No fear of being wrong — we learn fast from losses
