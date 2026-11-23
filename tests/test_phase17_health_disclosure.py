"""Phase 17 F-08 / F-09: readiness disclosure and database-work amplification.

F-08: an unauthenticated caller must learn only whether the instance is ready,
not the component names or whether rate limiting is configured.

F-09: repeated unauthenticated readiness probes must not repeat the database
schema checks. A successful check is cached for a short TTL; a failed check is
re-probed immediately so a transient fault cannot hold readiness down.
"""

from __future__ import annotations

from typing import Any

from conftest import InMemoryApiKeyStore, StubLiteLLMClient, make_config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from sabiroute.api import health as health_module
from sabiroute.gateway import build_gateway_state, empty_gateway_state
from sabiroute.main import create_app
from sabiroute.security.store import ensure_schema


def _state(**overrides: Any):
    defaults: dict[str, Any] = {
        "config": make_config(),
        "client": StubLiteLLMClient(),
        "key_store": InMemoryApiKeyStore(),
    }
    defaults.update(overrides)
    return build_gateway_state(**defaults)


def _valid_engine():
    """A real, fully migrated in-memory store so the lifespan check passes."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    ensure_schema(engine, groups="full")
    return engine


def test_ready_body_is_a_bare_verdict() -> None:
    with TestClient(create_app(state=_state())) as client:
        response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    text = response.text
    for disclosed in (
        "components",
        "startup",
        "registry",
        "key_store",
        "chat_store",
        "rate_limiter",
        "configured",
        "absent",
    ):
        assert disclosed not in text, disclosed


def test_not_ready_body_discloses_nothing() -> None:
    with TestClient(create_app(state=empty_gateway_state())) as client:
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}
    text = response.text
    for disclosed in ("failing", "components", "startup", "registry", "rate_limiter"):
        assert disclosed not in text, disclosed


def test_rate_limit_configuration_is_not_disclosed() -> None:
    # A non-None rate limiter used to surface as "configured" to anonymous
    # callers. The body must be identical whether or not one is present.
    with TestClient(create_app(state=_state())) as plain, TestClient(
        create_app(state=_state(rate_limiter=object()))
    ) as limited:
        assert limited.get("/health/ready").json() == {"status": "ready"}
        assert plain.get("/health/ready").json() == limited.get("/health/ready").json()


def test_repeated_readiness_calls_do_not_repeat_schema_work(
    monkeypatch: Any,
) -> None:
    calls = {"schema": 0, "shared": 0}

    def count_schema(_engine: Any) -> None:
        calls["schema"] += 1

    def count_shared(_engine: Any) -> None:
        calls["shared"] += 1

    # The lifespan uses main.py's own bindings; only the request path counts.
    monkeypatch.setattr(health_module, "check_schema", count_schema)
    monkeypatch.setattr(health_module, "check_shared_inference_schema", count_shared)

    state = _state()
    state.key_store._engine = _valid_engine()
    # Captured before the request path populates the cache.
    later = health_module._monotonic() + 3600.0

    with TestClient(create_app(state=state)) as client:
        for _ in range(3):
            assert client.get("/health/ready").status_code == 200
        assert calls == {"schema": 1, "shared": 1}

        # Advancing the cache clock past the TTL forces exactly one new check.
        monkeypatch.setattr(health_module, "_monotonic", lambda: later)
        assert client.get("/health/ready").status_code == 200
        assert calls == {"schema": 2, "shared": 2}


def test_failed_schema_check_is_not_cached(monkeypatch: Any) -> None:
    state = _state()
    state.key_store._engine = _valid_engine()

    real_check = health_module.check_schema
    calls = {"n": 0}

    def fail_once(engine: Any) -> None:
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("transient schema check failure")
        real_check(engine)

    monkeypatch.setattr(health_module, "check_schema", fail_once)

    with TestClient(create_app(state=state)) as client:
        first = client.get("/health/ready")
        second = client.get("/health/ready")

    assert first.status_code == 503
    assert first.json() == {"status": "not_ready"}
    assert second.status_code == 200
    assert second.json() == {"status": "ready"}
