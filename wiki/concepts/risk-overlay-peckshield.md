---
type: concept
last_updated: 2026-04-21
---

# Risk Overlay — PeckShield

Сквозной блокирующий слой: любое упоминание `theft|drain|exploit|halt|compromise` от @peckshieldalert — автоматический hold на связанных маршрутах до independent clearance.

## Почему это работает так

- PeckShield — независимый security feed, не marketing
- Используется как **negative evidence gate**, не как positive signal
- Если инцидент affects наш watched protocol — decision cards этого протокола переводятся в `BLOCKED` lane до: (1) official postmortem, (2) подтверждения что кошельки/код пофикшены

## Реализация

- Реализуется в `src/classify.py` — contradiction detector + risk overlay gate
- Связывает risk sentences из ingest с protocols через mention / keyword matching
- Adds `contradiction_flag=true` + `risk_flags=["security_incident"]` в cluster
- Gate в `src/decide.py`: если `risk_flags` непустые и нет clearance → verdict `BLOCKED`

## Текущий статус

- Захват от 2026-04-17 содержит @peckshieldalert items (TBD — посмотреть что конкретно)
- Пока не attached к конкретному протоколу из watchlist
- Will be enforced starting Sprint 2 (classify)

## Backlinks

- [[Wiki Index]]
- [[Wiki Log]]
- [[index]]
- [[log]]

