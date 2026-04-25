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


## Disaster Prevention (post 2026-04-25 git clean incident)

### Hard Rules
1. **NEVER run `git clean -fd` without backup.** It deletes untracked files irreversibly.
2. **Always run `./scripts/backup_untracked.sh` before any destructive git operation.**
3. **Use `./scripts/safety_git_clean.py` instead of raw `git clean`.** It forces dry-run + backup + typed confirmation.
4. **Commit early, commit often.** New src/ modules must be committed within 1 hour of creation.
5. **State files (.session, .log, .sqlite) are NEVER committed.** Pre-commit hook enforces this.

### Recovery
- Untracked backups live in `state/backups/untracked_backup_YYYYMMDD_HHMMSS.tar.gz`
- If GitHub is ahead of local: `git fetch origin && git reset --hard origin/main` (only after backup)
- If local has uncommitted work: `git stash` or `./scripts/backup_untracked.sh` before any reset.
