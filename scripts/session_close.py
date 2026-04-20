#!/usr/bin/env python3
"""Close a Claude Code session: update hot.md, log.md, session-summaries.jsonl, memory.

Run manually at the end of a session:
    python scripts/session_close.py --tasks="Task 1.3 done" --blockers="none" --next="Task 1.4"

Or without args — opens $EDITOR for interactive input.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).parent.parent


def _append_session_summary(tasks: str, blockers: str, next_task: str) -> None:
    summaries = _repo_root() / "state" / "session-summaries.jsonl"
    summaries.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "session_id": datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tasks_done": tasks,
        "blockers": blockers,
        "next_task": next_task,
    }
    with summaries.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _append_memory(file_name: str, entry: dict) -> None:
    path = _repo_root() / "state" / "memory" / file_name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _update_log(tasks: str) -> None:
    log = _repo_root() / "wiki" / "log.md"
    if not log.exists():
        return
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entry = f"\n## [{stamp}] session | {tasks}\n- Сессия закрыта. См. `state/session-summaries.jsonl` для деталей.\n"
    with log.open("a", encoding="utf-8") as f:
        f.write(entry)


def _update_hot(tasks: str, blockers: str, next_task: str) -> None:
    hot = _repo_root() / "wiki" / "hot.md"
    if not hot.exists():
        return
    text = hot.read_text()
    session_block = (
        f"\n## Session State (auto-updated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}Z)\n\n"
        f"- **Done:** {tasks}\n"
        f"- **Blockers:** {blockers}\n"
        f"- **Next:** {next_task}\n"
    )
    if "## Session State" in text:
        text = text.split("## Session State")[0].rstrip("\n") + session_block
    else:
        parts = text.split("---", 2)
        if len(parts) >= 3:
            text = parts[0] + "---" + parts[1] + "---" + parts[2] + session_block
        else:
            text = text.rstrip("\n") + session_block
    hot.write_text(text)


def main() -> int:
    parser = argparse.ArgumentParser(description="Close Claude Code session")
    parser.add_argument("--tasks", default="", help="What was done this session")
    parser.add_argument("--blockers", default="none", help="Open blockers")
    parser.add_argument("--next", default="", help="Next planned task")
    parser.add_argument("--preference", default="", help="New operator preference to remember")
    parser.add_argument("--incident", default="", help="Incident to remember (what went wrong)")
    parser.add_argument("--fix", default="", help="How the incident was fixed")
    args = parser.parse_args()

    if not args.tasks:
        print("No --tasks provided. Use --tasks='...' or run interactively.")
        return 1

    _append_session_summary(args.tasks, args.blockers, args.next)
    _update_log(args.tasks)
    _update_hot(args.tasks, args.blockers, args.next)

    if args.preference:
        _append_memory(
            "preferences.jsonl",
            {
                "date": datetime.now(timezone.utc).isoformat(),
                "text": args.preference,
                "source": "session_close",
            },
        )
        print("Preference saved to state/memory/preferences.jsonl")

    if args.incident:
        _append_memory(
            "incidents.jsonl",
            {
                "date": datetime.now(timezone.utc).isoformat(),
                "text": args.incident,
                "fix": args.fix,
                "source": "session_close",
            },
        )
        print("Incident saved to state/memory/incidents.jsonl")

    print("Session closed. Memory updated: state/session-summaries.jsonl, wiki/log.md, wiki/hot.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
