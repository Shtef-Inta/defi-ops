# defi-ops

Minimal DeFi research → Telegram decision pipeline for a $100k portfolio. Local-only, read-only ingest, manual execution.

## Quick start (after Sprint 0)

```bash
cd ~/defi-ops
python3.14 -m venv .venv
.venv/bin/pip install -r requirements.txt  # or via pyproject
cp .env.template .env && chmod 600 .env     # fill credentials
python -m src.cli run --only=ingest         # first ingest
python -m src.cli run                       # full dry cycle
python -m src.cli run --send --approve-send=approve-send  # real Telegram
```

## One-pipeline, one-db, one-bot

- 5 sources: X (syndication), YouTube (RSS), Web/Governance RSS, Telegram (user-session read), Wallets (Etherscan+Arkham)
- 1 SQLite at `state/ops.sqlite`
- ≤5 Telegram cards per day, 3 answers: BUY PROBE / WATCH / SKIP
- Outcome → source-reliability → voice-weighted confirmation for next cycle

## What it is NOT

- Not a trading bot. No signing, no onchain writes, no exchange APIs.
- Not a scoring playground. `decide.py` produces cards, not scores.
- Not a router. No entry/exit automation.

## Full plan

See `PLAN.md` for the 10-day sprint roadmap with task-level DoD.

## Status

- Sprint 0 in progress (scaffold + migration from Research-v2/openclaw)
- First real card target: Day 10
