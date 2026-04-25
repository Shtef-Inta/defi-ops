"""Cross-source analysis: cluster + wallets + liquidity + risk → broker brief data."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from src.db import get_conn
from src.liquidity import fetch_protocol_tvl, is_liquidity_verified


def _fetch_cluster_signals(conn: sqlite3.Connection, cluster_id: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT s.source_family, s.source_handle, s.content, s.sentiment, s.captured_at, s.url
        FROM signals s
        JOIN cluster_signals cs ON cs.signal_id = s.id
        WHERE cs.cluster_id = ?
        ORDER BY s.captured_at DESC
        """,
        (cluster_id,),
    ).fetchall()
    return [
        {
            "source_family": r[0],
            "source_handle": r[1],
            "content": r[2],
            "sentiment": r[3],
            "captured_at": r[4],
            "url": r[5],
        }
        for r in rows
    ]


_TOKEN_MAP: dict[str, list[str]] = {
    "aave": ["AAVE"],
    "uniswap": ["UNI"],
    "ethena": ["USDe", "sUSDe", "ENA"],
    "pendle": ["PENDLE"],
    "morpho": ["MORPHO"],
    "lido": ["stETH", "wstETH"],
    "hyperliquid": ["HYPE"],
    "fluid": ["FLUID"],
    "compound": ["COMP"],
    "curve": ["CRV", "crvUSD"],
    "sky": ["USDS", "SKY"],
    "spark": ["SPK"],
    "eigenlayer": ["EIGEN"],
    "gearbox": ["GEAR"],
    "balancer": ["BAL"],
    "gmx": ["GMX"],
    "dydx": ["DYDX"],
    "jupiter": ["JUP"],
}


def _fetch_wallet_confirmation(conn: sqlite3.Connection, protocol: str, hours: int = 24) -> dict | None:
    symbols = _TOKEN_MAP.get(protocol.lower(), [protocol.upper()])
    placeholders = ",".join("?" * len(symbols))

    row = conn.execute(
        f"""
        SELECT tracked_address, token_symbol, block_time
        FROM token_transfers
        WHERE tracked_address IN (
            SELECT address FROM wallet_tx WHERE wallet_group IN ('smart_money', 'cex_hotwallets')
        )
          AND token_symbol IN ({placeholders})
          AND datetime(block_time) >= datetime('now', '-{hours} hours')
        ORDER BY block_time DESC
        LIMIT 1
        """,
        symbols,
    ).fetchone()

    if row:
        return {
            "confirmed": True,
            "tx_count": 1,
            "latest": {
                "group": "smart_money",
                "tx_type": "token_transfer",
                "counterparties": row["token_symbol"],
                "block_time": row["block_time"],
            },
        }
    return None


def _has_risk_activity_for_protocol(conn: sqlite3.Connection, protocol: str, hours: int = 24) -> list[str]:
    flags: list[str] = []
    symbols = _TOKEN_MAP.get(protocol.lower(), [protocol.upper()])
    placeholders = ",".join("?" * len(symbols))

    row = conn.execute(
        f"""
        SELECT 1 FROM token_transfers
        WHERE tracked_address IN (
            SELECT address FROM wallet_tx WHERE wallet_group = 'risk_wallets'
        )
          AND token_symbol IN ({placeholders})
          AND datetime(block_time) >= datetime('now', '-{hours} hours')
        LIMIT 1
        """,
        symbols,
    ).fetchone()
    if row:
        flags.append("risk_wallet_active")

    like_pattern = f"%{protocol}%"
    row2 = conn.execute(
        """
        SELECT 1 FROM signals
        WHERE source_family = 'risk_overlay'
          AND (protocol = ? OR content LIKE ? OR asset_symbols LIKE ?)
          AND datetime(captured_at) >= datetime('now', '-6 hours')
        LIMIT 1
        """,
        (protocol, like_pattern, like_pattern),
    ).fetchone()
    if row2:
        flags.append("risk_overlay_alert")

    return flags


def _detect_contradiction(signals: list[dict], min_each_side: int = 2) -> tuple[bool, str | None]:
    _credible = {"official", "research", "aggregator", "governance", "onchain_analytics"}

    handle_sentiments: dict[str, list[str]] = {}
    for s in signals:
        if s.get("source_family") not in _credible:
            continue
        handle = s.get("source_handle") or s.get("source_family", "unknown")
        handle_sentiments.setdefault(handle, []).append(s.get("sentiment", "neutral"))

    bullish_handles = []
    bearish_handles = []
    for handle, sentiments in handle_sentiments.items():
        bullish_count = sentiments.count("bullish")
        bearish_count = sentiments.count("bearish")
        if bullish_count > bearish_count:
            bullish_handles.append(handle)
        elif bearish_count > bullish_count:
            bearish_handles.append(handle)

    if len(bullish_handles) >= min_each_side and len(bearish_handles) >= min_each_side:
        return True, f"bullish from {bullish_handles[:3]} vs bearish from {bearish_handles[:3]}"
    return False, None


_NATIVE_LIQUID = {"eth", "usdc", "usdt", "dot", "sol", "weth", "link", "trx", "eurc", "paxg"}


def _compute_action(
    contradiction: bool,
    risk_flags: list[str],
    liquidity_ok: bool,
    voice_weight: float,
    wallet_conf: dict | None,
    protocol: str = "",
) -> str:
    if risk_flags:
        return "избегать"
    if contradiction:
        return "ждать"
    if not liquidity_ok and protocol.lower() not in _NATIVE_LIQUID:
        return "ждать"
    if voice_weight >= 2.5:
        return "готовить вход"
    if voice_weight >= 1.5:
        return "наблюдать"
    return "ждать"


def _compute_capital_stance(action: str, protocol: str, tvl: dict | None) -> dict:
    portfolio = 100_000
    tvl_usd = tvl.get("tvl", 0) if tvl else 0

    if action == "готовить вход":
        if tvl_usd > 1_000_000_000:
            deploy = 15_000
        elif tvl_usd > 100_000_000:
            deploy = 10_000
        else:
            deploy = 5_000
        return {
            "deploy_now_usd": deploy,
            "keep_waiting_usd": portfolio - deploy,
            "reason": f"{protocol.upper()} имеет подтверждение из нескольких источников + onchain активность. TVL ${tvl_usd/1e9:.1f}B даёт уверенность в ликвидности.",
            "next_trigger": "Подтверждение цены входа и отсутствие новых risk-сигналов в ближайшие 2-4 часа.",
        }
    if action == "наблюдать":
        return {
            "deploy_now_usd": 0,
            "keep_waiting_usd": portfolio,
            "reason": f"Сигнал на {protocol.upper()} есть, но недостаточно подтверждений для немедленного входа.",
            "next_trigger": "Появление wallet-подтверждения или закрытие гэпа в данных.",
        }
    if action == "ждать":
        return {
            "deploy_now_usd": 0,
            "keep_waiting_usd": portfolio,
            "reason": "Сигнал слабый или единичный. Ранний этап формирования события.",
            "next_trigger": "Дополнительные источники подтверждают событие.",
        }
    return {
        "deploy_now_usd": 0,
        "keep_waiting_usd": portfolio,
        "reason": "Противоречия, risk-флаги или недостаточная ликвидность. Капитал вне рынка.",
        "next_trigger": "Разрешение противоречий и исчезновение risk-флагов.",
    }


def analyze_clusters(db_path: Optional[str] = None, max_items: int = 5, contradiction_threshold: int = 2, ignore_contradiction: bool = False) -> list[dict]:
    conn = get_conn(db_path)

    rows = conn.execute(
        """
        SELECT c.id, c.protocol, c.event_key, c.aspects, c.voice_weight,
               c.fusion_score, c.conviction,
               c.contradiction_flag, c.contradiction_reason, c.created_at
        FROM clusters c
        WHERE c.status = 'open'
        ORDER BY c.voice_weight DESC, c.created_at DESC
        LIMIT ?
        """,
        (max_items * 3,),
    ).fetchall()

    analyses = []

    for row in rows:
        cid, protocol, event_key, aspects_json, voice_weight, fusion_score, conviction, contra_flag, contra_reason, created_at = row
        if not protocol:
            continue
        aspects = json.loads(aspects_json) if aspects_json else []
        signals = _fetch_cluster_signals(conn, cid)

        if not signals:
            continue

        liquidity_ok = is_liquidity_verified(protocol)
        tvl = fetch_protocol_tvl(protocol) if liquidity_ok else None

        wallet_conf = _fetch_wallet_confirmation(conn, protocol)

        risk_flags = _has_risk_activity_for_protocol(conn, protocol)

        has_contra, contra_detail = _detect_contradiction(signals, min_each_side=contradiction_threshold)
        if ignore_contradiction:
            has_contra = False
            contra_text = None
        elif contra_flag or has_contra:
            has_contra = True
            contra_text = contra_reason or contra_detail or "противоречивые сигналы"
        else:
            contra_text = None

        action = _compute_action(has_contra, risk_flags, liquidity_ok, voice_weight or 0, wallet_conf, protocol)

        stance = _compute_capital_stance(action, protocol, tvl)

        latest_contents = [s["content"][:200] for s in signals[:3]]
        what_happened = " | ".join(latest_contents)

        event_type = event_key.split("_")[1] if "_" in event_key else "event"
        why_map = {
            "launch": "Запуск нового продукта обычно приводит к притоку TVL и спросу на токен.",
            "freeze": "Приостановка функциональности создаёт панику и отток капитала.",
            "depeg": "Потеря привязки стейблкоина вызывает массовый вывод ликвидности.",
            "integration": "Интеграция с крупным партнёром открывает новый спрос и TVL.",
            "governance": "Гovernance-решения могут изменить экономику протокола и токеномику.",
            "tvl_milestone": "Преодоление TVL-порога привлекает внимание институциональных игроков.",
            "yield": "Высокий APY привлекает капитал, но часто сопровождается риском деpeg.",
            "vault": "Новый vault создаёт дополнительный utility для токена.",
            "volume": "Рост объёма торгов указывает на интерес и потенциальное движение цены.",
            "cap": "Увеличение капа позволяет большему капиталу войти = рост TVL.",
            "rate": "Изменение ставки влияет на arbitrage и спрос на stablecoin.",
            "anomaly": "Аномальный onflow может предшествовать крупному ценовому движению.",
            "whale": "Движение китов часто предшествует значительному изменению цены.",
        }
        why_moves = why_map.get(event_type, f"Событие типа '{event_type}' влияет на восприятие протокола и спрос на токен.")

        affected = [protocol.upper()]
        for s in signals:
            sym = s.get("asset_symbols")
            if sym and sym not in affected:
                affected.append(sym)

        confirmed = []
        not_confirmed = []
        fams = {s["source_family"] for s in signals}
        if "official" in fams:
            confirmed.append("официальный источник протокола")
        if "research" in fams:
            confirmed.append("аналитический источник")
        if "onchain_analytics" in fams:
            confirmed.append("onchain-данные (Arkham)")
        if wallet_conf and wallet_conf.get("confirmed"):
            confirmed.append("подтверждение через wallet-активность")
        if "aggregator" in fams and "official" not in fams:
            not_confirmed.append("нет прямого подтверждения от протокола")
        if not wallet_conf:
            not_confirmed.append("нет onchain-подтверждения через watched wallets")
        if not liquidity_ok:
            not_confirmed.append("недостаточная ликвидность (<$1M TVL)")

        if action == "готовить вход":
            entry_trigger = "Цена входа подтверждена, slippage <1%, газ в норме."
            exit_trigger = "Stop-loss -5% от входа или появление bearish сигнала от official source."
        elif action == "наблюдать":
            entry_trigger = "Появление wallet-подтверждения или второго credible source."
            exit_trigger = "Противоречие между sources или risk-сигнал."
        elif action == "ждать":
            entry_trigger = "Накопление 2+ credible sources + liquidity verified."
            exit_trigger = "Н/A — позиция ещё не открыта."
        else:
            entry_trigger = "Разрешение всех risk-флагов и противоречий."
            exit_trigger = "Н/A — вход запрещён risk-фильтром."

        leverage = {"HIGH": 3, "SPECULATIVE": 5, "MEDIUM": 2, "SINGLE": 1}.get(conviction, 1)
        from datetime import datetime, timedelta, timezone
        expiry = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d")

        from src.wiki_rag import search_wiki
        wiki_results = search_wiki(f"{protocol} {event_key}", top_k=2)

        analyses.append({
            "cluster_id": cid,
            "protocol": protocol,
            "event_key": event_key,
            "what_happened": what_happened,
            "why_moves_money": why_moves,
            "affected_assets": affected,
            "confirmed_by": confirmed,
            "not_confirmed": not_confirmed,
            "action_now": action,
            "trigger_for_entry": entry_trigger,
            "trigger_for_exit": exit_trigger,
            "liquidity": tvl,
            "wallet_confirmation": wallet_conf,
            "risk_flags": risk_flags,
            "contradiction_reason": contra_text if has_contra else None,
            "capital_stance": stance,
            "signals_count": len(signals),
            "source_families": list(fams),
            "voice_weight": voice_weight or 0,
            "fusion_score": fusion_score or 0,
            "conviction": conviction or "SINGLE",
            "leverage": leverage,
            "expiry": expiry,
            "wiki_context": wiki_results,
            "created_at": created_at,
        })

        if len(analyses) >= max_items:
            break

    conn.close()
    return analyses
