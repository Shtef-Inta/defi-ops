"""Long-running daemon process for defi-ops pipeline."""
from __future__ import annotations

import logging
import logging.handlers
import os
import signal
import sys
import time
from pathlib import Path
from typing import Optional
from datetime import datetime

from src.ingest import ingest_all
from src.classify import classify_signals
from src.analyze import analyze_clusters
from src.deliver import deliver_briefs
from src.brief import format_digest
from src.paper_trading import snapshot_positions, get_open_positions, close_position
from src.quality import open_positions_summary, open_positions_by_strategy
from src.telegram_alerts import send_daily_brief, send_trade_alert, send_error_alert
from src import technical_analysis as ta
from src import ta_webhook_server as webhook
from src import dashboard_server as dashboard

_shutdown = False
_pid_path: Optional[Path] = None


def _setup_logging(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(
        str(log_path), maxBytes=5 * 1024 * 1024, backupCount=3
    )
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    handler.setFormatter(formatter)
    logger = logging.getLogger(__name__)
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def _write_pid(pid_path: Path) -> None:
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    pid_path.write_text(str(os.getpid()))


def _remove_pid(pid_path: Path) -> None:
    try:
        pid_path.unlink()
    except FileNotFoundError:
        pass


def _sigterm_handler(signum: int, frame: Optional[object]) -> None:
    global _shutdown
    _shutdown = True
    logging.getLogger(__name__).info("SIGTERM received, shutting down...")


def _check_risk(db_path: Optional[str]) -> None:
    logger = logging.getLogger(__name__)
    try:
        positions = get_open_positions(db_path=db_path)
    except Exception as exc:
        logger.error("get_open_positions failed in risk check: %s", exc)
        return

    for pos in positions:
        pnl = pos.get("latest_pnl_pct")
        if pnl is None:
            continue
        price = pos.get("latest_price") or pos.get("entry_price")
        if price is None:
            continue
        if pnl <= -0.05:
            try:
                close_position(pos["id"], float(price), "stop_loss", db_path=db_path)
                logger.info(
                    "Closed position %s stop-loss %.2f%%", pos["id"], pnl * 100
                )
            except Exception as exc:
                logger.error("Failed to close position %s: %s", pos["id"], exc)
        elif pnl >= 0.15:
            try:
                close_position(pos["id"], float(price), "take_profit", db_path=db_path)
                logger.info(
                    "Closed position %s take-profit %.2f%%", pos["id"], pnl * 100
                )
            except Exception as exc:
                logger.error("Failed to close position %s: %s", pos["id"], exc)


def _run_pipeline(db_path: Optional[str]) -> None:
    logger = logging.getLogger(__name__)
    logger.info("Pipeline started")

    # Auto-discover new sources every cycle, auto-enable top candidates
    try:
        from scripts.discover_sources import (
            discover_twitter_mentions,
            discover_youtube_channels,
            discover_telegram_channels,
            save_discoveries,
            auto_enable_top_candidates,
        )
        discoveries = {
            "twitter": discover_twitter_mentions(db_path, min_mentions=5),
            "youtube": discover_youtube_channels(db_path),
            "telegram": discover_telegram_channels(db_path),
        }
        save_discoveries(discoveries)
        total = sum(len(v) for v in discoveries.values())
        if total > 0:
            logger.info("Auto-discovered %s new source candidates", total)
        enabled = auto_enable_top_candidates(top_n=5, min_score=2)
        for section, handles in enabled.items():
            if handles:
                logger.info("Auto-enabled %s %s sources: %s", len(handles), section, ", ".join(handles))
    except Exception as exc:
        logger.error("source_discovery failed: %s", exc)

    # Generate Uniswap + Aave trading report
    try:
        import subprocess
        import sys
        subprocess.run(
            [sys.executable, "scripts/uniswap_aave_trader.py"],
            capture_output=True,
            timeout=30,
            cwd=Path(__file__).parent.parent,
        )
        logger.info("Trading report generated")
    except Exception as exc:
        logger.error("trading_report failed: %s", exc)

    # Whale intelligence (run every ~2 hours to preserve API credits)
    try:
        state_dir = Path(__file__).parent.parent / "state"
        last_whale_path = state_dir / ".last_whale_run"
        should_run = True
        if last_whale_path.exists():
            last_run = float(last_whale_path.read_text().strip())
            if time.time() - last_run < 7200:
                should_run = False
        if should_run:
            env = os.environ.copy()
            env["ARKHAM_API_KEY"] = os.getenv("ARKHAM_API_KEY", "")
            env["ETHERSCAN_API_KEY"] = os.getenv("ETHERSCAN_API_KEY", "")
            subprocess.run(
                [sys.executable, "scripts/whale_intelligence_v2.py"],
                capture_output=True,
                timeout=120,
                cwd=Path(__file__).parent.parent,
                env=env,
            )
            last_whale_path.write_text(str(time.time()))
            logger.info("Whale intelligence updated")
            
            try:
                from src.whale_alerts import check_and_alert
                check_and_alert()
                logger.info("Whale alerts checked")
            except Exception as alert_exc:
                logger.error("whale_alerts failed: %s", alert_exc)
    except Exception as exc:
        logger.error("whale_intelligence failed: %s", exc)

    try:
        from src.macro import macro_summary
        macro = macro_summary()
        logger.info("Macro regime: %s | BTC.D: %.1f%% | Size adj: %.2fx", macro["regime"], macro["btc_dominance"], macro["size_adjustment"])
    except Exception as exc:
        logger.error("macro_summary failed: %s", exc)

    try:
        from src.yield_scanner import scan
        yield_result = scan()
        if yield_result.get("anomalies"):
            logger.info("Yield anomalies: %d", len(yield_result["anomalies"]))
    except Exception as exc:
        logger.error("yield_scan failed: %s", exc)

    try:
        ingest_all(db_path=db_path)
    except Exception as exc:
        logger.error("ingest_all failed: %s", exc)

    try:
        classify_signals(db_path=db_path)
    except Exception as exc:
        logger.error("classify_signals failed: %s", exc)

    # ── Three-strategy analysis ──
    strategies = {
        "conservative": {"threshold": 2, "ignore": False, "deliver": True},
        "aggressive": {"threshold": 1, "ignore": False, "deliver": False},
        "ultra": {"threshold": 2, "ignore": True, "deliver": False},
    }
    all_analyses: dict[str, list] = {}

    for name, cfg in strategies.items():
        try:
            analyses = analyze_clusters(
                db_path=db_path,
                max_items=5,
                contradiction_threshold=cfg["threshold"],
                ignore_contradiction=cfg["ignore"],
            )
            all_analyses[name] = analyses
            buy_count = sum(1 for a in analyses if a.get("action_now") == "готовить вход")
            logger.info("Strategy %s: %d analyses, %d BUY signals", name, len(analyses), buy_count)
        except Exception as exc:
            logger.error("analyze_clusters (%s) failed: %s", name, exc)
            all_analyses[name] = []

    # Build flat list of all analyses for delivery
    flat_analyses = []
    for name, analyses in all_analyses.items():
        for a in analyses:
            a["_strategy"] = name
            flat_analyses.append(a)

    # Auto-open paper positions for all three strategies with sizing
    newly_opened = []
    try:
        from src.paper_trading import open_position
        from src.prices import snapshot_prices, PROTOCOL_TO_COIN
        from src.sizing import suggest_size
        for name, analyses in all_analyses.items():
            existing = get_open_positions(db_path=db_path, strategy=name)
            open_protocols = {p["protocol"].lower() for p in existing}
            for a in analyses:
                if a.get("action_now") != "готовить вход":
                    continue
                proto = a["protocol"].lower()
                if proto in open_protocols:
                    continue
                coin_id = PROTOCOL_TO_COIN.get(proto)
                price_data = {}
                if coin_id:
                    price_data = snapshot_prices(db_path, [coin_id], max_age_minutes=5) or {}
                current_price = 0.0
                if coin_id and price_data.get(coin_id):
                    current_price = float(price_data[coin_id].get("usd", 0))
                if current_price <= 0:
                    logger.warning("Cannot open %s position for %s: no price available", name, proto)
                    continue
                size_data = suggest_size(a, bankroll=100_000, current_positions=existing)
                size = size_data.get("deploy_usd", a.get("capital_stance", {}).get("deploy_now_usd", 10000))
                leverage = a.get("leverage", 1)
                stop = current_price * 0.95
                target = current_price * 1.15
                pos_id = open_position(
                    cluster_id=a["cluster_id"],
                    protocol=a["protocol"],
                    decision="entered",
                    entry_price=current_price,
                    size_usd=size,
                    source_families=",".join(a.get("source_families", [])),
                    signals_count=a.get("signals_count", 0),
                    voice_weight=a.get("voice_weight", 0),
                    db_path=db_path,
                    strategy=name,
                    leverage=leverage,
                    stop_loss=stop,
                    take_profit=target,
                )
                open_protocols.add(proto)
                newly_opened.append(a)
                logger.info("Auto-opened %s paper position %s for %s at $%.6f (size $%.0f, leverage %dx)", name, pos_id, proto, current_price, size, leverage)
    except Exception as exc:
        logger.error("auto_open_position failed: %s", exc)

    # Send ONE consolidated daily brief
    try:
        from src.telegram_alerts import send_daily_brief, send_trade_alert
        positions = open_positions_by_strategy(db_path=db_path)
        result = send_daily_brief(flat_analyses, positions)
        if result.get("ok"):
            logger.info("Daily brief sent")
        else:
            logger.error("Daily brief failed: %s", result.get("error"))
        # Immediate alerts only for newly opened positions
        for a in newly_opened:
            try:
                send_trade_alert(a)
            except Exception as alert_exc:
                logger.error("Trade alert failed: %s", alert_exc)
    except Exception as exc:
        logger.error("telegram_delivery failed: %s", exc)

    try:
        snapshot_positions(db_path=db_path)
    except Exception as exc:
        logger.error("snapshot_positions failed: %s", exc)

    # Night mode: AI education refresh (3 AM)
    try:
        now = datetime.now()
        if 3 <= now.hour < 4:
            state_dir = Path(__file__).parent.parent / "state"
            last_ai_refresh = state_dir / ".last_ai_refresh"
            should_refresh = True
            if last_ai_refresh.exists():
                last_date = last_ai_refresh.read_text().strip()
                if last_date == now.strftime("%Y-%m-%d"):
                    should_refresh = False
            if should_refresh:
                logger.info("Night mode: refreshing AI education content")
                env = os.environ.copy()
                env["ARKHAM_API_KEY"] = os.getenv("ARKHAM_API_KEY", "")
                env["ETHERSCAN_API_KEY"] = os.getenv("ETHERSCAN_API_KEY", "")
                subprocess.run(
                    [sys.executable, "scripts/fetch_ai_channels.py"],
                    capture_output=True, timeout=600,
                    cwd=Path(__file__).parent.parent, env=env,
                )
                subprocess.run(
                    [sys.executable, "scripts/ai_likbez_builder.py"],
                    capture_output=True, timeout=120,
                    cwd=Path(__file__).parent.parent, env=env,
                )
                last_ai_refresh.write_text(now.strftime("%Y-%m-%d"))
                logger.info("AI education refresh completed")
    except Exception as exc:
        logger.error("ai_education_refresh failed: %s", exc)

    logger.info("Pipeline finished")


def start_daemon(
    db_path: Optional[str],
    interval_ingest: int = 600,
    interval_snapshot: int = 1800,
    interval_risk: int = 900,
) -> None:
    """Run the defi-ops pipeline in a long-lived loop."""
    global _shutdown, _pid_path
    _shutdown = False
    repo_root = Path(__file__).parent.parent
    state_dir = repo_root / "state"
    log_path = state_dir / "daemon.log"
    pid_path = state_dir / "daemon.pid"
    _pid_path = pid_path

    _setup_logging(log_path)
    logger = logging.getLogger(__name__)

    if pid_path.exists():
        try:
            old_pid = int(pid_path.read_text().strip())
            os.kill(old_pid, 0)
            logger.error("Daemon already running (pid %d)", old_pid)
            sys.exit(1)
        except (ValueError, ProcessLookupError, OSError):
            pass

    _write_pid(pid_path)
    signal.signal(signal.SIGTERM, _sigterm_handler)

    logger.info("Daemon started (pid %d)", os.getpid())

    # Start TradingView webhook server
    try:
        webhook.start_webhook_server(db_path=db_path)
    except Exception as exc:
        logger.error("Webhook server failed to start: %s", exc)

    # Start Arkham-style dashboard
    try:
        dashboard.start_dashboard_server(db_path=db_path)
    except Exception as exc:
        logger.error("Dashboard server failed to start: %s", exc)

    next_ingest = time.time()
    next_snapshot = time.time()
    next_risk = time.time()
    next_ta = time.time()

    try:
        while not _shutdown:
            now = time.time()
            if now >= next_risk:
                _check_risk(db_path)
                next_risk = now + interval_risk
            if now >= next_snapshot:
                try:
                    snapshot_positions(db_path=db_path)
                    logger.info("Snapshot taken")
                except Exception as exc:
                    logger.error("Snapshot failed: %s", exc)
                next_snapshot = now + interval_snapshot
            if now >= next_ta:
                try:
                    ta.run_ta_for_all(db_path=db_path)
                    inserted = ta.ingest_ta_as_signals(db_path=db_path)
                    if inserted:
                        logger.info("TA: inserted %d technical signals", inserted)
                except Exception as exc:
                    logger.error("Technical analysis failed: %s", exc)
                next_ta = now + 1800
            if now >= next_ingest:
                _run_pipeline(db_path)
                next_ingest = now + interval_ingest
            time.sleep(1)
    finally:
        _remove_pid(pid_path)
        logger.info("Daemon stopped")


def stop_daemon() -> None:
    """Send SIGTERM to the running daemon."""
    pid_path = Path(__file__).parent.parent / "state" / "daemon.pid"
    if not pid_path.exists():
        print("Daemon not running (no pid file)")
        return
    try:
        pid = int(pid_path.read_text().strip())
    except ValueError:
        print("Invalid pid file")
        pid_path.unlink()
        return
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"Sent SIGTERM to daemon (pid {pid})")
    except ProcessLookupError:
        print("Daemon not running, cleaning up pid file")
        pid_path.unlink()
    except OSError as exc:
        print(f"Failed to stop daemon: {exc}")


def status() -> str:
    """Return daemon status string."""
    pid_path = Path(__file__).parent.parent / "state" / "daemon.pid"
    if not pid_path.exists():
        return "Daemon not running"
    try:
        pid = int(pid_path.read_text().strip())
        os.kill(pid, 0)
        return f"Daemon running (pid {pid})"
    except (ValueError, ProcessLookupError, OSError):
        return "Daemon not running (stale pid file)"


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "start"
    if cmd == "start":
        db_path = sys.argv[2] if len(sys.argv) > 2 else None
        start_daemon(db_path=db_path)
    elif cmd == "stop":
        stop_daemon()
    elif cmd == "status":
        print(status())
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
