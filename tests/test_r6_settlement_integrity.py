"""R6 settlement-integrity regression tests (findings E-01 and E-02).

AUTHORISED SCOPE
    Test additions only. This module changes no production source, schema,
    migration, configuration, or other test file, and it repairs neither
    defect.

EXPECTED STATE AT HEAD 319a711
    ``test_e01_*`` and both ``test_e02_unknown_*`` cases are expected to FAIL
    against the current implementation. That failure is the evidence this
    mission is asked to produce: each test is written against the approved
    contract, not against the observed behaviour, and is deliberately not
    weakened in order to pass.
    ``test_e02_known_zero_usage_*`` is a guard that must pass both before and
    after remediation — it exists so that a remediation cannot "fix" E-02 by
    collapsing known-zero usage into unknown usage.

CONTRACTS UNDER TEST
    E-01  A request that fails *after* its quota reservation is taken but
          *before* any provider attempt must keep its original failure
          semantics and must release the reservation. The implementation
          states this contract itself at ``api/completions.py:596-600``:
          "a request denied before any attempt releases its reservation".

    E-02  Owner decision B5, with its C-07 annotation
          (``docs/r6-t16-r6-decision-option-register.md`` §5 B5): unknown
          usage must settle at the full original estimate, never at a partial
          sum of known attempts, and the rule must hold for BOTH the budget
          and the quota governor.

ACCOUNTING VALUES
    No token counts, estimates, request ids, or window boundaries are
    invented. Every expected settlement figure is read back from the
    reservation row the request itself created.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from conftest import (
    _make_direct_completion_request,
    _make_free_chat_payload,
    _make_quota_and_budget_harness,
)

from sabiroute.api.completions import chat_completions
from sabiroute.freepool.eligibility import FreePoolPolicy
from sabiroute.providers.litellm_client import LiteLLMClientError


class _ScriptedStub:
    """Deterministic provider double that replays a fixed per-attempt script.

    Each script entry is either an exception instance to raise or a response
    body to return. Exhausting the script raises ``AssertionError`` rather
    than looping or fabricating a further response, so an unexpected extra
    attempt fails loudly instead of silently changing the scenario.
    """

    def __init__(self, script: list[Any]) -> None:
        self._script = list(script)
        self.calls: list[str] = []

    async def chat_completion(self, decision: Any, messages: Any, **extra: Any) -> Any:
        self.calls.append(decision.deployment)
        if not self._script:
            raise AssertionError(
                f"unexpected extra provider attempt #{len(self.calls)}; "
                "the test scenario only scripts the attempts it intends to make"
            )
        step = self._script.pop(0)
        if isinstance(step, BaseException):
            raise step
        return step

    async def start_chat_completion_stream(self, decision: Any, messages: Any, **extra: Any) -> Any:
        raise AssertionError("streaming is not exercised by this module")


def _success_body_without_usage() -> dict[str, Any]:
    """A well-formed provider success that reports no ``usage`` object at all."""
    return {
        "id": "chatcmpl-stub",
        "model": "primary",
        "choices": [{"message": {"role": "assistant", "content": "ok"}}],
    }


def _quota_snapshot(store: Any) -> dict[str, Any]:
    """Read the request's own quota reservation and window back from the store."""
    reservations = list(store.quota_reservations.values())
    assert len(reservations) == 1, (
        "expected exactly one quota reservation for this single-request scenario, "
        f"observed {len(reservations)}"
    )
    estimate, status, window_key = reservations[0]
    reserved_tokens, consumed_tokens = store.quota_windows[window_key]
    return {
        "estimate": estimate,
        "status": status,
        "reserved_tokens": reserved_tokens,
        "consumed_tokens": consumed_tokens,
    }


def _budget_tokens(store: Any, key_id: str) -> int:
    """Read back the budget tokens currently accounted against ``key_id``."""
    return sum(
        amount
        for (saved_key, _request_id), (amount, _cost) in store.budget_usage.items()
        if saved_key == key_id
    )


def _body(response: Any) -> dict[str, Any]:
    """Decode a JSONResponse returned directly by the route handler."""
    return json.loads(response.body)


def _widen_free_pool(state: Any) -> None:
    """Allow the built-in ``fast`` route's first two deployments in Free Pool.

    ``RoutingPolicy(name="fast")`` declares no explicit deployments, so it
    fans out over the registered deployments with ``max_attempts=2`` (see
    ``routing/policies.py``). Widening the Free Pool allowlist is what lets
    these scenarios reach a second provider attempt while keeping the quota
    gate active — the same fan-out pattern as
    ``tests/test_completions.py::test_policy_request_falls_back_to_next_deployment``.
    """
    state.free_pool = FreePoolPolicy(
        enabled=True,
        eligible_deployments=frozenset({"primary", "secondary"}),
    )


def _retry_payload(uid: str) -> Any:
    """Free-chat payload routed through the two-attempt ``fast`` policy."""
    return _make_free_chat_payload(uid).model_copy(update={"model": "fast"})


# ---------------------------------------------------------------------------
# E-01 — finish() reads the closure variable ``attempted`` before it is bound
# ---------------------------------------------------------------------------


def test_e01_pre_attempt_failure_keeps_original_error_and_releases_quota() -> None:
    """E-01: a post-reservation, pre-attempt failure must not become a 503 quota error.

    Scenario
        Free Pool request for an enrolled pilot user whose ``max_tokens`` is
        valid, so the quota reservation is taken — then the *second* routing
        eligibility evaluation (``api/completions.py:1166``) raises
        ``KeyError``, which is the documented route-configuration failure
        (``:1171``). This lands exactly in the window between
        ``quota_reserved = True`` (``:1161``) and the binding of
        ``attempted`` (``:1311``).

    Asserted
        1. The original failure semantics survive: status 503 with
           ``route_configuration_error``.
        2. The quota reservation is released, not stranded.
        3. The quota window is fully restored.
        4. No budget reservation was taken on this path, so nothing may
           appear in budget accounting.

    Why each assertion is necessary
        (1) alone would catch the masking, but a "fix" that returned the right
        error while leaking the reservation would still be wrong, so (2) and
        (3) pin the accounting consequence. (4) proves the failure really is
        pre-budget and that the test has not silently drifted into a
        different path.
    """
    state, store, _stub, _key_id, uid = _make_quota_and_budget_harness()
    request = _make_direct_completion_request(state)
    payload = _make_free_chat_payload(uid)

    # The Free Pool gate evaluates eligibility first (``:1035``) and the
    # post-reservation evaluation is the second call (``:1166``). Only the
    # second call raises, which is what places the failure inside the
    # reservation window.
    original_evaluate = state.router.evaluate_candidates
    evaluations = 0

    def evaluate_candidates(
        candidates: Any,
        *,
        required_capabilities: Any = (),
        attempted: Any = None,
    ) -> Any:
        nonlocal evaluations
        evaluations += 1
        if evaluations == 1:
            return original_evaluate(
                candidates,
                required_capabilities=required_capabilities,
                attempted=attempted,
            )
        raise KeyError("primary")

    state.router.evaluate_candidates = evaluate_candidates

    response = asyncio.run(chat_completions(payload, request))

    snapshot = _quota_snapshot(store)
    body = _body(response)

    assert body["error"]["type"] == "route_configuration_error", (
        "E-01: the pre-attempt route-configuration failure was replaced by "
        f"{body['error']['type']!r} (status {response.status_code}). "
        "Expected the original 'route_configuration_error'. Observed quota "
        f"reservation {snapshot!r}"
    )
    assert response.status_code == 503

    assert snapshot["status"] == "released", (
        "E-01: a request denied before any provider attempt must release its "
        f"quota reservation, but the reservation is {snapshot['status']!r}"
    )
    assert snapshot["reserved_tokens"] == 0, (
        "E-01: stranded reserved tokens remain in the quota window: "
        f"{snapshot['reserved_tokens']} of an estimate of {snapshot['estimate']}"
    )
    assert snapshot["consumed_tokens"] == 0, (
        "E-01: a request that made no provider attempt must not consume quota, "
        f"but {snapshot['consumed_tokens']} tokens were consumed"
    )
    assert store.budget_usage == {}, (
        "E-01: this path fails before budget reservation, so budget accounting "
        f"must be empty; observed {store.budget_usage!r}"
    )


# ---------------------------------------------------------------------------
# E-02 — unknown usage must settle at the full original estimate
# ---------------------------------------------------------------------------


def _run_known_failure_then_no_usage_success() -> dict[str, Any]:
    """B5 Spec 5: attempt 1 fails with known usage; attempt 2 succeeds with none.

    Attempt 1's usage object is complete — prompt, completion and an explicit
    ``total_tokens`` — so no unknown-usage signal exists for it. Attempt 2
    reports no ``usage`` object at all, which makes the request's settlement
    basis unknown. Under B5 the whole request must therefore settle at the
    full original estimate.

    Every expected figure is read back from the reservation the request made;
    none is computed or assumed by the test.
    """
    state, store, _stub, key_id, uid = _make_quota_and_budget_harness()
    _widen_free_pool(state)

    partial_total = 7
    stub = _ScriptedStub(
        [
            LiteLLMClientError(
                "upstream 500",
                status_code=500,
                response_body={
                    "usage": {
                        "prompt_tokens": 3,
                        "completion_tokens": 4,
                        "total_tokens": partial_total,
                    }
                },
            ),
            _success_body_without_usage(),
        ]
    )
    state.client = stub

    request = _make_direct_completion_request(state)
    payload = _retry_payload(uid)

    response = asyncio.run(chat_completions(payload, request))

    return {
        "response": response,
        "snapshot": _quota_snapshot(store),
        "budget_tokens": _budget_tokens(store, key_id),
        "partial_total": partial_total,
        "attempts": len(stub.calls),
    }


def _assert_spec5_scenario_ran(result: dict[str, Any]) -> None:
    """Assert the scenario preconditions before any settlement claim."""
    response = result["response"]
    assert response.status_code == 200, (
        f"scenario did not reach the success path; status {response.status_code}: {_body(response)}"
    )
    assert result["attempts"] == 2, (
        f"expected the retry to run (2 attempts), observed {result['attempts']}"
    )


def test_e02_spec5_quota_governor_holds_estimate() -> None:
    """E-02 (quota governor): B5 Spec 5 must settle at the full estimate.

    Asserted
        1. The scenario reached the success path via two attempts.
        2. Quota ``consumed_tokens`` equals the reservation's own estimate.
        3. Quota consumption is not attempt 1's partial total.

    (1) guards against a settlement assertion accidentally passing on a
    different code path. (3) names the prohibited value so the failure
    identifies the defect rather than only a numeric mismatch.
    """
    result = _run_known_failure_then_no_usage_success()
    _assert_spec5_scenario_ran(result)
    snapshot = result["snapshot"]

    assert snapshot["consumed_tokens"] == snapshot["estimate"], (
        "E-02 (quota governor): unknown usage from the successful attempt must "
        "settle at the full original estimate, but quota consumed "
        f"{snapshot['consumed_tokens']} against an estimate of "
        f"{snapshot['estimate']}"
    )
    assert snapshot["consumed_tokens"] != result["partial_total"], (
        "E-02: quota settled at attempt 1's partial total "
        f"({result['partial_total']}) instead of the full original estimate "
        f"({snapshot['estimate']})"
    )


def test_e02_spec5_budget_governor_holds_estimate() -> None:
    """E-02 (budget governor): B5 Spec 5 must hold the full estimate.

    Asserted
        1. The scenario reached the success path via two attempts.
        2. Budget accounted tokens equal the reservation's own estimate.
        3. Budget accounting is not attempt 1's partial total.

    The budget governor is asserted in its own test so its evidence stands
    independently of the quota governor, as the B5 / C-07 annotation requires.
    """
    result = _run_known_failure_then_no_usage_success()
    _assert_spec5_scenario_ran(result)
    snapshot = result["snapshot"]
    budget_tokens = result["budget_tokens"]

    assert budget_tokens == snapshot["estimate"], (
        "E-02 (budget governor): unknown usage from the successful attempt must "
        "hold the full original estimate, but budget accounted "
        f"{budget_tokens} against an estimate of {snapshot['estimate']}"
    )
    assert budget_tokens != result["partial_total"], (
        "E-02: budget settled at attempt 1's partial total "
        f"({result['partial_total']}) instead of the full original estimate "
        f"({snapshot['estimate']})"
    )


def test_e02_unknown_usage_on_earlier_attempt_holds_estimate_for_quota() -> None:
    """E-02 / C-07: the quota governor must honour the unknown-usage flag.

    Scenario
        Quota-only request (budget removed) so the quota governor is observed
        in isolation. Attempt 1 fails with prompt-only usage, which yields an
        unknowable total (``completions.py:239-250``) and therefore sets the
        unknown-usage flag; attempt 2 fails with a fully known usage object.
        Unknown usage wins for the whole request under B5, so the reservation
        must settle at its estimate rather than at the known attempts' sum.

        A budgeted variant cannot reach attempt 2 on this shape: the loop
        breaks at ``api/completions.py:1601`` as soon as a budget is reserved
        and the unknown-usage flag is set. Quota-only is therefore the minimal
        scenario that exercises the flag path end to end.

    Asserted
        1. The request failed as an upstream error (both attempts ran).
        2. Quota consumed equals the reservation's estimate.
        3. Quota consumption is not the known attempt's total.
    """
    state, store, _stub, key_id, uid = _make_quota_and_budget_harness()
    store.set_budget(key_id, None)  # isolate the quota governor
    _widen_free_pool(state)

    known_total = 20
    stub = _ScriptedStub(
        [
            LiteLLMClientError(
                "upstream 500",
                status_code=500,
                # Prompt-only usage: ``_actual_tokens`` derives a total only
                # when both prompt and completion counts are present
                # (completions.py:239-250), so this attempt's total is
                # genuinely unknown rather than 7.
                response_body={"usage": {"prompt_tokens": 3}},
            ),
            LiteLLMClientError(
                "upstream 502",
                status_code=502,
                response_body={
                    "usage": {
                        "prompt_tokens": 12,
                        "completion_tokens": 8,
                        "total_tokens": known_total,
                    }
                },
            ),
        ]
    )
    state.client = stub

    request = _make_direct_completion_request(state)
    payload = _retry_payload(uid)

    response = asyncio.run(chat_completions(payload, request))

    snapshot = _quota_snapshot(store)

    assert response.status_code == 502, (
        "scenario did not reach the all-attempts-failed path; status "
        f"{response.status_code}: {_body(response)}"
    )
    assert len(stub.calls) == 2, (
        f"expected both attempted failures (2 attempts), observed {len(stub.calls)}"
    )

    assert snapshot["consumed_tokens"] == snapshot["estimate"], (
        "E-02 (quota governor): a request containing an attempt whose usage is "
        "unknown must settle at the full original estimate, but quota consumed "
        f"{snapshot['consumed_tokens']} against an estimate of "
        f"{snapshot['estimate']}"
    )
    assert snapshot["consumed_tokens"] != known_total, (
        "E-02: quota settled at the partial sum of the known attempt "
        f"({known_total}) instead of the full original estimate "
        f"({snapshot['estimate']})"
    )


def test_e02_known_zero_usage_settles_zero_not_estimate() -> None:
    """E-02 guard: known *zero* usage is not unknown usage.

    Scenario
        A single successful attempt that explicitly reports zero prompt and
        completion tokens. Per B5 only *unknown* usage falls back to the
        estimate; a known zero must settle at zero in both governors.

    Asserted
        1. The request succeeded.
        2. Quota consumed zero.
        3. Budget accounted zero.

    Why: this passes at HEAD and must keep passing. It prevents a future
    remediation from "fixing" E-02 by always settling at the estimate, which
    would overcharge every provider that legitimately reports zero.
    """
    state, store, _stub, key_id, uid = _make_quota_and_budget_harness()

    stub = _ScriptedStub(
        [
            {
                "id": "chatcmpl-stub",
                "model": "primary",
                "choices": [{"message": {"role": "assistant", "content": "ok"}}],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            }
        ]
    )
    state.client = stub

    request = _make_direct_completion_request(state)
    payload = _make_free_chat_payload(uid)

    response = asyncio.run(chat_completions(payload, request))

    snapshot = _quota_snapshot(store)

    assert response.status_code == 200
    assert snapshot["estimate"] > 0, (
        "guard is only meaningful when the reservation holds a positive estimate"
    )
    assert snapshot["consumed_tokens"] == 0, (
        "known zero usage must settle at zero, but quota consumed "
        f"{snapshot['consumed_tokens']} against an estimate of "
        f"{snapshot['estimate']}"
    )
    assert _budget_tokens(store, key_id) == 0, (
        "known zero usage must account zero budget tokens, observed "
        f"{_budget_tokens(store, key_id)}"
    )
