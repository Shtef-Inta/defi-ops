---
type: concept
last_updated: 2026-04-20
---

# Risk Overlay — PeckShield

Сквозной блокирующий слой: любое упоминание `theft|drain|exploit|halt|compromise` от @peckshieldalert — автоматический hold на связанных маршрутах до independent clearance.

## Почему это работает так

- PeckShield — независимый security feed, не marketing
- Используется как **negative evidence gate**, не как positive signal
- Если инцидент affects наш watched protocol — route sheets этого протокола переводятся в `BLOCKED_BY_RISK` lane до: (1) официального postmortem, (2) подтверждения что кошельки/код пофикшены

## Реализация (планируется)

- Фаза C.3 в `PHASE_4_PLAN.md`: `scripts/apply_risk_overlay.py`
- Связывает risk sentences из `raw/x/peckshieldalert-*` с protocols через mention
- Adds `riskOverlayActive=true` в cluster → gate D.2 fails → no recommendation

## Текущий статус

- Захват от 2026-04-17 содержит @peckshieldalert items (TBD — посмотреть что конкретно)
- Пока не attached к конкретному протоколу из watchlist

## Cross-refs

- [[protocols/aave]], [[protocols/uniswap]], [[protocols/ethena]] (потенциально affected)
- [[concepts/governance]]
