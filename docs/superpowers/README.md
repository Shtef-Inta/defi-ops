# Superpowers (Kimi CLI Edition)

> Local alternative to `orba/superpowers` plugin for Claude Code.  
> Native subagent-driven development using Kimi Code CLI `Agent` tool.

## Workflow

```
idea → brainstorm → spec → plan → subagent task → review → verify → done
```

## Directories

| Path | Purpose |
|---|---|
| `docs/superpowers/specs/` | Design specs from brainstorming |
| `docs/superpowers/plans/` | Implementation plans per spec |
| `docs/superpowers/reviews/` | Code review reports from subagents |

## Skills

| Skill | Trigger | What it does |
|---|---|---|
| `brainstorming` | "let's design X" | Writes spec to `specs/` |
| `writing-plans` | "plan implementation of X" | Writes plan to `plans/` |
| `subagent-driven-development` | "execute plan X" | Runs coder agent + review agent per task |
| `verification-before-completion` | "verify task X" | Final check before marking done |

## Usage

```bash
# 1. Brainstorm → spec
kimi-cli agent --skill docs/superpowers/skills/brainstorming "Add wallet divergence alerts"

# 2. Plan → plan file
kimi-cli agent --skill docs/superpowers/skills/writing-plans "specs/wallet-divergence-spec.md"

# 3. Execute via subagents
kimi-cli agent --skill docs/superpowers/skills/subagent-driven-development "plans/wallet-divergence-plan.md"
```

## Rules

- Each task ≤400 lines of code (split if larger).
- Review agent runs after every task.
- No financial actions without explicit `--approve-send`.
- All changes tracked in git.
