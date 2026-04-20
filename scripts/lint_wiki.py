#!/usr/bin/env python3
"""Health-check the wiki for orphans, broken links, stale pages, missing backlink sections."""
from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.S)
DATE_RE = re.compile(r"last_updated:\s*(\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}Z)?)")


def _wiki_dir() -> Path:
    return Path(__file__).parent.parent / "wiki"


def discover_pages(wiki_dir: Path) -> dict[str, Path]:
    """Index pages by title, relative path, and stem."""
    pages: dict[str, Path] = {}
    for path in wiki_dir.rglob("*.md"):
        # By title
        title = None
        for line in path.read_text().splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
        if not title:
            title = path.stem.replace("-", " ").replace("_", " ").title()
        pages[title] = path
        # By relative path without extension (Obsidian style)
        rel = str(path.relative_to(wiki_dir).with_suffix(""))
        pages[rel] = path
        pages[path.stem] = path
    return pages


def _extract_links(text: str) -> set[str]:
    return set(WIKILINK_RE.findall(text))


def _get_last_updated(text: str) -> datetime | None:
    m = DATE_RE.search(text)
    if m:
        date_str = m.group(1)
        if "T" in date_str:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)
        return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return None


def lint() -> dict:
    pages = discover_pages(_wiki_dir())
    forward: dict[str, set[str]] = {name: set() for name in pages}
    for name, path in pages.items():
        text = path.read_text()
        links = _extract_links(text)
        for link in links:
            if link in pages:
                forward[name].add(link)

    backlinks: dict[str, set[str]] = {name: set() for name in pages}
    for src, targets in forward.items():
        for tgt in targets:
            backlinks[tgt].add(src)

    now = datetime.now(timezone.utc)
    orphans = []
    broken = set()
    stale = []
    missing_backlinks = []
    missing_frontmatter = []

    seen_paths = set()
    for name, path in pages.items():
        if path in seen_paths:
            continue
        seen_paths.add(path)
        text = path.read_text()
        rel = str(path.relative_to(_wiki_dir()))

        # Skip schema/template files
        if rel == "CLAUDE.md":
            continue

        # Broken links
        for link in _extract_links(text):
            if link not in pages:
                broken.add((rel, link))

        # Orphans: pages with no inbound links (except index, hot, log, overview, stubs)
        if rel not in {"index.md", "hot.md", "log.md", "overview.md", "CLAUDE.md"}:
            keys_for_path = {k for k, v in pages.items() if v == path}
            has_backlinks = any(bool(backlinks.get(k)) for k in keys_for_path)
            if not has_backlinks:
                orphans.append(rel)

        # Stale
        lu = _get_last_updated(text)
        if lu and (now - lu).days > 30:
            stale.append((rel, lu.strftime("%Y-%m-%d")))

        # Missing backlinks section
        if "## Backlinks" not in text:
            missing_backlinks.append(rel)

        # Missing frontmatter
        if not FRONTMATTER_RE.search(text):
            missing_frontmatter.append(rel)

    return {
        "total_pages": len(pages),
        "orphans": orphans,
        "broken_links": sorted(broken),
        "stale": stale,
        "missing_backlinks": missing_backlinks,
        "missing_frontmatter": missing_frontmatter,
    }


def main() -> int:
    results = lint()
    print(f"Wiki lint: {results['total_pages']} pages total")
    if results["orphans"]:
        print(f"\n⚠️  Orphans ({len(results['orphans'])}):")
        for o in results["orphans"]:
            print(f"  - {o}")
    if results["broken_links"]:
        print(f"\n⚠️  Broken links ({len(results['broken_links'])}):")
        for src, tgt in results["broken_links"]:
            print(f"  - [[{tgt}]] in {src}")
    if results["stale"]:
        print(f"\n⚠️  Stale pages ({len(results['stale'])}):")
        for name, date in results["stale"]:
            print(f"  - {name} (last {date})")
    if results["missing_backlinks"]:
        print(f"\n⚠️  Missing backlinks section ({len(results['missing_backlinks'])}):")
        for name in results["missing_backlinks"]:
            print(f"  - {name}")
    if results["missing_frontmatter"]:
        print(f"\n⚠️  Missing frontmatter ({len(results['missing_frontmatter'])}):")
        for name in results["missing_frontmatter"]:
            print(f"  - {name}")

    total_issues = (
        len(results["orphans"])
        + len(results["broken_links"])
        + len(results["stale"])
        + len(results["missing_backlinks"])
        + len(results["missing_frontmatter"])
    )
    if total_issues == 0:
        print("\n✅ Wiki is healthy.")
        return 0
    print(f"\n{total_issues} issue(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
