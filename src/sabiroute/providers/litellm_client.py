from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import httpx

from ..routing.router import RouteDecision


class LiteLLMClientError(RuntimeError):
    """Normalized error raised when the LiteLLM gateway cannot execute a request."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_body: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class LiteLLMClient:
    """Small OpenAI-compatible client for the SabiRoute -> LiteLLM boundary.

    SabiRoute chooses an eligible deployment alias. LiteLLM performs the actual
    provider call, provider-specific retries, cooldowns, load balancing, and
    configured fallbacks.
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:4000",
        api_key: str | None = None,
        timeout_seconds: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = httpx.Timeout(timeout_seconds)

    async def chat_completion(
        self,
        decision: RouteDecision,
        messages: Sequence[Mapping[str, Any]],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        """Execute one non-streaming chat completion through LiteLLM Proxy."""
        payload: dict[str, Any] = {
            "model": decision.deployment,
            "messages": list(messages),
            **extra,
        }

        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        url = f"{self.base_url}/v1/chat/completions"

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                headers=headers,
            ) as client:
                response = await client.post(url, json=payload)
        except httpx.TimeoutException as exc:
            raise LiteLLMClientError("LiteLLM gateway request timed out.") from exc
        except httpx.HTTPError as exc:
            raise LiteLLMClientError(f"LiteLLM gateway transport error: {exc}") from exc

        try:
            body = response.json()
        except ValueError:
            body = response.text

        if response.is_error:
            detail = body.get("error", body) if isinstance(body, dict) else body
            raise LiteLLMClientError(
                f"LiteLLM gateway returned HTTP {response.status_code}: {detail}",
                status_code=response.status_code,
                response_body=body,
            )

        if not isinstance(body, dict):
            raise LiteLLMClientError(
                "LiteLLM gateway returned a non-object JSON response.",
                status_code=response.status_code,
                response_body=body,
            )

        return body
