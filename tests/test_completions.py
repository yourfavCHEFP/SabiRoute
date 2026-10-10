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


def test_empty_registry_returns_503_with_startup_error():
    state = empty_gateway_state()
    state.startup_error = "config not found"
    key = provision_test_key(state)
    app = create_app(state=state)

    with TestClient(app, headers={"Authorization": f"Bearer {key}"}) as client:
        response = client.post(
            "/v1/chat/completions",
            json={"model": "primary", "messages": MESSAGES},
        )

    assert response.status_code == 503
    assert "config not found" in response.json()["error"]["message"]


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
