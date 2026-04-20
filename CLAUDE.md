# defi-ops — Project Context (Level 1)

Чистый DeFi pipeline для $100k капитала. Запись №4 — учтены уроки Research-v2 (53 скрипта) и openclaw TS (279 файлов).

## Цель проекта (одной фразой)

От сигналов из 5 источников → cross-source confirmation + wallet flow + liquidity + risk + contradiction → ≤5 карточек в день в Telegram → Хозяин решает руками → outcome → learning loop.

## Стек

- **Python 3.14**, stdlib-first
- Сторонние: `certifi`, `Telethon`, `tenacity`, `pytest`
- **SQLite** единая база (`state/ops.sqlite`)
- macOS launchd для автозапуска (в `~/defi-ops/`, вне Documents/TCC)

## Порядок чтения

1. `PLAN.md` — полный roadmap (Sprint 0–7)
2. `wiki/hot.md` — оперативный контекст
3. `wiki/index.md` — каталог DeFi-знаний
4. `src/<module>.py` — только при работе над этим модулем
5. `tests/test_<module>.py` — перед изменением кода модуля

## Главные файлы

| Файл | Что в нём |
|--|--|
| `PLAN.md` | 10-дневный sprint-план с DoD и tasks |
| `config/sources.yaml` | Все handles/channels/feeds/wallets в одном месте |
| `config/watchlist.yaml` | 12 протоколов + tier + event_keywords |
| `config/delivery.yaml` | Telegram chatId + topicId |
| `src/cli.py` | Единственная точка входа: `run`, `send`, `record`, `audit` |
| `state/ops.sqlite` | Вся операционная память |
| `wiki/` | Семантический слой Карпати (protocols/events/concepts/wallets) |

## Жёсткие правила (не нарушать)

1. **9 src-модулей максимум.** Если надо больше — срочное ревью архитектуры.
2. **Каждый файл ≤400 строк.** Split by responsibility.
3. **Никаких новых scoring/attribution layers** пока не накопится ≥3 реальных outcomes (иначе overfit).
4. **Все артефакты** содержат safety-флаги (`researchOnly=True`, `sendAllowed=False` по умолчанию).
5. **Credentials chmod 600** в `.env`, никогда в git. Шаблон — `.env.template`.
6. **Telegram send** только с `--send --approve-send=approve-send` + `TELEGRAM_BOT_TOKEN`.
7. **TDD** для `classify`, `decide`, `wallets:group_divergence`, `learn`. Для `ingest`/`deliver` — integration tests.
8. **Noise cap 5 карточек/день** в Telegram; порог адаптивный по outcome acceptance rate.

## Команды

| Что | Команда |
|--|--|
| Полный цикл (dry) | `python -m src.cli run` |
| Полный цикл + Telegram | `python -m src.cli run --send --approve-send=approve-send` |
| Только ingest | `python -m src.cli run --only=ingest` |
| Только classify | `python -m src.cli run --only=classify` |
| Outcome (ручной) | `python -m src.cli record --id=<id> --decision=entered --entry=<price> --notes=""` |
| Audit snapshot | `python -m src.cli audit` |
| Tests | `pytest` (в корне проекта) |

## Миграция из Research-v2

- Research-v2 остаётся в `/Users/shtef/Research-v2/` как **archive-frozen reference**
- LaunchAgent `com.research-v2.collect` выключен в Sprint 0
- Работающие фетчеры портируются функциями в `src/ingest.py`, НЕ копированием файлов
- Wiki-папка копируется с чисткой stale страниц

## Миграция из openclaw TS

- `~/.openclaw/workspace/` остаётся без изменений (klava-supervisor от него зависит)
- Выключаем cron jobs `defi-monitor-30m` и `daily-briefing-10am` (в Sprint 0) чтобы не было двух ботов в одном Telegram
- Telegram bot token забираем из `~/.openclaw/openclaw.json` → в `defi-ops/.env`
- DeFi-scripts из `src/defi-*.ts` НЕ портируем — изучаем patterns, применяем в чистом `src/classify.py` и `src/decide.py`

## Definition of Done проекта

Первая реальная Telegram-карточка → Хозяин отвечает `=ВХОЖУ <id>` → outcome сохранён → `source_reliability` обновлён → через неделю `audit` показывает топ-3 наиболее надёжных источников по реальным исходам.
