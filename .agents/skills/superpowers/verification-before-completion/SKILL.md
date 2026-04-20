# Skill: verification-before-completion

## Purpose
Final sanity check before declaring a task or milestone done.

## When to use
- After review passes.
- Before telling the user "task is complete".

## Steps
1. Run full test suite (`pytest`).
2. Run wiki lint (`scripts/lint_wiki.py`).
3. Check git status — all changes committed?
4. Verify no files >400 lines.
5. If any check fails → fix → re-verify.

## Output
```markdown
# Verification Report: <Task>

| Check | Status |
|---|---|
| pytest | ✅ / ❌ |
| wiki lint | ✅ / ❌ |
| git clean | ✅ / ❌ |
| line limits | ✅ / ❌ |

## Blockers
- ... (if any)
```

## Example trigger
"Verify task 3 of wallet-divergence plan before completion"
