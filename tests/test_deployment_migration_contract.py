"""F1/F2 regression: the real fresh-database deployment contract.

Why these tests run fresh-database work in a subprocess
--------------------------------------------------------
``tests/conftest.py::_ensure_schema_for_stores`` is autouse and patches
``PostgresApiKeyStore.__init__`` and ``SabiChatStore.__init__`` to call
``ensure_schema(..., groups="full")`` immediately after construction. That is
exactly the implicit schema creation production removed: inside pytest, a store
opened against an empty database silently gains a full schema, so the broken
production path cannot be observed. A subprocess does not import pytest or
conftest, so it exercises the constructors and ``python -m sabiroute.migrate``
with production semantics. Nothing here re-introduces the masking behaviour.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import yaml
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Tables ``check_schema`` requires of every SabiRoute database (F2 included).
REQUIRED_TABLES = {
    "sabiroute_api_keys",
    "sabiroute_api_key_budgets",
    "sabiroute_budget_reservations",
    "sabiroute_schema_versions",
    "sabiroute_request_usage",
    "sabiroute_accounting_lineages",
}

#: Constructs a real store against the given URL and reports what happened.
#: Deliberately does no DDL of its own: if the production store is implicit,
#: tables appear; if not, the database stays empty and check_schema fails.
_STORE_PROBE = """\
import os
from sqlalchemy import inspect
from sabiroute.security.store import PostgresApiKeyStore, check_schema

store = PostgresApiKeyStore(os.environ["DATABASE_URL"])
tables = inspect(store._engine).get_table_names()
print("tables=%d" % len(tables))
try:
    check_schema(store._engine)
except ValueError as exc:
    print("check_schema=failed")
    print("reason=%s" % exc)
else:
    print("check_schema=passed")
"""


def _subprocess_env(database_url: str) -> dict[str, str]:
    env = dict(os.environ)
    env["DATABASE_URL"] = database_url
    env["SABIROUTE_SCHEMA_GROUPS"] = "full"
    # The pytest isolation fixture must not leak into the child.
    env.pop("PYTEST_CURRENT_TEST", None)
    env.pop("SABIROUTE_DATABASE_URL", None)
    return env


def _run_python(args: list[str], *, database_url: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *args],
        cwd=REPO_ROOT,
        env=_subprocess_env(database_url),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def _sqlite_url(tmp_path: Path, name: str) -> str:
    return f"sqlite:///{tmp_path / name}"


def test_fresh_database_migrates_through_the_real_entry_point(tmp_path):
    """Fresh schema-less DB → explicit migration → schema validates."""
    url = _sqlite_url(tmp_path, "fresh.sqlite")

    # 1. Genuinely schema-less, and store construction creates nothing.
    engine = create_engine(url)
    assert inspect(engine).get_table_names() == []
    engine.dispose()

    probe = _run_python(["-c", _STORE_PROBE], database_url=url)
    assert probe.returncode == 0, probe.stderr
    assert "tables=0" in probe.stdout, probe.stdout
    assert "check_schema=failed" in probe.stdout, probe.stdout
    assert "sabiroute_api_keys" in probe.stdout, probe.stdout

    # 2. The actual SabiRoute migration mechanism (no pytest, no conftest).
    migrated = _run_python(["-m", "sabiroute.migrate"], database_url=url)
    assert migrated.returncode == 0, migrated.stderr
    assert "Migrations applied" in migrated.stdout, migrated.stdout

    # 3. The schema now exists and the read-only check accepts it.
    engine = create_engine(url)
    tables = set(inspect(engine).get_table_names())
    assert REQUIRED_TABLES <= tables
    assert "sabichat_users" in tables  # full group

    from sabiroute.security.store import check_sabichat_schema, check_schema

    check_schema(engine)
    check_sabichat_schema(engine)
    engine.dispose()

    # 4. Re-running the migration is an idempotent no-op, not a failure.
    rerun = _run_python(["-m", "sabiroute.migrate"], database_url=url)
    assert rerun.returncode == 0, rerun.stderr


def test_migration_failure_is_reported_and_leaves_nothing_half_applied(tmp_path):
    """A migration that cannot connect must exit non-zero, not silently pass."""
    # An unreachable PostgreSQL port: connect fails, migration must report it.
    url = "postgresql://sabiroute:not-a-real-password@127.0.0.1:1/sabiroute"
    result = _run_python(["-m", "sabiroute.migrate"], database_url=url)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "Migration failed" in result.stderr, result.stderr


def test_missing_accounting_lineages_after_migration_fails_closed(tmp_path):
    """F2: a real migrated database minus the lineage table is incompatible."""
    url = _sqlite_url(tmp_path, "no-lineage.sqlite")
    migrated = _run_python(["-m", "sabiroute.migrate"], database_url=url)
    assert migrated.returncode == 0, migrated.stderr

    engine = create_engine(url)
    with engine.begin() as connection:
        connection.exec_driver_sql("DROP TABLE sabiroute_accounting_lineages")

    remaining = set(inspect(engine).get_table_names())
    # Every other required table is still present: this isolates F2.
    assert (REQUIRED_TABLES - {"sabiroute_accounting_lineages"}) <= remaining
    assert "sabiroute_accounting_lineages" not in remaining

    from sabiroute.security.store import check_schema

    try:
        check_schema(engine)
    except ValueError as exc:
        assert "missing tables" in str(exc)
        assert "sabiroute_accounting_lineages" in str(exc)
    else:  # pragma: no cover - the assertion below is the failure message
        engine.dispose()
        raise AssertionError("missing accounting-lineage table passed validation")
    engine.dispose()


def test_unmigrated_database_cannot_report_healthy(tmp_path):
    """F1 startup contract: no migration means not ready, never falsely okay.

    Uses the same engine shape the gateway holds for a live store, so the
    startup validation in ``create_app`` runs for real. No repository store is
    constructed here, which is why the conftest constructor patch cannot mask
    this path.
    """
    from sabiroute.gateway import empty_gateway_state
    from sabiroute.main import create_app

    url = _sqlite_url(tmp_path, "unmigrated.sqlite")
    engine = create_engine(url)
    assert inspect(engine).get_table_names() == []

    state = empty_gateway_state()
    state.key_store = SimpleNamespace(_engine=engine)

    app = create_app(state=state)
    with TestClient(app) as client:
        live = client.get("/health/live")
        ready = client.get("/health/ready")

    # The process is up — that is not the question a deploy gate should ask.
    assert live.status_code == 200
    # But it must not be considered able to serve.
    assert ready.status_code == 503
    # Readiness reports the failing component without echoing the raw error
    # text; the schema diagnosis is carried by ``startup_error``.
    payload = ready.json()
    assert payload["status"] == "not_ready"
    assert "startup" in payload["failing"]
    assert state.startup_error is not None
    assert "Incompatible schema" in state.startup_error
    assert "sabiroute_api_keys" in state.startup_error
    assert state.key_store is None  # degraded state drops the unusable store
    engine.dispose()


def test_compose_runs_migration_before_the_api():
    """The supported deployment surface encodes the explicit ordering."""
    compose = yaml.safe_load((REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    services = compose["services"]

    migrate = services["sabiroute-migrate"]
    assert migrate["command"] == ["python", "-m", "sabiroute.migrate"]
    assert str(migrate["restart"]) == "no"  # one-shot, never restarted
    assert migrate["depends_on"]["postgres"]["condition"] == "service_healthy"

    api = services["sabiroute"]
    assert (
        api["depends_on"]["sabiroute-migrate"]["condition"]
        == "service_completed_successfully"
    )
    # Same artifact migrates and serves.
    assert api.get("image") == migrate.get("image")
    probe = " ".join(api["healthcheck"]["test"])
    assert "/health/ready" in probe
    assert "/health/live" not in probe
