"""Phase 18: request-guard, target resolution, streaming and telemetry seams.

The BYOK deny-list has strong end-to-end coverage in
``test_r3_byok_boundary.py``. These tests cover the seams that file does not
reach: the depth bound that must fail *closed*, content text that must not be
scanned, the alias/policy resolver, the SSE frame parsers, and the routing
attempt telemetry shape.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from functools import reduce
from types import SimpleNamespace

import pytest
from conftest import make_config

from sabiroute.api.completions import (
    RETRYABLE_STATUS_CODES,
    UnknownModelError,
    _contains_forbidden_provider_field,
    _deadline_at,
    _error_category,
    _error_response,
    _normalize_field_name,
    _resolve_target,
    _routing_attempt_event,
    _sse_data,
    _sse_usage,
)
from sabiroute.providers.litellm_client import LiteLLMClientError
from sabiroute.providers.registry import registry_from_config
from sabiroute.routing.health import HealthRegistry
from sabiroute.routing.policies import PolicyRegistry, RoutingPolicy
from sabiroute.routing.router import RouteDecision, Router


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("api_key", "apikey"),
        ("API-KEY", "apikey"),
        ("api.key", "apikey"),
        ("api key", "apikey"),
        ("\tapi_key ", "apikey"),
        ("api‐key", "apikey"),  # unicode hyphen
        (42, "42"),
        (None, "none"),
    ],
)
def test_normalize_field_name_reduces_to_alphanumerics(
    value: object, expected: str
) -> None:
    assert _normalize_field_name(value) == expected


def test_forbidden_scan_finds_nested_and_listed_credentials() -> None:
    assert _contains_forbidden_provider_field({"api_key": "x"}) is True
    assert _contains_forbidden_provider_field(
        {"extra_body": {"litellm_params": {"apiKey": "x"}}}
    )
    assert _contains_forbidden_provider_field([{"provider": "openai"}]) is True
    assert _contains_forbidden_provider_field(
        [{"role": "user", "content": "hi", "Authorization": "x"}]
    )


def test_forbidden_scan_ignores_content_text() -> None:
    # Only mapping *keys* are inspected, so a prompt that merely mentions a
    # credential is not rejected.
    assert _contains_forbidden_provider_field("please set api_key") is False
    assert (
        _contains_forbidden_provider_field(
            [{"role": "user", "content": "how do I rotate my api_key?"}]
        )
        is False
    )
    assert _contains_forbidden_provider_field({"top_p": 0.5}) is False


def test_forbidden_scan_fails_closed_past_the_depth_bound() -> None:
    def wrap(depth: int) -> dict:
        return reduce(lambda acc, _: {"wrap": acc}, range(depth), {"benign": 1})

    # Up to five enclosing mappings the scan completes and admits the body.
    assert _contains_forbidden_provider_field(wrap(5)) is False
    # At six the structure is no longer examined; the deny-list fails closed
    # rather than letting the bound itself become the bypass.
    assert _contains_forbidden_provider_field(wrap(6)) is True
    assert _contains_forbidden_provider_field(wrap(8)) is True


def _resolve_state(policies: PolicyRegistry | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        registry=registry_from_config(make_config()),
        policies=policies or PolicyRegistry(),
    )


def test_resolve_target_returns_a_single_alias_candidate() -> None:
    candidates, policy = _resolve_target(_resolve_state(), "primary")

    assert candidates == ["primary"]
    assert policy.name == "alias"
    assert policy.max_attempts == 2
    assert policy.strategy == "priority"


def test_resolve_target_strips_surrounding_whitespace() -> None:
    candidates, _ = _resolve_target(_resolve_state(), "  primary  ")

    assert candidates == ["primary"]


def test_resolve_target_fans_a_stateless_policy_over_every_deployment() -> None:
    candidates, policy = _resolve_target(_resolve_state(), "fast")

    # ``fast`` defines no deployments, so it covers the whole registry in
    # registration order.
    assert candidates == ["primary", "secondary", "cloudy", "literal-key"]
    assert policy.name == "fast"


def test_resolve_target_honours_a_policys_explicit_deployments() -> None:
    policies = PolicyRegistry(
        {
            "own": RoutingPolicy(
                name="own", deployments=["secondary", "cloudy"], max_attempts=1
            )
        }
    )

    candidates, policy = _resolve_target(_resolve_state(policies), "own")

    assert candidates == ["secondary", "cloudy"]
    assert policy.max_attempts == 1


def test_resolve_target_lowercases_and_strips_the_sabiroute_prefix() -> None:
    candidates, policy = _resolve_target(_resolve_state(), "SABIROUTE_FAST")

    assert policy.name == "fast"
    assert candidates == ["primary", "secondary", "cloudy", "literal-key"]


def test_resolve_target_is_case_sensitive_for_aliases() -> None:
    # Aliases match as registered; only policy names are case-folded. An
    # upper-cased alias therefore does not silently resolve.
    with pytest.raises(UnknownModelError) as excinfo:
        _resolve_target(_resolve_state(), "PRIMARY")

    assert isinstance(excinfo.value, KeyError)
    assert excinfo.value.args == ("PRIMARY",)


def test_resolve_target_unknown_model_raises() -> None:
    with pytest.raises(UnknownModelError):
        _resolve_target(_resolve_state(), "no-such-model")


def test_deadline_at_reads_only_numeric_state() -> None:
    assert _deadline_at(SimpleNamespace()) is None
    assert (
        _deadline_at(SimpleNamespace(state=SimpleNamespace(sabiroute_deadline_at=1.5)))
        == 1.5
    )
    assert (
        _deadline_at(SimpleNamespace(state=SimpleNamespace(sabiroute_deadline_at=5))) == 5
    )
    assert (
        _deadline_at(SimpleNamespace(state=SimpleNamespace(sabiroute_deadline_at="soon")))
        is None
    )


def test_sse_data_extracts_every_data_line() -> None:
    frame = b'event: message\ndata: {"a": 1}\ndata:[DONE]\n\n'

    assert _sse_data(frame) == ['{"a": 1}', "[DONE]"]


def test_sse_data_ignores_non_data_lines() -> None:
    # A line that is not prefixed exactly with ``data:`` is not an event,
    # and undecodable bytes are replaced rather than raising.
    assert _sse_data(b" data: indented\n") == []
    assert _sse_data(b"\xff\xfe data: x\n") == []
    assert _sse_data(b"") == []


def test_sse_usage_returns_the_first_event_carrying_usage() -> None:
    frame = (
        b'data: {"choices": []}\n\n'
        b"data: [DONE]\n\n"
        b'data: {"choices": [], "usage": {"prompt_tokens": 3}}\n\n'
    )

    assert _sse_usage(frame) == {"choices": [], "usage": {"prompt_tokens": 3}}


@pytest.mark.parametrize(
    "frame",
    [
        b'data: {"choices": []}\n\n',
        b"data: {not json}\n\n",
        b'data: {"usage": "not-a-mapping"}\n\n',
        b'data: [DONE]\n\n',
        b"",
    ],
)
def test_sse_usage_is_none_without_usable_usage(frame: bytes) -> None:
    assert _sse_usage(frame) is None


def test_error_response_shape_and_extra_fields() -> None:
    response = _error_response(418, "teapot", "testing", detail="short")

    assert response.status_code == 418
    assert json.loads(response.body) == {
        "error": {"message": "teapot", "type": "testing", "detail": "short"}
    }


def test_retryable_status_constant_excludes_client_errors() -> None:
    # The retry predicate is
    # ``status is None or status >= 500 or status in RETRYABLE_STATUS_CODES``,
    # so membership here is what makes a 4xx retryable. 400/404/408 must not
    # be: they describe a request the next deployment would reject too.
    assert RETRYABLE_STATUS_CODES == {401, 403, 429}
    for status in (400, 404, 408, 422):
        assert status not in RETRYABLE_STATUS_CODES


@pytest.mark.parametrize(
    ("status", "category"),
    [
        (401, "auth"),
        (403, "auth"),
        (429, "rate_limit"),
        (500, "server"),
        (503, "server"),
        (400, "client"),
        (404, "client"),
        # Observed behaviour: an HTTP 408 status is classified "client".
        # Only a transport-level timeout (no status, ``timed_out=True``)
        # maps to "timeout".
        (408, "client"),
    ],
)
def test_error_category_maps_statuses(status: int, category: str) -> None:
    assert _error_category(LiteLLMClientError("boom", status_code=status)) == category


def test_error_category_distinguishes_timeout_from_transport() -> None:
    assert _error_category(LiteLLMClientError("slow", timed_out=True)) == "timeout"
    assert _error_category(LiteLLMClientError("reset")) == "transport"


def _decision() -> RouteDecision:
    routing = Router(
        registry_from_config(make_config()), health=HealthRegistry()
    )
    return routing.choose_deployment(["primary", "secondary"], policy_name="fast")


def _event(decision: RouteDecision, **overrides: object) -> dict:
    now = datetime.now(UTC)
    fields: dict[str, object] = {
        "request_id": "req-1",
        "attempt": 2,
        "decision": decision,
        "request_type": "chat",
        "decided_at": now,
        "attempt_started_at": now,
        "attempt_completed_at": now,
        "outcome": "failure",
        "latency_ms": 12.5,
        "usage": (3, 4, 7),
        "actual_cost_usd": Decimal("0.5"),
        "failure_category": "server",
        "http_status": 503,
    }
    fields.update(overrides)
    return _routing_attempt_event(**fields)  # type: ignore[arg-type]


def test_routing_attempt_event_carries_the_explanation() -> None:
    event = _event(_decision())

    assert event["selected_deployment"] == "primary"
    assert event["candidate_deployments"] == ["primary", "secondary"]
    assert event["eligible_deployments"] == ["primary", "secondary"]
    assert event["capability_excluded_deployments"] == {}
    assert event["scoring_policy_version"] == "priority-v1"
    assert event["scoring_fallback_reason"] == "priority_strategy"
    assert event["routing_policy_id"] == "fast"
    assert event["fallback_attempt"] == 2
    assert event["outcome"] == "failure"
    assert event["http_status"] == 503
    assert event["failure_category"] == "server"
    assert event["usage"] == {
        "prompt_tokens": 3,
        "completion_tokens": 4,
        "total_tokens": 7,
    }
    assert event["actual_cost_usd"] == "0.5"
    assert event["attempt_schema_version"] == "1.1"


def test_routing_attempt_event_degrades_without_an_explanation() -> None:
    decision = RouteDecision(deployment="x", provider="p", reason="alias-direct")

    event = _event(
        decision,
        outcome="success",
        usage=None,
        actual_cost_usd=None,
        failure_category=None,
        http_status=None,
    )

    assert event["candidate_deployments"] == []
    assert event["capability_excluded_deployments"] == {}
    assert event["unhealthy_deployments"] == []
    assert event["candidate_scores"] == []
    assert event["ranked_candidates"] == []
    assert event["scoring_policy_version"] == "unknown"
    assert event["scoring_fallback_reason"] == "missing_explanation"
    assert event["scoring_weights"] == {}
    # Falls back to the raw decision reason when there is no explanation.
    assert event["selection_reason"] == "alias-direct"
    assert event["routing_policy_id"] == "alias-direct"
    assert event["usage"] is None
    assert event["actual_cost_usd"] is None
