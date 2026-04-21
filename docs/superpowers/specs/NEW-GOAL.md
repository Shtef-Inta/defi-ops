# New Goal: DeFi Intelligence Layer (v2)

> **Target:** Become the autonomous alpha-generation system for a $100k DeFi portfolio.  
> **Output:** 1-3 high-conviction trade ideas per day with entry/exit parameters, delivered to Telegram.  
> **Risk tolerance:** High. Smart leverage, aggressive sizing on high-probability setups.  
> **Hard constraint:** No onchain transactions without explicit `=ПОДПИСАТЬ` from operator.

## What We Build

Instead of "news aggregator → cards", we build a **signal-to-action pipeline**:

```
Raw feeds (Twitter, TG, RSS, onchain)
    ↓
Signal extraction (smart money, governance, yield, arbitrage)
    ↓
Cross-signal fusion (where 2+ independent sources agree)
    ↓
Risk-adjusted sizing (Kelly criterion, volatility regime)
    ↓
Pre-filled trade brief (token, entry, exit, size, rationale)
    ↓
Operator approval (Telegram reply)
    ↓
Manual execution by operator
```

## Source Families & Their Alpha Type

| Family | Alpha Type | What We Extract |
|---|---|---|
| **onchain_whales** | Positioning alpha | Accumulation/drain patterns, pre-announcement positioning |
| **governance** | Event alpha | Vote outcomes, parameter changes, treasury moves |
| **yield** | Carry alpha | APY anomalies, impermanent loss vs reward, new vaults |
| **social** | Sentiment alpha | Directional bias, FUD/FOMO intensity, influencer consensus |
| **macro** | Regime alpha | Funding rates, DXY correlation, BTC.D, ETH/BTC ratio |

## Decision Card Format (v2)

```
🎯 [HIGH/MEDIUM/LOW] CONVICTION — [PROTOCOL] [STRATEGY]

Signal Fusion:
  • Onchain: 3 whales accumulated $2.1M PT-sUSDe (Arkham)
  • Governance: Ethena proposal #42 to raise caps (Snapshot, ends 6h)
  • Yield: 34% APY on Pendle PT-sUSDe (DeFiLlama)
  • Social: @EvanLuthra + 2 researchers bullish (Twitter)

Trade:
  • Action: BUY PROBE
  • Token: PT-sUSDe (Pendle)
  • Entry: $1.023 — $1.028
  • Stop: $0.995 (-2.7%)
  • Target: $1.065 (+4.1%)
  • Size: $3,000 (3% of portfolio)
  • Rationale: 4-signal convergence, 6h governance catalyst, positive funding

Risk:
  • Max loss: $81
  • Liquidity: $45M TVL (verified)
  • Contradiction: None
  • Wallet divergence: None

Expiry: 48h or governance result
```

## Success Metrics

| Metric | Target |
|---|---|
| Signals/day | 50-100 raw → 3-5 fused |
| Hit rate (profit > 0) | ≥55% |
| Avg return per winning trade | +8% |
| Avg loss per losing trade | -3% |
| Sharpe (monthly) | > 1.5 |
| Operator ignore rate | < 40% |

## What We Do NOT Build

- No automated execution (no bots signing txs)
- No leverage above 3x recommendation
- No perp trading without explicit operator consent
- No "hold forever" — every trade has expiry
