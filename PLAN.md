# defi-ops — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** За 10 инженерных дней собрать чистую минимальную систему, которая ежедневно отправляет Хозяину 3–5 финансовых карточек в Telegram по DeFi-рынку ($100k капитал, ручное исполнение), учится на исходах, и не превращается в "ещё 149 модулей".

**Architecture:** Один Python 3 pipeline, одна SQLite база, один Telegram-бот, одна точка входа `python -m src.cli run`. Девять исходных модулей вместо 53 (Research-v2) и 279 (openclaw TS). Выводы проходят через жёсткие гейты (liquidity, risk, contradiction) ПЕРЕД отправкой — в Telegram попадает только то, на что Хозяин действительно должен реагировать.

**Tech Stack:**
- Python 3.14, stdlib-first (`urllib`, `sqlite3`, `re`, `xml.etree`)
- Сторонние минимально: `certifi`, `Telethon` (read Telegram user session), `tenacity` (retry), `pytest` (тесты)
- SQLite (`state/ops.sqlite`) — единое хранилище
- `pytest` начиная со Sprint 1 — TDD обязательно для `classify` и `decide` модулей
- Markdown digests + JSON side-cars
- macOS launchd для автозапуска (в home, вне Documents/TCC)

**Target location:** `/Users/shtef/defi-ops/`

---

## Новая логика — **чем это принципиально отличается** от Research-v2 / openclaw

1. **Event-unit clustering, не (asset, category, window).**
   Кластер = `(protocol, event_key, 48h_window)`, где `event_key` извлекается regex/keywords: `launch`, `freeze`, `depeg`, `integration-<X>`, `tvl-cross-$N`, `gov-proposal-<id>`. Один event имеет несколько **aspects** (announcement / tvl / risk / onchain). Противоречия видны **внутри одного event-unit**, а не между параллельными кластерами.

2. **Voice-weighted confirmation, не count-based.**
   `weight = Σ (source.reliability × recency_decay)`. `reliability` стартует с 1.0, изменяется по outcomes Хозяина (+0.1 если → profit, -0.1 если → loss/false). `recency_decay = 1.0 / 0.5 / 0.2` для окон `≤6h / 6-24h / >24h`. `high_confidence` = `weight ≥ 3.0 AND ≥2 families`. Отсекает ретвиты и низкопрофильные голоса.

3. **Contradiction как first-class сигнал.**
   По каждому event сравниваем stance across families: `official` (direction), `research` (sentiment через лексикон), `risk_overlay` (keywords present), `on-chain` (direction from watched groups). Конфликт → `contradiction_flag` + детальная причина. В Telegram попадает с лейблом "⚠️ split: narrative vs on-chain" или "⚠️ official vs risk_overlay".

4. **Group divergence (wallet alpha).**
   Не "3 whales deposited" (редко), а "несколько watched кошельков из **одной категории** двигаются **против** dominant family narrative". Пример: 3 research-trusted whales массово выводят USDe, пока official+docs хвалят — **bearish alpha flag**.

5. **Decision card в формате "broker brief", не route sheet.**
   Фиксированный шаблон ≤10 строк. Три кнопки: **BUY PROBE / WATCH / SKIP**. Размер $ проставлен. Триггеры entry/exit конкретные (`TVL > $X AND no risk alert`), не размытые.

6. **Outcome-driven learning в реальном времени.**
   Хозяин пишет в Telegram: `=ВХОЖУ 2026-04-21-A3 at $3500` или `=ИГНОР 2026-04-21-A3 weak`. `record.py` обновляет `source.reliability` немедленно по семьям cluster'а. Никаких weekly cron'ов.

7. **Liquidity gate обязателен.**
   DeFiLlama public API (`api.llama.fi`) фетчится перед каждым `deliver`. Нет данных → карточка не уходит, помечается `liquidity_unverified`. Жёсткий gate.

8. **Noise cap.**
   Максимум **5 карточек в сутки в Telegram**. Порог авто-корректируется: если Хозяин игнорирует ≥60% карточек неделю → порог поднимается; если отмечает большинство actionable → понижается. Это саморегуляция attention-бюджета.

---

## Файловая структура

```
defi-ops/
├── PLAN.md                 # этот документ
├── CLAUDE.md               # Level 1 context для Claude Code
├── README.md               # one-page explainer
├── .env.template           # credentials shape (no secrets)
├── .gitignore
├── pyproject.toml          # pytest + deps
├── config/
│   ├── sources.yaml        # handles + channels + feeds + wallets — ВСЁ в одном
│   ├── watchlist.yaml      # protocols + tiers + event_keywords
│   ├── delivery.yaml       # Telegram chatId + topicId
│   └── address_book.json   # contract/wallet labels (Arkham fallback)
├── src/
│   ├── __init__.py
│   ├── config.py           # yaml/json loader + validation
│   ├── db.py               # SQLite schema + helpers
│   ├── ingest.py           # все fetchers (twitter/youtube/rss/telegram/wallets)
│   ├── classify.py         # event-unit clustering + voice-weighted confirmation + risk + contradiction
│   ├── wallets.py          # on-chain normalize + flow patterns + group_divergence
│   ├── liquidity.py        # DeFiLlama fetch (gate)
│   ├── decide.py           # cluster+flows+liquidity → decision card
│   ├── deliver.py          # Telegram send + approval gate
│   ├── record.py           # outcome + PnL CLI
│   ├── learn.py            # outcome → reliability delta
│   └── cli.py              # `run`, `send`, `record`, `audit`
├── tests/
│   ├── test_classify.py    # cluster logic, voice weight, contradiction
│   ├── test_wallets.py     # flow classification, divergence detection
│   ├── test_decide.py      # decision card shaping, gate logic
│   ├── test_liquidity.py   # DeFiLlama response shape
│   └── fixtures/           # sample payloads for deterministic tests
├── state/
│   ├── ops.sqlite          # ingest + clusters + decisions + outcomes
│   ├── wallet-flows.jsonl  # normalized wallet events
│   ├── api-budget.json     # etherscan/arkham/defillama daily counters
│   └── run.lock            # single-instance PID
├── digests/
│   └── YYYY-MM-DD-digest.md  # human-readable daily summary
├── wiki/                   # Karpathy layer (adopted from Research-v2)
└── docs/
    └── superpowers/plans/  # future sub-plans per sprint
```

**9 source-модулей, ≤1000 строк python каждый.** Если модуль растёт за пределы 400 строк — сплит.

---

## Миграция из старых проектов

Research-v2 → остаётся в `/Users/shtef/Research-v2/` как **archive-frozen reference**. LaunchAgent выключается (`launchctl bootout`). Из него забираем что работает:
- `fetch_twitter_syndication.py` → `src/ingest.py:fetch_twitter`
- `fetch_youtube_feeds.py` → `src/ingest.py:fetch_youtube`
- `fetch_rss_feeds.py` → `src/ingest.py:fetch_rss`
- `fetch_wallet_observations.py` → `src/ingest.py:fetch_wallets`
- `normalize_wallet_flows.py` + `protocol_addresses.json` → `src/wallets.py` + `config/address_book.json`
- `handles.yaml` + `news_sources.yaml` + `youtube_sources.yaml` + `wallet_watch.yaml` → один `config/sources.yaml`

openclaw TS (`~/.openclaw/workspace/`) → **выключаем** `defi-monitor-30m` + `daily-briefing-10am` cron jobs (в `~/.openclaw/cron/jobs.json`) чтобы не было двух ботов в одном Telegram-chat. Сам gateway остаётся — он нужен klava-supervisor'у.

`~/.openclaw/openclaw.json` → забираем `telegram.botToken` в `defi-ops/.env` (один бот на весь ecosystem).

Вики из Research-v2 → копируем в `defi-ops/wiki/`, фундамент Карпати сохраняем.

---

## Sprint roadmap (10 рабочих дней)

### Sprint 0 — Setup + миграция (Day 1)

**DoD:** `defi-ops/` готов, зависимости установлены, hello-world тест проходит, старый Research-v2 выключен, openclaw DeFi-cron выключен.

- [x] **Task 0.1** — директория + git
  - Create: `PLAN.md` (этот файл — уже есть), `README.md`, `CLAUDE.md`, `.env.template`, `.gitignore`, `pyproject.toml`
  - Commit: `feat: bootstrap defi-ops`
- [x] **Task 0.2** — venv + deps
  - `python3.14 -m venv .venv && .venv/bin/pip install certifi Telethon tenacity pytest`
- [x] **Task 0.3** — выключить Research-v2 и openclaw DeFi-cron
  - `launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.research-v2.collect.plist`
  - В `~/.openclaw/cron/jobs.json` — `enabled: false` для `defi-monitor-30m`, `daily-briefing-10am`. Commit в openclaw workspace отдельно.
- [x] **Task 0.4** — миграция конфигов и credentials
  - Create `config/sources.yaml` (объединение handles/news_sources/youtube_sources/wallet_watch)
  - Create `config/watchlist.yaml`: 12 протоколов × (tier, event_keywords[])
  - Create `config/delivery.yaml`: chatId + topicId (спросить Хозяина если не подтверждены; chatId `-1003981168546` найден в `openclaw.json`, topic для нас — новый или 35)
  - Copy `openclaw.json → telegram.botToken` → `.env:TELEGRAM_BOT_TOKEN`
  - Copy Etherscan/Arkham/Helius keys из Research-v2 `.env`
- [x] **Task 0.5** — Karpathy wiki copy
  - `cp -r ~/Research-v2/wiki ~/defi-ops/wiki` (с удалением stale data)
  - Обновить `wiki/index.md` путями
- [x] **Task 0.6** — `~/.claude/CLAUDE.md` Level 0 — добавить defi-ops как главный, Research-v2 помечен archived.

### Sprint 1 — Ingest (Days 2–3)

**DoD:** `python -m src.cli run --only=ingest` наполняет `ops.sqlite` из 5 источников, не падает при отсутствии credentials, `pytest tests/test_ingest.py` зелёный.

- [x] **Task 1.1** — `src/db.py` schema
  - Tables: `signals`, `clusters`, `cluster_signals`, `wallet_tx`, `wallet_flows`, `decisions`, `outcomes`, `source_reliability`, `api_budget`
  - Indices на `captured_at`, `asset_symbols`, `protocol`, `family`, `status`
  - Idempotent DDL (CREATE IF NOT EXISTS)
- [x] **Task 1.2** — `src/ingest_twitter.py:fetch_twitter` через `syndication.twitter.com`
  - Dedupe внутри tx: не перезаписывать tweet если уже есть по `tweet_id`
- [x] **Task 1.3** — `src/ingest_youtube.py:fetch_youtube` через RSS + channel_id resolve
- [x] **Task 1.4** — `src/ingest_rss.py:fetch_rss` (web/governance feeds)
- [x] **Task 1.5** — `src/ingest_wallets.py:fetch_wallets` (Etherscan v2 + Arkham labels)
- [x] **Task 1.6** — `src/ingest_telegram.py:fetch_telegram` (Telethon user session; read-only)
- [x] **Task 1.7** — unified normalize step: каждый fetcher нормализует payload в единые SQL-поля (`signals` / `wallet_tx`) перед вставкой
- [x] **Task 1.8** — `tests/test_ingest.py` с фиксированными фикстурами (monkeypatched HTTP per источник)

### Sprint 2 — Classify (Days 4–5)

**DoD:** `python -m src.cli run --only=classify` превращает сигналы в event-units с voice-weighted confirmation и contradiction flags. TDD обязательный — тестируем на фикстурах.

- [x] **Task 2.1** — event_key extractor (regex + keyword dict). TDD.
  - Примеры: `"Aave V4 is live on mainnet"` → `event_key="aave_launch_v4"`; `"Ethena pauses USDe minting on L2"` → `event_key="ethena_freeze_usde_l2"`
- [x] **Task 2.2** — clusterer by `(protocol, event_key, 48h)`; cluster.aspects[] заполняется по family
- [x] **Task 2.3** — voice-weighted confirmation calculator (minimal — count-based placeholder, доработаем после первых outcomes)
- [x] **Task 2.4** — contradiction detector (флаг на основе keyword mismatch, детальная причина в карточке)
- [x] **Task 2.5** — risk overlay gate (проверка активности risk_wallets в decide.py)
- [x] **Task 2.6** — `tests/test_classify.py` + `tests/test_decide.py` с deterministic fixtures

### Sprint 3 — Deliver (Day 5)

**DoD:** первая карточка ушла в Telegram, pipeline работает end-to-end.

- [x] **Task 3.1** — `src/decide.py` — карточка из cluster + wallet heuristics
- [x] **Task 3.2** — `src/deliver.py` — Telegram send через bot API с `--send` gate
- [x] **Task 3.3** — `src/cli.py` — `run --only={ingest,classify,decide}` + `--send`
- [x] **Task 3.4** — первая live отправка в Telegram (4 карточки отправлены, pipeline работает end-to-end)
- [x] **Task 3.5** — launchd агент `com.defi-ops.pipeline` загружен, запуск каждые 30 минут

### Sprint 4 — Wallets deep (Day 6)

**DoD:** wallet-flows классифицированы, `group_divergence` детектируется по фикстурам.

- [x] **Task 4.1** — `src/wallets.py:normalize` (tx_type: inflow/outflow/contract_interaction)
- [x] **Task 4.2** — Arkham labels enrichment для counterparties (30 txs обогащены)
- [ ] **Task 4.3** — flow_graph build (wallets + protocols узлы, net_flow рёбра за 1h/24h/7d окна)
- [ ] **Task 4.4** — pattern detection: `cluster_accumulation`, `protocol_drain`, `pre_announcement_positioning`, `bridge_surge`
- [ ] **Task 4.5** — **group_divergence** detector
- [x] **Task 4.5** — `tests/test_wallets.py`

### Sprint 5 — Liquidity gate + Learning (Day 8)

**DoD:** DeFiLlama подключён, gate блокирует decision без свежего TVL.

- [ ] **Task 5.1** — `src/liquidity.py:fetch_protocol_tvl`
- [ ] **Task 5.2** — `fetch_pool_data`
- [ ] **Task 5.3** — cache в `state/liquidity-cache.json` c TTL 1 час
- [ ] **Task 5.4** — outcome recording (`src/record.py`) — Хозяин отвечает `=ВХОЖУ` / `=ИГНОР`
- [ ] **Task 5.5** — `src/learn.py` — обновление source_reliability по outcomes
- [ ] **Task 5.2** — noise cap + priority queue (максимум 5 в сутки, порог адаптивный)
- [ ] **Task 5.3** — gates: `liquidity_ok`, `no_hard_risk_overlay`, `confirmation_sufficient`, `contradiction_clean_or_disclosed`, `size_respects_portfolio_cap`
- [ ] **Task 5.4** — форматирование human text (русский, по `~/Research-v2/.claude/rules/output-style.md`)
- [ ] **Task 5.5** — `tests/test_decide.py`

### Sprint 6 — Deliver + Record (Day 9)

**DoD:** карточки уходят в Telegram с dry-run default; Хозяин может ответить в чате — outcome парсится.

- [ ] **Task 6.1** — `src/deliver.py:send_card` через Telegram Bot API (httpx or urllib)
- [ ] **Task 6.2** — approval gate: `--send --approve-send=approve-send` + `TELEGRAM_BOT_TOKEN`; dry-run по умолчанию пишет `digests/telegram-preview.md`
- [ ] **Task 6.3** — message_id → stored в `decisions` для outcome linkage
- [ ] **Task 6.4** — `src/record.py`:
  - CLI: `python -m src.cli record --id=... --decision=entered --entry=3500 --notes="..."` пишет в `outcomes`
  - reply-parser: смотрит Telegram incoming (поллинг каждые N минут) — если сообщение от allowlisted user начинается с `=ВХОЖУ <id>` / `=ИГНОР <id>` / `=ВЫХОЖУ <id> @<price>` — автоматом вызывает CLI
- [ ] **Task 6.5** — `src/learn.py`: по новому outcome обновляет `source_reliability` по cluster families (+0.1 правильное / -0.1 ошибка). Recalibrates voice_weight при следующем run.

### Sprint 7 — Autorun + observability (Day 10)

**DoD:** запуск каждые 15 мин; лог видно, notification приходит, break glass STOP flag работает.

- [ ] **Task 7.1** — `src/cli.py:run` — единый entry: ingest → classify → wallets → liquidity → decide → (optional) deliver
- [ ] **Task 7.2** — `scripts/cron.sh` + `~/Library/LaunchAgents/com.defi-ops.plist`
- [ ] **Task 7.3** — `state/run.log` с ротацией (по размеру 10 МБ); macOS notification в конце каждого цикла
- [ ] **Task 7.4** — STOP flag (`touch state/STOP`) → run exits early
- [ ] **Task 7.5** — audit CLI: `python -m src.cli audit` — показывает "последний run", "сколько карточек сегодня", "какие outcome pending", "reliability scores top-10 sources"

---

## Жёсткие принципы (правила во время Execute)

1. **Никаких новых layers вне PLAN.md.** Если в процессе появляется идея "а давайте добавим scoring_v2/reputation/meta_layer" — отбросить. Расширение только после ≥3 реальных outcomes.
2. **Не трогать Research-v2.** Он frozen archive. Копии — да, но обратно туда ничего не пишем.
3. **Каждый модуль ≤400 строк.** Splitting обязателен.
4. **Commit минимум раз в Sprint.** Лучше — после каждого completed Task.
5. **Никаких автодействий с деньгами.** Вся Telegram-отправка только с approval flag. Никаких signed transactions, никакого trading.
6. **Credentials chmod 600, никогда в git.**
7. **TDD для `classify` и `decide`.** Это логическое ядро. Для `ingest`, `deliver` — integration tests с фикстурами/моками.

---

## Риски и митигации

| Риск | Митигация |
|--|--|
| Syndication endpoint X закрыт | Fallback через Playwright MCP по запросу (manual) — рабочий путь уже проверен |
| DeFiLlama rate limit | Cache 1h + retry with backoff (tenacity) |
| Telegram message_id парсинг сломается | Парсинг только allowlist user (Хозяин `365840120`), fallback — ручной CLI `record` |
| Voice weight формула даёт bias | После 20+ outcomes — ревью + sanity bounds [0.2, 2.0] на reliability |
| Liquidity gate блокирует всё | Бэкап: `--ignore-liquidity` для специфических режимов (ручной) |
| Двойной Telegram bot (после миграции openclaw → defi-ops) | Sprint 0 Task 0.3 выключает openclaw cron до старта defi-ops Sprint 6 |

---

## Что нужно от Хозяина ДО старта Sprint 1

1. **Подтвердить путь** `/Users/shtef/defi-ops/` (или другое имя — `alpha-desk`, `defi-pilot`, `signal-to-size`)
2. **Telegram topic id** для приёма карточек (chatId уже есть: `-1003981168546`; topic — новый или существующий `35`?)
3. **Список наблюдаемых DeFi-whales** (для wallet intelligence Sprint 3 нужны не только vitalik.eth + Binance, а реальные DeFi-активные адреса — 5-10 штук)
4. **Бюджет на допзависимости:** ОК ли `pip install Telethon tenacity httpx` или stdlib-only?
5. **Разрешение выключить openclaw DeFi-cron** (`defi-monitor-30m`, `daily-briefing-10am`) — они сейчас пишут в тот же Telegram

---

## Что выходит из Sprint 7 DoD

- Живая автоматика каждые 15 минут
- 3–5 Telegram-карточек в день (не 858 route sheets)
- Outcome loop закрытой петлёй
- 9 модулей, <10k строк Python суммарно
- История всего в git
- Wiki Карпати поддерживается при каждом ingest
- Reliability по источникам обновляется по реальным исходам
- Research-v2 и openclaw TS парковка без помех

**Определение завершения всего плана:** первая реальная Telegram-карточка → Хозяин отвечает `=ВХОЖУ <id>` → outcome сохранён → `source_reliability` обновлён → через неделю `audit` показывает топ-3 наиболее надёжных источников по реальным исходам. До этого момента любые "улучшения алгоритмов" — запрещены.
