"""Config loader: .env, sources.yaml, watchlist.yaml, delivery.yaml."""
from __future__ import annotations

import os
from pathlib import Path


def load_env(path: str | None = None) -> None:
    """Parse .env file and set os.environ (no python-dotenv dependency)."""
    if path is None:
        path = str(Path(__file__).parent.parent / ".env")
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and val:
                os.environ.setdefault(key, val)


def load_delivery(path: str | None = None) -> dict:
    """Parse delivery.yaml into a flat dict."""
    if path is None:
        path = str(Path(__file__).parent.parent / "config" / "delivery.yaml")
    p = Path(path)
    if not p.exists():
        return {}
    data: dict = {}
    current_section: str | None = None
    current_key: str | None = None

    for raw in p.read_text().splitlines():
        line = raw.rstrip("\n")
        stripped = line.lstrip(" ")
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))

        if stripped == "bot:":
            current_section = "bot"
            continue
        if stripped == "chat:":
            current_section = "chat"
            continue
        if stripped == "topics:":
            current_section = "topics"
            continue
        if stripped == "limits:":
            current_section = "limits"
            continue
        if stripped == "replies:":
            current_section = "replies"
            continue

        if current_section == "bot" and indent == 2 and ":" in stripped:
            k, _, v = stripped.partition(":")
            data[f"bot_{k.strip()}"] = v.strip().strip('"').strip("'")
            continue

        if current_section == "chat" and indent == 2 and ":" in stripped:
            k, _, v = stripped.partition(":")
            data[f"chat_{k.strip()}"] = v.strip().strip('"').strip("'")
            continue

        if current_section == "topics" and indent == 2 and stripped.endswith(":"):
            current_key = stripped.rstrip(":").strip()
            continue

        if current_section == "topics" and current_key and indent == 4 and ":" in stripped:
            k, _, v = stripped.partition(":")
            data[f"topic_{current_key}_{k.strip()}"] = v.strip().strip('"').strip("'")
            continue

        if current_section == "limits" and indent == 2 and ":" in stripped:
            k, _, v = stripped.partition(":")
            data[f"limit_{k.strip()}"] = v.strip().strip('"').strip("'")
            continue

        if current_section == "replies" and indent == 2 and ":" in stripped:
            k, _, v = stripped.partition(":")
            data[f"reply_{k.strip()}"] = v.strip().strip('"').strip("'")
            continue

    return data
