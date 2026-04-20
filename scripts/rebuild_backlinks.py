#!/usr/bin/env python3
"""Rebuild ## Backlinks sections across a markdown wiki."""
from __future__ import annotations

import re
import sys
from pathlib import Path

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def _wiki_dir() -> Path:
    return Path(__file__).parent.parent / "wiki"


def discover_pages(wiki_dir: Path) -> dict[str, Path]:
    pages: dict[str, Path] = {}
    for path in wiki_dir.rglob("*.md"):
        title = None
        for line in path.read_text().splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
        if not title:
            title = path.stem.replace("-", " ").replace("_", " ").title()
        pages[title] = path
        rel = str(path.relative_to(wiki_dir).with_suffix(""))
        pages[rel] = path
        pages[path.stem] = path
    return pages


def extract_links(text: str) -> set[str]:
    return set(WIKILINK_RE.findall(text))


def rebuild_backlinks(wiki_dir: Path) -> None:
    pages = discover_pages(wiki_dir)
    # Build forward links
    forward: dict[str, set[str]] = {name: set() for name in pages}
    for name, path in pages.items():
        text = path.read_text()
        links = extract_links(text)
        for link in links:
            if link in pages:
                forward[name].add(link)

    # Invert to backlinks
    backlinks: dict[str, set[str]] = {name: set() for name in pages}
    for src, targets in forward.items():
        for tgt in targets:
            backlinks[tgt].add(src)

    # Write backlinks sections
    seen_paths = set()
    count = 0
    for name, path in pages.items():
        if path in seen_paths:
            continue
        seen_paths.add(path)
        text = path.read_text()
        # Remove existing ## Backlinks section only
        parts = re.split(r"\n## Backlinks\n", text, maxsplit=1)
        body = parts[0].rstrip("\n")

        # Collect all backlinks that point to this path (via any key)
        bl: set[str] = set()
        for k, v in pages.items():
            if v == path and backlinks.get(k):
                bl.update(backlinks[k])
        if bl:
            body += "\n\n## Backlinks\n\n"
            for src in sorted(bl):
                body += f"- [[{src}]]\n"

        path.write_text(body + "\n")
        count += 1

    print(f"Rebuilt backlinks for {count} pages in {wiki_dir}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <wiki-directory>")
        sys.exit(1)
    rebuild_backlinks(Path(sys.argv[1]))
