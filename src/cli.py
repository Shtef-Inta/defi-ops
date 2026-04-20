"""CLI entry point: ingest → classify → decide → deliver."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.config import load_env
from src.db import init_db


def cmd_run(args: argparse.Namespace) -> int:
    db_path = args.db or str(Path(__file__).parent.parent / "state" / "ops.sqlite")
    init_db(db_path).close()

    if not args.only or args.only == "ingest":
        from src.ingest import ingest_all

        print("[ingest] fetching all sources...")
        res = ingest_all(db_path)
        for src, stats in res.items():
            print(f"  {src}: {stats}")

    if not args.only or args.only == "classify":
        from src.classify import classify_signals

        print("[classify] extracting event keys and clustering...")
        stats = classify_signals(db_path)
        print(f"  classified: {stats['classified']}")

    if not args.only or args.only == "wallets":
        from src.wallets import classify_wallet_txs, detect_divergence, enrich_wallet_labels

        print("[wallets] classifying transactions...")
        stats = classify_wallet_txs(db_path)
        print(f"  classified: {stats['classified']}")

        print("[wallets] enriching Arkham labels...")
        stats = enrich_wallet_labels(db_path)
        print(f"  lookups: {stats['lookups']}, updated: {stats['updated']}")

        div = detect_divergence(db_path)
        if div:
            print(f"  divergence: {div}")

    if not args.only or args.only == "decide":
        from src.decide import build_cards

        print("[decide] building cards...")
        cards = build_cards(db_path, max_cards=args.max_cards)
        print(f"  cards: {len(cards)}")

        from src.deliver import deliver

        dry_run = not args.send
        results = deliver(cards, topic_id=args.topic, dry_run=dry_run, card_type=args.card_type)
        for r in results:
            print(f"  {r['cluster_id']}: {r['status']}")

    return 0


def main(argv: list[str] | None = None) -> int:
    load_env()
    parser = argparse.ArgumentParser(description="defi-ops pipeline")
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="run pipeline")
    run_p.add_argument("--only", choices=["ingest", "classify", "wallets", "decide"], help="run single stage")
    run_p.add_argument("--db", default=None, help="sqlite path")
    run_p.add_argument("--send", action="store_true", help="actually send to Telegram (default dry-run)")
    run_p.add_argument("--topic", default=None, help="Telegram topic ID")
    run_p.add_argument("--max-cards", type=int, default=5, help="max decision cards")
    run_p.add_argument("--card-type", default="decisions", help="delivery topic type (decisions/alerts/debug)")

    args = parser.parse_args(argv)
    if args.command == "run":
        return cmd_run(args)
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
