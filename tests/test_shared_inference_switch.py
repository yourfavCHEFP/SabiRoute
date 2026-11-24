"""Behavioural tests for the shared-inference kill switch (:mod:`sabiroute.api.shutdown`)."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from sabiroute.api import shutdown


class _Executor:
    def __init__(self, results: list[Any] | None = None, error: Exception | None = None) -> None:
        self.results = list(results or [])
        self.error = error
        self.calls: list[tuple[Any, tuple[Any, ...]]] = []

    async def run(self, func: Any, *args: Any) -> Any:
        self.calls.append((func, args))
        if self.error is not None:
            raise self.error
        if self.results:
            return self.results.pop(0)
        return func(*args)


class _Store:
    def __init__(self) -> None:
        self.set_calls: list[tuple[bool, str]] = []
        self.status_value: dict[str, Any] = {"enabled": True}

    def shared_inference_status(self) -> dict[str, Any]:
        return self.status_value

    def set_shared_inference(self, enabled: bool, actor: str) -> None:
        self.set_calls.append((enabled, actor))


def _request(store: Any = None, executor: Any = None) -> Any:
    gateway = SimpleNamespace(key_store=store, store_executor=executor)
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(gateway=gateway)))


def _payload(enabled: Any = True, reason: str | None = None) -> Any:
    return shutdown.SharedInferenceRequest(enabled=enabled, reason=reason)


def test_key_store_rejects_missing_state_with_503() -> None:
    with pytest.raises(HTTPException) as excinfo:
        shutdown._key_store(_request(store=None))

    assert excinfo.value.status_code == 503
    assert excinfo.value.detail["error"]["type"] == "shared_inference_unavailable"


def test_status_returns_the_store_snapshot() -> None:
    store = _Store()
    executor = _Executor()

    status = asyncio.run(shutdown.shared_inference_status(_request(store, executor)))

    assert status == store.status_value
    assert executor.calls[0][0] == store.shared_inference_status


def test_status_reports_503_when_the_store_read_fails() -> None:
    executor = _Executor(error=RuntimeError("database is down"))

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(shutdown.shared_inference_status(_request(_Store(), executor)))

    assert excinfo.value.status_code == 503
    assert excinfo.value.detail["error"]["type"] == "shared_inference_unavailable"


def test_set_applies_the_change_then_returns_fresh_status() -> None:
    store = _Store()
    executor = _Executor()

    status = asyncio.run(
        shutdown.set_shared_inference(_payload(enabled=False, reason="incident"), _request(store, executor))
    )

    assert store.set_calls == [(False, "admin")]
    assert status == store.status_value
    assert len(executor.calls) == 2


def test_set_reports_503_when_the_write_fails() -> None:
    executor = _Executor(error=RuntimeError("database is down"))

    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(
            shutdown.set_shared_inference(_payload(enabled=True), _request(_Store(), executor))
        )

    assert excinfo.value.status_code == 503


def test_payload_requires_a_strict_boolean() -> None:
    with pytest.raises(ValidationError):
        shutdown.SharedInferenceRequest.model_validate({"enabled": "yes"})


def test_payload_caps_the_reason_length() -> None:
    with pytest.raises(ValidationError):
        shutdown.SharedInferenceRequest.model_validate({"enabled": True, "reason": "x" * 281})
