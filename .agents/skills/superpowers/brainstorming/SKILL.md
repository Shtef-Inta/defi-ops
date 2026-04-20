# Skill: brainstorming

## Purpose
Transform a vague idea into a concrete design spec through dialogue, then save it to `docs/superpowers/specs/`.

## When to use
- User says "let's add X", "we need Y", "what if we did Z?"
- Before any implementation planning.

## Steps
1. Ask clarifying questions (scope, constraints, priority).
2. Write a concise spec with:
   - **Goal** (1 sentence)
   - **Requirements** (must / should / nice-to-have)
   - **Interface** (functions, CLI flags, DB schema changes)
   - **Open questions** (what we don't know yet)
3. Save to `docs/superpowers/specs/<kebab-name>-spec.md`.

## Output format
```markdown
# Spec: <Name>

## Goal
...

## Requirements
- MUST: ...
- SHOULD: ...
- NICE: ...

## Interface
```python
def new_feature(...):
    ...
```

## Open Questions
- ...
```

## Example trigger
"Design a system that alerts when 3+ smart_money wallets outflow the same token within 1h."
