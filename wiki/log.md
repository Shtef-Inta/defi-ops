# Wiki Log

Append-only хронология ingest/query/lint действий над wiki.
Формат: `## [YYYY-MM-DD] action | Title`. Не редактировать прошлые записи.

---

> **Archive disclaimer:** Записи ниже от 2026-04-20 перенесены из Research-v2 wiki при миграции в defi-ops. Они описывают состояние Research-v2 на момент аудита. Research-v2 и openclaw TS pipeline сейчас frozen archive.

## [2026-04-20] init | Wiki bootstrap per Karpathy method
- Создана структура `wiki/{protocols,assets,concepts,wallets,signals,events}/`
- Создан `index.md` (каталог)
- Создан `log.md` (этот файл)
- Правила maintenance закреплены в `index.md` и в `.claude/rules/wiki-method.md`
- Ingest начнётся с первой реальной страницы при следующем сигнале

## [2026-04-20] audit | Full machine scan — проекты, cron jobs, дубликаты
- Запустил general-purpose agent для scan всех проектов на `/Users/shtef/`
- Отчёт: [[machine-audit-2026-04-20]]
- Главное: **TS openclaw pipeline активен параллельно** (6 cron jobs, Postgres, gateway PID 19644), дублирует назначение Research-v2. Оба целятся в Telegram group `-1003981168546`. Нужно решение Хозяина.
- Telegram bot token доступен в `~/.openclaw/openclaw.json` (plaintext, chmod 600)
- Research-v2 имеет uncommitted изменения — Sprint 1/2/2.5 работы не защищены git

## [2026-04-20] infra | Переезд Research-v2 из Documents/ → ~/Research-v2/
- Причина: macOS TCC блокирует launchd в `/Users/shtef/Documents/`
- `/Users/shtef/Documents/Research-v2` теперь symlink → `/Users/shtef/Research-v2/` (backward compat)
- Обновлены absolute paths: `~/.claude/CLAUDE.md`, `~/Library/LaunchAgents/com.research-v2.collect.plist`, `cron_collect.sh`, `.claude/settings.json`, `PHASE_4_PLAN.md`, `.claude/rules/wiki-method.md`
- `.venv` пересоздания не требовалось — shebangs через symlink валидны
- LaunchAgent `com.research-v2.collect` загружен с новым plist, первый автозапуск через 15 мин

## [2026-04-20] ingest | Live parsers активированы (X/YouTube/RSS/Wallets)
- `fetch_twitter_syndication.py` — `syndication.twitter.com` endpoint без логина. 31 handle (18 работают из 20 core + 11 новых в `defi_core`/`research`). **1239+ свежих tweets за первый прогон**
- `fetch_youtube_feeds.py` — YouTube RSS по channel_id (resolve через HTML, кэш в `state/youtube-channel-ids.json`). 4/6 каналов работают: aavelabs/ethenalabs/bankless/uniswap. 41+ videos
- `fetch_rss_feeds.py` (+fixes) — 4 enabled RSS sources, 120+ items
- `fetch_wallet_observations.py` — 3 watched (vitalik.eth, Binance 8, Ronin exploit). Etherscan v2 + Arkham labels (вложенный chain-keyed ответ). 180 tx/прогон, ~60 с Arkham entity enrichment
- `normalize_wallet_flows.py` (C2.1) — нормализует raw/wallets → state/wallet-flows.jsonl. **Classification по tx_type:** transfer_between_wallets, transfer_from/to_cex, risk_interaction (обнаружен cluster Ronin ↔ Euler Exploiter), swap_on_dex, stablecoin_transfer
- `generate_executive_digest.py` — per-протокольный срез: сигналы/кластеры/confirmations/risk blocks/противоречия/on-chain touchpoints. Output: `digests/YYYY-MM-DD-executive-digest.{md,json}`
- Автомат: `cron_collect.sh` → 7 шагов → LaunchAgent `com.research-v2.collect` каждые 900 сек. macOS notification при завершении.

## [2026-04-20] config | Handle updates по facts-on-ground
- `morpho_labs → morpho` (Morpho Labs переехал, Playwright verified), `ethena_labs → ethena`, `kairosres → kairos_res`, `optimismFND → Optimism`
- Новые handles в `defi_core`: HyperliquidX, 0xfluid, InstaDApp, sparkdotfi, SkyEcosystem, eigen_da, JupiterExchange, GMX_IO, dydx, CurveFinance, BalancerLabs
- Новый канал в `youtube_sources.yaml`: @morpho
- Embed-disabled профили: 0 (все подверждённые верной записи)

## [2026-04-20] ingest | Aave, Uniswap, Ethena, PeckShield captures
- Источник: `raw/x/twitter-browser-observed-aave-uniswap-ethena-peckshield-atlas-capture-*.json`
- Захват: 2026-04-17 через ChatGPT Atlas
- Хэндлы: aave, uniswap, ethena, kairos_res, krakenfx, peckshieldalert
- Страницы созданы: [[protocols/aave]], [[protocols/uniswap]], [[protocols/ethena]], [[concepts/risk-overlay-peckshield]], [[events/2026-04-aave-v4-deposits]], [[events/2026-04-ethena-pt-listings]]

## [2026-04-20] infra | Playwright MCP подключён (системный Chrome, headless)
- Установлен `@playwright/mcp@latest` user-scope в `~/.claude.json`
- Использует системный Google Chrome (Chromium download заблокирован TLS-прокси)
- `claude mcp list` показывает ✓ Connected
- Tools `mcp__playwright__*` появятся в Claude Code после рестарта сессии
- Правила в `.claude/rules/mcp-playwright.md`
- Решает: JS-heavy сайты (DeFiLlama dashboard, Dune, Token Terminal), governance forums без RSS
- НЕ решает: закрытые TG (telethon), простой RSS (urllib), известные API (urllib)
- Безопасность: только публичные read-only по умолчанию, никаких credentials в формы, никаких onchain signing

## [2026-04-20] insight | Calibration про возможности (Хозяин уточнил)
- Модель: Opus 4.7 / 1M context (статус-строка показывает; system prompt ошибочный)
- НЕТ browser/computer use. Парсинга X/YouTube как такового тоже нет — только триангуляция через WebSearch + WebFetch вторичных источников
- Что работает: WebSearch (популярный контент), urllib HTTP (публичные RSS), Atlas-захваты от Хозяина
- Что НЕ работает: уникальный визуальный контент без обсуждений в индексе, x.com напрямую (402), youtu.be напрямую
- Зафиксировано в `.claude/rules/safety.md` секция "Честность про возможности"
- Если будущая сессия не увидит этой записи — может снова обещать "распарсю Twitter" → повторит ошибку

## [2026-04-20] sprint-1 | B.1+A.6+A.4+B.2 завершены
- **B.1** schema migration: добавлены `source_family`, `asset_symbols`, `category` колонки. 10 старых строк backfilled (official=7, research=1, social_community=1, risk_overlay=1).
- **A.6** handles.yaml расширен: +risk_overlay (peckshieldalert, peckshield, SlowMist_Team), +analytics (tokenterminal, defillama, dune), +kairosres в research, +optimismFND в infra. Таксономия source_family задокументирована inline.
- **A.4** RSS fetcher (`fetch_rss_feeds.py`) запущен на 5 источниках. 4 успешных: The Defiant, Aave Governance, Uniswap Governance, Compound Governance. Bankless 404 — отключён. Стек: certifi для macOS Python 3.14 SSL.
- **B.2** universal import runner (`import_all_sources.py`) — full pipeline за один вызов: fetch → import x/web/telegram → enrich → triage → dedupe → migrate. Прогнан без --skip-fetch на реальных данных.
- Total signals в SQLite: 130 (10 X + 120 RSS). Категории: launch=47, governance=37, risk=13, monitoring=12, integration=9, yield=3.
- Route sheets выросли с 3 до **105**: critical=59, important=1, normal=45. Действия: избегать=11, готовить вход=20, ждать=55, наблюдать=19.

## [2026-04-20] infra | Telegram ingest setup готов, ждём credentials
- Скрипт `fetch_telegram_channels.py` написан (telethon, native Python, без Docker)
- Template `.env.template` + рабочий `telegram_sources.yaml` (все enabled=false)
- Skill сохранён в `~/.claude/skills/telegram-ingest/SKILL.md` для будущих проектов
- Активация после: Хозяин получит api_id/hash на my.telegram.org → `.env` → SMS auth → enable channels

## [2026-04-20] policy | Credentials unblocked (read-only APIs)
- Хозяин снял блокировку на API credentials
- Разрешено: Telegram MCP, Etherscan, Arkham, DeFiLlama, Helius, Anthropic (read-only)
- Остаётся запрещено: trading, transfers, signing, onchain writes, private keys
- Обновлено: [[../.claude/rules/safety]], [[hot]]

## [2026-04-20] plan | Telegram MCP pattern wired into A.3
- Источник: youtu.be/DzBdeHauw6c + github.com/0x4graham/telegram-mcp
- Upgrade пути A.3 в PHASE_4_PLAN: вместо ручного bridge — Docker Telethon user-session + MCP
- Создано: [[../.claude/rules/mcp-telegram]] с правилами использования
- Создан template: `research/config/telegram_sources.yaml.template`
- Блокер: нужны credentials (api_id/hash, bot token) — ждём Хозяина

## [2026-04-20] infra | Hot cache + SessionStart/Stop hooks
- Добавлен [[hot]] — recent-context cache для continuity между сессиями
- Добавлен [[overview]] — executive summary с pipeline-диаграммой и watchlist
- `.claude/settings.json` → SessionStart hook инжектит `hot.md` в context при старте
- `.claude/settings.json` → Stop hook напоминает обновить `hot.md` в конце сессии
- CLAUDE.md project → добавлен порядок чтения (hot → index → overview → page)
- Источник метода: https://github.com/AgriciDaniel/claude-obsidian + https://youtu.be/eg5cWYK5Q04

## [2026-04-20] sprint-2 | B.3+C.1+C.3+A.2 завершены
- **B.3** cross_source_link.py: кластеризация по `(asset, category, ±2h)` → 50 кластеров из 109 park-сигналов. 23 multi-member. Output `digests/<date>-clusters.json`.
- **C.1** score_confirmation.py: грейды single/dual/cross_family/repeated_promotion. Результат: 27 single, 22 dual, **1 cross_family_confirmed** (AAVE launch — Aave Labs official + The Rollup research через YouTube bridge).
- **C.3** apply_risk_overlay.py: блокирующий gate по risk keywords на watched protocols. Требует ≥2 voices ИЛИ явный risk_overlay source. Gate устойчив к таксономии category (пере-enrich меняет 'risk' → 'risk/watch' → всё равно ловит по keywords). 1 кластер заблокирован (ETH depeg/hack/paused из Defiant + Aave governance).
- **A.2** import_youtube_observed.py + config/youtube_sources.yaml: bridge из `New project/out/youtube-*.json`. Поддерживает два формата — ask-chat-observed (полные видео) и candidates (search results). 4 bucket'а в `raw/youtube/`, интегрировано в import_all_sources.
- **Integration**: generate_route_sheet теперь читает clusters.json, приклеивает confirmation grade и riskOverlay к каждому маршруту. Блокированные routes получают actionNow='избегать'. 3 route sheet получили cross_family_confirmed, 2 blocked_by_risk.
- Пайплайн `import_all_sources.py` теперь включает cross_source_link → score_confirmation → apply_risk_overlay автоматически.

## [2026-04-20] ingest | YouTube → AAVE cross-family confirmation
- [[protocols/aave]] — V4 launch теперь имеет **cross_family_confirmed** cluster: official (Aave Labs YouTube "Aave V4 deep dive") + research (The Rollup interview).
- Это первый multi-family кластер в системе — раньше всё было single_source X посты или dual_source внутри docs.
- Следующий gap: нет independent governance confirmation (Aave governance форум парсится, но посты не пересекаются с V4 launch по времени — pub_date vs fetch_time mismatch).

## [2026-04-20] skill | obra/superpowers установлен (user-scope, v5.0.7)
- Источник: https://t.me/prog_ai/1005 + https://t.me/prog_ai/1049, маркетплейс `claude-plugins-official`
- Команда: `claude plugin install superpowers` → ✔ enabled user-scope
- 14 skills: using-superpowers, brainstorming, writing-plans, executing-plans, subagent-driven-development, dispatching-parallel-agents, test-driven-development, systematic-debugging, requesting-code-review, receiving-code-review, verification-before-completion, writing-skills, finishing-a-development-branch, using-git-worktrees
- Активируются после рестарта Claude Code (skills tool не подгружает их в live сессии)
- Правила интеграции в нашем workflow: [[../.claude/rules/superpowers-integration]]
- Жёсткие guardrails: `PHASE_4_PLAN.md` остаётся single source of truth (не переписывать в /docs/superpowers/plans!). `phase4-discipline` перебивает "1% MUST use" философию — отказываем если brainstorming хочет новый scoring layer.

## [2026-04-20] fix | RSS pub_date корректно пропагируется в captured_at
- Баг: `import_generic_dir` брал `payload.capturedAt` (batch fetch time) для всех items, игнорируя `item.published_iso`.
- Следствие: все 120 RSS-сигналов имели одинаковый captured_at → ±2h окно ловило ложные кластеры.
- Исправление: `captured_at` теперь `item.published_iso > item.observedAt > payload.capturedAt`. Для уже импортированных дубликатов — UPDATE captured_at если подхватился новый pub_date.
- Результат после прогона: clusters 49 → 148 (большинство singleton, что правильно — разнесены по реальным датам). Dual_source 22 → 10 (реальные), cross_family_confirmed 1 → 1 (AAVE V4 launch, window=0.1h, 4 независимых voice: aavelabs, aave-labs, the-rollup, capture).
- Route sheets: cross_family_confirmed 3 → 4 (все AAVE V4). blocked_by_risk 2 → 0 (было артефактом batch-fetch, real incidents — single-voice, flagged но не blocked).

## [2026-04-21] migrate | Unified wiki migration to defi-ops
- Переписаны `index.md`, `hot.md`, `overview.md` под defi-ops taxonomy.
- Обновлены `protocols/aave.md`, `protocols/ethena.md`, `protocols/uniswap.md`, `events/*.md`, `concepts/risk-overlay-peckshield.md`.
- Добавлен archive disclaimer в `log.md` и `machine-audit-2026-04-20.md`.
- Создан `docs/wiki-migration-inventory.md`.
- Research-v2 и openclaw wiki помечены как frozen reference.
