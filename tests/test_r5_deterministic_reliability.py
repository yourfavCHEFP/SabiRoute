"""R5 deterministic reliability proofs (R5-F1 through R5-F7).

Each test maps to one named gap and exercises only verified production
paths:

- ``sabiroute.api.completions.chat_completions`` (attempt loop, retry gate,
  deadline gate, accounting finalization)
- ``sabiroute.routing.health.HealthRegistry`` (cooldown + half-open)
- existing deadline semantics (``_deadline_expired`` + monotonic clock)

Determinism rules: provider and clock boundaries are stubbed/faked; no
``sleep()`` timing tests; no invented production behavior.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

from conftest import InMemoryApiKeyStore, StubLiteLLMClient, make_config, provision_test_key
from fastapi.testclient import TestClient

from sabiroute.api.completions import ChatCompletionRequest, chat_completions
from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app
from sabiroute.providers.litellm_client import LiteLLMClientError
from sabiroute.routing.health import HealthRegistry
from sabiroute.routing.policies import RoutingPolicy
from sabiroute.security.keys import ApiKeyIdentity

MESSAGES = [{"role": "user", "content": "hello"}]

# Gap index (recovered from the live attempt loop + health registry):
#   R5-F1 bounded retry/fallback (policy.max_attempts is a hard bound)
#   R5-F2 non-retryable no-amplification (4xx outside RETRYABLE_STATUS_CODES)
#   R5-F3 logical request identity/accounting across fallback (one request_id)
#   R5-F4 cooldown and half-open recovery (HealthRegistry.available)
#   R5-F5 recovery isolation (per-deployment health state)
#   R5-F6 deadline expiry between attempts (no new upstream work past deadline)
#   R5-F7 honest failure/success telemetry (health/metrics/errors/latency/usage)


def _client(
    stub: StubLiteLLMClient,
    *,
    policies: list[RoutingPolicy] | None = None,
) -> tuple[TestClient, Any]:
    state = build_gateway_state(
        config=make_config(), client=stub, key_store=InMemoryApiKeyStore()
    )
    for policy in policies or []:
        state.policies.register(policy)
    key = provision_test_key(state)
    app = create_app(state=state)
    return (
        TestClient(app, headers={"Authorization": f"Bearer {key}"}),
        state,
    )


def _fast_two() -> RoutingPolicy:
    return RoutingPolicy(
        name="fast",
        deployments=["primary", "secondary"],
        strategy="priority",
        max_attempts=2,
    )


def _event(state: Any) -> Any:
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    return next(iter(store.usage_events.values()))


def _direct_request(state: Any, *, deadline_at: float | None = None) -> Any:
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    record = next(iter(store.records.values()))
    return SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(gateway=state)),
        state=SimpleNamespace(
            api_identity=ApiKeyIdentity(
                key_id=record.key_id, project_id=record.project_id
            ),
            sabiroute_deadline_at=deadline_at,
        ),
    )


# --- R5-F1: bounded retry/fallback -------------------------------------------


def test_r5_f1_retryable_failures_bounded_by_max_attempts() -> None:
    """R5-F1: two retryable 500s under max_attempts=2 make exactly two calls."""
    stub = StubLiteLLMClient(failures={"primary": 1, "secondary": 1})
    client, state = _client(stub, policies=[_fast_two()])

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES},
    )

    assert response.status_code == 502
    assert stub.calls == ["primary", "secondary"]
    event = _event(state)
    assert [d["selected_deployment"] for d in event.routing_decisions] == [
        "primary",
        "secondary",
    ]
    assert [d["outcome"] for d in event.routing_decisions] == ["failure", "failure"]
    assert event.final_status == 502


def test_r5_f1_alias_request_bounded_by_candidates_not_max_attempts() -> None:
    """R5-F1: alias policy (max_attempts=2, one candidate) makes one call."""
    stub = StubLiteLLMClient(failures={"primary": 5})
    client, _ = _client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "primary", "messages": MESSAGES},
    )

    assert response.status_code == 502
    assert stub.calls == ["primary"]
    assert response.json()["error"]["attempts"] == ["primary"]


def test_r5_f1_success_stops_fallback_early() -> None:
    """R5-F1: first-attempt success never spends the second attempt."""
    stub = StubLiteLLMClient(failures={"primary": 1})
    client, _ = _client(stub, policies=[_fast_two()])

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES},
    )

    assert response.status_code == 200
    assert stub.calls == ["primary", "secondary"]
    # Counter-proof: with no failures only one upstream call exists.
    clean = StubLiteLLMClient()
    clean_client, _ = _client(clean, policies=[_fast_two()])
    ok = clean_client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES},
    )
    assert ok.status_code == 200
    assert clean.calls == ["primary"]


# --- R5-F2: non-retryable no-amplification ------------------------------------


def test_r5_f2_client_error_makes_single_attempt() -> None:
    """R5-F2: HTTP 400 is non-retryable and must not fan out."""
    stub = StubLiteLLMClient(failures={"primary": 3}, failure_status=400)
    client, state = _client(stub, policies=[_fast_two()])

    response = client.post(
        "/v1/chat/completions",
        json={"model": "ultimate", "messages": MESSAGES},
    )

    assert response.status_code == 502
    assert stub.calls == ["primary"]
    event = _event(state)
    assert len(event.routing_decisions) == 1
    assert event.routing_decisions[0]["outcome"] == "failure"
    assert event.routing_decisions[0]["failure_category"] == "client"
    assert event.routing_decisions[0]["http_status"] == 400


def test_r5_f2_each_retryable_status_still_bounded() -> None:
    """R5-F2: retryable 401/403/429 fall back once, then stop at the bound."""
    for status in (401, 403, 429):
        stub = StubLiteLLMClient(
            failures={"primary": 1, "secondary": 1}, failure_status=status
        )
        client, _ = _client(stub, policies=[_fast_two()])
        response = client.post(
            "/v1/chat/completions",
            json={"model": "fast", "messages": MESSAGES},
        )
        assert response.status_code == 502, f"status={status}"
        assert stub.calls == ["primary", "secondary"], f"status={status}"


# --- R5-F3: logical request identity/accounting -------------------------------


def test_r5_f3_single_logical_request_across_fallback() -> None:
    """R5-F3: fallback keeps one request_id, one usage row, ordered attempts."""
    stub = StubLiteLLMClient(failures={"primary": 1})
    client, state = _client(stub, policies=[_fast_two()])

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES},
    )

    assert response.status_code == 200
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    assert len(store.usage_events) == 1
    event = next(iter(store.usage_events.values()))
    request_id = event.request_id
    assert event.final_status == 200
    assert event.final_deployment == "secondary"
    assert len(event.pre_routing_features) == len(event.routing_decisions) == 2
    assert [s["attempt_number"] for s in event.pre_routing_features] == [1, 2]
    assert [d["fallback_attempt"] for d in event.routing_decisions] == [1, 2]
    assert {d["request_id"] for d in event.routing_decisions} == {request_id}
    assert {d["logical_request_id"] for d in event.routing_decisions} == {request_id}
    assert {s["logical_request_id"] for s in event.pre_routing_features} == {
        request_id
    }
    # Success usage from the stub (3 prompt + 2 completion) is attributed once.
    assert event.prompt_tokens == 3
    assert event.completion_tokens == 2
    assert event.total_tokens == 5


def test_r5_f3_failure_usage_sums_across_attempts() -> None:
    """R5-F3: failure usage on attempt 1 plus success usage sums honestly."""
    stub = StubLiteLLMClient()

    async def fail_primary_with_usage(
        decision: Any, messages: Any, **extra: Any
    ) -> dict[str, Any]:
        stub.calls.append(decision.deployment)
        if decision.deployment == "primary":
            raise LiteLLMClientError(
                "stub failure for primary",
                status_code=500,
                response_body={
                    "usage": {
                        "prompt_tokens": 3,
                        "completion_tokens": 0,
                        "total_tokens": 3,
                    }
                },
            )
        return {
            "id": "chatcmpl-stub",
            "model": decision.deployment,
            "choices": [{"message": {"role": "assistant", "content": "ok"}}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2},
        }

    stub.chat_completion = fail_primary_with_usage  # type: ignore[method-assign]
    client, state = _client(stub, policies=[_fast_two()])

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES},
    )

    assert response.status_code == 200
    event = _event(state)
    assert event.prompt_tokens == 6
    assert event.completion_tokens == 2
    assert event.total_tokens == 8
    assert [d["outcome"] for d in event.routing_decisions] == [
        "failure",
        "success",
    ]


# --- R5-F4: cooldown and half-open --------------------------------------------


class _Clock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


def test_r5_f4_tripped_deployment_excluded_until_half_open(monkeypatch) -> None:
    """R5-F4: cooldown excludes primary; expiry half-opens exactly one trial."""
    import sabiroute.routing.health as health_mod

    t0 = datetime(2026, 10, 11, 12, 0, 0, tzinfo=UTC)
    clock = _Clock(t0)
    monkeypatch.setattr(health_mod, "utc_now", clock)
    health = HealthRegistry(failure_threshold=3, cooldown_seconds=30)

    for _ in range(3):
        health.mark_failure("primary")
    assert health.available("primary") is False

    # One microsecond before expiry: still cooling down.
    clock.now = t0 + timedelta(seconds=30) - timedelta(microseconds=1)
    assert health.available("primary") is False
    # Exactly at expiry: half-open grants one fresh attempt and resets budget.
    clock.now = t0 + timedelta(seconds=30)
    assert health.available("primary") is True
    assert health.deployments["primary"].healthy is True
    assert health.deployments["primary"].consecutive_failures == 0
    # A single failure after recovery does not re-trip (fresh budget of 3).
    health.mark_failure("primary")
    assert health.available("primary") is True


def test_r5_f4_gateway_routes_around_cooling_deployment() -> None:
    """R5-F4: an in-cooldown primary is never invoked by the gateway."""
    stub = StubLiteLLMClient()
    client, state = _client(stub, policies=[_fast_two()])

    for _ in range(state.health.failure_threshold):
        state.health.mark_failure("primary")
    assert state.health.available("primary") is False

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES},
    )

    assert response.status_code == 200
    assert response.headers["X-SabiRoute-Deployment"] == "secondary"
    assert stub.calls == ["secondary"]
    event = _event(state)
    assert event.routing_decisions[0]["selected_deployment"] == "secondary"


# --- R5-F5: recovery isolation -------------------------------------------------


def test_r5_f5_health_state_isolated_per_deployment() -> None:
    """R5-F5: failures/success on one deployment never touch the other."""
    health = HealthRegistry(failure_threshold=3, cooldown_seconds=30)

    health.mark_failure("primary")
    health.mark_failure("primary")
    assert health.available("primary") is True
    assert health.available("secondary") is True

    health.mark_failure("primary")  # third strike trips primary only
    assert health.available("primary") is False
    assert health.available("secondary") is True

    health.mark_success("secondary")
    # Success elsewhere does not rescue the cooling deployment ...
    assert health.available("primary") is False
    # ... and tripping primary does not inflate secondary counters.
    assert health.deployments["secondary"].consecutive_failures == 0
    assert health.deployments["secondary"].total_failures == 0

    health.mark_success("primary")
    assert health.available("primary") is True
    assert health.deployments["primary"].consecutive_failures == 0
    assert health.deployments["primary"].total_failures == 3


def test_r5_f5_failed_attempt_does_not_poison_sibling() -> None:
    """R5-F5: primary 500 then secondary success isolates health/metrics."""
    stub = StubLiteLLMClient(failures={"primary": 1})
    client, state = _client(stub, policies=[_fast_two()])

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES},
    )

    assert response.status_code == 200
    snapshot = state.health.snapshot()
    assert snapshot["primary"]["total_failures"] == 1
    assert snapshot["secondary"]["total_failures"] == 0
    assert snapshot["secondary"]["healthy"] is True
    assert state.metrics.snapshot()["requests_successful"] == 1


# --- R5-F6: deadline expiry between attempts ------------------------------------


def test_r5_f6_deadline_between_attempts_starts_no_new_work(monkeypatch) -> None:
    """R5-F6: deadline expiring after attempt 1 never starts attempt 2."""
    import time as time_mod

    import sabiroute.api.completions as completions_mod

    base = time_mod.monotonic()
    current = {"now": base}
    monkeypatch.setattr(
        time_mod, "monotonic", lambda: current["now"], raising=False
    )
    monkeypatch.setattr(
        completions_mod.time, "monotonic", lambda: current["now"], raising=False
    )

    stub = StubLiteLLMClient()

    async def fail_once_then_advance_clock(
        decision: Any, messages: Any, **extra: Any
    ) -> dict[str, Any]:
        stub.calls.append(decision.deployment)
        # Attempt 1 consumes the whole deadline budget before failing.
        current["now"] = base + 10.0
        raise LiteLLMClientError("stub failure for primary", status_code=500)

    stub.chat_completion = fail_once_then_advance_clock  # type: ignore[method-assign]
    state = build_gateway_state(
        config=make_config(), client=stub, key_store=InMemoryApiKeyStore()
    )
    state.policies.register(_fast_two())
    provision_test_key(state)
    # Real deadline semantics: absolute monotonic instant, already expired
    # once the fake clock advances past it during attempt 1.
    request = _direct_request(state, deadline_at=base + 5.0)

    response = asyncio.run(
        chat_completions(
            ChatCompletionRequest(model="fast", messages=MESSAGES),
            request,
        )
    )

    assert response.status_code == 503
    assert stub.calls == ["primary"]
    event = _event(state)
    assert event.final_status == 503
    assert event.failure_category == "deadline_exceeded"
    assert [d["selected_deployment"] for d in event.routing_decisions] == ["primary"]
    assert event.routing_decisions[0]["failure_category"] == "server"


def test_r5_f6_deadline_before_first_attempt_starts_nothing(monkeypatch) -> None:
    """R5-F6: an already-expired deadline performs zero provider calls."""
    import sabiroute.api.completions as mod

    monkeypatch.setattr(mod, "_deadline_expired", lambda request: True)
    stub = StubLiteLLMClient()
    client, _ = _client(stub, policies=[_fast_two()])

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES},
    )

    assert response.status_code == 503
    assert response.json()["error"]["type"] == "deadline_exceeded"
    assert stub.calls == []


# --- R5-F7: honest failure/success telemetry -------------------------------------


def test_r5_f7_success_telemetry_marks_health_metrics_latency() -> None:
    """R5-F7: success records health success, metrics, latency, usage, no error."""
    stub = StubLiteLLMClient()
    client, state = _client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "primary", "messages": MESSAGES},
    )

    assert response.status_code == 200
    assert state.health.snapshot()["primary"]["total_successes"] == 1
    assert state.metrics.snapshot()["requests_successful"] == 1
    assert state.usage.totals()["primary"] == 5
    assert len(state.latency.samples["primary"]) == 1
    event = _event(state)
    assert event.final_status == 200
    assert event.failure_category is None
    assert event.routing_decisions[0]["outcome"] == "success"
    assert event.routing_decisions[0]["http_status"] == 200
    assert event.routing_decisions[0]["failure_category"] is None


def test_r5_f7_retryable_failure_telemetry_is_honest() -> None:
    """R5-F7: 500 failure records failure health, error category, and 502."""
    stub = StubLiteLLMClient(failures={"primary": 1}, failure_status=500)
    client, state = _client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "primary", "messages": MESSAGES},
    )

    assert response.status_code == 502
    assert state.health.snapshot()["primary"]["total_failures"] == 1
    assert state.metrics.snapshot()["requests_failed"] == 1
    assert len(state.latency.samples["primary"]) == 1
    event = _event(state)
    assert event.final_status == 502
    assert event.failure_category == "server"
    assert event.routing_decisions[0]["outcome"] == "failure"
    assert event.routing_decisions[0]["failure_category"] == "server"
    assert event.routing_decisions[0]["http_status"] == 500
