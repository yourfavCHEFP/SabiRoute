from __future__ import annotations

import asyncio
import logging
from datetime import datetime

import pytest
from conftest import InMemoryApiKeyStore, StubLiteLLMClient, make_config, provision_test_key
from fastapi.testclient import TestClient
from starlette.requests import Request

from sabiroute.api.completions import ChatCompletionRequest, chat_completions
from sabiroute.gateway import build_gateway_state, empty_gateway_state
from sabiroute.main import create_app, main
from sabiroute.routing.policies import RoutingPolicy
from sabiroute.security.keys import ApiKeyIdentity

MESSAGES = [{"role": "user", "content": "hello"}]


def make_client(stub: StubLiteLLMClient):
    state = build_gateway_state(config=make_config(), client=stub, key_store=InMemoryApiKeyStore())
    key = provision_test_key(state)
    app = create_app(state=state)
    return TestClient(app, headers={"Authorization": f"Bearer {key}"}), state


def make_direct_request(state):
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    record = next(iter(store.records.values()))
    app = create_app(state=state)
    return Request(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/v1/chat/completions",
            "raw_path": b"/v1/chat/completions",
            "query_string": b"",
            "root_path": "",
            "headers": [],
            "client": ("127.0.0.1", 12345),
            "server": ("test", 80),
            "app": app,
            "state": {
                "api_identity": ApiKeyIdentity(
                    key_id=record.key_id, project_id=record.project_id
                )
            },
        }
    )


def test_success_returns_body_and_routing_headers():
    stub = StubLiteLLMClient()
    client, state = make_client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "primary", "messages": MESSAGES},
    )

    assert response.status_code == 200
    assert response.headers["X-SabiRoute-Deployment"] == "primary"
    assert response.json()["model"] == "primary"
    assert stub.calls == ["primary"]

    assert state.metrics.snapshot()["requests_total"] == 1
    assert state.metrics.snapshot()["requests_successful"] == 1
    assert state.usage.totals()["primary"] == 5
    assert state.health.snapshot()["primary"]["healthy"] is True


def test_alias_request_does_not_fan_out():
    stub = StubLiteLLMClient(failures={"primary": 5})
    client, _ = make_client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "primary", "messages": MESSAGES},
    )

    assert response.status_code == 502
    assert response.json()["error"]["attempts"] == ["primary"]
    assert stub.calls == ["primary"]


def test_policy_request_falls_back_to_next_deployment():
    stub = StubLiteLLMClient(failures={"primary": 1})
    client, state = make_client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES},
    )

    assert response.status_code == 200
    assert response.headers["X-SabiRoute-Deployment"] == "secondary"
    assert response.headers["X-SabiRoute-Attempt"] == "2"
    assert stub.calls == ["primary", "secondary"]

    snapshot = state.health.snapshot()
    assert snapshot["primary"]["total_failures"] == 1
    assert snapshot["secondary"]["healthy"] is True


def test_measured_policy_scores_and_persists_each_fallback_decision():
    stub = StubLiteLLMClient(failures={"secondary": 1})
    client, state = make_client(stub)
    state.policies.register(
        RoutingPolicy(
            name="fast",
            deployments=["primary", "secondary"],
            strategy="measured",
            max_attempts=2,
        )
    )
    for _ in range(5):
        state.health.mark_success("primary")
        state.health.mark_success("secondary")
        state.latency.record("primary", 100)
        state.latency.record("secondary", 10)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES},
    )

    assert response.status_code == 200
    assert stub.calls == ["secondary", "primary"]
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    usage_event = next(iter(store.usage_events.values()))
    attempts = usage_event.routing_decisions
    features = usage_event.pre_routing_features
    assert [item["attempt_number"] for item in features] == [1, 2]
    assert all(item["feature_schema_version"] == "1.1" for item in features)
    assert all(
        item["historical_summary_as_of"] == item["decision_timestamp"] for item in features
    )
    assert all("content" not in item for item in features)
    assert all("outcome" not in item for item in features)
    historical = features[0]["deterministic_score_context"]
    assert all(item["reliability_state_scope_id"] for item in historical)
    assert all(item["latency_state_scope_id"] for item in historical)
    assert all(
        item["latest_reliability_observation"] <= features[0]["historical_summary_as_of"]
        for item in historical
    )
    assert all(
        item["latest_latency_observation"] <= features[0]["historical_summary_as_of"]
        for item in historical
    )
    assert [item["selected_deployment"] for item in attempts] == [
        "secondary",
        "primary",
    ]
    assert attempts[0]["scoring_policy_version"] == "deterministic-v1"
    assert attempts[0]["fallback_attempt"] == 1
    assert attempts[0]["outcome"] == "failure"
    assert attempts[1]["outcome"] == "success"
    for attempt in attempts:
        started = datetime.fromisoformat(attempt["attempt_started_at"])
        completed = datetime.fromisoformat(attempt["attempt_completed_at"])
        recorded = datetime.fromisoformat(attempt["outcome_recorded_at"])
        assert started <= completed <= recorded
        assert attempt["attempt_schema_version"] == "1.1"
    assert attempts[0]["eligible_deployments"] == ["primary", "secondary"]
    assert [score["deployment"] for score in attempts[0]["candidate_scores"]] == [
        "primary",
        "secondary",
    ]


def test_current_attempt_outcome_is_not_in_its_own_feature_snapshot():
    stub = StubLiteLLMClient()
    client, state = make_client(stub)
    state.policies.register(
        RoutingPolicy(name="measured_one", deployments=["primary"], strategy="measured")
    )

    first = client.post(
        "/v1/chat/completions",
        json={"model": "measured_one", "messages": MESSAGES},
    )
    second = client.post(
        "/v1/chat/completions",
        json={"model": "measured_one", "messages": MESSAGES},
    )

    assert first.status_code == second.status_code == 200
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    snapshots = [event.pre_routing_features[0] for event in store.usage_events.values()]
    assert snapshots[0]["deterministic_score_context"][0]["reliability_samples"] == 0
    assert snapshots[0]["deterministic_score_context"][0]["latency_samples"] == 0
    assert snapshots[1]["deterministic_score_context"][0]["reliability_samples"] == 1
    assert snapshots[1]["deterministic_score_context"][0]["latency_samples"] == 1


def test_feature_snapshot_is_durable_before_provider_execution():
    stub = StubLiteLLMClient()
    original_completion = stub.chat_completion
    client, state = make_client(stub)
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)

    async def inspect_before_execution(decision, messages, **extra):
        event = next(iter(store.usage_events.values()))
        assert event.final_status is None
        assert len(event.pre_routing_features) == 1
        assert event.routing_decisions == ()
        return await original_completion(decision, messages, **extra)

    stub.chat_completion = inspect_before_execution  # type: ignore[method-assign]
    response = client.post(
        "/v1/chat/completions",
        json={"model": "primary", "messages": MESSAGES},
    )

    assert response.status_code == 200
    event = next(iter(store.usage_events.values()))
    assert event.final_status == 200
    assert len(event.pre_routing_features) == len(event.routing_decisions) == 1


def test_snapshot_persistence_failure_prevents_provider_execution():
    stub = StubLiteLLMClient()
    client, state = make_client(stub)
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    store.fail_feature_snapshot_writes = True

    response = client.post(
        "/v1/chat/completions",
        json={"model": "primary", "messages": MESSAGES},
    )

    assert response.status_code == 503
    assert response.json()["error"]["type"] == "telemetry_store_unavailable"
    assert stub.calls == []
    event = next(iter(store.usage_events.values()))
    assert event.final_status is None
    assert event.pre_routing_features == ()
    assert event.routing_decisions == ()


def test_unexpected_provider_exception_persists_attempt_timestamps_without_fallback():
    stub = StubLiteLLMClient()

    async def unexpected_error(decision, messages, **kwargs):
        stub.calls.append(decision.deployment)
        raise RuntimeError("simulated provider adapter exception")

    stub.chat_completion = unexpected_error  # type: ignore[method-assign]
    client, state = make_client(stub)
    client = TestClient(client.app, headers=client.headers, raise_server_exceptions=False)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES},
    )

    assert response.status_code == 500
    assert stub.calls == ["primary"]
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    event = next(iter(store.usage_events.values()))
    assert event.final_status == 500
    attempt = event.routing_decisions[0]
    assert attempt["outcome"] == "failure"
    assert attempt["failure_category"] == "provider_exception"
    assert attempt["attempt_started_at"] <= attempt["attempt_completed_at"]
    assert attempt["attempt_completed_at"] <= attempt["outcome_recorded_at"]


def test_policy_alias_normalization():
    stub = StubLiteLLMClient(failures={"primary": 1})
    client, _ = make_client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "SabiRoute_Fast", "messages": MESSAGES},
    )

    assert response.status_code == 200
    assert response.headers["X-SabiRoute-Deployment"] == "secondary"


def test_non_retryable_client_error_stops_retrying():
    stub = StubLiteLLMClient(failures={"primary": 3}, failure_status=400)
    client, _ = make_client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "ultimate", "messages": MESSAGES},
    )

    assert response.status_code == 502
    assert stub.calls == ["primary"]


def test_unknown_model_returns_available_list():
    stub = StubLiteLLMClient()
    client, _ = make_client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "nope", "messages": MESSAGES},
    )

    assert response.status_code == 404
    assert "primary" in response.json()["error"]["available_models"]


def test_streaming_returns_incremental_sse_and_records_telemetry():
    stub = StubLiteLLMClient()
    client, state = make_client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "primary", "messages": MESSAGES, "stream": True},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "hello" in response.text and " world" in response.text
    assert response.text.count("[DONE]") == 1
    assert response.headers["X-SabiRoute-Deployment"] == "primary"
    assert state.metrics.snapshot()["requests_successful"] == 1
    assert state.usage.totals()["primary"] == 5
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    event = next(iter(store.usage_events.values()))
    assert event.final_status == 200
    assert event.routing_decisions[0]["outcome"] == "success"
    assert event.pre_routing_features[0]["streaming"] is True
    attempt = event.routing_decisions[0]
    assert attempt["attempt_started_at"] <= attempt["attempt_completed_at"]
    assert attempt["attempt_completed_at"] <= attempt["outcome_recorded_at"]


def test_streaming_falls_back_only_before_first_event():
    stub = StubLiteLLMClient(failures={"primary": 1})
    client, state = make_client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES, "stream": True},
    )

    assert response.status_code == 200
    assert response.headers["X-SabiRoute-Deployment"] == "secondary"
    assert response.headers["X-SabiRoute-Attempt"] == "2"
    assert stub.calls == ["primary", "secondary"]
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    event = next(iter(store.usage_events.values()))
    assert [attempt["outcome"] for attempt in event.routing_decisions] == [
        "failure",
        "success",
    ]
    assert all(attempt["attempt_schema_version"] == "1.1" for attempt in event.routing_decisions)


def test_streaming_failure_after_first_event_is_not_replayed():
    stub = StubLiteLLMClient()

    class InterruptedStream:
        async def events(self):
            yield b'data: {"choices":[{"delta":{"content":"partial"}}]}\n\n'
            raise RuntimeError("simulated mid-stream failure")

        async def aclose(self):
            return None

    async def interrupted_stream(decision, messages, **extra):
        stub.calls.append(decision.deployment)
        return InterruptedStream()

    stub.start_chat_completion_stream = interrupted_stream
    client, state = make_client(stub)
    state.policies.register(
        RoutingPolicy(
            name="fast",
            deployments=["primary", "secondary"],
            strategy="measured",
            max_attempts=2,
        )
    )

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES, "stream": True},
    )

    assert response.status_code == 200
    assert "partial" in response.text
    assert '"type":"upstream_error"' in response.text
    assert response.text.count("[DONE]") == 1
    assert stub.calls == ["primary"]
    assert state.health.snapshot()["primary"]["total_failures"] == 1
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    event = next(iter(store.usage_events.values()))
    assert event.final_status == 502
    assert event.failure_category == "stream_interrupted"
    assert event.routing_decisions[0]["outcome"] == "failure"
    attempt = event.routing_decisions[0]
    assert attempt["attempt_started_at"] <= attempt["attempt_completed_at"]
    assert attempt["attempt_completed_at"] <= attempt["outcome_recorded_at"]


def test_non_stream_cancellation_finalizes_an_interrupted_attempt():
    stub = StubLiteLLMClient()

    async def cancelled_completion(decision, messages, **extra):
        stub.calls.append(decision.deployment)
        raise asyncio.CancelledError

    stub.chat_completion = cancelled_completion  # type: ignore[method-assign]
    _, state = make_client(stub)
    request = make_direct_request(state)

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(
            chat_completions(
                ChatCompletionRequest(model="primary", messages=MESSAGES), request
            )
        )

    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    event = next(iter(store.usage_events.values()))
    assert event.final_status == 499
    assert len(event.pre_routing_features) == len(event.routing_decisions) == 1
    assert event.routing_decisions[0]["failure_category"] == "client_cancelled"
    assert event.routing_decisions[0]["outcome"] == "failure"
    # Cancellation must not poison deployment health: no failure recorded.
    snapshot = state.health.snapshot()
    assert snapshot["primary"]["healthy"] is True
    assert snapshot["primary"]["total_failures"] == 0


def test_stream_cancellation_before_first_frame_finalizes_attempt():
    stub = StubLiteLLMClient()

    async def cancelled_stream(decision, messages, **extra):
        stub.calls.append(decision.deployment)
        raise asyncio.CancelledError

    stub.start_chat_completion_stream = cancelled_stream  # type: ignore[method-assign]
    _, state = make_client(stub)
    request = make_direct_request(state)

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(
            chat_completions(
                ChatCompletionRequest(
                    model="primary", messages=MESSAGES, stream=True
                ),
                request,
            )
        )

    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    event = next(iter(store.usage_events.values()))
    assert event.final_status == 499
    assert len(event.pre_routing_features) == len(event.routing_decisions) == 1
    assert event.routing_decisions[0]["failure_category"] == "client_cancelled"


def test_stream_cancellation_during_setup_cleanup_still_finalizes_attempt():
    stub = StubLiteLLMClient()

    class CancelledStream:
        async def events(self):
            raise asyncio.CancelledError
            yield b""  # Keep this an async iterator.

        async def aclose(self):
            raise asyncio.CancelledError

    async def start_stream(decision, messages, **extra):
        stub.calls.append(decision.deployment)
        return CancelledStream()

    stub.start_chat_completion_stream = start_stream  # type: ignore[method-assign]
    _, state = make_client(stub)
    request = make_direct_request(state)

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(
            chat_completions(
                ChatCompletionRequest(model="primary", messages=MESSAGES, stream=True),
                request,
            )
        )

    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    event = next(iter(store.usage_events.values()))
    assert event.final_status == 499
    assert len(event.pre_routing_features) == len(event.routing_decisions) == 1
    assert event.routing_decisions[0]["failure_category"] == "client_cancelled"


def test_stream_cancellation_after_partial_delivery_is_recorded_as_client_cancel():
    stub = StubLiteLLMClient()

    class CancelledStream:
        async def events(self):
            yield b'data: {"choices":[{"delta":{"content":"partial"}}]}\n\n'
            raise asyncio.CancelledError

        async def aclose(self):
            raise asyncio.CancelledError

    async def start_stream(decision, messages, **extra):
        stub.calls.append(decision.deployment)
        return CancelledStream()

    stub.start_chat_completion_stream = start_stream  # type: ignore[method-assign]
    _, state = make_client(stub)
    request = make_direct_request(state)

    async def consume_until_cancelled():
        response = await chat_completions(
            ChatCompletionRequest(model="primary", messages=MESSAGES, stream=True),
            request,
        )
        iterator = response.body_iterator.__aiter__()
        first = await anext(iterator)
        assert b"partial" in first
        with pytest.raises(asyncio.CancelledError):
            await anext(iterator)

    asyncio.run(consume_until_cancelled())

    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    event = next(iter(store.usage_events.values()))
    assert event.final_status == 499
    assert len(event.pre_routing_features) == len(event.routing_decisions) == 1
    assert event.routing_decisions[0]["failure_category"] == "client_cancelled"


def test_stream_finalization_failure_is_logged_and_remains_unfinalized(caplog):
    stub = StubLiteLLMClient()
    client, state = make_client(stub)
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    store.fail_finalize_usage_writes = True

    with caplog.at_level(logging.ERROR, logger="sabiroute.api.completions"):
        response = client.post(
            "/v1/chat/completions",
            json={"model": "primary", "messages": MESSAGES, "stream": True},
        )

    assert response.status_code == 200
    assert response.text.count("[DONE]") == 1
    assert "Durable request telemetry finalization failed." in caplog.text
    event = next(iter(store.usage_events.values()))
    assert event.final_status is None
    assert len(event.pre_routing_features) == 1
    assert event.routing_decisions == ()


def test_non_stream_finalization_failure_returns_unavailable_and_stays_unfinalized():
    stub = StubLiteLLMClient()
    client, state = make_client(stub)
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    store.fail_finalize_usage_writes = True

    response = client.post(
        "/v1/chat/completions",
        json={"model": "primary", "messages": MESSAGES},
    )

    assert response.status_code == 503
    assert response.json()["error"]["type"] == "usage_store_unavailable"
    assert stub.calls == ["primary"]
    event = next(iter(store.usage_events.values()))
    assert event.final_status is None
    assert len(event.pre_routing_features) == 1
    assert event.routing_decisions == ()


def test_empty_registry_returns_503_without_startup_detail():
    state = empty_gateway_state()
    state.startup_error = "config not found at /srv/sabiroute/config/config.yaml"
    key = provision_test_key(state)
    app = create_app(state=state)

    with TestClient(app, headers={"Authorization": f"Bearer {key}"}) as client:
        response = client.post(
            "/v1/chat/completions",
            json={"model": "primary", "messages": MESSAGES},
        )

    assert response.status_code == 503
    body = response.json()["error"]
    assert body["type"] == "sabiroute_not_configured"
    assert body["message"] == "SabiRoute has no deployments configured."
    assert "config not found" not in response.text
    assert "/srv/sabiroute" not in response.text


def test_exhausted_attempts_omit_upstream_error_detail():
    # Upstream prose must not reach API callers: the terminal 502 carries
    # the stable category and per-attempt telemetry, never provider text.
    marker = "provider-says-no-such-model-xyz"
    stub = StubLiteLLMClient(failures={"primary": 5, "secondary": 5})
    original = stub.chat_completion

    async def failing(decision, messages, **extra):
        from sabiroute.providers.litellm_client import LiteLLMClientError

        stub.calls.append(decision.deployment)
        remaining = stub.failures_remaining.get(decision.deployment, 0)
        if remaining > 0:
            stub.failures_remaining[decision.deployment] = remaining - 1
            raise LiteLLMClientError(f"{marker} for {decision.deployment}")
        return await original(decision, messages, **extra)

    stub.chat_completion = failing  # type: ignore[method-assign]
    client, state = make_client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES},
    )

    assert response.status_code == 502
    body = response.json()["error"]
    assert body["type"] == "sabiroute_upstream_error"
    assert body["failure_category"] == "transport"
    assert "last_error" not in body
    assert marker not in response.text

    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    event = next(iter(store.usage_events.values()))
    assert event.final_status == 502
    assert event.failure_category == "transport"


def test_extras_pass_through_to_client():
    stub = StubLiteLLMClient()
    captured: dict = {}
    original = stub.chat_completion

    async def capture(decision, messages, **extra):
        captured.update(extra)
        return await original(decision, messages, **extra)

    stub.chat_completion = capture  # type: ignore[method-assign]
    client, _ = make_client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "primary",
            "messages": MESSAGES,
            "temperature": 0.2,
            "top_p": 0.9,
        },
    )

    assert response.status_code == 200
    assert captured["temperature"] == 0.2
    assert captured["top_p"] == 0.9


def test_console_entry_point_exists():
    assert callable(main)


def test_policy_exhaustion_fails_closed_with_finalized_telemetry():
    stub = StubLiteLLMClient(failures={"primary": 5, "secondary": 5})
    client, state = make_client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES},
    )

    assert response.status_code == 502
    assert response.json()["error"]["attempts"] == ["primary", "secondary"]
    assert stub.calls == ["primary", "secondary"]

    # Cooldown trips only at three consecutive failures, so one failure
    # each increments the counters without marking either unhealthy.
    snapshot = state.health.snapshot()
    assert snapshot["primary"]["total_failures"] == 1
    assert snapshot["secondary"]["total_failures"] == 1
    assert snapshot["primary"]["healthy"] is True
    assert snapshot["secondary"]["healthy"] is True

    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    event = next(iter(store.usage_events.values()))
    assert event.final_status == 502
    assert [attempt["outcome"] for attempt in event.routing_decisions] == [
        "failure",
        "failure",
    ]


def test_upstream_rate_limit_falls_back_and_records_attempt():
    stub = StubLiteLLMClient(failures={"primary": 1}, failure_status=429)
    client, state = make_client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES},
    )

    assert response.status_code == 200
    assert response.headers["X-SabiRoute-Deployment"] == "secondary"
    assert stub.calls == ["primary", "secondary"]

    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    event = next(iter(store.usage_events.values()))
    assert event.final_status == 200
    first, second = event.routing_decisions
    assert first["outcome"] == "failure"
    assert first["failure_category"] == "rate_limit"
    assert first["http_status"] == 429
    assert second["outcome"] == "success"


def test_upstream_auth_failure_fails_over_without_client_denial():
    # A 401 from the upstream provider is SabiRoute being denied, not the
    # client: the attempt is recorded and the next deployment is tried.
    # Client authentication still happens before any attempt (dependency),
    # so this path can never OBSERVE a client-denied request.
    from sabiroute.providers.litellm_client import LiteLLMClientError

    stub = StubLiteLLMClient()

    async def expired_key_first(decision, messages, **kwargs):
        if decision.deployment == "primary":
            raise LiteLLMClientError(
                "LiteLLM gateway returned HTTP 401: invalid provider key",
                status_code=401,
            )
        return await StubLiteLLMClient.chat_completion(
            stub, decision, messages, **kwargs
        )

    stub.chat_completion = expired_key_first  # type: ignore[method-assign]
    client, state = make_client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES},
    )

    assert response.status_code == 200
    assert response.headers["X-SabiRoute-Deployment"] == "secondary"

    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    event = next(iter(store.usage_events.values()))
    assert event.final_status == 200
    first, second = event.routing_decisions
    assert first["selected_deployment"] == "primary"
    assert first["outcome"] == "failure"
    assert first["failure_category"] == "auth"
    assert first["http_status"] == 401
    assert second["selected_deployment"] == "secondary"
    assert second["outcome"] == "success"


def test_upstream_timeout_retries_next_deployment():
    from sabiroute.providers.litellm_client import LiteLLMClientError

    stub = StubLiteLLMClient()

    async def timeout_first(decision, messages, **kwargs):
        if decision.deployment == "primary" and not getattr(
            timeout_first, "fired", False
        ):
            timeout_first.fired = True  # type: ignore[attr-defined]
            raise LiteLLMClientError(
                "LiteLLM gateway request timed out.", status_code=None
            )
        return await StubLiteLLMClient.chat_completion(
            stub, decision, messages, **kwargs
        )

    stub.chat_completion = timeout_first  # type: ignore[method-assign]
    client, state = make_client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES},
    )

    assert response.status_code == 200
    assert response.headers["X-SabiRoute-Deployment"] == "secondary"
    assert stub.calls == ["secondary"]

    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    event = next(iter(store.usage_events.values()))
    first, second = event.routing_decisions
    assert first["selected_deployment"] == "primary"
    assert first["outcome"] == "failure"
    assert first["failure_category"] == "transport"
    assert second["selected_deployment"] == "secondary"
    assert second["outcome"] == "success"


def test_all_unhealthy_candidates_rejected_before_provider_execution():
    stub = StubLiteLLMClient()
    client, state = make_client(stub)
    # The fixture "fast" policy spans more than primary/secondary, so every
    # registered deployment must be cooling down for the pool to be empty.
    for _ in range(3):
        for name in ("primary", "secondary", "cloudy", "literal-key"):
            state.health.mark_failure(name)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES},
    )

    assert response.status_code == 503
    assert response.json()["error"]["type"] == "no_healthy_deployment"
    assert stub.calls == []

    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    event = next(iter(store.usage_events.values()))
    assert event.final_status == 503
    assert event.failure_category == "no_healthy_deployment"
    assert tuple(event.routing_decisions) == ()


def test_malformed_upstream_text_body_fails_closed_without_retry():
    # Mirrors LiteLLMClient: HTTP 200 whose body is not JSON raises with
    # status 200 and a text response_body. Replay-unsafe: no fallback.
    from sabiroute.providers.litellm_client import LiteLLMClientError

    stub = StubLiteLLMClient()

    async def text_body(decision, messages, **kwargs):
        stub.calls.append(decision.deployment)
        raise LiteLLMClientError(
            "LiteLLM gateway returned a non-object JSON response.",
            status_code=200,
            response_body="upstream gateway error page",
        )

    stub.chat_completion = text_body  # type: ignore[method-assign]
    client, state = make_client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "primary", "messages": MESSAGES},
    )

    assert response.status_code == 502
    assert response.json()["error"]["type"] == "sabiroute_upstream_error"
    assert response.json()["error"]["attempts"] == ["primary"]
    assert response.headers["X-SabiRoute-Request-ID"]
    assert stub.calls == ["primary"]

    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    event = next(iter(store.usage_events.values()))
    assert event.final_status == 502
    (decision,) = event.routing_decisions
    assert decision["outcome"] == "failure"
    assert decision["failure_category"] == "client"
    assert decision["http_status"] == 200
    assert decision["usage"] is None
    assert decision["actual_cost_usd"] is None
    assert event.total_tokens is None


def test_malformed_upstream_list_body_fails_closed_without_retry():
    # Mirrors LiteLLMClient: HTTP 200 with valid JSON of unexpected
    # top-level type raises with status 200. Same no-retry contract.
    from sabiroute.providers.litellm_client import LiteLLMClientError

    stub = StubLiteLLMClient()

    async def list_body(decision, messages, **kwargs):
        stub.calls.append(decision.deployment)
        raise LiteLLMClientError(
            "LiteLLM gateway returned a non-object JSON response.",
            status_code=200,
            response_body=[{"unexpected": "list"}],
        )

    stub.chat_completion = list_body  # type: ignore[method-assign]
    client, state = make_client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "primary", "messages": MESSAGES},
    )

    assert response.status_code == 502
    assert response.json()["error"]["type"] == "sabiroute_upstream_error"
    assert response.json()["error"]["attempts"] == ["primary"]
    assert response.headers["X-SabiRoute-Request-ID"]
    assert stub.calls == ["primary"]

    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    event = next(iter(store.usage_events.values()))
    assert event.final_status == 502
    (decision,) = event.routing_decisions
    assert decision["outcome"] == "failure"
    assert decision["failure_category"] == "client"
    assert decision["http_status"] == 200
    assert decision["usage"] is None
    assert decision["actual_cost_usd"] is None
    assert event.total_tokens is None


@pytest.mark.parametrize(
    ("model", "failures", "expected_status"),
    [
        ("primary", {}, 200),
        ("fast", {"primary": 5, "secondary": 5}, 502),
    ],
)
def test_telemetry_finalized_exactly_once(model, failures, expected_status):
    stub = StubLiteLLMClient(failures=failures)
    client, state = make_client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": model, "messages": MESSAGES},
    )

    assert response.status_code == expected_status
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    assert store.finalize_calls == 1
    event = next(iter(store.usage_events.values()))
    assert event.final_status == expected_status


def test_denied_request_finalized_exactly_once():
    # Budget denial needs no Redis: the denial path must still finalize once.
    from sabiroute.security.keys import ApiKeyBudget

    stub = StubLiteLLMClient()
    client, state = make_client(stub)
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    record = next(iter(store.records.values()))
    assert store.set_budget(record.key_id, ApiKeyBudget(daily_tokens=1))

    denied = client.post(
        "/v1/chat/completions",
        json={"model": "primary", "messages": MESSAGES, "max_tokens": 5},
    )

    assert denied.status_code == 429
    assert denied.json()["error"]["type"] == "budget_exceeded"
    assert stub.calls == []
    assert store.finalize_calls == 1


def test_streaming_open_exhaustion_returns_json_error_without_partial_stream():
    stub = StubLiteLLMClient(failures={"primary": 5, "secondary": 5})
    client, state = make_client(stub)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES, "stream": True},
    )

    assert response.status_code == 502
    assert "text/event-stream" not in response.headers.get("content-type", "")
    assert "[DONE]" not in response.text
    assert response.json()["error"]["attempts"] == ["primary", "secondary"]

    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    event = next(iter(store.usage_events.values()))
    assert event.final_status == 502
    assert [attempt["outcome"] for attempt in event.routing_decisions] == [
        "failure",
        "failure",
    ]


def test_sustained_failure_cools_down_and_recovers():
    stub = StubLiteLLMClient(failures={"primary": 100})
    client, state = make_client(stub)

    deployments = []
    for _ in range(5):
        response = client.post(
            "/v1/chat/completions",
            json={"model": "fast", "messages": MESSAGES},
        )
        assert response.status_code == 200
        deployments.append(response.headers["X-SabiRoute-Deployment"])

    # Primary fails every time: after three consecutive failures it cools
    # down, so later requests skip it and go straight to secondary.
    assert deployments[:3] == ["secondary"] * 3
    assert stub.calls.count("primary") == 3
    assert deployments[3:] == ["secondary"] * 2
    assert stub.calls.count("primary") == 3
    assert state.health.deployments["primary"].healthy is False

    # After cooldown expiry the failed deployment is tried again.
    from datetime import timedelta as _td

    from sabiroute.routing.health import utc_now as _utc_now

    state.health.deployments["primary"].cooldown_until = _utc_now() - _td(seconds=1)
    before = stub.calls.count("primary")
    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES},
    )
    assert response.status_code == 200
    assert stub.calls.count("primary") == before + 1


def test_request_lifecycle_reconstructable_from_persisted_telemetry():
    stub = StubLiteLLMClient(failures={"primary": 1})
    client, state = make_client(stub)
    client.post("/v1/chat/completions", json={"model": "fast", "messages": MESSAGES})

    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    (event,) = store.usage_events.values()

    # Reconstruct the incident from the persisted record alone.
    assert event.final_status == 200
    attempts = sorted(
        event.routing_decisions, key=lambda attempt: attempt["fallback_attempt"]
    )
    assert [attempt["fallback_attempt"] for attempt in attempts] == [1, 2]
    assert [attempt["selected_deployment"] for attempt in attempts] == [
        "primary",
        "secondary",
    ]
    assert [attempt["outcome"] for attempt in attempts] == ["failure", "success"]
    assert attempts[0]["failure_category"] is not None
    assert event.final_deployment == attempts[-1]["selected_deployment"]
    assert all(
        attempt["logical_request_id"] == event.request_id for attempt in attempts
    )
    assert all(attempt["attempt_schema_version"] == "1.1" for attempt in attempts)


def test_missing_key_store_fails_closed_at_endpoint_layer():
    # Defense in depth: even past authentication, a missing store must not
    # execute. Via HTTP this is unreachable (the auth dependency rejects
    # first), so the endpoint is exercised directly.
    import json

    stub = StubLiteLLMClient()
    _, state = make_client(stub)
    request = make_direct_request(state)
    state.key_store = None

    response = asyncio.run(
        chat_completions(
            ChatCompletionRequest(model="primary", messages=MESSAGES), request
        )
    )

    assert response.status_code == 503
    assert json.loads(response.body)["error"]["type"] == "usage_store_unavailable"
    assert stub.calls == []


def test_cli_help_exits_without_starting_server(capsys):
    from unittest import mock

    from sabiroute.main import CLI_USAGE, main

    with mock.patch("uvicorn.run") as run:
        assert main(["--help"]) is None
    run.assert_not_called()
    assert "Usage: sabiroute" in capsys.readouterr().out
    assert CLI_USAGE.startswith("Usage: sabiroute")


def test_cli_unknown_arguments_fail_without_starting_server(capsys):
    from unittest import mock

    import pytest

    from sabiroute.main import main

    with mock.patch("uvicorn.run") as run:
        with pytest.raises(SystemExit) as exc_info:
            main(["--port", "9000"])
    run.assert_not_called()
    assert exc_info.value.code != 0
    assert "Usage: sabiroute" in capsys.readouterr().err


def test_large_text_body_handled_without_error():
    stub = StubLiteLLMClient()
    client, state = make_client(stub)
    big_text = "hello world, this is a large payload. " * 8192  # ~300KB

    response = client.post(
        "/v1/chat/completions",
        json={"model": "primary", "messages": [{"role": "user", "content": big_text}]},
    )

    assert response.status_code == 200
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    event = next(iter(store.usage_events.values()))
    assert event.final_status == 200
    assert event.total_tokens == 5
