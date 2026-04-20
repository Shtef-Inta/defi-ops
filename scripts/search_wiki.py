#!/usr/bin/env python3
"""Simple search over wiki pages (grep-like, case-insensitive)."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def search(query: str, wiki_dir: Path) -> list[tuple[Path, int, str]]:
    results: list[tuple[Path, int, str]] = []
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    for path in wiki_dir.rglob("*.md"):
        for i, line in enumerate(path.read_text().splitlines(), 1):
            if pattern.search(line):
                results.append((path, i, line.strip()))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Search wiki pages")
    parser.add_argument("query", help="Search string")
    args = parser.parse_args()

    wiki_dir = Path(__file__).parent.parent / "wiki"
    results = search(args.query, wiki_dir)

    if not results:
        print(f'No matches for "{args.query}"')
        return 1

    print(f'{len(results)} match(es) for "{args.query}":\n')
    for path, line_no, line in results:
        rel = path.relative_to(wiki_dir)
        print(f"{rel}:{line_no}: {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
