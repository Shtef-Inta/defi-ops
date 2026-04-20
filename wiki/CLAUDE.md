# Wiki Schema — LLM Librarian Config

This is the schema file for the defi-ops wiki. It tells the LLM how to structure, maintain, and lint the wiki. Based on Karpathy's LLM Knowledge Base pattern.

## Three Layers

```
state/raw/          — immutable source payloads (x, youtube, rss, wallets, telegram)
wiki/               — LLM-generated markdown (you write and maintain this)
output/             — query results, reports, slides, charts (filed back into wiki)
```

## Directory Structure

| Directory | Content | Maintained By |
|--|--|--|
| `wiki/protocols/` | Per-protocol pages (aave.md, uniswap.md) | LLM |
| `wiki/events/` | Time-bound events (2026-04-aave-v4-deposits.md) | LLM |
| `wiki/concepts/` | Abstract ideas (risk-overlay.md, voice-weight.md) | LLM |
| `wiki/signals/` | Recurring signal definitions | LLM |
| `wiki/wallets/` | Watched wallet profiles | LLM |
| `wiki/index.md` | Catalog of all pages with one-line summaries | LLM |
| `wiki/log.md` | Append-only chronology of ingests and updates | LLM |
| `wiki/hot.md` | Active context cache (TTL 24h, rewrite fully) | LLM |

## Page Template

```markdown
---
type: protocol | event | concept | signal | wallet
last_updated: YYYY-MM-DDTHH:MMZ
sources:
  - state/raw/x/aave-20260421120000.json
---

# Title

## Summary

2-3 sentences capturing the essence.

## Details

Freeform markdown. Use bullet points for facts, bold for key numbers.
