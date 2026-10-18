"""Sprint 5: deployment foundation — startup, readiness, container/CI config.

Proves the container/CI/static configuration matches the implementation and
that startup, readiness, and shutdown behave with and without persistence.
Live infrastructure is NOT used here.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml
from conftest import InMemoryApiKeyStore, StubLiteLLMClient, make_config
from fastapi.testclient import TestClient

from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app
from sabiroute.security.store import PostgresApiKeyStore

REPO_ROOT = Path(__file__).resolve().parents[1]


def make_state(**kwargs):
    defaults = {
        "config": make_config(),
        "client": StubLiteLLMClient(),
        "key_store": InMemoryApiKeyStore(),
    }
    defaults.update(kwargs)
    return build_gateway_state(**defaults)


def test_readiness_reports_ready_without_providers(tmp_path):
    state = make_state()
    with TestClient(create_app(state=state)) as client:
        live = client.get("/health/live")
        assert live.status_code == 200

        ready = client.get("/health/ready")
        assert ready.status_code == 200
        body = ready.json()
        assert body["status"] == "ready"
        assert body["components"]["startup"] == "ok"
        assert body["components"]["registry"] == "ok"
        assert body["components"]["key_store"] == "ok"
        # No Redis configured: reported, never probed, never a failure.
        assert body["components"]["rate_limiter"] == "absent"


def test_readiness_fails_without_request_accounting(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    state = build_gateway_state(
        config=make_config(),
        client=StubLiteLLMClient(),
    )
    assert state.key_store is None
    with TestClient(create_app(state=state)) as client:
        ready = client.get("/health/ready")
        assert ready.status_code == 503
        assert ready.json()["status"] == "not_ready"
        assert "key_store" in ready.json()["failing"]


def test_lifespan_closes_key_store(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    key_store = PostgresApiKeyStore(
        f"sqlite:///{tmp_path / 'lifespan.sqlite'}"
    )
    state = make_state(key_store=key_store)
    with TestClient(create_app(state=state)):
        pass

    try:
        assert key_store.applied_revisions() == [
            "0001-usage-source",
            "0002-sabichat-backend",
            "0003-shared-inference-switch",
            "0004-user-quota-ledger",
        ]
    finally:
        key_store.close()


def test_web_dir_override(monkeypatch, tmp_path):
    from sabiroute.main import _web_dir

    monkeypatch.setenv("SABIROUTE_WEB_DIR", str(tmp_path))
    assert _web_dir() == tmp_path
    monkeypatch.setenv("SABIROUTE_WEB_DIR", str(tmp_path / "missing"))
    assert _web_dir() is None
    monkeypatch.delenv("SABIROUTE_WEB_DIR", raising=False)
    assert (_web_dir() / "index.html").is_file()


def test_dockerfile_matches_runtime_contract():
    text = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "python:3.11-slim" in text
    assert "uv sync --frozen --no-dev" in text
    assert "--no-install-project" in text
    assert "USER sabiroute" in text
    assert "/health/live" in text
    assert "EXPOSE 8000" in text
    assert 'CMD ["sabiroute"]' in text
    assert "COPY src/ ./src/" in text
    assert "COPY config/ ./config/" in text
    assert "COPY web/ ./web/" in text
    assert "COPY pyproject.toml uv.lock README.md LICENSE ./" in text
    assert "SABIROUTE_CONFIG_PATH=/srv/sabiroute/config/config.yaml" in text
    assert "SABIROUTE_ROUTES_PATH=/srv/sabiroute/config/routes" in text
    assert "SABIROUTE_WEB_DIR=/srv/sabiroute/web" in text
    assert ".env" not in text


def test_dockerignore_protects_secrets_and_keeps_runtime():
    lines = (REPO_ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
    entries = {line.strip() for line in lines if line.strip() and not line.startswith("#")}

    for excluded in (".env", ".venv/", "__pycache__/", "*.sqlite", ".git/", "tests/", "docs/"):
        assert excluded in entries, excluded
    for required in ("src/", "web/", "config/", "pyproject.toml", "uv.lock"):
        assert not any(entry.rstrip("/") == required.rstrip("/") for entry in entries), required


def test_ci_workflow_is_valid_and_secret_free():
    text = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    workflow = yaml.safe_load(text)

    # Note: YAML 1.1 parses the `on` key as boolean True.
    triggers = workflow.get("on", workflow.get(True))
    assert "push" in triggers and "pull_request" in triggers
    steps = workflow["jobs"]["checks"]["steps"]
    run_lines = [step.get("run", "") for step in steps if "run" in step]
    blob = "\n".join(run_lines)
    for expected in ("pytest", "ruff check", "mypy src", "node --check web/app.js", "docker build"):
        assert expected in blob, expected
    assert "services" in workflow["jobs"]["checks"]
    assert "SABIROUTE_TEST_REDIS_URL" in text
    assert "secrets." not in text
    assert "${{" not in text
    assert "sk-" not in text


def test_env_template_documents_free_pool_and_placeholders():
    text = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")

    assert "SABIROUTE_FREEPOOL_ENABLED=" in text
    assert "SABIROUTE_FREEPOOL_DEPLOYMENTS=" in text
    assert "DATABASE_URL=" in text
    # Assigned sk- values are obvious placeholders, never real secrets.
    assigned = [
        line for line in text.splitlines() if re.match(r"^[A-Z_]+=.*sk-", line)
    ]
    assert assigned
    assert all("change-this" in line for line in assigned)
