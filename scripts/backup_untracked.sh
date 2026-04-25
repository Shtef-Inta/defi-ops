#!/bin/bash
# Backup all untracked files before dangerous git operations
set -e
REPO_ROOT="$(git rev-parse --show-toplevel)"
BACKUP_DIR="${REPO_ROOT}/state/backups"
mkdir -p "$BACKUP_DIR"
TS=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/untracked_backup_${TS}.tar.gz"

cd "$REPO_ROOT"
UNTRACKED=$(git ls-files --others --exclude-standard)
if [ -z "$UNTRACKED" ]; then
    echo "No untracked files to backup."
    exit 0
fi

echo "$UNTRACKED" | tar -czf "$BACKUP_FILE" -T -
echo "Backup created: $BACKUP_FILE ($(echo "$UNTRACKED" | wc -l | xargs) files)"
