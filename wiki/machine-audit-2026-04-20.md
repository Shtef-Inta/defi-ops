---
type: audit
date: 2026-04-20
last_updated: 2026-04-20
---

# Machine Audit — 2026-04-20

_Полное сканирование `/Users/shtef/` на предмет DeFi/research/crypto/parser проектов. Цель — выявить что где реально работает, где дубликаты, где ошибки._

## Executive summary

На машине **три активных центра DeFi/research-работы**: Research-v2 (наш Python), openclaw workspace (TS, параллельный), Claude Code runtime. Плюс 107 GB архивов SMM/Research.

**Критическая проблема:** параллельно с Research-v2 всё ещё живёт **весь TS openclaw pipeline** — 6 активных cron jobs через openclaw gateway (PID 19644, uptime 2 дня), launchd agent `ai.openclaw.gateway` с `KeepAlive=true`, отдельная Postgres@16 (uptime 7 дней), отдельный Telegram bot token. **Два pipeline отправляют сообщения в один и тот же Telegram group `-1003981168546`**, не зная друг о друге. Если Research-v2 включит send — в чате будут две независимые карточки от двух ботов на каждое событие.

## Активные проекты (last activity < 90 days)

### `/Users/shtef/Research-v2/` — главный DeFi pipeline
- Stack: Python 3, stdlib-only, `.venv` локально; SQLite; plain markdown wiki
- Git: 10 commits, последний `bfe2917`. **Много uncommitted** (schema migrations, новые cross-source scripts, `cron_collect.sh`, `fetch_twitter_syndication.py`, etc)
- Цепочка: `cron_collect.sh` каждые 15 мин (launchd `com.research-v2.collect`) → 4 fetcher'а → `import_all_sources` → `normalize_wallet_flows` → `generate_route_sheet` → `digests/YYYY-MM-DD-route-sheets.{json,md}`
- Последний прогон: 2026-04-20 17:33Z, **1653 сигнала**, 249 кластеров, 858 route sheets
- Raw: 113 X captures, 28 YouTube, 28 web, 3 wallets
- 53 Python-скрипта в `research/scripts/`
- `.env` chmod 600 (156 байт — ETHERSCAN/ARKHAM/HELIUS keys live, TELEGRAM пустые)

### `/Users/shtef/.openclaw/workspace/` — TS DeFi pipeline (формально "reference only", фактически production)
- Эта же директория symlink'ается как `/Users/shtef/Documents/New project/`
- Stack: TypeScript, Node 22.22, 174 MB node_modules, 6 MB dist (551 .js), 255 MB out/
- Git: инициализирован, **0 commits** (279 TS-файлов untracked). История оборвалась 4 апреля в archive mirror.
- **Процессы:** `gateway` PID 19644 (2+ дня uptime), Codex instances с `--dangerously-bypass-approvals-and-sandbox`, tmux сессии `klava-supervised` и `op-auth-*`
- 149 из 279 файлов с префиксом `defi-` — та самая запрещённая scoring/attribution зона из PROJECT_STATE.md. **Она уже построена и гудит.**
- `package.json` содержит 176 scripts: `parse:twitter`, `parse:youtube`, `parse:rss`, `parse:web`, `ingest:telegram`, десятки `defi:*`, `defi:operator-cycle:dry`/`send`
- Последнее изменение src: 2026-04-19, последний out: 2026-04-20 (`defi-monitor`, `klava-safe-dispatcher`)
- src/parsers/: rss.ts, telegram.ts, twitter.ts, twitter-browser-observed.ts, web.ts, youtube.ts — готовые парсеры, **некоторые дублируют то что я писал сегодня на Python**

### `/Users/shtef/.openclaw/` — openclaw orchestra runtime
- `gateway` (port 18789) — launchd `ai.openclaw.gateway.plist` `KeepAlive=true`, работает
- **6 cron jobs** в `/Users/shtef/.openclaw/cron/jobs.json`:
  - `daily-briefing-10am` (enabled) — отправляет ежедневный брифинг в **Telegram topic `-1003981168546:35`**
  - `defi-monitor-30m` (enabled) — каждые 30 мин DeFi monitor
  - `telegram-topic-schema-203-autopilot` (enabled)
  - `workspace-memory-maintenance` (enabled)
  - `workspace-autopilot-watchdog` (disabled)
  - `telegram-reminder-vet-2026-04-13-1700` (disabled, разовый)
- `klava-supervisor` + `klava-watchdog` — 3 launchd plists ещё
- **Postgres@16** запущен PID 28213, uptime 7 дней (`/Users/shtef/.openclaw/var/postgresql@16`)
- **Telegram: `openclaw.json` содержит bot token plaintext** и allowlisted user `365840120` (Хозяин)
- `agents/`, `tasks/runs.sqlite`, `memory/main.sqlite`, `flows/registry.sqlite` — параллельная state-машина

### `/Users/shtef/.claude/` — Claude Code runtime
- `CLAUDE.md` (global level-0), `history.jsonl` 41 KB
- 3 active projects tracked: Research-v2, openclaw workspace, home root
- Plugin: `superpowers@claude-plugins-official v5.0.7` (user scope)
- MCP: только `playwright` headless Chrome
- `/Users/shtef/.claude/skills/telegram-ingest/` — установленный skill

### `/Users/shtef/.codex/` — Codex CLI runtime
- `logs_1.sqlite` 149 MB (active, WAL +4 MB — **не ротируется**)
- `.codex/superpowers/` — параллельная копия superpowers (Cursor/OpenCode/Codex версии)
- `automations/klava-supervisor-inbox/` — свой автоматический контур
- `auth.json` — OpenAI credentials (chmod 600)
- `/Users/shtef/bin/klava` — wrapper запускает Codex с `--dangerously-bypass-approvals-and-sandbox` в openclaw workspace

## Неактивные / архивные

### `/Users/shtef/Documents/Recovered Projects Archive/2026-04-14/` — 107 GB
- `Research/Research-workspace/` (35 MB) — snapshot openclaw workspace от 14 апр, 84 TS-файла (старее активного)
- `Research/GitHub/openclaw-workspace.git` — git mirror, **45 commits до 2026-04-04**. Это PYTHON оригинал Research-v2 до разветвления на TS
- `SMM/expedition-content-studio/` (52 GB) — SMM (non-DeFi)
- `SMM/expedition-codex/` (1.9 GB) — Codex worktree
- `SMM/New project/` (54 GB) — iCloud-снимок с `expedition-content-studio` внутри (почти дубликат, экономия ~54 GB при дедупе)
- `SMM/Snapshots/icloud-root-snapshot/universal-telegram-bridge/` (228 KB) — забытый Telegram-bridge, assistant-first continuity

### Одинокие файлы
- `/Users/shtef/self-improving/corrections.md` (2 KB)
- `/Users/shtef/.claude.backup.20260419T111630Z/` — бэкап Claude Code config от вчера
- `/Users/shtef/Applications/Claude Code URL Handler.app/`

## Секреты / credentials — разбросаны

| Что | Где | Права | Комментарий |
|--|--|--|--|
| Telegram bot token | `/Users/shtef/.openclaw/openclaw.json` | 600 | **plaintext**, дублирует Research-v2 назначение |
| Telegram allowlist `365840120` | та же | 600 | Хозяин |
| Gateway token `07893e...` | та же | 600 | Локальный gateway auth |
| Research-v2 creds | `/Users/shtef/Research-v2/research/.env` | 600 | ETHERSCAN+ARKHAM+HELIUS live; TG пустые |
| OpenAI auth | `/Users/shtef/.codex/auth.json` | 600 | — |
| Claude OAuth | `/Users/shtef/.claude.json` | 600 | — |
| **1Password recovery code** | `/Users/shtef/Downloads/Код восстановления 1Password.txt` | 600 | **Плохое место — убрать из Downloads** |
| Telegram Desktop data | `/Users/shtef/Downloads/Telegram Desktop/` (498 files) | — | 15 MB exports |

## Launchd agents — пересекаются

| Label | Status | Что делает |
|--|--|--|
| `ai.openclaw.gateway` | PID 19644 running | TS gateway keepalive, port 18789 |
| `com.research-v2.collect` | loaded (PID `-`) | Каждые 900 сек cron_collect.sh |
| `ai.openclaw.klava-supervisor` | loaded, polling 60 сек | klava watcher |
| `ai.openclaw.klava-watchdog` | loaded | Klava watchdog |
| `com.shtef.klava-acceptance-watch` | loaded | Klava acceptance tests |
| `com.openai.atlas.agent-xpc` | running | Atlas browser agent |
| `homebrew.mxcl.postgresql@16` | loaded | Postgres для openclaw |
| `com.google.GoogleUpdater.wake` | normal | Chrome updater |

## Дубликаты / конфликты

1. **Параллельный DeFi pipeline**: openclaw TS (6 cron jobs, Postgres, gateway PID 19644) работает одновременно с Research-v2. `.claude/CLAUDE.md` помечает openclaw "📦 Reference only", но `defi-monitor-30m` продолжает писать в тот же Telegram topic раз в 30 мин. **Это прямое нарушение `PROJECT_STATE.md` «не строить scoring layers» — уже построен и активен.**
2. **Telegram send — две independent lanes.** Research-v2 планирует через `config/delivery.yaml` + `TELEGRAM_BOT_TOKEN`. openclaw уже отправляет через `openclaw.json`. Оба целятся в `-1003981168546`. Если Research-v2 включит send — **две карточки от двух ботов** в один topic.
3. **Две SQLite vs Postgres.** Research-v2 SQLite. openclaw Postgres@16. Данные несинхронизированы.
4. **Три копии openclaw workspace:** active + archive snapshot от 14 апр + iCloud snapshot.
5. **Symlinks путают:** `Documents/New project` → `.openclaw/workspace`, `Documents/Research-v2` → `Research-v2`. Это **один физический объект** в каждой паре.
6. **Две superpowers installations:** `~/.claude/plugins/` и `~/.codex/superpowers/` — могут рассинхронизироваться.
7. **Archive 107 GB:** два почти идентичных SMM снимка (52 GB + 54 GB).

## Ошибки / нарушения

1. **CLAUDE.md level-0** говорил путь `/Users/shtef/Documents/Research-v2/` — я сегодня обновил на `/Users/shtef/Research-v2/` после переезда.
2. **openclaw workspace `.git` имеет 0 commits.** Archive mirror — 45 commits до 4 апреля. **История проекта оборвалась 4 апреля** — всё после (279 TS файлов) нигде в git не зафиксировано.
3. **openclaw.json**: `ssrfPolicy.allowedHostnames: ["*"]` + `dangerouslyAllowPrivateNetwork: true` — gateway не ограничен. Через Codex/klava это означает доступ в любой внутренний хост.
4. **cron_collect.sh** untracked в Research-v2 git — launchd запускает файл, не защищённый git.
5. **Research-v2 нет Telegram delivery**. `generate_route_sheet.py` делает md/json, но никто их в Telegram не кладёт. openclaw делает свои TS-дайджесты — **Хозяин получает TS-дайджесты и НЕ получает Python-route sheets**.
6. **universal-telegram-bridge** (в icloud snapshot) — забытый третий канал, если включится → третий бот в том же чате.

## Сюрпризы

- `~/bin/klava` запускает Codex с `--dangerously-bypass-approvals-and-sandbox`. Launchd `klava-supervisor` (polling 60 сек) каждую минуту может запускать Codex в обход approvals.
- `~/Downloads/BROWSER_CONTROL_HANDOFF.md` + `SKILL.md` — следы старой попытки browser-control skill.
- `~/.codex/logs_1.sqlite` 149 MB и растёт, никем не ротируется.
- `/Users/shtef/.openclaw/qqbot/` — не исследован, имя подозрительное.
- В `research/raw/x/` `0xngmi` имеет 6 capture'ов за день — syndication fetcher не дедуплицирует (берёт тот же timeline каждый cron tick).
- `/Users/shtef/.openclaw/workspace/.openclaw/workspace-state.json` — рекурсивное state.
- Codex exec instances работают 2 дня с `model_reasoning_effort="xhigh"` — серьёзный расход токенов.

## Cross-refs

- [[index]] — каталог wiki
- [[hot]] — оперативный контекст
- Level-1 CLAUDE.md: `/Users/shtef/Research-v2/CLAUDE.md`
- Level-0 global: `/Users/shtef/.claude/CLAUDE.md`

## Решения — нужны от Хозяина

1. **Что делать с openclaw TS pipeline?**
   - **A.** Выключить `defi-monitor-30m` + `daily-briefing-10am` cron jobs, оставить только Research-v2 как источник истины
   - **B.** Признать openclaw production, убрать из level-0 CLAUDE.md формулировку "reference only", фиксить дублирование по-другому
2. **Использовать ли bot token из `openclaw.json` для Research-v2 delivery?** Если да — тот же bot пишет и TS и Python, конфликта нет, но нужно выключить TS отправку.
3. **Коммитить Research-v2 uncommitted изменения?** (schema migration + новые scripts + cron_collect.sh + wiki — сегодняшняя работа). Сейчас всё работает, но в git не защищено.
4. **Архив 107 GB** — дедупнуть SMM-копии (освободит ~54 GB)?
5. **Переместить 1Password recovery code** из Downloads в защищённое место?
