"""R6.2-R6.5 — the request-transform pipeline, contract by contract.

Each test names the contract it pins. The negative cases are the point: a contract that
only passes on well-formed input has not been tested.
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
import logging
from typing import Any, cast

import pytest
from conftest import InMemoryApiKeyStore, StubLiteLLMClient, make_config
from fastapi.testclient import TestClient
from pydantic import ValidationError
from redis.asyncio import Redis

from sabiroute.capabilities import Capability
from sabiroute.config.validation import (
    OptimizationPolicy,
    load_optimization_settings,
    resolve_optimization_policy,
)
from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app
from sabiroute.request_transform import (
    BypassReason,
    CanonicalisationError,
    CapabilityLoss,
    EffectiveRequestError,
    FrozenOriginal,
    TransformError,
    ValidationFailure,
    canonical_bytes,
    check_capability_preservation,
    compress,
    derive_effective,
    evaluate_bypass,
    fail_to_original,
    is_canonical,
    protected_indices,
    run,
    tool_spans,
    validate_effective,
    within_budget,
)
from sabiroute.request_transform import pipeline as pipeline_module
from sabiroute.routing.policies import RoutingPolicy
from sabiroute.security.keys import issue_api_key
from sabiroute.security.rate_limit import RedisTokenBucket

LOGGER = logging.getLogger("test.request_transform")

def _messages() -> list[dict[str, object]]:
    return [
        {"role": "system", "content": "be brief"},
        {"role": "user", "content": "one"},
        {"role": "assistant", "content": "two"},
        {"role": "user", "content": "three"},
    ]

# --- I1: immutable original -------------------------------------------------

def test_i1_byte_equality_pre_and_post_freeze():
    messages = _messages()
    before = canonical_bytes(messages)

    frozen = FrozenOriginal.freeze(messages)

    assert canonical_bytes(frozen.as_messages()) == before

def test_i1_mutating_the_source_cannot_reach_the_snapshot():
    messages = _messages()
    frozen = FrozenOriginal.freeze(messages)

    messages[0]["content"] = "MUTATED"
    messages.append({"role": "user", "content": "injected"})

    assert frozen.as_messages()[0]["content"] == "be brief"
    assert len(frozen) == 4

def test_i1_mutating_the_returned_copy_cannot_reach_the_snapshot():
    frozen = FrozenOriginal.freeze(_messages())

    copy = frozen.as_messages()
    copy[0]["content"] = "MUTATED"

    assert frozen.as_messages()[0]["content"] == "be brief"

def test_i1_nested_structures_are_frozen_too():
    messages = [
        {
            "role": "user",
            "content": [{"type": "text", "text": "hi"}],
        }
    ]
    frozen = FrozenOriginal.freeze(messages)

    messages[0]["content"][0]["text"] = "MUTATED"

    assert frozen.as_messages()[0]["content"][0]["text"] == "hi"

def test_i1_rejects_non_mapping_messages():
    with pytest.raises(TypeError):
        FrozenOriginal.freeze(["not a mapping"])  # type: ignore[list-item]

# --- I2: canonical representation -------------------------------------------

def test_i2_is_deterministic():
    messages = _messages()

    assert canonical_bytes(messages) == canonical_bytes(messages)

def test_i2_is_idempotent():
    messages = _messages()
    once = canonical_bytes(messages)

    twice = canonical_bytes(json.loads(once))

    assert twice == once
    assert is_canonical(messages)

def test_i2_never_expands():
    messages = _messages()
    default = json.dumps(messages, ensure_ascii=False).encode("utf-8")

    assert within_budget(default, canonical_bytes(messages))

def test_i2_unsupported_shape_fails_closed():
    with pytest.raises(CanonicalisationError):
        canonical_bytes([{"role": "user", "content": object()}])

def test_i2_non_sequence_fails_closed():
    with pytest.raises(CanonicalisationError):
        canonical_bytes({"role": "user"})

# --- I3: effective request ---------------------------------------------------

def test_i3_monotone_shrink_rejects_expansion():
    original = [{"role": "user", "content": "x"}]
    expanded = [{"role": "user", "content": "x" * 100}]

    with pytest.raises(EffectiveRequestError):
        derive_effective(original, expanded, policy_id=None, policy_version=1)

def test_i3_shrunk_flag_tracks_actual_shrinkage():
    original = _messages()

    same = derive_effective(original, list(original), policy_id=None, policy_version=1)
    smaller = derive_effective(original, original[:2], policy_id=None, policy_version=1)

    assert same.shrunk is False
    assert smaller.shrunk is True

def test_i3_effective_request_is_frozen():
    effective = derive_effective(
        _messages(), _messages(), policy_id=None, policy_version=1
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        effective.policy_version = 2  # type: ignore[misc]

# --- I4: transformation metadata --------------------------------------------

def test_i4_record_carries_no_message_text():
    # A distinctive marker, so a substring collision with a field name cannot mask a leak.
    marker = "SENTINEL-CONTENT-7f3a"
    messages = [
        {"role": "system", "content": marker},
        {"role": "user", "content": marker + "-user"},
    ]
    outcome = run(
        messages=messages,
        policy=OptimizationPolicy(enabled=True, max_ratio=0.5),
        request_id="req-1",
        logger=LOGGER,
    )

    assert outcome.record is not None
    serialised = json.dumps(outcome.record.to_dict())
    assert marker not in serialised

def test_i4_record_is_scalar_only():
    outcome = run(
        messages=_messages(),
        policy=OptimizationPolicy(enabled=True, max_ratio=0.5),
        request_id="req-1",
        logger=LOGGER,
    )

    assert outcome.record is not None
    for value in outcome.record.to_dict().values():
        assert value is None or isinstance(value, (str, int, float, bool))

# --- I5: the optimisation policy --------------------------------------------

def test_i5_defaults_to_disabled_with_no_ratio():
    settings = load_optimization_settings(None)

    assert settings.policy.enabled is False
    assert settings.policy.max_ratio is None

def test_i5_rejects_a_ratio_above_one():
    with pytest.raises(ValidationError):
        OptimizationPolicy(max_ratio=1.5)

def test_i5_rejects_a_ratio_of_zero():
    with pytest.raises(ValidationError):
        OptimizationPolicy(max_ratio=0.0)

def test_i5_per_route_override_applies():
    settings = load_optimization_settings(
        {"policy": {"enabled": False}, "routes": {"fast": {"enabled": True}}}
    )

    assert resolve_optimization_policy(settings, "fast").enabled is True
    assert resolve_optimization_policy(settings, "other").enabled is False

# --- I6: capability preservation --------------------------------------------

def test_i6_dropping_multimodal_content_fails():
    original = [
        {"role": "user", "content": [{"type": "image_url", "image_url": {}}]},
        {"role": "user", "content": "keep"},
    ]

    with pytest.raises(CapabilityLoss):
        check_capability_preservation(
            original, original[1:], frozenset({Capability.VISION})
        )

def test_i6_dropping_a_tool_call_fails():
    original = [
        {"role": "assistant", "content": "", "tool_calls": [{"id": "c1"}]},
        {"role": "user", "content": "keep"},
    ]

    with pytest.raises(CapabilityLoss):
        check_capability_preservation(
            original, original[1:], frozenset({Capability.TOOL_USE})
        )

def test_i6_no_requirement_means_no_failure():
    original = [
        {"role": "user", "content": [{"type": "image_url", "image_url": {}}]},
        {"role": "user", "content": "keep"},
    ]

    check_capability_preservation(original, original[1:], frozenset())

# --- I7: explicit bypass -----------------------------------------------------

def test_i7_policy_disabled_bypasses():
    decision = evaluate_bypass(
        policy_enabled=False, caller_signal=None, request_id="r"
    )

    assert decision.bypassed is True
    assert decision.reason is BypassReason.POLICY_DISABLED

def test_i7_caller_signal_true_bypasses():
    decision = evaluate_bypass(
        policy_enabled=True, caller_signal=True, request_id="r"
    )

    assert decision.bypassed is True
    assert decision.reason is BypassReason.CALLER_SIGNAL

def test_i7_malformed_signal_falls_back_to_the_operator_default():
    decision = evaluate_bypass(
        policy_enabled=True, caller_signal="yes please", request_id="r"
    )

    assert decision.bypassed is False
    assert decision.reason is BypassReason.MALFORMED_SIGNAL

def test_i7_absent_signal_does_not_bypass():
    decision = evaluate_bypass(
        policy_enabled=True, caller_signal=None, request_id="r"
    )

    assert decision.bypassed is False
    assert decision.reason is BypassReason.NOT_BYPASSED

# --- I8: validation ----------------------------------------------------------

def test_i8_rejects_an_empty_request():
    with pytest.raises(ValidationFailure):
        validate_effective([])

def test_i8_rejects_too_many_messages():
    with pytest.raises(ValidationFailure):
        validate_effective([{"role": "user", "content": "x"}] * 257)

def test_i8_rejects_oversized_characters():
    with pytest.raises(ValidationFailure):
        validate_effective([{"role": "user", "content": "x" * 500_001}])

def test_i8_rejects_a_message_with_no_role():
    with pytest.raises(ValidationFailure):
        validate_effective([{"content": "x"}])

def test_i8_accepts_a_normal_request():
    validate_effective(_messages())

# --- I9: fail-to-original ----------------------------------------------------

def test_i9_returns_the_original_on_exception():
    original = _messages()

    def boom() -> list[dict[str, object]]:
        raise TransformError("nope")

    result = fail_to_original(
        boom, original, logger=LOGGER, request_id="r", reason="test"
    )

    assert result is original

def test_i9_does_not_swallow_cancelled_error():
    original = _messages()

    def cancel() -> list[dict[str, object]]:
        raise asyncio.CancelledError()

    with pytest.raises(asyncio.CancelledError):
        fail_to_original(
            cancel, original, logger=LOGGER, request_id="r", reason="test"
        )

# --- R6.4: compression -------------------------------------------------------

def test_r64_protects_system_last_user_and_last_assistant():
    messages = _messages()

    protected = protected_indices(messages)

    assert 0 in protected  # system
    assert 3 in protected  # last user
    assert 2 in protected  # last assistant

def test_r64_protects_everything_up_to_the_last_cache_breakpoint():
    messages = [
        {"role": "user", "content": "a"},
        {"role": "user", "content": "b", "cache_control": {"type": "ephemeral"}},
        {"role": "user", "content": "c"},
        {"role": "user", "content": "d"},
    ]

    protected = protected_indices(messages)

    assert {0, 1} <= protected
    assert 2 not in protected

def test_r64_tool_span_is_contiguous_and_atomic():
    messages = [
        {"role": "assistant", "content": "", "tool_calls": [{"id": "c1"}]},
        {"role": "tool", "tool_call_id": "c1", "content": "result"},
        {"role": "user", "content": "next"},
    ]

    assert tool_spans(messages) == [(0, 1)]

def test_r64_never_rewrites_a_cached_prefix():
    messages = [
        {"role": "user", "content": "a" * 400},
        {"role": "user", "content": "b" * 400, "cache_control": {"type": "ephemeral"}},
        {"role": "user", "content": "c" * 400},
        {"role": "user", "content": "d" * 400},
    ]

    result = compress(messages, max_ratio=0.1, count_tokens=lambda m: len(m) * 100)

    assert result[0] is messages[0]
    assert result[1] is messages[1]

def test_r64_never_splits_a_tool_exchange():
    messages = [
        {"role": "assistant", "content": "", "tool_calls": [{"id": "c1"}]},
        {"role": "tool", "tool_call_id": "c1", "content": "result"},
        {"role": "user", "content": "a" * 400},
        {"role": "user", "content": "b" * 400},
    ]

    result = compress(messages, max_ratio=0.1, count_tokens=lambda m: len(m) * 100)

    kept_ids = {id(m) for m in result}
    assert (id(messages[0]) in kept_ids) == (id(messages[1]) in kept_ids)

def test_r64_never_produces_invalid_json():
    messages = [
        {"role": "user", "content": json.dumps({"a": 1})},
        {"role": "user", "content": json.dumps({"b": 2})},
        {"role": "user", "content": json.dumps({"c": 3})},
    ]

    result = compress(messages, max_ratio=0.1, count_tokens=lambda m: len(m) * 100)

    for message in result:
        json.loads(str(message["content"]))

def test_r64_ratio_none_means_off():
    messages = _messages()

    assert compress(messages, max_ratio=None, count_tokens=lambda m: 1) == messages

def test_r64_failing_estimator_skips_compression():
    messages = _messages()

    result = compress(messages, max_ratio=0.1, count_tokens=lambda m: None)

    assert result == messages

def test_r64_never_empties_the_request():
    messages = [{"role": "user", "content": "only"}]

    result = compress(messages, max_ratio=0.0, count_tokens=lambda m: 100)

    assert result

# --- B5: the pipeline ships dark --------------------------------------------

def test_b5_disabled_policy_sends_byte_identical_messages():
    messages = _messages()
    before = canonical_bytes(messages)

    outcome = run(
        messages=messages,
        policy=OptimizationPolicy(enabled=False),
        request_id="req-1",
        logger=LOGGER,
    )

    assert canonical_bytes(outcome.messages) == before
    assert outcome.bypass.reason is BypassReason.POLICY_DISABLED
    assert outcome.effective is None

def test_b5_enabled_with_no_ratio_is_still_byte_identical():
    messages = _messages()
    before = canonical_bytes(messages)

    outcome = run(
        messages=messages,
        policy=OptimizationPolicy(enabled=True, max_ratio=None),
        request_id="req-1",
        logger=LOGGER,
    )

    assert canonical_bytes(outcome.messages) == before

def test_b5_enabled_with_a_ratio_shrinks_and_records():
    messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "a" * 400},
        {"role": "user", "content": "b" * 400},
        {"role": "user", "content": "c" * 400},
    ]

    outcome = run(
        messages=messages,
        policy=OptimizationPolicy(enabled=True, max_ratio=0.5),
        request_id="req-1",
        logger=LOGGER,
    )

    assert outcome.record is not None
    assert outcome.record.effective_count <= outcome.record.original_count
    assert len(canonical_bytes(outcome.messages)) <= len(canonical_bytes(messages))

def test_b5_capability_loss_degrades_to_the_original(monkeypatch):
    messages = [
        {"role": "user", "content": [{"type": "image_url", "image_url": {}}]},
        {"role": "user", "content": "keep"},
    ]
    before = canonical_bytes(messages)

    def drop_everything(m, *, max_ratio, count_tokens):
        return m[1:]

    monkeypatch.setattr(pipeline_module, "compress", drop_everything)

    outcome = run(
        messages=messages,
        policy=OptimizationPolicy(enabled=True, max_ratio=0.5),
        required_capabilities=frozenset({Capability.VISION}),
        request_id="req-1",
        logger=LOGGER,
    )

    assert canonical_bytes(outcome.messages) == before
    assert outcome.bypass.reason is BypassReason.CAPABILITY_LOSS

def test_b5_an_exception_inside_the_transform_leaves_the_original_intact(monkeypatch):
    messages = _messages()
    before = canonical_bytes(messages)

    def boom(m, *, max_ratio, count_tokens):
        raise RuntimeError("compressor exploded")

    monkeypatch.setattr(pipeline_module, "compress", boom)

    outcome = run(
        messages=messages,
        policy=OptimizationPolicy(enabled=True, max_ratio=0.5),
        request_id="req-1",
        logger=LOGGER,
    )

    assert canonical_bytes(outcome.messages) == before
    assert outcome.bypass.reason is BypassReason.TRANSFORM_ERROR
    assert outcome.record is not None
    assert outcome.record.fallback_reason == "transform_error"


# --- Call-site integration: the wiring, not just the module ------------------
#
# Every test above exercises the transform in isolation. These two prove the
# call site in ``api/completions.py`` is actually reached and that the disabled
# default sends the client's own bytes to the provider. Without these, a typo in
# the wiring would leave the whole suite green.

class _CapturingClient(StubLiteLLMClient):
    """Records the message list the provider would receive."""

    def __init__(self) -> None:
        super().__init__()
        self.sent: list[Any] = []

    async def chat_completion(
        self, decision: Any, messages: Any, **extra: Any
    ) -> dict[str, Any]:
        self.sent.append([dict(message) for message in messages])
        return await super().chat_completion(decision, messages, **extra)

class _NoopRedis:
    async def eval(self, *args: object) -> list[int]:
        return [1, 0]

    async def aclose(self) -> None:
        return None

def _gateway(
    optimization: dict[str, Any] | None = None, *, failures: dict[str, int] | None = None
) -> tuple[Any, Any, str]:
    store = InMemoryApiKeyStore()
    stub = _CapturingClient()
    stub.failures_remaining = dict(failures or {})
    config = make_config()
    if optimization is not None:
        config = config.model_copy(update={"optimization": optimization})
    state = build_gateway_state(
        config=config,
        client=stub,
        key_store=store,
        rate_limiter=RedisTokenBucket(cast(Redis, _NoopRedis())),
    )
    state.policies.register(
        RoutingPolicy(
            name="fast",
            deployments=["primary", "secondary"],
            strategy="priority",
            max_attempts=2,
        )
    )
    _, secret = issue_api_key(store, project_id="p", name="c")
    return state, stub, secret

def test_call_site_is_reached_and_disabled_default_sends_identical_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SABIROUTE_ADMIN_KEY", "r6-admin")
    state, stub, secret = _gateway()
    messages = [
        {"role": "system", "content": "be brief"},
        {"role": "user", "content": "one"},
        {"role": "assistant", "content": "two"},
        {"role": "user", "content": "three"},
    ]

    with TestClient(create_app(state=state)) as client:
        response = client.post(
            "/v1/chat/completions",
            json={"model": "fast", "messages": messages},
            headers={"Authorization": f"Bearer {secret}"},
        )

    assert response.status_code == 200
    assert len(stub.sent) == 1, "the provider was not called"
    assert stub.sent[0] == messages

def test_call_site_honours_an_enabled_policy_from_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SABIROUTE_ADMIN_KEY", "r6-admin")
    state, stub, secret = _gateway(
        {"policy": {"enabled": True, "strategy": "whole_message_removal", "max_ratio": 0.4}}
    )
    messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "a" * 400},
        {"role": "user", "content": "b" * 400},
        {"role": "user", "content": "c" * 400},
        {"role": "user", "content": "d" * 400},
    ]

    with TestClient(create_app(state=state)) as client:
        response = client.post(
            "/v1/chat/completions",
            json={"model": "fast", "messages": messages},
            headers={"Authorization": f"Bearer {secret}"},
        )

    assert response.status_code == 200
    # Strictly fewer messages. A `<=` here would pass just as happily with the
    # call site wired to the untransformed list, which is the failure this test
    # exists to catch.
    assert len(stub.sent[0]) < len(messages)
    assert len(canonical_bytes(stub.sent[0])) <= len(canonical_bytes(messages))

def test_invalid_optimization_config_fails_startup() -> None:
    with pytest.raises(Exception) as excinfo:
        _gateway({"policy": {"max_ratio": 4.0}})

    assert "max_ratio" in str(excinfo.value)

def test_transform_runs_once_for_a_request_that_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """I3: one effective request per logical request, not one per attempt.

    A transform inside the attempt loop would run twice here and could send two
    different effective requests against a single reservation.
    """
    monkeypatch.setenv("SABIROUTE_ADMIN_KEY", "r6-admin")
    state, stub, secret = _gateway(
        {"policy": {"enabled": True, "max_ratio": 0.4}}, failures={"primary": 1}
    )
    calls: list[int] = []

    original_run = pipeline_module.run

    def counting_run(*args: Any, **kwargs: Any) -> Any:
        calls.append(1)
        return original_run(*args, **kwargs)

    monkeypatch.setattr("sabiroute.api.completions.run_transform", counting_run)

    messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "a" * 400},
        {"role": "user", "content": "b" * 400},
        {"role": "user", "content": "c" * 400},
        {"role": "user", "content": "d" * 400},
    ]

    with TestClient(create_app(state=state)) as client:
        response = client.post(
            "/v1/chat/completions",
            json={"model": "fast", "messages": messages},
            headers={"Authorization": f"Bearer {secret}"},
        )

    assert response.status_code == 200
    assert len(stub.sent) == 2, "expected a failed attempt then a fallback"
    assert len(calls) == 1, "the transform ran once per attempt, not once per request"
    assert stub.sent[0] == stub.sent[1], "attempts saw different effective requests"
