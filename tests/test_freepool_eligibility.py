"""Behavioural tests for :mod:`sabiroute.freepool.eligibility`."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest

from sabiroute.freepool import eligibility


def test_policy_parses_an_explicit_mapping() -> None:
    policy = eligibility.FreePoolPolicy.from_mapping(
        {"enabled": True, "eligible_deployments": [" alpha ", "beta"]}
    )

    assert policy.enabled is True
    assert policy.eligible_deployments == frozenset({"alpha", "beta"})


def test_policy_rejects_a_non_mapping() -> None:
    with pytest.raises(TypeError):
        eligibility.FreePoolPolicy.from_mapping(["not", "a", "mapping"])  # type: ignore[arg-type]


def test_policy_rejects_missing_keys() -> None:
    with pytest.raises(ValueError) as excinfo:
        eligibility.FreePoolPolicy.from_mapping({"enabled": True})

    assert "missing" in str(excinfo.value)


def test_policy_rejects_non_boolean_enabled() -> None:
    with pytest.raises(ValueError) as excinfo:
        eligibility.FreePoolPolicy.from_mapping(
            {"enabled": "yes", "eligible_deployments": ["a"]}
        )

    assert "must be a boolean" in str(excinfo.value)


def test_policy_rejects_blank_deployment_names() -> None:
    with pytest.raises(ValueError) as excinfo:
        eligibility.FreePoolPolicy.from_mapping(
            {"enabled": True, "eligible_deployments": ["a", "  "]}
        )

    assert "non-empty deployment alias" in str(excinfo.value)


def test_disabled_policy_passes_candidates_through() -> None:
    decision = eligibility.evaluate_free_pool(["a", "b"], eligibility.FreePoolPolicy())

    assert decision.allowed is True
    assert decision.reason is None
    assert decision.eligible_candidates == ("a", "b")


def test_enabled_policy_intersects_with_the_allowlist() -> None:
    policy = eligibility.FreePoolPolicy(
        enabled=True, eligible_deployments=frozenset({"b"})
    )

    decision = eligibility.evaluate_free_pool(["a", "b"], policy)

    assert decision.allowed is True
    assert decision.eligible_candidates == ("b",)


def test_enabled_policy_denies_when_nothing_matches() -> None:
    policy = eligibility.FreePoolPolicy(
        enabled=True, eligible_deployments=frozenset({"z"})
    )

    decision = eligibility.evaluate_free_pool(["a"], policy)

    assert decision.allowed is False
    assert decision.reason == eligibility.FREE_POOL_UNMAPPED_DEPLOYMENT
    assert decision.eligible_candidates == ()


def test_deny_reason_prefers_capability_over_health() -> None:
    incapable = SimpleNamespace(
        capability_eligible_deployments=(), available_deployments=()
    )
    unhealthy = SimpleNamespace(
        capability_eligible_deployments=("a",), available_deployments=()
    )
    servable = SimpleNamespace(
        capability_eligible_deployments=("a",), available_deployments=("a",)
    )

    assert (
        eligibility.deny_reason_for_evaluation(incapable)
        == eligibility.FREE_POOL_NO_CAPABLE_DEPLOYMENT
    )
    assert (
        eligibility.deny_reason_for_evaluation(unhealthy)
        == eligibility.FREE_POOL_NO_HEALTHY_DEPLOYMENT
    )
    assert eligibility.deny_reason_for_evaluation(servable) is None


class _Executor:
    def __init__(self, result: Any = None, error: Exception | None = None) -> None:
        self._result = result
        self._error = error

    async def run(self, func: Any, *args: Any) -> Any:
        if self._error is not None:
            raise self._error
        return self._result


class _Store:
    def get_shared_inference(self) -> None:  # pragma: no cover - never called directly
        return None


def _denial(state: Any, store: Any) -> str | None:
    return asyncio.run(eligibility.shared_inference_denial(state, store))


def test_shared_inference_denies_without_a_store() -> None:
    assert _denial(SimpleNamespace(), None) == eligibility.SHARED_INFERENCE_DISABLED


def test_shared_inference_denies_without_an_executor() -> None:
    assert _denial(SimpleNamespace(), _Store()) == eligibility.SHARED_INFERENCE_DISABLED


def test_shared_inference_denies_when_the_read_raises() -> None:
    state = SimpleNamespace(store_executor=_Executor(error=RuntimeError("down")))

    assert _denial(state, _Store()) == eligibility.SHARED_INFERENCE_DISABLED


def test_shared_inference_admits_only_on_an_explicit_true() -> None:
    enabled = SimpleNamespace(store_executor=_Executor(result=True))
    disabled = SimpleNamespace(store_executor=_Executor(result=False))
    non_boolean = SimpleNamespace(store_executor=_Executor(result="yes"))

    assert _denial(enabled, _Store()) is None
    assert _denial(disabled, _Store()) == eligibility.SHARED_INFERENCE_DISABLED
    assert _denial(non_boolean, _Store()) == eligibility.SHARED_INFERENCE_DISABLED
