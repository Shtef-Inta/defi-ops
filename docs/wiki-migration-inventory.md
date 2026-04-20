# Wiki Migration Inventory

Date: 2026-04-21
Sources: `defi-ops/wiki` (active), `Research-v2/wiki` (archive), `.openclaw/workspace/wiki` (archive)

## Source comparison

- `Research-v2/wiki` and `defi-ops/wiki` are **byte-identical** (verified with `diff -rq`).
  - defi-ops/wiki was copied from Research-v2/wiki in Sprint 0 Task 0.5.
  - Therefore Research-v2 contributes **no new files** beyond what is already in defi-ops/wiki.
- `.openclaw/workspace/wiki` contains 23 files: system-level TS pipeline documentation (topics, schema, signals, storage, alerts, tests, telegram, twitter, web, youtube, document, media).
  - No DeFi domain knowledge (protocols, assets, events, concepts).
  - Only `methods/karpathy-wiki-memory.md` has methodology value, but the Karpathy method is already documented in defi-ops `CLAUDE.md` and `index.md`.

## Per-file decisions

| File | Source | Decision | Reason |
|------|--------|----------|--------|
| `wiki/index.md` | defi-ops (copied from R-v2) | **rewrite** | Describes Research-v2 structure, references `obsidian/`, `PHASE_4_PLAN.md`. Must become defi-ops catalog. |
| `wiki/hot.md` | defi-ops (copied from R-v2) | **rewrite** | Entirely stale Research-v2 state (Phase 4 sprints, 1653 signals, live parsers). Must reflect current defi-ops state. |
| `wiki/overview.md` | defi-ops (copied from R-v2) | **merge/rewrite** | Watchlist table and safety rules are useful. Pipeline diagram and project references are stale. |
| `wiki/log.md` | defi-ops (copied from R-v2) | **keep + disclaimer** | Historical record of 2026-04-20 actions. Prepend archive disclaimer; do not edit past entries. |
| `wiki/machine-audit-2026-04-20.md` | defi-ops (copied from R-v2) | **keep + disclaimer** | Valuable machine audit (parallel pipelines, credentials, launchd). Mark as archive reference. Update cross-refs. |
| `wiki/protocols/aave.md` | defi-ops (copied from R-v2) | **merge/rewrite** | DeFi facts are good (V4, $30M, PT listings). Remove Research-v2 terms: `route sheets`, `cross_family_confirmed` clusters, `PHASE_4_PLAN`. |
| `wiki/protocols/ethena.md` | defi-ops (copied from R-v2) | **merge/rewrite** | Same as Aave. Keep protocol facts, remove old taxonomy. |
| `wiki/protocols/uniswap.md` | defi-ops (copied from R-v2) | **merge/rewrite** | Thin but valid. Remove stale refs. |
| `wiki/events/2026-04-aave-v4-deposits.md` | defi-ops (copied from R-v2) | **merge/rewrite** | Event facts are valid. Remove `route sheet` references and old confirmation taxonomy. |
| `wiki/events/2026-04-ethena-pt-listings.md` | defi-ops (copied from R-v2) | **merge/rewrite** | Same as above. |
| `wiki/concepts/risk-overlay-peckshield.md` | defi-ops (copied from R-v2) | **merge/rewrite** | Core concept for defi-ops. Remove `PHASE_4_PLAN` / `C.3 phase` refs. Update to current plan language. |
| `wiki/assets/*` | empty dirs | **skip** | No files. Will populate during ingest. |
| `wiki/signals/*` | empty dirs | **skip** | No files. |
| `wiki/wallets/*` | empty dirs | **skip** | No files. Populated in Sprint 3. |
| `.openclaw/workspace/wiki/*` | 23 system docs | **skip** | No DeFi domain knowledge. Methodology already in CLAUDE.md. |

## Conflicts / open questions

1. **Confirmation taxonomy mismatch.** Research-v2 used `single_source` / `dual_source` / `cross_family_confirmed`. defi-ops uses `high` (≥3.0 weight, ≥2 families) / `medium` / `single`.
   - Resolution: rewrite event pages to use new taxonomy, but preserve raw source list.
2. **"Cross-family confirmed" claim on Aave V4.** In Research-v2 this meant Aave Labs YouTube + The Rollup interview.
   - In defi-ops this maps to `official` + `research` families within the same event-unit.
   - Resolution: keep the source list, rephrase with defi-ops taxonomy.
3. **Machine audit references openclaw as "production" and Research-v2 as "main."**
   - In defi-ops both are archived. Resolution: add archive disclaimer, keep factual audit data.
4. **Event pages reference route sheets and action codes (`готовить вход`, `избегать`).**
   - defi-ops uses `BUY_PROBE / WATCH / SKIP / BLOCKED`.
   - Resolution: replace action language with defi-ops decision card terms.

## Import summary

- **Pages imported/rewritten**: 10 (index, hot, overview, log-prefixed, machine-audit, 3 protocols, 2 events, 1 concept)
- **Pages skipped**: 0 markdown files with content (all empty subdirs + openclaw system docs)
- **Pages kept as archive with disclaimer**: 2 (log, machine-audit)
