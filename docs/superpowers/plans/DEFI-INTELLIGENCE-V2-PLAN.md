# DeFi Intelligence Layer (v2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform defi-ops from "news cards" to "alpha signal-to-action pipeline" with cross-signal fusion, risk-adjusted sizing, and pre-filled trade briefs.

**Architecture:** Add 3 new modules (yield scanner, macro tracker, portfolio tracker) + upgrade 3 existing (wallets, decide, deliver). Keep total ≤9 source modules.

**Tech Stack:** Python 3.14 stdlib-first, SQLite, Telegram Bot API, DeFiLlama, Arkham, Etherscan.

---

## Task 1: Yield Anomaly Scanner

**Files:**
- Create: `src/yield_scanner.py`
- Test: `tests/test_yield_scanner.py`

- [ ] **Step 1: Write the failing test**
```python
def test_detect_yield_anomaly():
    # Mock DeFiLlama yields data
    pools = [
        {"pool": "aave-v3-usdc", "apy": 12.5, "tvlUsd": 50000000},
        {"pool": "aave-v3-usdc", "apy": 4.2, "tvlUsd": 48000000},  # historical
    ]
    result = detect_yield_anomaly(pools)
    assert result == [{"pool": "aave-v3-usdc", "apy_delta": 8.3, "z_score": 3.1}]
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_yield_scanner.py::test_detect_yield_anomaly -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**
```python
def detect_yield_anomaly(pools: list[dict], history: list[dict]) -> list[dict]:
    """Detect pools where APY deviates >2σ from 7d average."""
    ...
```

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_yield_scanner.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add tests/test_yield_scanner.py src/yield_scanner.py
git commit -m "feat: yield anomaly scanner (Task 1)"
```

---

## Task 2: Cross-Signal Fusion Engine

**Files:**
- Modify: `src/classify.py`
- Modify: `src/decide.py`
- Test: `tests/test_fusion.py`

- [ ] **Step 1: Add `fuse_signals()` to classify.py**
For each cluster, check if 2+ independent families agree:
- `onchain_whales` + `governance` + `yield` = HIGH conviction
- `social` + `governance` = MEDIUM
- Single family = LOW (filtered out)

- [ ] **Step 2: Update decide.py to use fusion score**
Cards only generated for clusters with `fusion_score >= 2`.

- [ ] **Step 3: Tests**
```python
def test_fusion_high():
    cluster = {"aspects": ["onchain_whales", "governance", "yield"]}
    assert fusion_score(cluster) == 3
```

- [ ] **Step 4: Commit**
```bash
git add src/classify.py src/decide.py tests/test_fusion.py
git commit -m "feat: cross-signal fusion engine (Task 2)"
```

---

## Task 3: Risk-Adjusted Sizing (Kelly Criterion)

**Files:**
- Create: `src/sizing.py`
- Test: `tests/test_sizing.py`

- [ ] **Step 1: Implement Kelly fraction**
```python
def kelly_size(p: float, b: float, bankroll: float = 100000) -> float:
    """p = win probability, b = avg win/avg loss ratio."""
    kelly = (p * b - (1 - p)) / b
    return min(kelly * 0.25, 0.05) * bankroll  # Quarter-Kelly, max 5%
```

- [ ] **Step 2: Integrate into decide.py**
Add `size_usd` and `max_loss` to card dict.

- [ ] **Step 3: Tests**
Test edge cases: p=0.55, b=2.5 → reasonable size. p=0.45 → 0 (no trade).

- [ ] **Step 4: Commit**
```bash
git add src/sizing.py src/decide.py tests/test_sizing.py
git commit -m "feat: Kelly criterion sizing (Task 3)"
```

---

## Task 4: Portfolio Tracker

**Files:**
- Create: `src/portfolio.py`
- Create: `config/portfolio.yaml`
- Test: `tests/test_portfolio.py`

- [ ] **Step 1: Schema**
```yaml
positions:
  - token: PT-sUSDe
    protocol: pendle
    entry_price: 1.025
    size_usd: 3000
    opened_at: 2026-04-21
```

- [ ] **Step 2: PnL tracking**
```python
def position_pnl(position: dict, current_price: float) -> dict:
    return {"unrealized_pnl": ..., "roi_pct": ...}
```

- [ ] **Step 3: Rebalancing suggestions**
If one position > 15% of portfolio → suggest trim.

- [ ] **Step 4: Commit**
```bash
git add src/portfolio.py config/portfolio.yaml tests/test_portfolio.py
git commit -m "feat: portfolio tracker with PnL (Task 4)"
```

---

## Task 5: Upgrade Decision Card (v2 format)

**Files:**
- Modify: `src/decide.py`
- Modify: `src/deliver.py`
- Test: `tests/test_decide.py`

- [ ] **Step 1: New card format**
Include:
- Conviction level (HIGH/MEDIUM/LOW)
- Signal fusion breakdown
- Trade parameters (entry, stop, target, size)
- Risk metrics (max loss, liquidity, contradictions)
- Expiry

- [ ] **Step 2: Update deliver.py**
Use `topic_decisions_id = 203` for HIGH, `topic_alerts_id = 206` for MEDIUM/LOW.

- [ ] **Step 3: Commit**
```bash
git add src/decide.py src/deliver.py tests/test_decide.py
git commit -m "feat: decision card v2 with trade params (Task 5)"
```

---

## Task 6: Macro Regime Tracker

**Files:**
- Create: `src/macro.py`
- Test: `tests/test_macro.py`

- [ ] **Step 1: Fetch key metrics**
- Funding rates (Hyperliquid API)
- BTC.D (DeFiLlama or CoinGecko)
- DXY proxy (if available)

- [ ] **Step 2: Regime classification**
```python
def current_regime() -> str:
    # "risk_on", "risk_off", "neutral"
    ...
```

- [ ] **Step 3: Gate trades**
If `risk_off` → reduce size by 50%, increase stop tightness.

- [ ] **Step 4: Commit**
```bash
git add src/macro.py tests/test_macro.py
git commit -m "feat: macro regime tracker (Task 6)"
```

---

## Task 7: Smart Money Pattern Detection (Upgrade)

**Files:**
- Modify: `src/wallets.py`
- Test: `tests/test_wallets.py`

- [ ] **Step 1: Detect accumulation pattern**
3+ inflows to same token within 24h from `smart_money` group.

- [ ] **Step 2: Detect drain pattern**
3+ outflows from same protocol within 24h.

- [ ] **Step 3: Pre-announcement positioning**
Smart money moves 6-48h before governance proposal deadline.

- [ ] **Step 4: Commit**
```bash
git add src/wallets.py tests/test_wallets.py
git commit -m "feat: smart money patterns (Task 7)"
```

---

## Task 8: End-to-End Integration & Launch

**Files:**
- Modify: `src/cli.py`
- Modify: `PLAN.md`

- [ ] **Step 1: Wire all modules in cli.py**
```
ingest → classify (fusion) → wallets (patterns) → yield_scanner → macro → decide (sizing) → deliver
```

- [ ] **Step 2: Run full pipeline dry-run**
```bash
.venv/bin/python -m src.cli run --only=decide
```

- [ ] **Step 3: Send first v2 card to Telegram**
```bash
.venv/bin/python -m src.cli run --only=decide --send
```

- [ ] **Step 4: Update PLAN.md with new goal**
Replace old Sprint 1-5 with new architecture.

- [ ] **Step 5: Final commit**
```bash
git add -A
git commit -m "feat: DeFi Intelligence Layer v2 — alpha signal-to-action pipeline"
```

---

## Execution Order & Dependencies

```
Task 1 (yield) ──┐
Task 2 (fusion) ─┼→ Task 5 (cards v2)
Task 3 (sizing) ─┘
Task 4 (portfolio) ──→ Task 8 (integration)
Task 6 (macro) ──────→ Task 8
Task 7 (wallets) ────→ Task 8
```

**Estimated timeline:** 7-10 engineering days (matching original 10-day budget).
