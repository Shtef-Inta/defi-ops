# defi-ops Agent Bootstrap

This file is the repo-level entry point for Codex, Claude, Kimi, Claw, and other coding agents.

## Startup Order

1. Read `CLAUDE.md`.
2. Read `KIMI.md` if the current worker is Kimi/Kimi Claw, or if the worker needs concise operating rules.
3. Read `PLAN.md` only far enough to identify the next unchecked task.
4. Read `wiki/hot.md` for current market/research context.
5. Read only the source and test files required for the next task.

Do not scan old projects, archives, or the whole wiki unless the current task explicitly requires it.

## Persistent Memory Rule

The model is not trusted to remember operational preferences across fresh sessions. Persistent memory lives in files:

- `CLAUDE.md` for project context and hard rules.
- `KIMI.md` for Kimi/Kimi Claw operating style.
- `PLAN.md` for the current implementation queue.
- `wiki/` for the Karpathy semantic library.
- `state/ops.sqlite` for pipeline runtime memory.

If a session learns something durable, write it into the appropriate project file. Do not rely on chat memory.

## Execution Rule

Work one unchecked `PLAN.md` task at a time. Finish with checks. Do not call an intermediate state done.

## Safety Rule

No Telegram send, live API spending, wallet mutation, signing, onchain action, trade, swap, transfer, or private-key handling without separate explicit approval from the user.

