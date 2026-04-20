---
type: audit
date: 2026-04-20
last_updated: 2026-04-21
source: Research-v2/wiki (archive)
---

# Machine Audit — 2026-04-20

_Полное сканирование `/Users/shtef/` на предмет DeFi/research/crypto/parser проектов. Цель — выявить что где реально работает, где дубликаты, где ошибки._

> **Archive note:** Этот аудит выполнен в контексте Research-v2 (2026-04-20). На момент аудита на машине работали три параллельных контура: Research-v2 Python, openclaw TS, Claude Code runtime. С 2026-04-21 Research-v2 и openclaw DeFi-cron выключены; активный проект — defi-ops. Факты об архитектуре и секретах ниже остаются валидными для cleanup.

## Executive summary

На машине **три активных центра DeFi/research-работы**: Research-v2 (наш Python), openclaw workspace (TS, параллельный), Claude Code runtime. Плюс 107 GB архивов SMM/Research.

**Критическая проблема (устарела 2026-04-21):** параллельно с Research-v2 всё ещё живёт **весь TS openclaw pipeline** — 6 активных cron jobs через openclaw gateway (PID 19644, uptime 2 дня), launchd agent `ai.openclaw.gateway` с `KeepAlive=true`, отдельная Postgres@16 (uptime 7 дней), отдельный Telegram bot token. **Два pipeline отправляют сообщения в один и тот же Telegram group `-1003981168546`**, не зная друг о друге.

> **Resolution 2026-04-21:** openclaw DeFi-cron jobs (`defi-monitor-30m`, `daily-briefing-10am`) disabled. Research-v2 LaunchAgent `com.research-v2.collect` booted out. defi-ops — единственный активный DeFi pipeline.

## Активные проекты (last activity < 90 days)

### `/Users/shtef/Research-v2/` — archived Python pipeline
- Stack: Python 3, stdlib-only, `.venv` локально; SQLite; plain markdown wiki
- Git: 10 commits, последний `bfe2917`. **Много uncommitted** (schema migrations, новые cross-source scripts, `cron_collect.sh`, `fetch_twitter_syndication.py`, etc)
- Цепочка: `cron_collect.sh` каждые 15 мин (launchd `com.research-v2.collect`) → 4 fetcher'а → `import_all_sources` → `normalize_wallet_flows` → `generate_route_sheet` → `digests/YYYY-MM-DD-route-sheets.{json,md}`
- Последний прогон: 2026-04-20 17:33Z, **1653 сигнала**, 249 кластеров, 858 route sheets
- Raw: 113 X captures, 28 YouTube, 28 web, 3 wallets
- 53 Python-скрипта в `research/scripts/`
- `.env` chmod 600 (156 байт — ETHERSCAN/ARKHAM/HELIUS keys live, TELEGRAM пустые)

### `/Users/shtef/.openclaw/workspace/` — TS pipeline (archived for DeFi, gateway kept for klava)
- Stack: TypeScript, Node 22.22, 174 MB node_modules, 6 MB dist (551 .js), 255 MB out/
- Git: инициализирован, **0 commits** (279 TS-файлов untracked). История оборвалась 4 апреля в archive mirror.
- **Процессы:** `gateway` PID 19644 (2+ дня uptime), Codex instances с `--dangerously-bypass-approvals-and-sandbox`, tmux сессии `klava-supervised` и `op-auth-*`
- 149 из 279 файлов с префиксом `defi-` — та самая запрещённая scoring/attribution зона.
- `package.json` содержит 176 scripts: `parse:twitter`, `parse:youtube`, `parse:rss`, `parse:web`, `ingest:telegram`, десятки `defi:*`, `defi:operator-cycle:dry`/`send`
- src/parsers/: rss.ts, telegram.ts, twitter.ts, twitter-browser-observed.ts, web.ts, youtube.ts — готовые парсеры

### `/Users/shtef/.openclaw/` — openclaw orchestra runtime
- `gateway` (port 18789) — launchd `ai.openclaw.gateway.plist` `KeepAlive=true`
- **Cron jobs** в `/Users/shtef/.openclaw/cron/jobs.json` (DeFi jobs disabled 2026-04-21)
- `klava-supervisor` + `klava-watchdog` — 3 launchd plists
- **Postgres@16** запущен PID 28213
- **Telegram: `openclaw.json` содержит bot token plaintext** и allowlisted user `365840120`

### `/Users/shtef/.claude/` — Claude Code runtime
- `CLAUDE.md` (global level-0), `history.jsonl`
- Plugin: `superpowers@claude-plugins-official v5.0.7` (user scope)
- MCP: `playwright` headless Chrome
- `/Users/shtef/.claude/skills/telegram-ingest/` — установленный skill

### `/Users/shtef/.codex/` — Codex CLI runtime
- `logs_1.sqlite` 149 MB (active, WAL — не ротируется)
- `.codex/superpowers/` — параллельная копия superpowers
- `automations/klava-supervisor-inbox/` — свой автоматический контур
- `/Users/shtef/bin/klava` — wrapper запускает Codex с `--dangerously-bypass-approvals-and-sandbox`

## Неактивные / архивные

### `/Users/shtef/Documents/Recovered Projects Archive/2026-04-14/` — 107 GB
- `Research/Research-workspace/` (35 MB) — snapshot openclaw workspace от 14 апр
- `Research/GitHub/openclaw-workspace.git` — git mirror, **45 commits до 2026-04-04**
- `SMM/expedition-content-studio/` (52 GB), `SMM/expedition-codex/` (1.9 GB), `SMM/New project/` (54 GB)
- `SMM/Snapshots/icloud-root-snapshot/universal-telegram-bridge/` (228 KB)

## Секреты / credentials — разбросаны

| Что | Где | Права | Комментарий |
|--|--|--|--|
| Telegram bot token | `/Users/shtef/.openclaw/openclaw.json` | 600 | **plaintext**, reused in defi-ops `.env` |
| Telegram allowlist `365840120` | та же | 600 | Хозяин |
| Gateway token `07893e...` | та же | 600 | Локальный gateway auth |
| Research-v2 creds | `/Users/shtef/Research-v2/research/.env` | 600 | ETHERSCAN+ARKHAM+HELIUS live; TG пустые |
| OpenAI auth | `/Users/shtef/.codex/auth.json` | 600 | — |
| Claude OAuth | `/Users/shtef/.claude.json` | 600 | — |
| **1Password recovery code** | `/Users/shtef/Downloads/Код восстановления 1Password.txt` | 600 | **Плохое место — убрать из Downloads** |
| Telegram Desktop data | `/Users/shtef/Downloads/Telegram Desktop/` (498 files) | — | 15 MB exports |

## Launchd agents — пересекаются

| Label | Status (2026-04-20) | Что делает |
|--|--|--|
| `ai.openclaw.gateway` | PID 19644 running | TS gateway keepalive, port 18789 |
| `com.research-v2.collect` | loaded (PID `-`) | Каждые 900 сек cron_collect.sh |
| `ai.openclaw.klava-supervisor` | loaded, polling 60 сек | klava watcher |
| `ai.openclaw.klava-watchdog` | loaded | Klava watchdog |
| `com.shtef.klava-acceptance-watch` | loaded | Klava acceptance tests |
| `com.openai.atlas.agent-xpc` | running | Atlas browser agent |
| `homebrew.mxcl.postgresql@16` | loaded | Postgres для openclaw |

> **2026-04-21 update:** `com.research-v2.collect` booted out. openclaw DeFi cron jobs disabled.

## Дубликаты / конфликты

1. **Параллельный DeFi pipeline:** openclaw TS (6 cron jobs, Postgres, gateway PID 19644) работал одновременно с Research-v2. **Resolved:** DeFi cron disabled, defi-ops — единственный активный pipeline.
2. **Telegram send — две independent lanes.** Research-v2 планировал через `config/delivery.yaml` + `TELEGRAM_BOT_TOKEN`. openclaw уже отправлял через `openclaw.json`. Оба целились в `-1003981168546`. **Resolved:** bot token reused in defi-ops; TS send disabled.
3. **Две SQLite vs Postgres.** Research-v2 SQLite. openclaw Postgres@16. Данные несинхронизированы. **Status:** Research-v2 archived; defi-ops uses SQLite.
4. **Три копии openclaw workspace:** active + archive snapshot от 14 апр + iCloud snapshot.
5. **Symlinks путают:** `Documents/New project` → `.openclaw/workspace`, `Documents/Research-v2` → `Research-v2`.
6. **Две superpowers installations:** `~/.claude/plugins/` и `~/.codex/superpowers/`.
7. **Archive 107 GB:** два почти идентичных SMM снимка (52 GB + 54 GB).

## Ошибки / нарушения

1. **openclaw workspace `.git` имеет 0 commits.** Archive mirror — 45 commits до 4 апреля. **История проекта оборвалась 4 апреля**.
2. **openclaw.json**: `ssrfPolicy.allowedHostnames: ["*"]` + `dangerouslyAllowPrivateNetwork: true` — gateway не ограничен.
3. **cron_collect.sh** untracked в Research-v2 git — launchd запускает файл, не защищённый git.
4. **Research-v2 нет Telegram delivery**. `generate_route_sheet.py` делает md/json, но никто их в Telegram не кладёт.
5. **universal-telegram-bridge** (в icloud snapshot) — забытый третий канал.

## Сюрпризы

- `~/bin/klava` запускает Codex с `--dangerously-bypass-approvals-and-sandbox`. Launchd `klava-supervisor` (polling 60 сек) каждую минуту может запускать Codex в обход approvals.
- `~/.codex/logs_1.sqlite` 149 MB и растёт, никем не ротируется.
- `/Users/shtef/.openclaw/qqbot/` — не исследован.
- В `research/raw/x/` `0xngmi` имеет 6 capture'ов за день — syndication fetcher не дедуплицирует.
- `/Users/shtef/.openclaw/workspace/.openclaw/workspace-state.json` — рекурсивное state.
- Codex exec instances работают 2 дня с `model_reasoning_effort="xhigh"`.

## Backlinks

- [[Wiki Index]]
- [[Wiki Log]]
- [[index]]
- [[log]]

