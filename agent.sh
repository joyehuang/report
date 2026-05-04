#!/usr/bin/env bash
# agent.sh — Auto-commit and push any changes in the report repo.
# Usage: ./agent.sh ["commit message"]

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_DIR"

# Check if there are any changes
if git diff --quiet && git diff --cached --quiet; then
    echo "No changes to commit."
    exit 0
fi

MSG="${1:-$(date '+%Y-%m-%d %H:%M:%S') update}"

git add -A
git commit -m "$MSG"
git push origin main

echo "Pushed: $MSG"
