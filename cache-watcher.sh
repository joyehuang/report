#!/usr/bin/env bash
# Watches ~/.hermes/state.db for modifications and regenerates cache.html
# Handles SQLite file replacement (new inode) by watching the parent directory too.
set -e

DB_DIR="$HOME/.hermes"
DB_FILE="$DB_DIR/state.db"
SCRIPT_DIR="/mnt/hermes-data/personal/report"

cd "$SCRIPT_DIR"

# Initial generation on startup
python3 generate_cache.py

# Watch both the file (modify) and the directory (create/move — for SQLite file replacement)
while true; do
    inotifywait -e modify,close_write "$DB_FILE" 2>/dev/null || \
    inotifywait -e create,moved_to -t 30 "$DB_DIR" 2>/dev/null || true
    [ -f "$DB_FILE" ] && python3 generate_cache.py
done
