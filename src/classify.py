"""Classify: event-unit clustering, voice-weighted confirmation, contradiction."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional


def _parse_yaml_value(val: str):
    """Parse a simple YAML value: string, inline list, or empty."""
    val = val.strip()
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1]
        if not inner.strip():
            return []
        parts = []
        for part in inner.split(","):
            part = part.strip().strip('"').strip("'")
            if part:
                parts.append(part)
        return parts
    return val


def _parse_watchlist(text: str) -> list[dict]:
    """Extract protocols list from watchlist YAML (stdlib parser)."""
    protocols: list[dict] = []
    in_protocols = False
    current_proto: dict | None = None
    current_list_key: str | None = None
    current_list: list[str] = []
    current_dict_key: str | None = None
    current_dict: dict[str, list[str]] = {}
    dict_indent = 0

    for raw in text.splitlines():
        line = raw.rstrip("\n")
        stripped = line.lstrip(" ")
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))

        if stripped == "protocols:":
            in_protocols = True
            continue

        if in_protocols and indent == 0:
            break

        if not in_protocols:
            continue

        # new protocol entry
        if indent == 2 and stripped.startswith("- "):
            if current_proto:
                if current_dict_key:
                    current_proto[current_dict_key] = current_dict
                    current_dict_key = None
                    current_dict = {}
                if current_list_key:
                    current_proto[current_list_key] = current_list
                    current_list_key = None
                    current_list = []
                protocols.append(current_proto)
            current_proto = {}
            current_dict_key = None
            current_dict = {}
            current_list_key = None
            current_list = []
            rest = stripped[2:].strip()
            if ":" in rest:
                k, _, v = rest.partition(":")
                current_proto[k.strip()] = _parse_yaml_value(v)
            continue

        if current_proto is None:
            continue

        # close any open nested dict when indent drops back
        if current_dict_key and indent <= dict_indent:
            current_proto[current_dict_key] = current_dict
            current_dict_key = None
            current_dict = {}

        # close any open list when indent drops back
        if current_list_key and indent <= 4 and not stripped.startswith("- "):
            current_proto[current_list_key] = current_list
            current_list_key = None
            current_list = []

        # indent 4 keys inside a protocol
        if indent == 4 and ":" in stripped:
            k, _, v = stripped.partition(":")
            key = k.strip()
            val = _parse_yaml_value(v)
            if val == "" or val == []:
                # could be start of a nested dict or a list
                current_list_key = None
                current_list = []
                current_dict_key = key
                current_dict = {}
                dict_indent = indent
            else:
                current_proto[key] = val
            continue

        # indent 6: list items or dict values
        if indent == 6 and current_dict_key and ":" in stripped:
            k, _, v = stripped.partition(":")
            dkey = k.strip()
            dval = _parse_yaml_value(v)
            if dval == "" or dval == []:
                # start of a list under dict key
                current_dict[dkey] = []
                current_list_key = f"__dictlist__{dkey}"
                current_list = []
            elif isinstance(dval, list):
                current_dict[dkey] = dval
            else:
                current_dict[dkey] = [dval]
            continue

        if indent == 8 and current_list_key and current_list_key.startswith("__dictlist__"):
            if stripped.startswith("- "):
                item = stripped[2:].strip().strip('"').strip("'")
                current_list.append(item)
                dkey = current_list_key.replace("__dictlist__", "")
                current_dict[dkey] = current_list
            continue

        if indent == 6 and current_list_key and stripped.startswith("- "):
            item = stripped[2:].strip().strip('"').strip("'")
            current_list.append(item)
            current_proto[current_list_key] = current_list
            continue

    if current_proto:
        if current_dict_key:
            current_proto[current_dict_key] = current_dict
        if current_list_key and not current_list_key.startswith("__dictlist__"):
            current_proto[current_list_key] = current_list
        protocols.append(current_proto)

    return protocols


def _load_watchlist(path: Optional[str] = None) -> list[dict]:
    if path:
        text = Path(path).read_text()
    else:
        text = (Path(__file__).parent.parent / "config" / "watchlist.yaml").read_text()
    return _parse_watchlist(text)


# ---------------------------------------------------------------------------
# Event key extractor
# ---------------------------------------------------------------------------


def extract_event_key(text: str, watchlist_text: Optional[str] = None) -> tuple[str | None, str | None]:
    """Return (protocol, event_key) for a signal text, or (None, None)."""
    protocols = _parse_watchlist(watchlist_text) if watchlist_text else _load_watchlist()
    if not protocols:
        return (None, None)

    lower_text = text.lower()
    matched_proto: dict | None = None
    best_alias_len = 0

    for proto in protocols:
        aliases = proto.get("aliases", [])
        if isinstance(aliases, str):
            aliases = [aliases]
        for alias in aliases:
            if alias.lower() in lower_text:
                if len(alias) > best_alias_len:
                    best_alias_len = len(alias)
                    matched_proto = proto

    if matched_proto is None:
        return (None, None)

    proto_name = matched_proto.get("name", "unknown")
    event_keywords = matched_proto.get("event_keywords", {})
    if not isinstance(event_keywords, dict):
        return (proto_name, None)

    matched_keyword = None

    for keyword, triggers in event_keywords.items():
        if not isinstance(triggers, list):
            triggers = [triggers]
        for trigger in triggers:
            if trigger.lower() in lower_text:
                matched_keyword = keyword
                break
        if matched_keyword:
            break

    if matched_keyword is None:
        return (proto_name, None)

    suffix = _extract_suffix(text, matched_proto)
    event_key = f"{proto_name}_{matched_keyword}" + (f"_{suffix}" if suffix else "")
    return (proto_name, event_key)


def _extract_suffix(text: str, proto: dict) -> str | None:
    lower = text.lower()
    # Version suffix
    m = re.search(r"\bv(\d+)\b", lower)
    if m:
        return f"v{m.group(1)}"

    # Token/asset suffix from aliases (excluding the protocol name itself)
    proto_name = proto.get("name", "").lower()
    aliases = proto.get("aliases", [])
    if isinstance(aliases, str):
        aliases = [aliases]
    for alias in aliases:
        al = alias.lower()
        if al != proto_name and al in lower:
            # normalize: remove spaces/dashes
            safe = re.sub(r"[^a-z0-9]", "", al)
            return safe

    # Network suffix
    for net in ("l2", "mainnet", "arbitrum", "optimism", "base"):
        if net in lower:
            return net

    return None


# ---------------------------------------------------------------------------
# Clustering
# ---------------------------------------------------------------------------


def classify_signals(db_path: Optional[str] = None) -> dict:
    """Fill event_key for unclassified signals and build/update clusters."""
    from src.db import get_conn

    conn = get_conn(db_path)
    protocols = _load_watchlist()

    # Step 1: extract event keys
    rows = conn.execute(
        "SELECT id, content FROM signals WHERE event_key IS NULL"
    ).fetchall()

    for row in rows:
        sid, content = row
        proto, event_key = extract_event_key(content or "")
        if event_key:
            conn.execute(
                "UPDATE signals SET protocol = ?, event_key = ? WHERE id = ?",
                (proto, event_key, sid),
            )

    conn.commit()

    # Step 2: cluster signals
    _build_clusters(conn)
    conn.commit()
    conn.close()
    return {"classified": len(rows)}


def _build_clusters(conn) -> None:
    """Group signals by (protocol, event_key) into 48h clusters."""
    rows = conn.execute(
        """
        SELECT s.id, s.protocol, s.event_key, s.captured_at, s.source_family
        FROM signals s
        WHERE s.event_key IS NOT NULL
          AND s.id NOT IN (SELECT signal_id FROM cluster_signals)
        ORDER BY s.captured_at
        """
    ).fetchall()

    for sid, protocol, event_key, captured_at, family in rows:
        # Find an existing cluster for this (protocol, event_key) within 48h
        cluster = conn.execute(
            """
            SELECT id, window_end, aspects FROM clusters
            WHERE protocol = ? AND event_key = ?
              AND datetime(window_end) >= datetime(?, '-2 days')
            ORDER BY window_end DESC
            LIMIT 1
            """,
            (protocol, event_key, captured_at),
        ).fetchone()

        if cluster:
            cid, window_end, aspects_json = cluster
            # Update window_end if this signal is later
            if captured_at > window_end:
                conn.execute(
                    "UPDATE clusters SET window_end = ? WHERE id = ?",
                    (captured_at, cid),
                )
            # Update aspects
            import json

            aspects = json.loads(aspects_json) if aspects_json else []
            if family not in aspects:
                aspects.append(family)
                conn.execute(
                    "UPDATE clusters SET aspects = ? WHERE id = ?",
                    (json.dumps(aspects), cid),
                )
            conn.execute(
                "INSERT INTO cluster_signals (cluster_id, signal_id) VALUES (?, ?)",
                (cid, sid),
            )
        else:
            import json

            conn.execute(
                """
                INSERT INTO clusters (protocol, event_key, window_start, window_end, aspects)
                VALUES (?, ?, ?, ?, ?)
                """,
                (protocol, event_key, captured_at, captured_at, json.dumps([family])),
            )
            cid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute(
                "INSERT INTO cluster_signals (cluster_id, signal_id) VALUES (?, ?)",
                (cid, sid),
            )
