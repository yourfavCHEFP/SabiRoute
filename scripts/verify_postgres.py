"""Verify PostgreSQL connectivity and the SabiRoute API-key lifecycle."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from sabiroute.main import create_app

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SMOKE_MODEL = "phase08-smoke-invalid-model"
SMOKE_MESSAGES = [{"role": "user", "content": "x"}]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--host",
        help="Temporarily override the DATABASE_URL host for this process only.",
    )
    args = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env", override=False)
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is unset; configure it for the target runtime.")
    admin_key = os.environ.get("SABIROUTE_ADMIN_KEY")
    if not admin_key:
        raise SystemExit("SABIROUTE_ADMIN_KEY is unset; configure it before the smoke test.")

    parsed = make_url(database_url)
    if args.host:
        parsed = parsed.set(host=args.host)
    parsed = parsed.set(drivername="postgresql+psycopg")
    engine_url = str(parsed)
    engine = create_engine(parsed, connect_args={"connect_timeout": 5})
    project_id = f"phase08-smoke-{uuid4().hex}"

    try:
        with engine.connect() as connection:
            database, role = connection.execute(
                text("SELECT current_database(), current_user")
            ).one()
        print(f"PostgreSQL reachable: database={database}, role={role}")

        os.environ["DATABASE_URL"] = engine_url
        with TestClient(create_app()) as client:
            admin_headers = {"Authorization": f"Bearer {admin_key}"}
            unauthenticated = client.get("/admin/health")
            if unauthenticated.status_code != 401:
                raise RuntimeError("Admin endpoint did not reject a missing credential.")

            created = client.post(
                "/admin/api-keys",
                headers=admin_headers,
                json={"project_id": project_id, "name": "temporary-postgresql-verification"},
            )
            if created.status_code != 201:
                raise RuntimeError(
                    f"PostgreSQL-backed key creation failed: HTTP {created.status_code}."
                )
            first = created.json()
            first_key = first["api_key"]
            first_id = first["id"]

            first_headers = {"Authorization": f"Bearer {first_key}"}
            accepted = client.post(
                "/v1/chat/completions",
                headers=first_headers,
                json={"model": SMOKE_MODEL, "messages": SMOKE_MESSAGES},
            )
            if accepted.status_code != 404:
                raise RuntimeError("Newly created key did not pass completion authentication.")

            rotated = client.post(
                f"/admin/api-keys/{first_id}/rotate", headers=admin_headers
            )
            if rotated.status_code != 201:
                raise RuntimeError("PostgreSQL-backed key rotation failed.")
            second = rotated.json()
            second_key = second["api_key"]
            second_id = second["id"]

            revoked_old = client.post(
                "/v1/chat/completions",
                headers=first_headers,
                json={"model": SMOKE_MODEL, "messages": SMOKE_MESSAGES},
            )
            if revoked_old.status_code != 401:
                raise RuntimeError("Old key remained valid after rotation.")

            accepted_new = client.post(
                "/v1/chat/completions",
                headers={"Authorization": f"Bearer {second_key}"},
                json={"model": SMOKE_MODEL, "messages": SMOKE_MESSAGES},
            )
            if accepted_new.status_code != 404:
                raise RuntimeError("Replacement key did not pass completion authentication.")

            revoked = client.post(
                f"/admin/api-keys/{second_id}/revoke", headers=admin_headers
            )
            if revoked.status_code != 200:
                raise RuntimeError("PostgreSQL-backed key revocation failed.")
            revoked_use = client.post(
                "/v1/chat/completions",
                headers={"Authorization": f"Bearer {second_key}"},
                json={"model": SMOKE_MODEL, "messages": SMOKE_MESSAGES},
            )
            if revoked_use.status_code != 401:
                raise RuntimeError("Revoked key remained valid.")

        with engine.connect() as connection:
            stored = connection.execute(
                text("SELECT key_hash FROM sabiroute_api_keys WHERE project_id = :project_id"),
                {"project_id": project_id},
            ).scalars().all()
        expected_hashes = {
            hashlib.sha256(first_key.encode("utf-8")).hexdigest(),
            hashlib.sha256(second_key.encode("utf-8")).hexdigest(),
        }
        if set(stored) != expected_hashes:
            raise RuntimeError("PostgreSQL did not contain only the expected key hashes.")
        print("SabiRoute PostgreSQL API lifecycle: create/authenticate/rotate/revoke PASS")
    finally:
        try:
            with engine.begin() as connection:
                connection.execute(
                    text("DELETE FROM sabiroute_api_keys WHERE project_id = :project_id"),
                    {"project_id": project_id},
                )
        except Exception:
            # Table creation or connectivity may itself have failed.
            pass
        engine.dispose()


if __name__ == "__main__":
    main()
