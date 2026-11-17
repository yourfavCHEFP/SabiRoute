#!/usr/bin/env bash
# R7 Tranche D2 — local disposable PostgreSQL backup/restore helper.
# WRITTEN, NOT RUN. Never point this at a managed or production database.
set -euo pipefail

: "${PGHOST:?PGHOST must be set to a disposable local host}"
: "${PGPORT:=5432}"
: "${PGUSER:?PGUSER must be set}"
: "${PGDATABASE:?PGDATABASE must be a disposable local database}"
: "${BACKUP_FILE:?BACKUP_FILE must be set}"

action="${1:-backup}"

case "$action" in
  backup)
    pg_dump --format=custom --file="$BACKUP_FILE" "$PGDATABASE"
    ;;
  restore)
    pg_restore --clean --if-exists --dbname="$PGDATABASE" "$BACKUP_FILE"
    ;;
  *)
    echo "usage: $0 {backup|restore}" >&2
    exit 2
    ;;
esac
