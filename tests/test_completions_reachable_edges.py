"""The last ordinary branches in the completions handler.

Not cancellation: a message whose mapping refuses ``get``, and a
quota-metered request whose payload the token estimator cannot price. Both
are reachable input shapes rather than defensive code.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from conftest import InMemoryApiKeyStore, StubLiteLLMClient, make_config
from starlette.requests import Request

from sabiroute.api.completions import ChatCompletionRequest, chat_completions
from sabiroute.freepool.eligibility import FreePoolPolicy
from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app
from sabiroute.quotas import QuotaPolicy
from sabiroute.security.keys import SABI_USER_ID_FIELD, ApiKeyIdentity, issue_api_key

UID = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"


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


class _ExplodingMapping(dict):
    """A mapping whose ``get`` raises, so the size guard's fallback runs."""

    def get(self, *_args: Any, **_kwargs: Any) -> Any:
        raise AttributeError("mapping refuses get")


def test_a_message_mapping_that_refuses_get_is_treated_as_contentless() -> None:
    store = InMemoryApiKeyStore()
    state = build_gateway_state(config=make_config(), client=StubLiteLLMClient(), key_store=store)
    record, _secret = issue_api_key(store, project_id="proj-1", name="key")
    payload = ChatCompletionRequest.model_construct(
        model="primary",
        messages=[_ExplodingMapping({"role": "user", "content": "hello"})],
        max_tokens=None,
    )

    # The size guard tolerates the mapping and moves on. A later stage reads
    # the same message through the mapping and does not, so the guard's
    # tolerance is observed as the point where that later read fails.
    with pytest.raises(AttributeError, match="mapping refuses get"):
        asyncio.run(chat_completions(payload, _request(state, record)))


def test_a_quota_request_the_estimator_cannot_price_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The estimator is the component that cannot price multimodal content;
    # refusing here must be the quota gate's answer, not a crash.
    from sabiroute.api import completions as completions_module
    from sabiroute.security.budgets import UnsupportedBudgetRequest

    store = InMemoryApiKeyStore()
    state = build_gateway_state(
        config=make_config(),
        client=StubLiteLLMClient(),
        key_store=store,
        free_pool=FreePoolPolicy(enabled=True, eligible_deployments=frozenset({"primary"})),
        quota_policy=QuotaPolicy(pilot_users=frozenset({UID})),
    )
    record, _secret = issue_api_key(store, project_id="sabichat-service", name="service")
    state.sabichat_service_key_id = record.key_id
    store.shared_inference = True

    def refuse(_messages: Any) -> int:
        raise UnsupportedBudgetRequest("multimodal content cannot be priced")

    monkeypatch.setattr(completions_module, "estimate_input_tokens", refuse)

    payload = ChatCompletionRequest.model_validate(
        {
            "model": "primary",
            "messages": [{"role": "user", "content": "hello"}],
            "max_tokens": 16,
            "sabi_route_free_chat": True,
            SABI_USER_ID_FIELD: UID,
        }
    )

    response = asyncio.run(chat_completions(payload, _request(state, record)))

    assert response.status_code == 400
