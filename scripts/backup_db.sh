#!/bin/bash
DB_PATH="data/bodai.sqlite3"
BACKUP_DIR="backups"

mkdir -p "$BACKUP_DIR"
TS=$(date +"%Y-%m-%d_%H%M%S")

cp "$DB_PATH" "$BACKUP_DIR/bodai_$TS.sqlite3"

# Șterge backup-urile mai vechi de 14 zile
find "$BACKUP_DIR" -name "bodai_*.sqlite3" -type f -mtime +14 -delete
