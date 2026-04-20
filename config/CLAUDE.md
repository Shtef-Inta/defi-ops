# config/ — Level 2 Context

## Files

| File | Format | What it controls |
|--|--|--|
| `sources.yaml` | YAML (manual parse) | All handles/channels/feeds/wallets across 5 families |
| `watchlist.yaml` | YAML (manual parse) | 12 protocols × tier × event_keywords |
| `delivery.yaml` | YAML (manual parse) | Telegram chatId + topicId |
| `address_book.json` | JSON | Contract/wallet labels (Arkham fallback) |

## Rules

1. **Never commit credentials.** `.env` only, chmod 600.
2. **Sources.yaml is the single source of truth.** No other handle lists anywhere.
3. **Manual YAML parsing in code.** stdlib-only — no PyYAML dependency.
4. **Watchlist tiers:** `critical` (Aave, Uniswap), `important` (Ethena, Morpho), `monitored` (остальные).
5. **Event keywords** drive `classify.py` event_key extractor. Add new keywords here first.
