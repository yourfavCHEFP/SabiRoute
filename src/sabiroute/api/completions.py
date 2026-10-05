"""OpenAI-compatible chat completions with health-aware routing and fallback."""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from ..gateway import GatewayState
from ..providers.litellm_client import LiteLLMClientError
from ..routing.policies import RoutingPolicy

router = APIRouter(tags=["completions"])

# Non-5xx statuses that a different deployment may still resolve
# (expired key on one provider, quota exhausted, throttling).
RETRYABLE_STATUS_CODES = {401, 403, 429}


class UnknownModelError(KeyError):
    """Raised when a requested model matches neither alias nor policy."""


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible request body; unknown fields pass through."""

    model_config = ConfigDict(extra="allow")

    model: str = Field(min_length=1)
    messages: list[dict[str, Any]] = Field(min_length=1)


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
            RoutingPolicy(name="alias", max_attempts=2, strategy="passthrough"),
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
    usage = body.get("usage")
    if not isinstance(usage, dict):
        return

    state.usage.record(
        model=deployment,
        prompt_tokens=usage.get("prompt_tokens") or 0,
        completion_tokens=usage.get("completion_tokens") or 0,
    )


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


@router.post("/v1/chat/completions")
async def chat_completions(
    payload: ChatCompletionRequest,
    request: Request,
) -> JSONResponse:
    state: GatewayState = request.app.state.gateway

    if len(state.registry) == 0:
        detail = "SabiRoute has no deployments configured."
        if state.startup_error:
            detail = f"{detail} Startup error: {state.startup_error}"
        return _error_response(503, detail, "sabiroute_not_configured")

    try:
        candidates, policy = _resolve_target(state, payload.model)
    except UnknownModelError:
        return _error_response(
            404,
            f"Unknown model {payload.model!r}.",
            "invalid_request_error",
            available_models=[
                deployment.name for deployment in state.registry.list_deployments()
            ],
        )

    extras = {
        key: value
        for key, value in (payload.model_extra or {}).items()
        if value is not None and key not in {"model", "messages"}
    }
    if extras.pop("stream", False):
        return _error_response(
            400,
            "Streaming is not supported yet.",
            "invalid_request_error",
        )
    temperature = extras.pop("temperature", None)
    max_tokens = extras.pop("max_tokens", None)

    attempted: list[str] = []
    last_error: LiteLLMClientError | None = None

    for attempt in range(1, policy.max_attempts + 1):
        try:
            decision = state.router.choose_deployment(
                candidates,
                policy_name=policy.name,
                attempted=attempted,
            )
        except ValueError:
            break  # every candidate has been attempted

        attempted.append(decision.deployment)
        state.metrics.record_request(decision.deployment)

        started = time.perf_counter()
        try:
            body = await state.client.chat_completion(
                decision,
                payload.messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **extras,
            )
        except LiteLLMClientError as exc:
            elapsed_ms = (time.perf_counter() - started) * 1000
            state.health.mark_failure(decision.deployment)
            state.metrics.record_failure()
            state.errors.record(_error_category(exc), decision.deployment, str(exc))
            state.latency.record(decision.deployment, elapsed_ms)
            last_error = exc

            status = exc.status_code
            retryable = (
                status is None or status >= 500 or status in RETRYABLE_STATUS_CODES
            )
            if not retryable:
                break
            continue

        elapsed_ms = (time.perf_counter() - started) * 1000
        state.health.mark_success(decision.deployment)
        state.metrics.record_success()
        state.latency.record(decision.deployment, elapsed_ms)
        _record_usage(state, decision.deployment, body)

        return JSONResponse(
            status_code=200,
            content=body,
            headers={
                "X-SabiRoute-Deployment": decision.deployment,
                "X-SabiRoute-Policy": policy.name,
                "X-SabiRoute-Attempt": str(attempt),
            },
        )

    return _error_response(
        502,
        "All routing attempts failed.",
        "sabiroute_upstream_error",
        policy=policy.name,
        attempts=attempted,
        last_error=str(last_error) if last_error else None,
    )
