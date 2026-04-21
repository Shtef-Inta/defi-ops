# Superpowers (Kimi CLI Edition)

> Local alternative to `orba/superpowers` plugin for Claude Code.  
> Native subagent-driven development using Kimi Code CLI `Agent` tool.

## Workflow

```
idea → brainstorm → spec → plan → execute → review → verify → done
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
| `brainstorming` | "let's design X" | Writes spec to `specs/`, requires user approval before code |
| `writing-plans` | "plan implementation of X" | Writes detailed plan to `plans/` with bite-sized tasks |
| `executing-plans` | "execute plan X inline" | Batch execution with checkpoints (no subagents) |
| `subagent-driven-development` | "execute plan X via subagents" | Fresh coder agent per task + mandatory review agent |
| `verification-before-completion` | "verify task X" | Final check before marking done |

## Usage

```bash
# 1. Brainstorm → spec (user approval required before any code)
kimi-cli agent --skill .agents/skills/superpowers/brainstorming "Add wallet divergence alerts"

# 2. Plan → plan file
kimi-cli agent --skill .agents/skills/superpowers/writing-plans "specs/wallet-divergence-design.md"

# 3a. Execute via subagents (recommended)
kimi-cli agent --skill .agents/skills/superpowers/subagent-driven-development "plans/wallet-divergence-plan.md"

# 3b. Or execute inline
kimi-cli agent --skill .agents/skills/superpowers/executing-plans "plans/wallet-divergence-plan.md"
```

## Rules

- **Hard gate:** No code before design approval (brainstorming skill).
- **No placeholders:** Every plan step must have actual code/commands.
- **Each task ≤400 lines** of code (split if larger).
- **Review mandatory** between tasks in subagent mode.
- **No financial actions** without explicit `--approve-send`.
- **All changes tracked** in git.
