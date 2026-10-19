"""OpenAI-compatible chat completions with health-aware routing and fallback."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator
from dataclasses import replace
from datetime import UTC, datetime
from decimal import ROUND_FLOOR, Decimal
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from ..capabilities import RequestType, classify_request
from ..freepool.eligibility import (
    FREE_CHAT_MARKER,
    FREE_POOL_NO_CAPABLE_DEPLOYMENT,
    FREE_POOL_ROUTE_CONFIGURATION_ERROR,
    FREE_POOL_UNAVAILABLE,
    FREE_POOL_UNMAPPED_DEPLOYMENT,
    SHARED_INFERENCE_DISABLED,
    deny_reason_for_evaluation,
    evaluate_free_pool,
    shared_inference_denial,
)
from ..gateway import GatewayState
from ..intelligence.dataset import FEATURE_SCHEMA_VERSION, make_pre_routing_snapshot
from ..providers.litellm_client import LiteLLMClientError, LiteLLMStream
from ..quotas import (
    QUOTA_EXCEEDED,
    QUOTA_MAX_TOKENS_REQUIRED,
    QUOTA_UNAVAILABLE,
    quota_reset_at,
    quota_window_start,
)
from ..routing.policies import RoutingPolicy
from ..routing.router import NoCapableDeploymentError, NoHealthyDeploymentError
from ..security.auth import require_client_key
from ..security.budgets import UnsupportedBudgetRequest, estimate_input_tokens, estimated_cost_usd
from ..security.keys import (
    MAX_USER_ID_CHARS,
    SABI_USER_ID_FIELD,
    ApiKeyIdentity,
    RequestUsageEvent,
    UsageEventValidationError,
)

router = APIRouter(tags=["completions"], dependencies=[Depends(require_client_key)])

# Non-5xx statuses that a different deployment may still resolve
# (expired key on one provider, quota exhausted, throttling).
RETRYABLE_STATUS_CODES = {401, 403, 429}
logger = logging.getLogger(__name__)


class UnknownModelError(KeyError):
    """Raised when a requested model matches neither alias nor policy."""


#: Hard caps on user-controlled request shape. Conservative values that
#: admit every supported use case while bounding validation, telemetry, and
#: provider payloads. Operators cannot raise these via environment; they are
#: release constants, not tuning knobs.
MAX_MESSAGES_PER_REQUEST = 256
MAX_MESSAGE_CHARS = 500_000


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible request body; unknown fields pass through."""

    model_config = ConfigDict(extra="allow")

    model: str = Field(min_length=1, max_length=256)
    messages: list[dict[str, Any]] = Field(min_length=1, max_length=MAX_MESSAGES_PER_REQUEST)
    sabi_route_request_type: RequestType | None = None


def _resolve_target(state: GatewayState, model: str) -> tuple[list[str], RoutingPolicy]:
    """Resolve the requested model to candidate deployments and a policy.

    A request may name a deployment alias directly (``sabiroute-openai``)
    or a routing policy (``fast``, ``SabiRoute_Ultimate``). Policy
    requests fan out over the policy's deployments, or every registered
    deployment when the policy defines none.
    """

    alias = model.strip()
    if state.registry.has_deployment(alias):
        return (
            [alias],
            RoutingPolicy(name="alias", max_attempts=2, strategy="priority"),
        )

    policy_key = alias.lower().removeprefix("sabiroute_")
    try:
        policy = state.policies.get(policy_key)
    except ValueError as exc:
        raise UnknownModelError(model) from exc

    candidates = policy.deployments or [
        deployment.name for deployment in state.registry.list_deployments()
    ]
    return candidates, policy


def _deadline_at(request: Any) -> float | None:
    """Absolute monotonic deadline published by DeadlineMiddleware, if any."""
    state = getattr(request, "state", None)
    value = getattr(state, "sabiroute_deadline_at", None)
    return value if isinstance(value, (int, float)) else None


def _deadline_expired(request: Any) -> bool:
    """Whether this request's absolute deadline has passed, if one exists.

    The middleware enforces the deadline by cancelling the downstream task,
    which arrives here as CancelledError — indistinguishable from a caller
    disconnect without comparing against the published instant.
    """
    deadline_at = _deadline_at(request)
    return deadline_at is not None and time.monotonic() >= deadline_at


def _error_category(exc: LiteLLMClientError) -> str:
    if exc.status_code is None:
        return "timeout" if exc.timed_out else "transport"
    if exc.status_code in {401, 403}:
        return "auth"
    if exc.status_code == 429:
        return "rate_limit"
    if exc.status_code >= 500:
        return "server"
    return "client"


def _record_usage(state: GatewayState, deployment: str, body: dict[str, Any]) -> None:
    usage = _usage_object(body)
    if not isinstance(usage, dict):
        return

    prompt_tokens = _safe_token_count(usage.get("prompt_tokens"))
    completion_tokens = _safe_token_count(usage.get("completion_tokens"))
    if prompt_tokens is None and completion_tokens is None:
        return
    state.usage.record(
        model=deployment,
        prompt_tokens=prompt_tokens or 0,
        completion_tokens=completion_tokens or 0,
    )


def _usage_object(body: Any) -> dict[str, Any] | None:
    if not isinstance(body, dict):
        return None
    usage = body.get("usage")
    if not isinstance(usage, dict) and isinstance(body.get("error"), dict):
        usage = body["error"].get("usage")
    return usage if isinstance(usage, dict) else None


def _safe_token_count(value: Any) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return None


def _actual_tokens(body: Any) -> tuple[int | None, int | None, int | None] | None:
    usage = _usage_object(body)
    if usage is None:
        return None
    prompt = _safe_token_count(usage.get("prompt_tokens"))
    completion = _safe_token_count(usage.get("completion_tokens"))
    total = _safe_token_count(usage.get("total_tokens"))
    if total is None and prompt is not None and completion is not None:
        total = prompt + completion
    if prompt is None and completion is None and total is None:
        return None
    return prompt, completion, total


def _sum_actual_tokens(
    parts: list[tuple[int | None, int | None, int | None]],
) -> tuple[int | None, int | None, int | None]:
    prompt_values = [part[0] for part in parts if part[0] is not None]
    completion_values = [part[1] for part in parts if part[1] is not None]
    total_values = [part[2] for part in parts if part[2] is not None]
    prompt = sum(prompt_values) if prompt_values else None
    completion = sum(completion_values) if completion_values else None
    total = sum(total_values) if total_values else None
    if total is None and prompt is not None and completion is not None:
        total = prompt + completion
    return prompt, completion, total


def _error_response(
    status_code: int,
    message: str,
    error_type: str,
    **extra: Any,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"message": message, "type": error_type, **extra}},
    )


def _sse_data(frame: bytes) -> list[str]:
    return [
        line[5:].strip()
        for line in frame.decode("utf-8", errors="replace").splitlines()
        if line.startswith("data:")
    ]


def _sse_usage(frame: bytes) -> dict[str, Any] | None:
    for data in _sse_data(frame):
        if data == "[DONE]":
            continue
        try:
            event = json.loads(data)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict) and isinstance(event.get("usage"), dict):
            return event
    return None


@router.post("/v1/chat/completions")
async def chat_completions(
    payload: ChatCompletionRequest,
    request: Request,
) -> Response:
    state: GatewayState = request.app.state.gateway

    identity = getattr(request.state, "api_identity", None)
    if not isinstance(identity, ApiKeyIdentity):
        return _error_response(
            500,
            "Authenticated request identity is unavailable.",
            "request_identity_unavailable",
        )
    store = state.key_store
    if store is None:
        return _error_response(
            503,
            "Request accounting is unavailable.",
            "usage_store_unavailable",
        )

    for _msg in payload.messages:
        try:
            _content = _msg.get("content") if isinstance(_msg, dict) else None
        except AttributeError:
            _content = None
        if isinstance(_content, str) and len(_content) > MAX_MESSAGE_CHARS:
            return _error_response(
                413,
                f"Message content exceeds the {MAX_MESSAGE_CHARS}-character limit.",
                "message_content_too_large",
            )
    request_id = str(uuid4())
    # Usage-source attribution starts as "unknown" for every request. It becomes
    # "free_pool" only below, when the Free Pool gate actually allows the
    # request — never from the client-supplied marker alone, and never for
    # denied requests. Historical rows predate the column entirely.
    event = RequestUsageEvent(
        request_id=request_id,
        key_id=identity.key_id,
        project_id=identity.project_id,
        created_at=datetime.now(UTC),
        requested_alias=payload.model[:256],
        feature_schema_version=None,
    )
    try:
        # Durable admission record comes before Redis so a persistence failure
        # cannot consume a request token and then reject the request.
        await state.store_executor.run(store.create_usage_event, event)
    except Exception:
        response = _error_response(
            503,
            "Durable request accounting is unavailable.",
            "usage_store_unavailable",
        )
        response.headers["X-SabiRoute-Request-ID"] = request_id
        return response

    budget_reserved = False
    estimated_input = 0
    reserved_tokens = 0
    estimated_cost: Decimal | None = None
    routing_decisions: list[dict[str, Any]] = []
    pre_routing_features: list[dict[str, Any]] = []
    quota_reserved = False
    quota_user_id: str | None = None
    # Request-local accounting ledger: every database mutation that must be
    # compensated on cancellation is recorded here with enough detail to
    # make cleanup idempotent. Entries are appended only after the worker
    # reports success, so cleanup never acts on work that never committed.
    # Each entry is one of:
    #   ("quota", user_id)  — quota estimate held
    #   ("budget", None)    — budget estimate held
    # (The admission usage row is created before any cancellation window
    # exists, so it needs no ledger entry; finalization covers it exactly
    # once via finish().)
    ledger: list[tuple[str, str | None]] = []
    # Cleanup observability: every failed compensation is appended here
    # instead of being swallowed, so operators can see stuck reservations.
    cleanup_errors: list[str] = []
    # In-flight accounting worker tracking: at most one accounting worker
    # runs per request at a time. ``in_flight`` names it; ``in_flight_done``
    # resolves exactly once when that worker exits (success or failure), on
    # every exit path. finish() waits for it before inspecting the ledger,
    # so cleanup decisions always observe committed state. Repeated
    # cancellation re-waits on the same barrier rather than abandoning it.
    in_flight: str | None = None
    in_flight_done: asyncio.Event | None = None

    def _track(name: str) -> asyncio.Event:
        nonlocal in_flight, in_flight_done
        done = asyncio.Event()
        in_flight = name
        in_flight_done = done
        return done

    def _untrack(name: str, done: asyncio.Event | None = None) -> None:
        nonlocal in_flight
        target = done if done is not None else in_flight_done
        if in_flight == name and (done is None or in_flight_done is done):
            in_flight = None
        # Resolve on every exit path, including exceptions: waiters must
        # never hang on a worker that already left.
        if target is not None and not target.is_set():
            target.set()

    def _untrack_closed_loop(name: str, done: asyncio.Event | None = None) -> None:
        """Clear in-flight state when the owning event loop is already closed.

        Safe to call from a worker thread: never invokes ``asyncio.Event.set()``
        off-thread, preventing cross-thread Event mutation or a secondary
        ``RuntimeError`` inside the worker ``finally`` block.
        """
        nonlocal in_flight
        if in_flight == name and (done is None or in_flight_done is done):
            in_flight = None

    async def _run_accounting(
        name: str,
        func: Any,
        /,
        *args: Any,
        shield_cancellation: bool = False,
        **kwargs: Any,
    ) -> Any:
        """Run one accounting mutation with in-flight tracking.

        Returns the worker result. For admission/snapshot steps
        (``shield_cancellation=False``), cancellation while queued propagates to
        the caller without starting work, and cancellation after a worker thread
        has been spawned leaves the worker to finish and raises
        ``CancelledError`` only after the worker exits. For cleanup and
        finalization steps (``shield_cancellation=True``), the executor call
        runs inside a shielded task so repeated cancellations while queued or
        running never withdraw the semaphore waiter, never lose FIFO queue
        position, and always deliver the worker's actual return value or
        exception.
        """
        nonlocal budget_reserved, quota_reserved, quota_user_id
        loop = asyncio.get_running_loop()
        done = _track(name)
        worker_spawned = False
        worker_outcome: tuple[str, Any] | None = None

        def _mark_worker_spawned() -> None:
            nonlocal worker_spawned
            worker_spawned = True

        def _invoke_tracked() -> Any:
            nonlocal worker_spawned, worker_outcome
            worker_spawned = True
            try:
                result = func(*args, **kwargs)
            except BaseException as exc:
                worker_outcome = ("err", exc)
                raise
            else:
                worker_outcome = ("ok", result)
                return result
            finally:
                try:
                    loop.call_soon_threadsafe(_untrack, name, done)
                except RuntimeError:
                    _untrack_closed_loop(name, done)

        _invoke_tracked._on_worker_spawned = _mark_worker_spawned  # type: ignore[attr-defined]

        if shield_cancellation:
            shielded_task = asyncio.create_task(
                state.store_executor.run(_invoke_tracked)
            )
            # Initialized for the type checker only: the loop below either
            # assigns via break or raises, so this value is never observed.
            result: Any = None
            try:
                while True:
                    try:
                        result = await asyncio.shield(shielded_task)
                        break
                    except asyncio.CancelledError:
                        continue
            except BaseException:
                _untrack(name, done)
                raise
            _untrack(name, done)
            return result

        try:
            result = await state.store_executor.run(_invoke_tracked)
        except asyncio.CancelledError:
            # Pre-capacity cancel: the executor acquired no slot and spawned no
            # worker thread, so untrack and propagate immediately.
            if not worker_spawned:
                _untrack(name, done)
                raise
            while not done.is_set():
                try:
                    await done.wait()
                except asyncio.CancelledError:
                    # Repeated cancellation while waiting: keep waiting
                    # for the worker rather than abandoning cleanup.
                    continue
            _untrack(name, done)
            if name == "quota_reserve" and worker_outcome == ("ok", True):
                quota_reserved = True
                quota_user_id = args[0]
            elif name == "budget_reserve" and worker_outcome == ("ok", None):
                budget_reserved = True
            raise
        except BaseException:
            _untrack(name, done)
            raise
        _untrack(name, done)
        return result

    async def finish(
        response: JSONResponse,
        *,
        deployment: str | None = None,
        tokens: tuple[int | None, int | None, int | None] = (None, None, None),
        failure_category: str | None = None,
        actual_cost: Decimal | None = None,
        release_budget: bool = False,
    ) -> JSONResponse:
        nonlocal budget_reserved, quota_reserved
        # Wait for any in-flight accounting worker before inspecting state:
        # cleanup decisions must observe committed outcomes, not races.
        # Repeated cancellation re-waits on the same barrier.
        while in_flight is not None:
            done = in_flight_done
            if done is None or done.is_set():
                break
            try:
                await done.wait()
            except asyncio.CancelledError:
                continue
        if budget_reserved:
            try:
                if release_budget:
                    await _run_accounting(
                        "budget_cleanup",
                        store.release_budget,
                        identity.key_id,
                        request_id,
                        shield_cancellation=True,
                    )
                    budget_reserved = False
                else:
                    await _run_accounting(
                        "budget_cleanup",
                        store.reconcile_budget,
                        identity.key_id,
                        request_id,
                        tokens[2],
                        actual_cost,
                        shield_cancellation=True,
                    )
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error("Budget reservation could not be reconciled: %s", exc)
                cleanup_errors.append("budget_cleanup_failed")
                response = _error_response(
                    503,
                    "Budget reservation could not be reconciled.",
                    "budget_store_unavailable",
                )
        if quota_reserved and quota_user_id is not None:
            # Quota settlement mirrors budget reconciliation: attempts made
            # settle with summed actuals (unknown usage holds the estimate);
            # a request denied before any attempt releases its reservation.
            # Exactly one settle-or-release runs per logical request.
            try:
                if attempted:
                    quota_total = _sum_actual_tokens(actual_usage_parts)[2]
                    await _run_accounting(
                        "quota_cleanup",
                        store.settle_quota,
                        quota_user_id,
                        request_id,
                        quota_total,
                        shield_cancellation=True,
                    )
                else:
                    await _run_accounting(
                        "quota_cleanup",
                        store.release_quota,
                        quota_user_id,
                        request_id,
                        shield_cancellation=True,
                    )
                quota_reserved = False
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error("Quota reservation could not be reconciled: %s", exc)
                cleanup_errors.append("quota_cleanup_failed")
                response = _error_response(
                    503,
                    "Quota reservation could not be reconciled.",
                    QUOTA_UNAVAILABLE,
                )
        final_event = replace(
            event,
            final_deployment=deployment,
            final_status=response.status_code,
            prompt_tokens=tokens[0],
            completion_tokens=tokens[1],
            total_tokens=tokens[2],
            failure_category=failure_category,
            estimated_input_tokens=estimated_input or None,
            reserved_tokens=reserved_tokens if budget_reserved else None,
            estimated_cost_usd=estimated_cost,
            actual_cost_usd=actual_cost,
            routing_decisions=tuple(routing_decisions),
            feature_schema_version=FEATURE_SCHEMA_VERSION if pre_routing_features else None,
            pre_routing_features=tuple(pre_routing_features),
        )
        validation_failed = False
        try:
            persisted = await _run_accounting(
                "finalize",
                store.finalize_usage_event,
                final_event,
                shield_cancellation=True,
            )
        except asyncio.CancelledError:
            raise
        except UsageEventValidationError as exc:
            logger.error("Request telemetry rejected at finalization: %s", exc)
            persisted = False
            validation_failed = True
        except Exception:
            logger.error("Durable request telemetry finalization failed.")
            persisted = False
        if not persisted:
            failed = _error_response(
                500 if validation_failed else 503,
                "Request telemetry failed its integrity checks."
                if validation_failed
                else "Durable request accounting could not be finalized.",
                "telemetry_integrity_error"
                if validation_failed
                else "usage_store_unavailable",
            )
            failed.headers["X-SabiRoute-Request-ID"] = request_id
            return failed
        response.headers["X-SabiRoute-Request-ID"] = request_id
        return response

    async def _compensate_all() -> None:
        """Release every held reservation, idempotently, in reverse order.

        Each release is a no-op unless its reservation actually committed,
        so calling this after a cancelled admission is safe whether the
        worker ran or not. Flags clear only on observed success; failures
        are recorded in ``cleanup_errors``, and repeated cancellations during
        one cleanup step never skip remaining cleanup steps.
        """
        nonlocal budget_reserved, quota_reserved
        # Reverse order of acquisition (budget held after quota).
        if budget_reserved:
            try:
                await _run_accounting(
                    "budget_cleanup",
                    store.release_budget,
                    identity.key_id,
                    request_id,
                    shield_cancellation=True,
                )
                budget_reserved = False
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error("Budget reservation release failed: %s", exc)
                cleanup_errors.append("budget_cleanup_failed")
        if quota_reserved and quota_user_id is not None:
            try:
                await _run_accounting(
                    "quota_cleanup",
                    store.release_quota,
                    quota_user_id,
                    request_id,
                    shield_cancellation=True,
                )
                quota_reserved = False
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error("Quota reservation release failed: %s", exc)
                cleanup_errors.append("quota_cleanup_failed")

    async def _cancelled_finish(
        response: JSONResponse,
        *,
        failure_category: str | None = None,
    ) -> JSONResponse:
        """Finalize a cancelled request without touching reservations.

        Reservations must already be compensated (via _compensate_all or
        the admission handlers above) before calling this: it only
        finalizes the usage event. It waits for any in-flight worker like
        finish() does, preserves the 499 client_cancelled envelope, and
        never marks RELEASED/SETTLED/FINALIZED unless the store confirms.
        """
        while in_flight is not None:
            done = in_flight_done
            if done is None or done.is_set():
                break
            try:
                await done.wait()
            except asyncio.CancelledError:
                continue
        final_event = replace(
            event,
            final_deployment=None,
            final_status=response.status_code,
            prompt_tokens=None,
            completion_tokens=None,
            total_tokens=None,
            failure_category=failure_category,
            estimated_input_tokens=estimated_input or None,
            reserved_tokens=reserved_tokens if budget_reserved else None,
            estimated_cost_usd=estimated_cost,
            actual_cost_usd=None,
            routing_decisions=tuple(routing_decisions),
            feature_schema_version=FEATURE_SCHEMA_VERSION if pre_routing_features else None,
            pre_routing_features=tuple(pre_routing_features),
        )
        try:
            persisted = await _run_accounting(
                "finalize",
                store.finalize_usage_event,
                final_event,
                shield_cancellation=True,
            )
        except asyncio.CancelledError:
            raise
        except UsageEventValidationError as exc:
            logger.error("Request telemetry rejected at finalization: %s", exc)
            persisted = False
        except Exception:
            logger.error("Durable request telemetry finalization failed.")
            persisted = False
        if not persisted:
            failed = _error_response(
                503,
                "Durable request accounting could not be finalized.",
                "usage_store_unavailable",
            )
            failed.headers["X-SabiRoute-Request-ID"] = request_id
            return failed
        response.headers["X-SabiRoute-Request-ID"] = request_id
        return response

    async def snapshot_persistence_failure() -> JSONResponse:
        nonlocal budget_reserved, quota_reserved
        if budget_reserved:
            try:
                await _run_accounting(
                    "budget_cleanup",
                    store.release_budget,
                    identity.key_id,
                    request_id,
                    shield_cancellation=True,
                )
                budget_reserved = False
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error(
                    "Budget reservation release failed after snapshot persistence error: %s",
                    exc,
                )
                cleanup_errors.append("budget_cleanup_failed")
        if quota_reserved and quota_user_id is not None:
            # Same contract as budgets on this path: release, matching the
            # adjacent budget handling exactly.
            try:
                await _run_accounting(
                    "quota_cleanup",
                    store.release_quota,
                    quota_user_id,
                    request_id,
                    shield_cancellation=True,
                )
                quota_reserved = False
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error(
                    "Quota reservation release failed after snapshot persistence error: %s",
                    exc,
                )
                cleanup_errors.append("quota_cleanup_failed")
        response = _error_response(
            503,
            "Decision telemetry could not be persisted; provider execution was not started.",
            "telemetry_store_unavailable",
        )
        response.headers["X-SabiRoute-Request-ID"] = request_id
        return response

    try:
        key_limit = await state.store_executor.run(
            store.get_rate_limit, identity.key_id
        )
    except Exception:
        return await finish(
            _error_response(
                503,
                "Rate-limit configuration is unavailable.",
                "rate_limit_unavailable",
            ),
            failure_category="rate_limit_config_unavailable",
        )

    if key_limit is not None:
        if state.rate_limiter is None:
            return await finish(
                _error_response(503, "Rate limiting is unavailable.", "rate_limiter_unavailable"),
                failure_category="redis_unavailable",
            )
        try:
            rate_decision = await state.rate_limiter.admit(identity.key_id, key_limit)
        except Exception:
            return await finish(
                _error_response(503, "Rate limiting is unavailable.", "rate_limiter_unavailable"),
                failure_category="redis_unavailable",
            )
        if not rate_decision.admitted:
            state.metrics.record_rate_limited()
            denied = _error_response(
                429,
                "Per-key request rate limit exceeded.",
                "rate_limit_exceeded",
            )
            denied.headers["Retry-After"] = str(rate_decision.retry_after_seconds or 1)
            return await finish(denied, failure_category="rate_limited")

    if len(state.registry) == 0:
        return await finish(
            _error_response(
                503,
                "SabiRoute has no deployments configured.",
                "sabiroute_not_configured",
            ),
            failure_category="no_deployments",
        )

    try:
        candidates, policy = _resolve_target(state, payload.model)
    except UnknownModelError:
        return await finish(
            _error_response(
                404,
                f"Unknown model {payload.model!r}.",
                "invalid_request_error",
                available_models=[
                    deployment.name for deployment in state.registry.list_deployments()
                ],
            ),
            failure_category="unknown_alias",
        )

    extras = {
        key: value
        for key, value in (payload.model_extra or {}).items()
        if value is not None and key not in {"model", "messages"}
    }
    stream_requested = extras.pop("stream", False) is True
    temperature = extras.pop("temperature", None)
    max_tokens = extras.pop("max_tokens", None)
    # Free Chat mode marker. Popped here — alongside the other SabiRoute-owned
    # fields — so it is never forwarded to LiteLLM and never trips the budget
    # estimator's unsupported-parameter contract below. Activation is strict:
    # only the exact marker key with a JSON true value selects Free Chat, so
    # no alias, truthy string, or unrelated field can enable it by accident.
    free_chat_requested = extras.pop(FREE_CHAT_MARKER, None) is True
    # Internal SabiChat user ID, if present. Popped here so it can never
    # reach provider payloads, snapshot options, or budget parameters. It
    # becomes trusted identity only via the service-key provenance check
    # inside the Free Chat gate below; anywhere else it is ignored.
    raw_sabi_user_id = extras.pop(SABI_USER_ID_FIELD, None)
    sabi_user_id: str | None = None

    try:
        budget = await state.store_executor.run(store.get_budget, identity.key_id)
    except Exception:
        return await finish(
            _error_response(
                503,
                "Budget configuration is unavailable.",
                "budget_store_unavailable",
            ),
            failure_category="budget_config_unavailable",
        )
    if budget is not None:
        if not isinstance(max_tokens, int) or isinstance(max_tokens, bool) or max_tokens < 1:
            return await finish(
                _error_response(
                    400,
                    "A positive max_tokens is required for budgeted requests.",
                    "budget_output_cap_required",
                ),
                failure_category="budget_output_cap_required",
            )
        try:
            estimated_input = estimate_input_tokens(payload.messages)
        except UnsupportedBudgetRequest as exc:
            return await finish(
                _error_response(400, str(exc), "budget_request_unsupported"),
                failure_category="budget_request_unsupported",
            )
        unsupported_parameters = set(extras) - {
            "top_p",
            "frequency_penalty",
            "presence_penalty",
            "stop",
            "stream_options",
        }
        if unsupported_parameters:
            return await finish(
                _error_response(
                    400,
                    "This request includes parameters outside the budget estimator contract.",
                    "budget_request_unsupported",
                ),
                failure_category="budget_request_unsupported",
            )

    classification = classify_request(
        explicit_type=payload.sabi_route_request_type,
        options=payload.model_extra or {},
        messages=payload.messages,
        policy_requirements=policy.required_capabilities,
    )

    if free_chat_requested:
        # Trusted identity provenance: the field is honored only when the
        # request bears the server-held SabiChat service credential, whose
        # key ID the chat backend recorded on gateway state after issuance.
        # Ordinary API-key callers — even ones echoing the field name, a
        # header, or nested metadata — never satisfy this check. A service
        # request with a missing or malformed field is a server-side bug and
        # fails loudly instead of proceeding without identity.
        service_key_id = state.sabichat_service_key_id
        if service_key_id is not None and identity.key_id == service_key_id:
            if (
                not isinstance(raw_sabi_user_id, str)
                or not 1 <= len(raw_sabi_user_id) <= MAX_USER_ID_CHARS
            ):
                return await finish(
                    _error_response(
                        500,
                        "Internal identity unavailable.",
                        "internal_identity_error",
                    ),
                    failure_category="internal_identity_error",
                )
            sabi_user_id = raw_sabi_user_id
        # Free Pool gate: narrow this request to explicitly mapped deployments
        # before the general eligibility checks, any budget reservation, or
        # provider execution. The attempt loop below routes over ``candidates``,
        # so reassigning it here also keeps fallback inside the allowlist.
        # Denial always happens before LiteLLM, with a Free-Pool-typed reason.
        shared_denial = await shared_inference_denial(state, store)
        if shared_denial is not None:
            # Emergency kill-switch: shared inference is not admitted, before
            # any budget reservation or provider execution.
            return await finish(
                _error_response(
                    403,
                    "Shared inference is currently disabled.",
                    shared_denial,
                ),
                failure_category=shared_denial,
            )
        if not state.free_pool.enabled:
            # Fail closed: a disabled gateway is not production-ready Free Chat.
            return await finish(
                _error_response(
                    503,
                    "Free Chat is not enabled on this gateway.",
                    FREE_POOL_UNAVAILABLE,
                ),
                failure_category=FREE_POOL_UNAVAILABLE,
            )
        free_pool_decision = evaluate_free_pool(candidates, state.free_pool)
        if not free_pool_decision.allowed:
            return await finish(
                _error_response(
                    403,
                    "The requested model is not eligible for Free Chat.",
                    free_pool_decision.reason or FREE_POOL_UNMAPPED_DEPLOYMENT,
                ),
                failure_category=free_pool_decision.reason
                or FREE_POOL_UNMAPPED_DEPLOYMENT,
            )
        try:
            free_pool_eligibility = state.router.evaluate_candidates(
                free_pool_decision.eligible_candidates,
                required_capabilities=classification.required_capabilities,
            )
        except (KeyError, ValueError):
            return await finish(
                _error_response(
                    503,
                    "The Free Chat route is misconfigured.",
                    FREE_POOL_ROUTE_CONFIGURATION_ERROR,
                ),
                failure_category=FREE_POOL_ROUTE_CONFIGURATION_ERROR,
            )
        free_pool_denial = deny_reason_for_evaluation(free_pool_eligibility)
        if free_pool_denial is not None:
            if free_pool_denial == FREE_POOL_NO_CAPABLE_DEPLOYMENT:
                message = (
                    "No Free Chat deployment is verified for "
                    "this request's capabilities."
                )
            else:
                message = (
                    "No healthy Free Chat deployment is currently eligible "
                    "for this request."
                )
            return await finish(
                _error_response(503, message, free_pool_denial),
                failure_category=free_pool_denial,
            )
        candidates = list(free_pool_decision.eligible_candidates)
        # Authoritative attribution: the gate allowed this request, so every
        # later exit — success, fallback, provider failure, budget
        # reconciliation — finalizes through finish() with "free_pool".
        event = replace(event, usage_source="free_pool")
        # Per-user quota admission (pilot only): atomic check-and-reserve
        # before budget reservation or provider execution. Only requests
        # carrying trusted identity for an enrolled pilot user enter; every
        # other shape keeps the exact pre-quota path below.
        if sabi_user_id is not None and state.quota_policy.covers(sabi_user_id):
            if (
                not isinstance(max_tokens, int)
                or isinstance(max_tokens, bool)
                or max_tokens < 1
            ):
                return await finish(
                    _error_response(
                        400,
                        "A positive max_tokens is required for quota-metered requests.",
                        QUOTA_MAX_TOKENS_REQUIRED,
                    ),
                    failure_category=QUOTA_MAX_TOKENS_REQUIRED,
                )
            try:
                quota_input = estimate_input_tokens(payload.messages)
            except UnsupportedBudgetRequest as exc:
                return await finish(
                    _error_response(400, str(exc), QUOTA_MAX_TOKENS_REQUIRED),
                    failure_category=QUOTA_MAX_TOKENS_REQUIRED,
                )
            quota_window = quota_window_start(event.created_at)
            try:
                admitted = await _run_accounting(
                    "quota_reserve",
                    store.check_and_reserve_quota,
                    sabi_user_id,
                    request_id,
                    quota_input + max_tokens,
                    quota_window,
                    state.quota_policy.daily_tokens,
                )
            except asyncio.CancelledError:
                # Admission was cancelled: the worker either never started
                # (queued-cancel: nothing reserved) or ran to completion and
                # _run_accounting already waited for its exit. Settle the
                # ambiguity by compensating idempotently: release is a no-op
                # unless this request_id actually holds a reservation.
                try:
                    await _run_accounting(
                        "quota_cleanup",
                        store.release_quota,
                        sabi_user_id,
                        request_id,
                        shield_cancellation=True,
                    )
                    quota_reserved = False
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    logger.error(
                        "Quota reservation release failed after cancellation: %s", exc
                    )
                    cleanup_errors.append("quota_cleanup_failed")
                return await _cancelled_finish(
                    _error_response(
                        499, "Client cancelled the request.", "client_cancelled"
                    ),
                    failure_category="client_cancelled",
                )
            except Exception:
                quota_denial: str | None = QUOTA_UNAVAILABLE
            else:
                quota_denial = None if admitted else QUOTA_EXCEEDED
            if quota_denial is not None:
                quota_status = 503 if quota_denial == QUOTA_UNAVAILABLE else 429
                message = (
                    "Quota enforcement is unavailable."
                    if quota_denial == QUOTA_UNAVAILABLE
                    else "Daily Free Chat quota exceeded."
                )
                reset_at = quota_reset_at(quota_window).isoformat()
                denied = _error_response(
                    quota_status,
                    message,
                    quota_denial,
                    reset_at=reset_at,
                )
                if quota_denial != QUOTA_UNAVAILABLE:
                    retry_after = quota_reset_at(quota_window) - datetime.now(UTC)
                    denied.headers["Retry-After"] = str(
                        max(0, int(retry_after.total_seconds()))
                    )
                return await finish(
                    denied,
                    failure_category=quota_denial,
                )
            quota_reserved = True
            quota_user_id = sabi_user_id
            ledger.append(("quota", sabi_user_id))

    try:
        eligibility = state.router.evaluate_candidates(
            candidates,
            required_capabilities=classification.required_capabilities,
        )
    except (KeyError, ValueError):
        return await finish(
            _error_response(
                503,
                "The requested route is misconfigured.",
                "route_configuration_error",
            ),
            failure_category="route_configuration_error",
        )
    if not eligibility.capability_eligible_deployments:
        return await finish(
            _error_response(
                503,
                "No configured deployment is verified for this request's capabilities.",
                "no_capable_deployment",
            ),
            failure_category="no_capable_deployment",
        )
    if not eligibility.available_deployments:
        return await finish(
            _error_response(
                503,
                "No healthy deployment is currently eligible for this request.",
                "no_healthy_deployment",
            ),
            failure_category="no_healthy_deployment",
        )

    if budget is not None:
        reserved_tokens = estimated_input + max_tokens
        candidate_deployments = [state.registry.get(name) for name in candidates]
        estimated_cost = estimated_cost_usd(candidate_deployments, estimated_input, max_tokens)
        if (
            budget.daily_cost_usd is not None or budget.monthly_cost_usd is not None
        ) and estimated_cost is None:
            return await finish(
                _error_response(
                    503,
                    "Pricing metadata is unavailable for this request's routing candidates.",
                    "budget_pricing_unavailable",
                ),
                failure_category="budget_pricing_unavailable",
            )
        try:
            denial = await _run_accounting(
                "budget_reserve",
                store.reserve_budget,
                identity.key_id,
                request_id,
                reserved_tokens,
                estimated_cost,
                event.created_at,
            )
        except asyncio.CancelledError:
            # Same contract as quota admission above: compensate
            # idempotently (release is a no-op without a reservation),
            # then finalize as cancelled.
            try:
                await _run_accounting(
                    "budget_cleanup",
                    store.release_budget,
                    identity.key_id,
                    request_id,
                    shield_cancellation=True,
                )
                budget_reserved = False
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error(
                    "Budget reservation release failed after cancellation: %s", exc
                )
                cleanup_errors.append("budget_cleanup_failed")
            # A quota reservation may already be held from the earlier
            # gate; release it too so pre-dispatch cancellation leaves
            # neither resource reserved.
            if quota_reserved and quota_user_id is not None:
                try:
                    await _run_accounting(
                        "quota_cleanup",
                        store.release_quota,
                        quota_user_id,
                        request_id,
                        shield_cancellation=True,
                    )
                    quota_reserved = False
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    logger.error(
                        "Quota reservation release failed after cancellation: %s", exc
                    )
                    cleanup_errors.append("quota_cleanup_failed")
            return await _cancelled_finish(
                _error_response(
                    499, "Client cancelled the request.", "client_cancelled"
                ),
                failure_category="client_cancelled",
            )
        except Exception:
            return await finish(
                _error_response(
                    503,
                    "Budget reservation is unavailable.",
                    "budget_store_unavailable",
                ),
                failure_category="budget_reservation_unavailable",
            )
        if denial is not None:
            if denial == "budget_changed":
                return await finish(
                    _error_response(
                        503,
                        "Budget configuration changed during admission.",
                        "budget_store_unavailable",
                    ),
                    failure_category="budget_config_changed",
                )
            if denial.endswith("pricing_unknown"):
                return await finish(
                    _error_response(
                        503,
                        "Pricing metadata is unavailable for the configured monetary budget.",
                        "budget_pricing_unavailable",
                    ),
                    failure_category="budget_pricing_unavailable",
                )
            return await finish(
                _error_response(
                    429,
                    "The API key's configured budget would be exceeded.",
                    "budget_exceeded",
                    window=denial.split("_", 1)[0],
                ),
                failure_category="budget_exceeded",
            )
        budget_reserved = True
        ledger.append(("budget", None))

    attempted: list[str] = []
    last_error_category: str | None = None
    last_deployment: str | None = None
    actual_usage_parts: list[tuple[int | None, int | None, int | None]] = []
    cost_usage_parts: list[tuple[str, tuple[int | None, int | None, int | None]]] = []
    provider_usage_unknown = False

    async def _handle_attempt_loop_cancellation(
        exc: asyncio.CancelledError,
    ) -> JSONResponse:
        if attempted:
            await finish(
                _error_response(
                    499, "Client cancelled the request.", "client_cancelled"
                ),
                deployment=last_deployment,
                tokens=(None, None, None)
                if provider_usage_unknown
                else _sum_actual_tokens(actual_usage_parts),
                failure_category="client_cancelled",
                actual_cost=_actual_cost(
                    state, cost_usage_parts, provider_usage_unknown
                ),
                release_budget=False,
            )
            raise exc
        await _compensate_all()
        return await _cancelled_finish(
            _error_response(
                499, "Client cancelled the request.", "client_cancelled"
            ),
            failure_category="client_cancelled",
        )

    for attempt in range(1, policy.max_attempts + 1):
        if _deadline_expired(request):
            # Absolute deadline passed before this attempt could start.
            # Never begin upstream work merely to report a richer error.
            last_error_category = "deadline_exceeded"
            break
        if free_chat_requested:
            # Kill-switch re-check per attempt: a disable lands no later than
            # the next routing decision on every instance. In-flight attempts
            # are never cancelled by this — documented limitation — but no
            # further deployment is attempted once disabled.
            try:
                allowed_shared = await _run_accounting(
                    "shared_inference_check",
                    store.get_shared_inference,
                )
            except asyncio.CancelledError as exc:
                return await _handle_attempt_loop_cancellation(exc)
            except Exception:
                attempt_denial: str | None = SHARED_INFERENCE_DISABLED
            else:
                attempt_denial = (
                    None if allowed_shared is True else SHARED_INFERENCE_DISABLED
                )
            if attempt_denial is not None:
                return await finish(
                    _error_response(
                        403,
                        "Shared inference is currently disabled.",
                        attempt_denial,
                    ),
                    deployment=last_deployment,
                    tokens=(None, None, None)
                    if provider_usage_unknown
                    else _sum_actual_tokens(actual_usage_parts),
                    actual_cost=_actual_cost(
                        state, cost_usage_parts, provider_usage_unknown
                    ),
                    release_budget=not attempted,
                    failure_category=attempt_denial,
                )
        decision_at = datetime.now(UTC) if policy.strategy != "measured" else None
        try:
            route_decision = state.router.choose_deployment(
                candidates,
                policy_name=policy.name,
                attempted=attempted,
                required_capabilities=classification.required_capabilities,
                request_type=classification.request_type,
                strategy=policy.strategy,
            )
        except (NoCapableDeploymentError, NoHealthyDeploymentError, ValueError):
            break  # every candidate has been attempted

        decision_at = (
            route_decision.explanation.scoring_as_of
            if route_decision.explanation is not None
            and route_decision.explanation.scoring_as_of is not None
            else decision_at or datetime.now(UTC)
        )

        attempt_max_tokens = max_tokens
        if budget_reserved and budget is not None:
            if budget.daily_cost_usd is not None or budget.monthly_cost_usd is not None:
                spent_cost = _actual_cost(state, cost_usage_parts, False)
                if spent_cost is None and cost_usage_parts:
                    break
                if estimated_cost is None:
                    break
                remaining_cost = estimated_cost - (spent_cost or Decimal(0))
                deployment = state.registry.get(route_decision.deployment)
                input_price = deployment.input_cost_per_million_tokens
                output_price = deployment.output_cost_per_million_tokens
                if input_price is None or output_price is None:
                    break
                input_cost = Decimal(estimated_input) * input_price / Decimal(1_000_000)
                output_cost = output_price / Decimal(1_000_000)
                if remaining_cost <= input_cost:
                    break
                if output_cost > 0:
                    cost_output_cap = int(
                        ((remaining_cost - input_cost) / output_cost).to_integral_value(
                            rounding=ROUND_FLOOR
                        )
                    )
                    attempt_max_tokens = min(attempt_max_tokens, cost_output_cap)
            if attempt_max_tokens < 1:
                break

        try:
            feature_snapshot = make_pre_routing_snapshot(
                logical_request_id=request_id,
                attempt_number=attempt,
                decision_timestamp=decision_at,
                requested_alias=payload.model[:256],
                request_type=classification.request_type.value,
                routing_policy_id=policy.name,
                routing_strategy=policy.strategy,
                messages=payload.messages,
                options={
                    **extras,
                    "stream": stream_requested,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                decision=route_decision,
            )
        except Exception:
            logger.error("Pre-routing feature snapshot construction failed.")
            return await finish(
                _error_response(
                    500,
                    "Decision telemetry could not be constructed.",
                    "telemetry_integrity_error",
                ),
                deployment=last_deployment,
                tokens=(None, None, None)
                if provider_usage_unknown
                else _sum_actual_tokens(actual_usage_parts),
                actual_cost=_actual_cost(state, cost_usage_parts, provider_usage_unknown),
                release_budget=not attempted,
                failure_category="telemetry_snapshot_invalid",
            )
        try:
            snapshot_persisted = await _run_accounting(
                "snapshot",
                store.append_pre_routing_feature_snapshot,
                request_id,
                feature_snapshot,
            )
        except asyncio.CancelledError as exc:
            # Snapshot write cancelled: when no upstream attempt has run yet,
            # compensate held reservations and finalize as an unattempted
            # cancelled request; when an earlier attempt already executed,
            # reconcile/settle and finalize with that attempt's attribution.
            return await _handle_attempt_loop_cancellation(exc)
        except UsageEventValidationError as exc:
            logger.error("Pre-routing feature snapshot rejected: %s", exc)
            return await finish(
                _error_response(
                    500,
                    "Decision telemetry failed its integrity checks.",
                    "telemetry_integrity_error",
                ),
                deployment=last_deployment,
                tokens=(None, None, None)
                if provider_usage_unknown
                else _sum_actual_tokens(actual_usage_parts),
                actual_cost=_actual_cost(state, cost_usage_parts, provider_usage_unknown),
                release_budget=not attempted,
                failure_category="telemetry_snapshot_invalid",
            )
        except Exception:
            logger.error("Pre-routing feature snapshot persistence failed.")
            return await snapshot_persistence_failure()
        if not snapshot_persisted:
            logger.error("Pre-routing feature snapshot persistence was rejected.")
            return await snapshot_persistence_failure()

        pre_routing_features.append(feature_snapshot)
        attempted.append(route_decision.deployment)
        last_deployment = route_decision.deployment
        state.metrics.record_request(route_decision.deployment)

        attempt_started_at = datetime.now(UTC)
        started = time.perf_counter()
        stream_session: LiteLLMStream | None = None
        stream_iterator: AsyncIterator[bytes] | None = None
        first_frame: bytes | None = None
        try:
            if stream_requested:
                stream_extras = dict(extras)
                stream_extras["stream_options"] = stream_extras.get(
                    "stream_options", {"include_usage": True}
                )
                stream_session = await state.client.start_chat_completion_stream(
                    route_decision,
                    payload.messages,
                    temperature=temperature,
                    max_tokens=attempt_max_tokens,
                    **stream_extras,
                )
                stream_iterator = stream_session.events()
                try:
                    first_frame = await anext(stream_iterator)
                except StopAsyncIteration as exc:
                    raise LiteLLMClientError(
                        "LiteLLM stream ended before its first event."
                    ) from exc
                except Exception as exc:
                    raise LiteLLMClientError(
                        "LiteLLM stream failed before its first event."
                    ) from exc
            else:
                body = await state.client.chat_completion(
                    route_decision,
                    payload.messages,
                    temperature=temperature,
                    max_tokens=attempt_max_tokens,
                    **extras,
                )
        except LiteLLMClientError as exc:
            attempt_completed_at = datetime.now(UTC)
            if stream_session is not None:
                try:
                    await stream_session.aclose()
                except Exception:
                    # Preserve the provider failure outcome even if cleanup fails.
                    pass
            elapsed_ms = (time.perf_counter() - started) * 1000
            state.health.mark_failure(route_decision.deployment)
            state.metrics.record_failure()
            state.errors.record(_error_category(exc), route_decision.deployment, str(exc))
            state.latency.record(route_decision.deployment, elapsed_ms)
            last_error_category = _error_category(exc)
            failure_usage = _actual_tokens(exc.response_body)
            if failure_usage is not None:
                actual_usage_parts.append(failure_usage)
                cost_usage_parts.append((route_decision.deployment, failure_usage))
                if failure_usage[2] is None:
                    provider_usage_unknown = True
            elif budget_reserved:
                provider_usage_unknown = True

            failure_cost = _actual_cost(
                state,
                [(route_decision.deployment, failure_usage)] if failure_usage else [],
                failure_usage is None or failure_usage[2] is None,
            )
            routing_decisions.append(
                _routing_attempt_event(
                    request_id=request_id,
                    attempt=attempt,
                    decision=route_decision,
                    request_type=classification.request_type.value,
                    decided_at=decision_at,
                    attempt_started_at=attempt_started_at,
                    attempt_completed_at=attempt_completed_at,
                    outcome="failure",
                    latency_ms=elapsed_ms,
                    usage=failure_usage,
                    actual_cost_usd=failure_cost,
                    failure_category=last_error_category,
                    http_status=exc.status_code,
                )
            )

            status = exc.status_code
            retryable = status is None or status >= 500 or status in RETRYABLE_STATUS_CODES
            if not retryable or (budget_reserved and provider_usage_unknown):
                break
            if budget_reserved and failure_usage is not None:
                used = sum(part[2] or 0 for part in actual_usage_parts)
                remaining = reserved_tokens - used
                if remaining <= estimated_input:
                    break
                max_tokens = min(max_tokens, remaining - estimated_input)
            continue
        except asyncio.CancelledError:
            # Cancellation arrives here for caller disconnects AND for the
            # middleware deadline (which cancels the downstream task). The
            # published deadline instant tells them apart: past it, this is
            # our own budget expiring, not proof the caller left.
            attempt_completed_at = datetime.now(UTC)
            if stream_session is not None:
                try:
                    await stream_session.aclose()
                except asyncio.CancelledError:
                    # The request is already being finalized as cancelled;
                    # cleanup cancellation must not bypass its telemetry.
                    pass
                except Exception:
                    pass
            elapsed_ms = (time.perf_counter() - started) * 1000
            if _deadline_expired(request):
                if budget_reserved:
                    provider_usage_unknown = True
                state.errors.record(
                    "deadline_exceeded",
                    route_decision.deployment,
                    "Request deadline exceeded before the attempt completed.",
                )
                routing_decisions.append(
                    _routing_attempt_event(
                        request_id=request_id,
                        attempt=attempt,
                        decision=route_decision,
                        request_type=classification.request_type.value,
                        decided_at=decision_at,
                        attempt_started_at=attempt_started_at,
                        attempt_completed_at=attempt_completed_at,
                        outcome="failure",
                        latency_ms=elapsed_ms,
                        usage=None,
                        actual_cost_usd=None,
                        failure_category="deadline_exceeded",
                        http_status=None,
                    )
                )
                last_error_category = "deadline_exceeded"
                return await finish(
                    _error_response(
                        503,
                        "The request exceeded its processing deadline.",
                        "deadline_exceeded",
                    ),
                    deployment=route_decision.deployment,
                    tokens=(None, None, None),
                    failure_category="deadline_exceeded",
                    actual_cost=None,
                )
            routing_decisions.append(
                _routing_attempt_event(
                    request_id=request_id,
                    attempt=attempt,
                    decision=route_decision,
                    request_type=classification.request_type.value,
                    decided_at=decision_at,
                    attempt_started_at=attempt_started_at,
                    attempt_completed_at=attempt_completed_at,
                    outcome="failure",
                    latency_ms=elapsed_ms,
                    usage=None,
                    actual_cost_usd=None,
                    failure_category="client_cancelled",
                    http_status=None,
                )
            )
            await finish(
                _error_response(499, "Client cancelled the request.", "client_cancelled"),
                deployment=route_decision.deployment,
                tokens=(None, None, None),
                failure_category="client_cancelled",
                actual_cost=None,
            )
            raise
        except Exception:
            # Preserve existing exception propagation (and therefore fallback
            # behavior) while making the executed attempt temporally auditable.
            attempt_completed_at = datetime.now(UTC)
            elapsed_ms = (time.perf_counter() - started) * 1000
            provider_usage_unknown = budget_reserved or provider_usage_unknown
            routing_decisions.append(
                _routing_attempt_event(
                    request_id=request_id,
                    attempt=attempt,
                    decision=route_decision,
                    request_type=classification.request_type.value,
                    decided_at=decision_at,
                    attempt_started_at=attempt_started_at,
                    attempt_completed_at=attempt_completed_at,
                    outcome="failure",
                    latency_ms=elapsed_ms,
                    usage=None,
                    actual_cost_usd=None,
                    failure_category="provider_exception",
                    http_status=None,
                )
            )
            await finish(
                _error_response(
                    500,
                    "Provider execution raised an unexpected exception.",
                    "provider_exception",
                ),
                deployment=route_decision.deployment,
                tokens=(None, None, None)
                if provider_usage_unknown
                else _sum_actual_tokens(actual_usage_parts),
                actual_cost=_actual_cost(
                    state, cost_usage_parts, provider_usage_unknown
                ),
                release_budget=not attempted,
                failure_category="provider_exception",
            )
            raise

        if stream_requested and stream_session is not None and stream_iterator is not None:
            assert first_frame is not None

            async def stream_body(
                first_event: bytes = first_frame,
                events: AsyncIterator[bytes] = stream_iterator,
                upstream: LiteLLMStream = stream_session,
                attempt_started: float = started,
                attempt_started_at: datetime = attempt_started_at,
                decision: Any = route_decision,
                attempt_number: int = attempt,
                decision_time: datetime = decision_at,
            ) -> AsyncIterator[bytes]:
                nonlocal provider_usage_unknown
                streamed_usage: dict[str, Any] | None = None
                completed = False
                stream_error: str | None = None
                client_cancelled = False
                deadline_expired = False
                try:
                    frame = first_event
                    while True:
                        usage_event = _sse_usage(frame)
                        if usage_event is not None:
                            streamed_usage = usage_event
                        is_done = "[DONE]" in _sse_data(frame)
                        yield frame
                        if is_done:
                            completed = True
                            break
                        try:
                            frame = await anext(events)
                        except StopAsyncIteration:
                            break
                except asyncio.CancelledError:
                    # Same ambiguity as the attempt handler: the middleware
                    # deadline arrives as cancellation too. Compare against
                    # the published instant; a genuine disconnect keeps the
                    # client_cancelled outcome and health stays untouched.
                    if _deadline_expired(request):
                        deadline_expired = True
                        stream_error = "Request deadline exceeded during streaming."
                    else:
                        client_cancelled = True
                        stream_error = "Client disconnected during provider streaming."
                except Exception:
                    stream_error = "Provider stream terminated unexpectedly."
                    error_event = json.dumps(
                        {"error": {"message": stream_error, "type": "upstream_error"}},
                        separators=(",", ":"),
                    )
                    yield f"data: {error_event}\n\n".encode()
                    yield b"data: [DONE]\n\n"
                finally:
                    try:
                        await upstream.aclose()
                    except asyncio.CancelledError:
                        if not completed:
                            client_cancelled = True
                            stream_error = "Client disconnected during provider stream cleanup."
                    except Exception:
                        if not completed and stream_error is None:
                            stream_error = "Provider stream cleanup failed before completion."

                attempt_completed_at = datetime.now(UTC)
                elapsed_ms = (time.perf_counter() - attempt_started) * 1000
                if completed:
                    state.health.mark_success(decision.deployment)
                    state.metrics.record_success()
                    if streamed_usage is not None:
                        _record_usage(state, decision.deployment, streamed_usage)
                    usage = _actual_tokens(streamed_usage) if streamed_usage else None
                    if usage is not None:
                        actual_usage_parts.append(usage)
                        cost_usage_parts.append((decision.deployment, usage))
                    actual_cost = _actual_cost(
                        state,
                        [(decision.deployment, usage)] if usage else [],
                        usage is None or usage[2] is None,
                    )
                    outcome = "success"
                    category = None
                else:
                    provider_usage_unknown = budget_reserved or provider_usage_unknown
                    category = (
                        "client_cancelled"
                        if client_cancelled
                        else "deadline_exceeded"
                        if deadline_expired
                        else "stream_interrupted"
                    )
                    if not client_cancelled and not deadline_expired:
                        state.health.mark_failure(decision.deployment)
                        state.metrics.record_failure()
                    state.errors.record(
                        category,
                        decision.deployment,
                        stream_error or "Provider stream ended without [DONE].",
                    )
                    state.latency.record(decision.deployment, elapsed_ms)
                    usage = _actual_tokens(streamed_usage) if streamed_usage else None
                    actual_cost = _actual_cost(
                        state,
                        [(decision.deployment, usage)] if usage else [],
                        usage is None or usage[2] is None,
                    )
                    outcome = "failure"

                if completed:
                    state.latency.record(decision.deployment, elapsed_ms)
                routing_decisions.append(
                    _routing_attempt_event(
                        request_id=request_id,
                        attempt=attempt_number,
                        decision=decision,
                        request_type=classification.request_type.value,
                        decided_at=decision_time,
                        attempt_started_at=attempt_started_at,
                        attempt_completed_at=attempt_completed_at,
                        outcome=outcome,
                        latency_ms=elapsed_ms,
                        usage=usage,
                        actual_cost_usd=actual_cost,
                        failure_category=category,
                        http_status=None
                        if client_cancelled or deadline_expired
                        else 200
                        if completed
                        else 502,
                    )
                )
                finalize_status = (
                    499
                    if client_cancelled
                    else 503
                    if deadline_expired
                    else 200
                    if completed
                    else 502
                )
                await finish(
                    JSONResponse(status_code=finalize_status, content={}),
                    deployment=decision.deployment,
                    tokens=(None, None, None)
                    if provider_usage_unknown
                    else (usage or _sum_actual_tokens(actual_usage_parts)),
                    failure_category=category,
                    actual_cost=_actual_cost(state, cost_usage_parts, provider_usage_unknown),
                    release_budget=not attempted,
                )
                if client_cancelled:
                    raise asyncio.CancelledError

            stream_response = StreamingResponse(
                stream_body(),
                status_code=200,
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                    "X-SabiRoute-Deployment": route_decision.deployment,
                    "X-SabiRoute-Policy": policy.name,
                    "X-SabiRoute-Attempt": str(attempt),
                    "X-SabiRoute-Request-ID": request_id,
                },
            )
            return stream_response

        attempt_completed_at = datetime.now(UTC)
        elapsed_ms = (time.perf_counter() - started) * 1000
        state.health.mark_success(route_decision.deployment)
        state.metrics.record_success()
        state.latency.record(route_decision.deployment, elapsed_ms)
        _record_usage(state, route_decision.deployment, body)
        success_usage = _actual_tokens(body)
        if success_usage is not None:
            actual_usage_parts.append(success_usage)
            cost_usage_parts.append((route_decision.deployment, success_usage))
        success_cost = _actual_cost(
            state,
            [(route_decision.deployment, success_usage)] if success_usage else [],
            success_usage is None or success_usage[2] is None,
        )
        routing_decisions.append(
            _routing_attempt_event(
                request_id=request_id,
                attempt=attempt,
                decision=route_decision,
                request_type=classification.request_type.value,
                decided_at=decision_at,
                attempt_started_at=attempt_started_at,
                attempt_completed_at=attempt_completed_at,
                outcome="success",
                latency_ms=elapsed_ms,
                usage=success_usage,
                actual_cost_usd=success_cost,
                failure_category=None,
                http_status=200,
            )
        )

        success_headers = {
            "X-SabiRoute-Deployment": route_decision.deployment,
            "X-SabiRoute-Policy": policy.name,
            "X-SabiRoute-Attempt": str(attempt),
        }
        if sabi_user_id is not None:
            # Gateway attestation of the accepted identity, for the calling
            # backend only. Never set from client input (see provenance
            # check above) and never forwarded anywhere downstream.
            success_headers["X-SabiRoute-User"] = sabi_user_id
        response = JSONResponse(
            status_code=200,
            content=body,
            headers=success_headers,
        )
        durable = await finish(
            response,
            deployment=route_decision.deployment,
            tokens=(None, None, None)
            if provider_usage_unknown
            else _sum_actual_tokens(actual_usage_parts),
            actual_cost=_actual_cost(state, cost_usage_parts, provider_usage_unknown),
            release_budget=not attempted,
        )
        return durable

    if last_error_category == "deadline_exceeded":
        return await finish(
            _error_response(
                503,
                "The request exceeded its processing deadline.",
                "deadline_exceeded",
                policy=policy.name,
                attempts=attempted,
            ),
            deployment=last_deployment,
            tokens=(None, None, None)
            if provider_usage_unknown
            else _sum_actual_tokens(actual_usage_parts),
            actual_cost=_actual_cost(state, cost_usage_parts, provider_usage_unknown),
            release_budget=not attempted,
            failure_category="deadline_exceeded",
        )
    return await finish(
        _error_response(
            502,
            "All routing attempts failed.",
            "sabiroute_upstream_error",
            policy=policy.name,
            attempts=attempted,
            failure_category=last_error_category or "upstream_error",
        ),
        deployment=last_deployment,
        tokens=(None, None, None)
        if provider_usage_unknown
        else _sum_actual_tokens(actual_usage_parts),
        actual_cost=_actual_cost(state, cost_usage_parts, provider_usage_unknown),
        release_budget=not attempted,
        failure_category=last_error_category or "upstream_error",
    )


def _actual_cost(
    state: GatewayState,
    parts: list[tuple[str, tuple[int | None, int | None, int | None]]],
    has_unknown_usage: bool,
) -> Decimal | None:
    if has_unknown_usage or not parts:
        return None
    total = Decimal(0)
    for deployment_name, (prompt, completion, _) in parts:
        if prompt is None or completion is None:
            return None
        deployment = state.registry.get(deployment_name)
        input_price = deployment.input_cost_per_million_tokens
        output_price = deployment.output_cost_per_million_tokens
        if input_price is None or output_price is None:
            return None
        total += (
            Decimal(prompt) * Decimal(str(input_price))
            + Decimal(completion) * Decimal(str(output_price))
        ) / Decimal(1_000_000)
    return total


def _routing_attempt_event(
    *,
    request_id: str,
    attempt: int,
    decision: Any,
    request_type: str,
    decided_at: datetime,
    attempt_started_at: datetime,
    attempt_completed_at: datetime,
    outcome: str,
    latency_ms: float,
    usage: tuple[int | None, int | None, int | None] | None,
    actual_cost_usd: Decimal | None,
    failure_category: str | None,
    http_status: int | None,
) -> dict[str, Any]:
    explanation = decision.explanation
    scores = (
        [
            {
                "deployment": item.deployment,
                "score": item.score,
                "success_rate": item.success_rate,
                "reliability_samples": item.reliability_samples,
                "average_latency_ms": item.average_latency_ms,
                "latency_normalized": item.latency_normalized,
                "latency_samples": item.latency_samples,
            }
            for item in explanation.candidate_scores
        ]
        if explanation is not None
        else []
    )
    return {
        "request_id": request_id,
        "logical_request_id": request_id,
        "request_type": request_type,
        "candidate_deployments": list(explanation.candidate_deployments)
        if explanation is not None
        else [],
        "capability_eligible_deployments": list(explanation.capability_eligible_deployments)
        if explanation is not None
        else [],
        "eligible_deployments": list(explanation.eligible_deployments)
        if explanation is not None
        else [],
        "capability_excluded_deployments": {
            name: list(reasons)
            for name, reasons in explanation.capability_excluded_deployments.items()
        }
        if explanation is not None
        else {},
        "unhealthy_deployments": list(explanation.unhealthy_deployments)
        if explanation is not None
        else [],
        "scoring_policy_version": explanation.scoring_policy_version
        if explanation is not None
        else "unknown",
        "routing_policy_id": decision.reason.removeprefix("policy:"),
        "scoring_weights": explanation.scoring_weights if explanation is not None else {},
        "scoring_fallback_reason": explanation.scoring_fallback_reason
        if explanation is not None
        else "missing_explanation",
        "candidate_scores": scores,
        "ranked_candidates": list(explanation.ranked_candidates) if explanation is not None else [],
        "selected_deployment": decision.deployment,
        "selection_reason": explanation.selection_reason
        if explanation is not None
        else decision.reason,
        "decision_timestamp": decided_at.isoformat(),
        "attempt_schema_version": "1.1",
        "attempt_started_at": attempt_started_at.isoformat(),
        "attempt_completed_at": attempt_completed_at.isoformat(),
        "outcome_recorded_at": datetime.now(UTC).isoformat(),
        "fallback_attempt": attempt,
        "outcome": outcome,
        "http_status": http_status,
        "failure_category": failure_category,
        "latency_ms": latency_ms,
        "usage": {
            "prompt_tokens": usage[0],
            "completion_tokens": usage[1],
            "total_tokens": usage[2],
        }
        if usage is not None
        else None,
        "actual_cost_usd": str(actual_cost_usd) if actual_cost_usd is not None else None,
    }
