# defi-ops — DeFi Intelligence Layer (v2)

> **Goal:** Autonomous alpha-generation system for a $100k DeFi portfolio.  
> **Output:** 1-3 high-conviction trade ideas per day with entry/exit parameters.  
> **Risk tolerance:** High. Smart leverage, aggressive sizing on high-probability setups.  
> **Hard constraint:** No onchain transactions without explicit `=ПОДПИСАТЬ` from operator.

**New architecture:** Signal-to-action pipeline with cross-signal fusion, risk-adjusted sizing, and pre-filled trade briefs.

```
Raw feeds (Twitter oEmbed, TG, RSS, onchain, yield APIs)
    ↓
Signal extraction (smart money, governance, yield, macro, social)
    ↓
Cross-signal fusion (where 2+ independent sources agree)
    ↓
Risk-adjusted sizing (Kelly criterion, macro regime)
    ↓
Pre-filled trade brief (token, entry, exit, size, rationale)
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
  - Tests: `tests/test_yield_scanner.py`

- [ ] **Task 2** — Cross-Signal Fusion Engine
  - Upgrade `src/classify.py` with `fuse_signals()`: 2+ families = HIGH
  - Upgrade `src/decide.py` to filter by `fusion_score >= 2`
  - Tests: `tests/test_fusion.py`

- [ ] **Task 3** — Risk-Adjusted Sizing (`src/sizing.py`)
  - Kelly criterion (quarter-Kelly, max 5% of portfolio)
  - Integrate into decision cards
  - Tests: `tests/test_sizing.py`

### Phase 2: Tracking & Patterns (Days 4-6)

- [ ] **Task 4** — Portfolio Tracker (`src/portfolio.py` + `config/portfolio.yaml`)
  - Position PnL, rebalancing suggestions
  - Tests: `tests/test_portfolio.py`

- [ ] **Task 5** — Macro Regime Tracker (`src/macro.py`)
  - Funding rates, BTC.D, regime classification (risk_on/off/neutral)
  - Gate: reduce size 50% in risk_off
  - Tests: `tests/test_macro.py`

- [ ] **Task 6** — Smart Money Patterns (upgrade `src/wallets.py`)
  - Accumulation: 3+ inflows same token within 24h
  - Drain: 3+ outflows same protocol within 24h
  - Pre-announcement positioning: smart money moves 6-48h before gov deadline
  - Tests: `tests/test_wallets.py`

### Phase 3: Delivery & Integration (Days 7-10)

- [ ] **Task 7** — Decision Card v2 (upgrade `src/decide.py` + `src/deliver.py`)
  - Format: conviction, signal fusion, trade params, risk metrics, expiry
  - Topic routing: HIGH → schema/203, MEDIUM/LOW → alerts/206
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
| 7 | `src/sizing.py` | Kelly criterion position sizing | ⬜ (Task 3) |
| 8 | `src/decide.py` | Trade brief builder | 🔄 (Task 7) |
| 9 | `src/deliver.py` | Telegram send + topic routing | 🔄 (Task 7) |

**Extra:** `src/portfolio.py` (counts as config/tooling, not core source)

---

## Success Metrics

| Metric | Target |
|---|---|
| Raw signals/day | 50-100 |
| Fused alpha ideas/day | 1-3 |
| Hit rate (profit > 0) | ≥55% |
| Avg win | +8% |
| Avg loss | -3% |
| Operator ignore rate | < 40% |

---

## What We Do NOT Build

- No automated execution (no bot signing txs)
- No leverage > 3x recommendation
- No "hold forever" — every trade has expiry
- No perp trading without explicit operator consent
