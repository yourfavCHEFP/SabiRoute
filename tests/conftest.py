from __future__ import annotations

from typing import Any

import pytest

from sabiroute.config.models import SabiRouteConfig
from sabiroute.config.validation import validate_config
from sabiroute.providers.litellm_client import LiteLLMClientError


def make_config() -> SabiRouteConfig:
    """Build a small in-memory config covering the credential shapes."""

    return validate_config(
        SabiRouteConfig.from_mapping(
            {
                "model_list": [
                    {
                        "model_name": "primary",
                        "litellm_params": {
                            "model": "openai/gpt-4o-mini",
                            "api_key": "os.environ/OPENAI_API_KEY",
                        },
                    },
                    {
                        "model_name": "secondary",
                        "litellm_params": {
                            "model": "groq/llama-3.1-8b-instant",
                            "api_key": "os.environ/GROQ_API_KEY",
                        },
                    },
                    {
                        "model_name": "cloudy",
                        "litellm_params": {
                            "model": "cloudflare/@cf/meta/llama-3.3-70b",
                            "api_key": "os.environ/CLOUDFLARE_API_KEY",
                            "account_id": "os.environ/CLOUDFLARE_ACCOUNT_ID",
                        },
                    },
                    {
                        "model_name": "literal-key",
                        "litellm_params": {
                            "model": "together/meta-llama/Llama-3-70b",
                            "api_key": "sk-literal-test",
                        },
                    },
                ]
            }
        )
    )


class StubLiteLLMClient:
    """Test double for the LiteLLM proxy client.

    Fails the first N calls per deployment, then succeeds.
    """

    def __init__(
        self,
        failures: dict[str, int] | None = None,
        failure_status: int = 500,
    ) -> None:
        self.failures_remaining = dict(failures or {})
        self.failure_status = failure_status
        self.calls: list[str] = []

    async def chat_completion(
        self,
        decision: Any,
        messages: Any,
        **extra: Any,
    ) -> dict[str, Any]:
        self.calls.append(decision.deployment)

        remaining = self.failures_remaining.get(decision.deployment, 0)
        if remaining > 0:
            self.failures_remaining[decision.deployment] = remaining - 1
            raise LiteLLMClientError(
                f"stub failure for {decision.deployment}",
                status_code=self.failure_status,
            )

        return {
            "id": "chatcmpl-stub",
            "model": decision.deployment,
            "choices": [{"message": {"role": "assistant", "content": "ok"}}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2},
        }


@pytest.fixture
def config() -> SabiRouteConfig:
    return make_config()
