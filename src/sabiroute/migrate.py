"""Explicit migration entry point for SabiRoute schema.

Schema changes are applied ONLY through this module, never during normal
application startup. Run with: python -m sabiroute.migrate
"""
from __future__ import annotations

import os
import sys

from sqlalchemy import text

from sabiroute.security.store import (
    _connect,
    ensure_schema,
    ensure_schema_in_connection,
    resolve_schema_groups,
)

# Fixed, documented SabiRoute-specific advisory lock key (PostgreSQL).
# Used with pg_advisory_xact_lock(bigint) so the lock is transaction-scoped
# and released automatically on commit/rollback.
SABIROUTE_MIGRATION_LOCK_KEY = 0x534142524F555445  # "SABROUT E"-ish namespace
LOCK_TIMEOUT_SECONDS = 30


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL") or os.environ.get("SABIROUTE_DATABASE_URL")
    if not url:
        print("DATABASE_URL is required", file=sys.stderr)
        raise SystemExit(2)
    return url


def main() -> int:
    url = _database_url()
    engine = _connect(url, None)
    try:
        groups = resolve_schema_groups()
    except ValueError as exc:
        print(f"Migration failed: {exc}", file=sys.stderr)
        return 1
    dialect = engine.dialect.name
    try:
        if dialect == "postgresql":
            with engine.begin() as connection:
                connection.execute(
                    text(f"SET LOCAL lock_timeout = '{LOCK_TIMEOUT_SECONDS}s'")
                )
                connection.execute(
                    text("SELECT pg_advisory_xact_lock(:key)"),
                    {"key": SABIROUTE_MIGRATION_LOCK_KEY},
                )
                ensure_schema_in_connection(connection, engine, groups=groups)
        else:
            # SQLite: separate path, no advisory-lock guarantees.
            ensure_schema(engine, groups=groups)
    except Exception as exc:
        print(f"Migration failed: {exc}", file=sys.stderr)
        return 1
    print(f"Migrations applied (groups={groups}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
