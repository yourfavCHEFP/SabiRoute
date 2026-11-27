"""Behavioural tests for the readiness contract in :mod:`sabiroute.api.health`.

The readiness probe answers with a bare verdict: component names and whether a
rate limiter is configured are never disclosed to an unauthenticated caller
(F-08), and a failed schema re-check is response-local rather than written back
to shared gateway state (F-09). These tests pin that contract.
"""
from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from typing import Any

import pytest

from sabiroute.api import health as health_module


def _gateway(
    *,
    registry: Any = None,
    key_store: Any = None,
    chat_store: Any = None,
    rate_limiter: Any = None,
    startup_error: Any = None,
) -> Any:
    return SimpleNamespace(
        registry=[object()] if registry is None else registry,
        key_store=SimpleNamespace(_engine=object()) if key_store is None else key_store,
        chat_store=chat_store,
        rate_limiter=rate_limiter,
        startup_error=startup_error,
    )


def _request(gateway: Any) -> Any:
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(gateway=gateway)))


def _ready(gateway: Any) -> Any:
    return asyncio.run(health_module.readiness(_request(gateway)))


def _body(response: Any) -> Any:
    return json.loads(response.body)


@pytest.fixture(autouse=True)
def _stub_schema_checks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(health_module, "check_schema", lambda engine: None)
    monkeypatch.setattr(health_module, "check_shared_inference_schema", lambda engine: None)
    monkeypatch.setattr(health_module, "check_sabichat_schema", lambda engine: None)


def test_health_and_liveness_are_static_answers() -> None:
    assert asyncio.run(health_module.health()) == {
        "status": "ok",
        "service": "sabiroute",
    }
    assert asyncio.run(health_module.liveness()) == {"status": "alive"}


def test_readiness_without_a_gateway_fails_closed() -> None:
    response = asyncio.run(
        health_module.readiness(SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace())))
    )

    assert response.status_code == 503
    body = _body(response)
    assert body["status"] == "not_ready"
    # F-08: which components failed is not disclosed to an unauthenticated caller.
    assert set(body) == {"status"}


def test_readiness_reports_a_startup_error() -> None:
    response = _ready(_gateway(startup_error="boom"))

    assert response.status_code == 503
    assert _body(response) == {"status": "not_ready"}


def test_readiness_is_ready_when_every_component_is_present() -> None:
    response = _ready(_gateway())

    assert response.status_code == 200
    assert _body(response) == {"status": "ready"}


def test_readiness_does_not_disclose_the_rate_limiter() -> None:
    """A configured rate limiter must not be visible in the public verdict."""
    assert _ready(_gateway(rate_limiter=object())).status_code == 200
    assert _body(_ready(_gateway(rate_limiter=object()))) == {"status": "ready"}
    assert _body(_ready(_gateway(rate_limiter=None))) == {"status": "ready"}


def test_readiness_fails_when_no_deployments_are_configured() -> None:
    response = _ready(_gateway(registry=[]))

    assert response.status_code == 503
    assert _body(response) == {"status": "not_ready"}


def test_readiness_fails_when_the_key_store_is_missing() -> None:
    gateway = _gateway()
    gateway.key_store = None

    response = _ready(gateway)

    assert response.status_code == 503
    assert _body(response) == {"status": "not_ready"}


def test_schema_failure_is_response_local_and_leaves_gateway_state_intact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A transient schema failure must not poison shared gateway state.

    Mutating ``startup_error`` or dropping the stores here would make a single
    failed unauthenticated probe permanently report not-ready.
    """

    def exploding(engine: Any) -> None:
        raise RuntimeError("connection refused")

    monkeypatch.setattr(health_module, "check_schema", exploding)
    gateway = _gateway()
    key_store = gateway.key_store

    response = _ready(gateway)

    assert response.status_code == 503
    assert gateway.startup_error is None
    assert gateway.key_store is key_store


def test_schema_failures_are_not_cached_but_successes_are() -> None:
    """F-09: a healthy steady state is cached; a failure is re-probed."""
    cache = health_module.SchemaCheckCache(ttl_seconds=5.0)

    cache.record(set())
    assert cache.failures() == frozenset()

    cache.record({"key_store"})
    assert cache.failures() is None
