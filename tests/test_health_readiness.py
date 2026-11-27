"""Behavioural tests for the readiness contract in :mod:`sabiroute.api.health`."""
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
    assert body["failing"] == ["startup", "registry", "key_store"]


def test_readiness_reports_a_startup_error() -> None:
    response = _ready(_gateway(startup_error="boom"))

    assert response.status_code == 503
    assert "startup" in _body(response)["failing"]


def test_readiness_is_ready_when_every_component_is_present() -> None:
    response = _ready(_gateway())

    assert response.status_code == 200
    body = _body(response)
    assert body["status"] == "ready"
    assert body["components"]["startup"] == "ok"
    assert body["components"]["registry"] == "ok"
    assert body["components"]["key_store"] == "ok"
    assert body["components"]["rate_limiter"] == "absent"


def test_readiness_reports_the_rate_limiter_informationally() -> None:
    response = _ready(_gateway(rate_limiter=object()))

    assert _body(response)["components"]["rate_limiter"] == "configured"


def test_readiness_fails_when_no_deployments_are_configured() -> None:
    response = _ready(_gateway(registry=[]))

    assert response.status_code == 503
    assert _body(response)["failing"] == ["registry"]


def test_readiness_fails_when_the_key_store_is_missing() -> None:
    gateway = _gateway()
    gateway.key_store = None

    response = _ready(gateway)

    assert response.status_code == 503
    assert _body(response)["failing"] == ["key_store"]


def test_schema_failure_is_recorded_and_stores_are_dropped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def exploding(engine: Any) -> None:
        raise RuntimeError("connection refused")

    monkeypatch.setattr(health_module, "check_schema", exploding)
    monkeypatch.setattr(health_module, "redact_secrets", lambda exc: f"redacted:{exc}")
    gateway = _gateway()

    response = _ready(gateway)

    assert response.status_code == 503
    assert gateway.startup_error == "redacted:connection refused"
    assert gateway.key_store is None
    assert gateway.chat_store is None
