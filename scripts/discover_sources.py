#!/usr/bin/env python3
"""Stub for source discovery. Original lost in git clean disaster."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional


def discover(db_path: Optional[str] = None) -> dict:
    """Return empty discovery result."""
    return {
        "new_channels": [],
        "new_handles": [],
        "sources_checked": 0,
        "note": "stub: original discover_sources.py was lost in git clean -fd",
    }


if __name__ == "__main__":
    result = discover()
    print(json.dumps(result, ensure_ascii=False, indent=2))
