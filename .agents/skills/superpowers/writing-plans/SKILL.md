# Skill: writing-plans

## Purpose
Turn a spec into a step-by-step implementation plan with checkpoints.

## When to use
- After brainstorming produces a spec.
- Before any code is written.

## Steps
1. Read the spec from `docs/superpowers/specs/<name>-spec.md`.
2. Break into tasks (each ≤1 engineering day, ≤400 lines of code).
3. For each task define:
   - **Files to create/modify**
   - **Tests to add** (TDD required for classify/decide/wallets)
   - **Dependencies** (other tasks that must finish first)
4. Save to `docs/superpowers/plans/<name>-plan.md`.

## Output format
```markdown
# Plan: <Name>

## Task 1 — <Short title>
- **Files**: `src/x.py`, `tests/test_x.py`
- **Tests**: ...
- **Deps**: none

## Task 2 — ...
```

## Example trigger
"Write an implementation plan for specs/wallet-divergence-spec.md"
