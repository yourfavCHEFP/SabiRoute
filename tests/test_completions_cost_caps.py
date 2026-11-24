"""Monetary cost caps in the fallback loop.

A cost-budgeted request must stop retrying when the remaining money cannot
underwrite another attempt. Each break here is a different reason for that
refusal: unknown spend, an unpriced deployment, an input cost that already
exhausts the budget, or a cap that leaves no room for a single output token.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Any

from conftest import InMemoryApiKeyStore
from starlette.requests import Request

from sabiroute.api.completions import ChatCompletionRequest, chat_completions
from sabiroute.config.models import SabiRouteConfig
from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app
from sabiroute.providers.litellm_client import LiteLLMClientError
from sabiroute.security.keys import ApiKeyBudget, ApiKeyIdentity, issue_api_key


def _priced_config(*, input_price: str = "1", output_price: str = "1") -> Any:
    from sabiroute.config.validation import validate_config

    return validate_config(
        SabiRouteConfig.from_mapping(
            {
                "model_list": [
                    {
                        "model_name": "primary",
                        "capabilities": {"chat": True, "streaming": True},
                        "input_cost_per_million_tokens": input_price,
                        "output_cost_per_million_tokens": output_price,
                        "litellm_params": {
                            "model": "openai/gpt-4o-mini",
                            "api_key": "os.environ/OPENAI_API_KEY",
                        },
                    },
                    {
                        "model_name": "secondary",
                        "capabilities": {"chat": True, "streaming": True},
                        "input_cost_per_million_tokens": input_price,
                        "output_cost_per_million_tokens": output_price,
                        "litellm_params": {
                            "model": "groq/llama-3.1-8b-instant",
                            "api_key": "os.environ/GROQ_API_KEY",
                        },
                    },
                ]
            }
        )
    )


class _Client:
    def __init__(self, *, usage: dict[str, Any] | None = None) -> None:
        self.calls = 0
        self._usage = usage

    async def chat_completion(self, *_args: Any, **_kwargs: Any) -> Any:
        self.calls += 1
        raise LiteLLMClientError(
            "upstream failure",
            status_code=500,
            response_body={"usage": self._usage} if self._usage is not None else None,
        )

    async def start_chat_completion_stream(self, *_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("streaming path is not used here")


def _request(state: Any, record: Any) -> Request:
    app = create_app(state=state)
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/v1/chat/completions",
            "raw_path": b"/v1/chat/completions",
            "query_string": b"",
            "root_path": "",
            "headers": [],
            "client": ("127.0.0.1", 1),
            "server": ("test", 80),
            "app": app,
            "state": {
                "api_identity": ApiKeyIdentity(key_id=record.key_id, project_id=record.project_id)
            },
        }
    )


def _payload(max_tokens: int = 16) -> ChatCompletionRequest:
    return ChatCompletionRequest.model_validate(
        {
            "model": "primary",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": max_tokens,
        }
    )


def _run(config: Any, client: Any, budget: ApiKeyBudget) -> tuple[Any, Any]:
    store = InMemoryApiKeyStore()
    state = build_gateway_state(config=config, client=client, key_store=store)
    record, _secret = issue_api_key(store, project_id="proj-1", name="key")
    store.set_budget(record.key_id, budget)
    response = asyncio.run(chat_completions(_payload(), _request(state, record)))
    return response, client


def test_a_retry_with_unknown_spend_stops() -> None:
    client = _Client(usage={"total_tokens": 5})

    response, client = _run(
        _priced_config(),
        client,
        ApiKeyBudget(daily_cost_usd=Decimal("100")),
    )

    assert response.status_code == 502
    assert client.calls == 1


def test_an_unpriced_deployment_stops_the_retry(monkeypatch: Any) -> None:
    # The deployment carries no token price, so the loop cannot compute what
    # one more attempt would cost. The estimator is quoted here so the earlier
    # pricing pre-check is not what answers: the guard under test is the
    # loop's own.
    from sabiroute.api import completions as completions_module
    from sabiroute.config.validation import validate_config

    config = validate_config(
        SabiRouteConfig.from_mapping(
            {
                "model_list": [
                    {
                        "model_name": "primary",
                        "capabilities": {"chat": True, "streaming": True},
                        "litellm_params": {
                            "model": "openai/gpt-4o-mini",
                            "api_key": "os.environ/OPENAI_API_KEY",
                        },
                    },
                ]
            }
        )
    )
    client = _Client()
    store = InMemoryApiKeyStore()
    state = build_gateway_state(config=config, client=client, key_store=store)
    record, _secret = issue_api_key(store, project_id="proj-1", name="key")
    store.set_budget(record.key_id, ApiKeyBudget(daily_cost_usd=Decimal("100")))
    monkeypatch.setattr(completions_module, "estimated_cost_usd", lambda *_a, **_k: Decimal("100"))

    response = asyncio.run(chat_completions(_payload(), _request(state, record)))

    assert response.status_code == 502
    assert client.calls == 0


def test_an_input_cost_that_exhausts_the_budget_stops() -> None:
    client = _Client()

    response, client = _run(
        _priced_config(input_price="1", output_price="0"),
        client,
        ApiKeyBudget(daily_cost_usd=Decimal("0.000001")),
    )

    assert response.status_code == 502
    assert client.calls == 0


def test_a_cap_without_room_for_one_output_token_stops() -> None:
    # The first attempt fails after reporting 15 output tokens. Its cost is
    # just under the estimate, leaving one dollar of headroom at a two-dollar
    # per-token price: the computed cap floors to zero.
    client = _Client(usage={"prompt_tokens": 1, "completion_tokens": 15})

    response, client = _run(
        _priced_config(input_price="1", output_price="1000000"),
        client,
        ApiKeyBudget(daily_cost_usd=Decimal("100")),
    )

    assert response.status_code == 502
    assert client.calls == 1


def test_a_retry_with_unknown_spend_stops_on_a_combined_budget() -> None:
    # A combined token+cost budget passes the token retry gate because the
    # failed attempt reports one token against a sixteen-token reservation.
    # The cost block then finds spend it cannot price and stops the retry.
    client = _Client(usage={"total_tokens": 1})

    response, client = _run(
        _priced_config(input_price="1", output_price="1"),
        client,
        ApiKeyBudget(daily_tokens=1000, daily_cost_usd=Decimal("100")),
    )

    assert response.status_code == 502
    assert client.calls == 1
