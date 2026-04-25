#!/usr/bin/env python3
"""Safety wrapper for git clean. Prevents git clean -fd disasters."""
import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def _run_git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True)


def _backup_untracked():
    repo = Path.cwd()
    backup_dir = repo / "state" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"untracked_backup_{ts}.tar.gz"
    result = _run_git("ls-files", "--others", "--exclude-standard")
    untracked = [l for l in result.stdout.strip().split("\n") if l]
    if not untracked:
        return None, 0
    # Create tar of untracked files
    cmd = ["tar", "-czf", str(backup_path), "-C", str(repo)] + untracked
    subprocess.run(cmd, check=False)
    return backup_path, len(untracked)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--dry-run", action="store_true")
    parser.add_argument("-f", "--force", action="store_true")
    parser.add_argument("-d", action="store_true")
    parser.add_argument("-x", action="store_true")
    parser.add_argument("-e", "--exclude", action="append", default=[])
    parser.add_argument("path", nargs="*")
    args = parser.parse_args()

    # Always show what would be deleted first
    dry = _run_git("clean", "-ndX" if args.x else "-nd", *args.path)
    print("=== Untracked files that would be deleted ===")
    print(dry.stdout or "(none)")
    print("=" * 45)

    if args.dry_run:
        sys.exit(0)

    if not args.force:
        print("\nERROR: git clean without -f is blocked by safety wrapper.")
        print("Use:  python scripts/safety_git_clean.py -fd  (shows dry-run only)")
        print("Or:   git clean -fd  (if you really know what you're doing)")
        sys.exit(1)

    # Backup before delete
    backup_path, count = _backup_untracked()
    if backup_path:
        print(f"\nBACKUP CREATED: {backup_path} ({count} untracked files)")

    answer = input("\nType 'DELETE' to proceed with git clean -fd: ")
    if answer.strip() != "DELETE":
        print("Aborted.")
        sys.exit(1)

    # Run actual git clean
    cmd = ["git", "clean", "-fd"]
    if args.x:
        cmd.append("-x")
    for ex in args.exclude:
        cmd.extend(["-e", ex])
    cmd.extend(args.path)
    subprocess.run(cmd)


if __name__ == "__main__":
    main()
