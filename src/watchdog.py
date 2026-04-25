#!/usr/bin/env python3
"""Watchdog: monitors daemon and other processes, restarts if needed."""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).parent.parent
PID_FILE = REPO / "state" / "daemon.pid"
LOG_FILE = REPO / "state" / "daemon.log"
INTERVAL = 60


def _is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _start_daemon():
    print("[watchdog] Starting daemon...")
    subprocess.Popen(
        [sys.executable, "src/daemon.py"],
        cwd=REPO,
        stdout=open(LOG_FILE, "a"),
        stderr=subprocess.STDOUT,
    )


def main():
    print("[watchdog] Started")
    while True:
        pid = None
        if PID_FILE.exists():
            try:
                pid = int(PID_FILE.read_text().strip())
            except ValueError:
                pass
        if pid is None or not _is_alive(pid):
            _start_daemon()
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
