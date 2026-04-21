---
name: subagent-driven-development
description: Execute a plan using isolated subagents - one coder per task + one reviewer after each task
---

# Subagent-Driven Development

Execute a plan using isolated subagents: one coder per task + one reviewer after each task.

## When to use
- A plan exists in `docs/superpowers/plans/`.
- Tasks are independent enough for isolated execution.

## Steps
1. Read the plan.
2. For each task in order (respect dependencies):
   a. Launch `coder` subagent with the task description.
   b. Wait for completion.
   c. Launch `reviewer` subagent to check the code.
   d. If review fails → fix → re-review.
   e. If review passes → commit.
3. After all tasks: run full test suite.

## Review Checklist (for reviewer agent)
- [ ] Code follows project style (≤400 lines per module).
- [ ] Tests added and passing.
- [ ] No hardcoded secrets.
- [ ] No financial actions without gate.
- [ ] Wiki / docs updated if needed.

## Remember
- Each task gets a fresh subagent with clean context.
- Review is mandatory between tasks.
- If a task fails review twice, escalate to human.
