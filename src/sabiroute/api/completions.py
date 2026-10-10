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
from ..gateway import GatewayState
from ..intelligence.dataset import FEATURE_SCHEMA_VERSION, make_pre_routing_snapshot
from ..providers.litellm_client import LiteLLMClientError, LiteLLMStream
from ..routing.policies import RoutingPolicy
from ..routing.router import NoCapableDeploymentError, NoHealthyDeploymentError
from ..security.auth import require_client_key
from ..security.budgets import UnsupportedBudgetRequest, estimate_input_tokens, estimated_cost_usd
from ..security.keys import ApiKeyIdentity, RequestUsageEvent, UsageEventValidationError

router = APIRouter(tags=["completions"], dependencies=[Depends(require_client_key)])

# Non-5xx statuses that a different deployment may still resolve
# (expired key on one provider, quota exhausted, throttling).
RETRYABLE_STATUS_CODES = {401, 403, 429}
logger = logging.getLogger(__name__)


class UnknownModelError(KeyError):
    """Raised when a requested model matches neither alias nor policy."""


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible request body; unknown fields pass through."""

    model_config = ConfigDict(extra="allow")

    model: str = Field(min_length=1)
    messages: list[dict[str, Any]] = Field(min_length=1)
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


def _error_category(exc: LiteLLMClientError) -> str:
    if exc.status_code is None:
        return "transport"
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

    request_id = str(uuid4())
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
        store.create_usage_event(event)
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

    def finish(
        response: JSONResponse,
        *,
        deployment: str | None = None,
        tokens: tuple[int | None, int | None, int | None] = (None, None, None),
        failure_category: str | None = None,
        actual_cost: Decimal | None = None,
        release_budget: bool = False,
    ) -> JSONResponse:
        if budget_reserved:
            try:
                if release_budget:
                    store.release_budget(identity.key_id, request_id)
                else:
                    store.reconcile_budget(
                        identity.key_id,
                        request_id,
                        tokens[2],
                        actual_cost,
                    )
            except Exception:
                response = _error_response(
                    503,
                    "Budget reservation could not be reconciled.",
                    "budget_store_unavailable",
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
            persisted = store.finalize_usage_event(final_event)
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

    def snapshot_persistence_failure() -> JSONResponse:
        if budget_reserved:
            try:
                store.release_budget(identity.key_id, request_id)
            except Exception:
                logger.error("Budget reservation release failed after snapshot persistence error.")
        response = _error_response(
            503,
            "Decision telemetry could not be persisted; provider execution was not started.",
            "telemetry_store_unavailable",
        )
        response.headers["X-SabiRoute-Request-ID"] = request_id
        return response

    try:
        key_limit = store.get_rate_limit(identity.key_id)
    except Exception:
        return finish(
            _error_response(
                503,
                "Rate-limit configuration is unavailable.",
                "rate_limit_unavailable",
            ),
            failure_category="rate_limit_config_unavailable",
        )

    if key_limit is not None:
        if state.rate_limiter is None:
            return finish(
                _error_response(503, "Rate limiting is unavailable.", "rate_limiter_unavailable"),
                failure_category="redis_unavailable",
            )
        try:
            rate_decision = await state.rate_limiter.admit(identity.key_id, key_limit)
        except Exception:
            return finish(
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
            return finish(denied, failure_category="rate_limited")

    if len(state.registry) == 0:
        detail = "SabiRoute has no deployments configured."
        if state.startup_error:
            detail = f"{detail} Startup error: {state.startup_error}"
        return finish(
            _error_response(503, detail, "sabiroute_not_configured"),
            failure_category="no_deployments",
        )

    try:
        candidates, policy = _resolve_target(state, payload.model)
    except UnknownModelError:
        return finish(
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

    try:
        budget = store.get_budget(identity.key_id)
    except Exception:
        return finish(
            _error_response(
                503,
                "Budget configuration is unavailable.",
                "budget_store_unavailable",
            ),
            failure_category="budget_config_unavailable",
        )
    if budget is not None:
        if not isinstance(max_tokens, int) or isinstance(max_tokens, bool) or max_tokens < 1:
            return finish(
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
            return finish(
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
            return finish(
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
    try:
        eligibility = state.router.evaluate_candidates(
            candidates,
            required_capabilities=classification.required_capabilities,
        )
    except (KeyError, ValueError):
        return finish(
            _error_response(
                503,
                "The requested route is misconfigured.",
                "route_configuration_error",
            ),
            failure_category="route_configuration_error",
        )
    if not eligibility.capability_eligible_deployments:
        return finish(
            _error_response(
                503,
                "No configured deployment is verified for this request's capabilities.",
                "no_capable_deployment",
            ),
            failure_category="no_capable_deployment",
        )
    if not eligibility.available_deployments:
        return finish(
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
            return finish(
                _error_response(
                    503,
                    "Pricing metadata is unavailable for this request's routing candidates.",
                    "budget_pricing_unavailable",
                ),
                failure_category="budget_pricing_unavailable",
            )
        try:
            denial = store.reserve_budget(
                identity.key_id,
                request_id,
                reserved_tokens,
                estimated_cost,
                event.created_at,
            )
        except Exception:
            return finish(
                _error_response(
                    503,
                    "Budget reservation is unavailable.",
                    "budget_store_unavailable",
                ),
                failure_category="budget_reservation_unavailable",
            )
        if denial is not None:
            if denial == "budget_changed":
                return finish(
                    _error_response(
                        503,
                        "Budget configuration changed during admission.",
                        "budget_store_unavailable",
                    ),
                    failure_category="budget_config_changed",
                )
            if denial.endswith("pricing_unknown"):
                return finish(
                    _error_response(
                        503,
                        "Pricing metadata is unavailable for the configured monetary budget.",
                        "budget_pricing_unavailable",
                    ),
                    failure_category="budget_pricing_unavailable",
                )
            return finish(
                _error_response(
                    429,
                    "The API key's configured budget would be exceeded.",
                    "budget_exceeded",
                    window=denial.split("_", 1)[0],
                ),
                failure_category="budget_exceeded",
            )
        budget_reserved = True

    attempted: list[str] = []
    last_error: LiteLLMClientError | None = None
    last_error_category: str | None = None
    last_deployment: str | None = None
    actual_usage_parts: list[tuple[int | None, int | None, int | None]] = []
    cost_usage_parts: list[tuple[str, tuple[int | None, int | None, int | None]]] = []
    provider_usage_unknown = False

    for attempt in range(1, policy.max_attempts + 1):
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
            return finish(
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
            snapshot_persisted = store.append_pre_routing_feature_snapshot(
                request_id, feature_snapshot
            )
        except UsageEventValidationError as exc:
            logger.error("Pre-routing feature snapshot rejected: %s", exc)
            return finish(
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
            return snapshot_persistence_failure()
        if not snapshot_persisted:
            logger.error("Pre-routing feature snapshot persistence was rejected.")
            return snapshot_persistence_failure()

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
            last_error = exc
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
            finish(
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
            finish(
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
                    category = "client_cancelled" if client_cancelled else "stream_interrupted"
                    if not client_cancelled:
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
                        http_status=None if client_cancelled else 200 if completed else 502,
                    )
                )
                finalize_status = 499 if client_cancelled else 200 if completed else 502
                finish(
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

        response = JSONResponse(
            status_code=200,
            content=body,
            headers={
                "X-SabiRoute-Deployment": route_decision.deployment,
                "X-SabiRoute-Policy": policy.name,
                "X-SabiRoute-Attempt": str(attempt),
            },
        )
        durable = finish(
            response,
            deployment=route_decision.deployment,
            tokens=(None, None, None)
            if provider_usage_unknown
            else _sum_actual_tokens(actual_usage_parts),
            actual_cost=_actual_cost(state, cost_usage_parts, provider_usage_unknown),
            release_budget=not attempted,
        )
        return durable

    return finish(
        _error_response(
            502,
            "All routing attempts failed.",
            "sabiroute_upstream_error",
            policy=policy.name,
            attempts=attempted,
            last_error=str(last_error) if last_error else None,
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
