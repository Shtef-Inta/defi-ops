# New Goal: DeFi Intelligence Layer (v2)

> **Target:** Become the autonomous alpha-generation system for a DeFi portfolio.  
> **Output:** 0-10 trade ideas per day with entry/exit parameters, delivered to Telegram. No cap on conviction levels — from speculative degen plays to high-probability arbitrage.  
> **Risk tolerance:** Very high. Leverage, perps, options, asymmetric bets, directional speculation — all fair game.  
> **Hard constraint:** No onchain transactions without explicit `=ПОДПИСАТЬ` from operator. Everything else is fair game.

## What We Build

Instead of "news aggregator → cards", we build a **signal-to-action pipeline**:

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

## Source Families & Their Alpha Type

| Family | Alpha Type | What We Extract |
|---|---|---|
| **onchain_whales** | Positioning alpha | Accumulation/drain patterns, pre-announcement positioning, MEV leaks |
| **governance** | Event alpha | Vote outcomes, parameter changes, treasury moves, delegate shifts |
| **yield** | Carry alpha | APY anomalies, impermanent loss vs reward, new vaults, points farming |
| **social** | Sentiment alpha | Directional bias, FUD/FOMO intensity, influencer consensus, viral narratives |
| **macro** | Regime alpha | Funding rates, DXY correlation, BTC.D, ETH/BTC, VIX proxy, rate expectations |
| **arbitrage** | Structural alpha | Cross-DEX price gaps, CEX-DEX basis, funding rate arbitrage, cross-chain bridges |

## Decision Card Format (v2)

```
🎯 [DEGEN/SPECULATIVE/MEDIUM/HIGH] CONVICTION — [PROTOCOL] [STRATEGY]

Signal Fusion:
  • Onchain: 3 whales accumulated $2.1M PT-sUSDe (Arkham)
  • Governance: Ethena proposal #42 to raise caps (Snapshot, ends 6h)
  • Yield: 34% APY on Pendle PT-sUSDe (DeFiLlama)
  • Social: @EvanLuthra + 2 researchers bullish (Twitter)
  • Macro: funding positive, risk_on regime

Trade:
  • Action: BUY PROBE / LONG PERP / YIELD FARM / ARBITRAGE
  • Token: PT-sUSDe (Pendle)
  • Entry: $1.023 — $1.028
  • Stop: $0.995 (-2.7%) or -5% on perp
  • Target: $1.065 (+4.1%) or +15% on perp
  • Leverage: 1x spot / 3x perp / 10x degen
  • Size: $3,000 (3% of portfolio) or $300 (0.3% degen)
  • Rationale: 5-signal convergence, 6h governance catalyst, positive funding

Risk:
  • Max loss: $81 (spot) / $450 (perp 3x)
  • Liquidity: $45M TVL (verified)
  • Contradiction: None
  • Wallet divergence: None
  • Liquidation price (if perp): $0.341

Expiry: 48h or governance result or stop/target hit
```

## Success Metrics

| Metric | Target |
|---|---|
| Signals/day | 100-500 raw → 0-10 fused |
| Hit rate (profit > 0) | ≥45% (diversified portfolio) |
| Avg return per winning trade | +15% |
| Avg loss per losing trade | -5% |
| Sharpe (monthly) | > 1.0 |
| Operator ignore rate | < 60% (we show more, he picks) |

## What We Do NOT Build

- No automated execution (no bots signing txs) — pre-filled txs only
- No "hold forever" — every trade has expiry or trigger
- No fear of being wrong — we learn fast from losses
