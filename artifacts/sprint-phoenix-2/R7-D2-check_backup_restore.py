"""R7 Tranche D2 — backup/restore check against a disposable local PostgreSQL.

WRITTEN, NOT RUN. The filename deliberately avoids pytest collection: executing this check
requires an explicitly created local database and is not authorised by Row D.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "R7-D2-backup_restore.sh"


def _dsn() -> str:
    required = ("PGHOST", "PGUSER", "PGDATABASE")
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise SystemExit(f"missing required local-test env: {', '.join(missing)}")
    host = os.environ["PGHOST"]
    if host not in {"localhost", "127.0.0.1", "::1", "/tmp"}:
        raise SystemExit("refusing non-local PGHOST; managed databases are out of scope")
    return (
        f"host={host} port={os.environ.get('PGPORT', '5432')} "
        f"user={os.environ['PGUSER']} dbname={os.environ['PGDATABASE']}"
    )


def main() -> int:
    dsn = _dsn()
    with tempfile.TemporaryDirectory() as tmp:
        backup = str(Path(tmp) / "disposable.backup")
        env = {**os.environ, "BACKUP_FILE": backup}

        # The sentinel must exist at backup time: pg_restore --clean only drops objects
        # present in the archive, not arbitrary tables created after the dump.
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("DROP TABLE IF EXISTS restore_probe")
                cur.execute("CREATE TABLE restore_probe (value text)")
                cur.execute("INSERT INTO restore_probe VALUES ('sentinel')")
            conn.commit()

        subprocess.run(["bash", str(SCRIPT), "backup"], check=True, env=env)

        # Damage the live database after the backup.
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("DROP TABLE restore_probe")
            conn.commit()

        subprocess.run(["bash", str(SCRIPT), "restore"], check=True, env=env)

        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT value FROM restore_probe")
                rows = cur.fetchall()
                if rows != [("sentinel",)]:
                    raise SystemExit(f"restore did not recover sentinel: {rows!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
