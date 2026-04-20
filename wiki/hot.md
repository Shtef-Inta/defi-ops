---
type: cache
last_updated: 2026-04-20T17:40Z
purpose: Recent context cache loaded by SessionStart hook
---

# Hot Cache

Это первое, что я читаю при старте каждой новой сессии. Если здесь недостаточно — открываю `wiki/index.md`.

## Личность и условия

- Хозяин — пользователь, обращение `Хозяин`, русский язык
- Модель: **Opus 4.7 / 1M context** (статус-строка в Claude Code это подтверждает; system prompt может ошибочно показывать другую модель — игнорировать)
- Permission mode: **bypassPermissions / acceptEdits** — без confirmations
- Credentials: **read-only API разрешены** (Telegram, Etherscan, Arkham, DeFiLlama, Helius, Anthropic). Финансовые операции запрещены. См. `.claude/rules/safety.md`
- Browser: **есть Playwright MCP с системным Chrome** (зарегистрирован 2026-04-20 user-scope). Tools `mcp__playwright__*` доступны после рестарта Claude Code. Правила использования: `.claude/rules/mcp-playwright.md`. Token-economy строгие — не делать `snapshot` без необходимости.
- Computer use: нет (только browser через playwright)
- **Superpowers plugin**: установлен user-scope 2026-04-20 (`superpowers@claude-plugins-official v5.0.7`). 14 skills: using-superpowers/brainstorming/writing-plans/executing-plans/subagent-driven-development/dispatching-parallel-agents/test-driven-development/systematic-debugging/requesting-code-review/receiving-code-review/verification-before-completion/writing-skills/finishing-a-development-branch/using-git-worktrees. Активны после рестарта CC. Правила интеграции: `.claude/rules/superpowers-integration.md` (phase4-discipline перебивает). `PHASE_4_PLAN.md` остаётся единственным roadmap'ом — не дублировать в `/docs/superpowers/plans/`.

## Где мы сейчас (последняя активная работа)

- **Phase 4 — Route Execution** — in progress
- **Sprint 0 (фундамент скилла) — DONE**:
  - CLAUDE.md hierarchical context (Level 0 + Level 1)
  - `.claude/rules/{safety, phase4-discipline, output-style, wiki-method}.md`
  - Wiki layer per Karpathy method (raw/wiki/schema)
  - SessionStart/Stop hooks для continuity
- **Sprint 1 (фундамент проекта) — DONE 2026-04-20**:
  - B.1 schema migration ✅ (3 колонки + 10 backfilled)
  - A.6 handles.yaml ✅ (+risk_overlay, +analytics семьи)
  - A.4 RSS fetcher ✅ (4 источника, 120 items)
  - B.2 universal import runner ✅ (130 signals, 105 route sheets)
- **Sprint 2 (cross-source) — DONE 2026-04-20**:
  - B.3 cross_source_link.py ✅ (50 clusters, 23 multi-member, 1 cross_family)
  - C.1 score_confirmation.py ✅ (27 single / 22 dual / 1 cross_family_confirmed)
  - C.3 apply_risk_overlay.py ✅ (1 cluster blocked — ETH depeg/hack/paused)
  - A.2 import_youtube_observed.py + youtube_sources.yaml ✅ (AAVE Labs + The Rollup ⇒ cross-family confirm для V4 launch)
  - Integration ✅: route_sheet теперь несёт confirmation grade + risk gate. 3 routes cross_family, 2 blocked_by_risk.
- **Sprint 2.5 (wallet intelligence) — IN PROGRESS**:
  - A.5 wallet fetcher ✅ (3 enabled: vitalik.eth, Binance 8, Ronin exploit; Etherscan+Arkham labels)
  - C2.1 normalize_wallet_flows.py ✅ (136+ records, tx_type классификация, Ronin↔Euler Exploiter risk_interaction обнаружен)
  - C2.2–C2.6 — остались
- **Live parsers активированы (2026-04-20 ~17Z)**:
  - `fetch_twitter_syndication.py` через syndication.twitter.com (18/20 handles + 11 новых defi_core: Hyperliquid/Fluid/InstaDApp/Spark/Sky/EigenLayer/Jupiter/GMX/dYdX/Curve/Balancer)
  - `fetch_youtube_feeds.py` через YouTube RSS + channel_id resolve (4/6 каналов: aavelabs/ethenalabs/bankless/uniswap)
  - `fetch_rss_feeds.py` live (4 sources)
  - `fetch_wallet_observations.py` live (3 watched wallets)
  - `cron_collect.sh` → LaunchAgent `com.research-v2.collect` каждые 900 сек + macOS notification в конце
- **Переезд проекта (2026-04-20 ~17Z)**: `/Users/shtef/Documents/Research-v2` → `/Users/shtef/Research-v2`. Причина — macOS TCC блокировал launchd в Documents. Старый путь оставлен symlink'ом для backward compat.
- **Машинный аудит (2026-04-20 ~17:40Z)**: [[machine-audit-2026-04-20]] — найдены **параллельные openclaw TS pipeline (6 cron jobs, Postgres, gateway)** и **Telegram bot token в `~/.openclaw/openclaw.json`**. Оба пайплайна целятся в Telegram group `-1003981168546`. Нужно решение Хозяина.

## Что уже работает

- Python pipeline (Phase 1-2): X + RSS + YouTube capture → SQLite → triage → defi-summary
- **Live парсеры**: Twitter/YouTube/RSS/Wallets через public endpoints без Atlas bridge (A.1-live, A.2-live, A.4, A.5)
- `fetch_twitter_syndication.py` — 31 handle, ~1200 tweets/прогон
- `fetch_youtube_feeds.py` — 6 каналов, ~40 videos/прогон
- `fetch_wallet_observations.py` + `normalize_wallet_flows.py` — Etherscan+Arkham enrichment; classification tx_type
- `import_all_sources.py` — полный pipeline за один вызов (ingest → enrich → triage → dedupe → migrate → cluster → score → risk-gate)
- Cross-source: `cross_source_link.py` + `score_confirmation.py` + `apply_risk_overlay.py` → `digests/<date>-clusters.json`
- `generate_route_sheet.py` — **858 маршрутов** (303 critical, 81 important) с cluster confirmation grade и risk overlay
- `generate_executive_digest.py` — per-протокольный срез (18 watched: Aave/Uniswap/Hyperliquid/Fluid/Ethena/Morpho/Pendle/Lido/Compound/Curve/Maker/Spark/EigenLayer/Gearbox/Balancer/GMX/dYdX/Jupiter)
- **1653 сигналов в БД** на момент аудита (social 487 · research 419 · official 291 · risk_overlay 201 · docs 130 · aggregator 125)
- Autorun: `cron_collect.sh` через LaunchAgent каждые 15 минут, macOS notification при завершении
- Wiki: 7+ страниц + machine-audit

## Активные кейсы в watchlist

- [[protocols/aave]] tier=critical — V4 deposits $30M, **cross_family_confirmed** (Aave Labs YouTube + The Rollup research). Нужен governance + TVL gate.
- [[protocols/ethena]] tier=important — PT caps на Aave/Plasma, ждать (нужен governance verification)
- [[protocols/uniswap]] tier=critical — CCA auctions context, наблюдать
- [[concepts/risk-overlay-peckshield]] — пока не attached к watched protocols

## Открытые блокеры

- DeFiLlama не подключён — нет независимого liquidity context
- Wallet observations не подключены — Sprint 2.5
- Telegram delivery не интегрирована — Sprint 4

## Жёсткие правила (не нарушать)

- Не строить новые scoring layers до доведения route execution → реальный Telegram → outcome
- **Financial граница**: запрещены trading, transfers, signing, onchain writes, использование private keys
- **Credentials разрешены** (с 2026-04-20): Telegram MCP, Etherscan, Arkham, DeFiLlama, Helius, Anthropic — всё read-only
- Credentials хранятся в `~/.claude/.mcp.json` или `./data/.env` с `chmod 600`, никогда в git
- Telegram OUTGOING (send) только с `--send --approve-send=approve-send`
- При новом сигнале — обновлять `wiki/` (ingest workflow в `.claude/rules/wiki-method.md`)

## Последнее изменение wiki

- `2026-04-20 17:40Z` — machine audit + live parsers + переезд проекта из Documents в home. См. [[machine-audit-2026-04-20]] + [[log]].
- Если эта строка старше 24 часов и были новые ingest — обновить hot.md обязательно

## Куда смотреть дальше

| Если задача про... | Открыть |
|--|--|
| Что делаем сейчас | `tasks/todo.md`, `obsidian/01_ACTIVE_CONTEXT.md` |
| Полный roadmap | `PHASE_4_PLAN.md` |
| Что мы знаем про конкретный protocol | `wiki/protocols/<name>.md` |
| Цели и запреты | `obsidian/projects/research/PROJECT_STATE.md` |
| Правила работы | `.claude/rules/*.md` |
