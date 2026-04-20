#!/usr/bin/env python3
"""Cross-session handoff: restore context from session-summaries and memory."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).parent.parent


def _summaries_path() -> Path:
    return _repo_root() / "state" / "session-summaries.jsonl"


def _hot_path() -> Path:
    return _repo_root() / "wiki" / "hot.md"


def _memory_dir() -> Path:
    return _repo_root() / "state" / "memory"


def read_last_summaries(n: int = 3) -> list[dict]:
    path = _summaries_path()
    if not path.exists():
        return []
    lines = [l.strip() for l in path.read_text().splitlines() if l.strip() and not l.strip().startswith("#")]
    entries = []
    for line in lines[-n:]:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def read_memory(file_name: str) -> list[dict]:
    path = _memory_dir() / file_name
    if not path.exists():
        return []
    lines = [l.strip() for l in path.read_text().splitlines() if l.strip() and not l.strip().startswith("#")]
    entries = []
    for line in lines:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def check_hot_stale() -> bool:
    text = _hot_path().read_text()
    for line in text.splitlines():
        if line.startswith("last_updated:"):
            date_str = line.split(":", 1)[1].strip()
            try:
                lu = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                return (datetime.now(timezone.utc) - lu).total_seconds() > 86400
            except Exception:
                return True
    return True


def main() -> int:
    print("=== Session Start Handoff ===\n")

    summaries = read_last_summaries(3)
    if summaries:
        print("Last sessions:")
        for s in summaries:
            ts = s.get("timestamp", "?")[:19]
            tasks = s.get("tasks_done", "?")
            nxt = s.get("next_task", "?")
            print(f"  [{ts}] Done: {tasks} | Next: {nxt}")
        print()

    preferences = read_memory("preferences.jsonl")
    if preferences:
        print("Active preferences:")
        for p in preferences[-3:]:
            print(f"  - {p.get('text', '')}")
        print()

    incidents = read_memory("incidents.jsonl")
    if incidents:
        print("Recent incidents:")
        for i in incidents[-3:]:
            print(f"  [{i.get('date', '?')}] {i.get('text', '')}")
        print()

    if check_hot_stale():
        print("⚠️  wiki/hot.md is stale (>24h). Run: python scripts/session_close.py --tasks='...' --next='...'")
    else:
        print("✅ wiki/hot.md is fresh.")

    print("\n=== Ready to work ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
