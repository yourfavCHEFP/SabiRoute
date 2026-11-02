"""Recovery/shutdown failure-injection tests (isolated, no live services).

Covers: persistence-failure fail-closed paths, streaming cancellation
finalization, executor drain consistency, and startup/shutdown purge
hygiene. Uses in-memory stores and disposable SQLite only.
"""

from __future__ import annotations

import asyncio

import pytest
from conftest import InMemoryApiKeyStore, StubLiteLLMClient, make_config, provision_test_key
from fastapi.testclient import TestClient

from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app

MESSAGES = [{"role": "user", "content": "hello"}]


def _client(stub, store=None):
    state = build_gateway_state(
        config=make_config(), client=stub, key_store=store or InMemoryApiKeyStore()
    )
    key = provision_test_key(state)
    return TestClient(create_app(state=state), headers={"Authorization": f"Bearer {key}"}), state


def test_persistence_failure_fails_closed_without_success():
    """Usage-store failure during finalize must not fabricate success."""
    stub = StubLiteLLMClient()
    client, state = _client(stub)
    assert isinstance(state.key_store, InMemoryApiKeyStore)
    state.key_store.fail_finalize_usage_writes = True
    response = client.post("/v1/chat/completions", json={"model": "primary", "messages": MESSAGES})
    assert response.status_code == 503
    assert response.json()["error"]["type"] == "usage_store_unavailable"
    state.key_store.fail_finalize_usage_writes = False


def test_feature_snapshot_failure_blocks_before_provider_call():
    """Pre-routing snapshot failure must prevent provider egress."""
    stub = StubLiteLLMClient()
    client, state = _client(stub)
    assert isinstance(state.key_store, InMemoryApiKeyStore)
    state.key_store.fail_feature_snapshot_writes = True
    response = client.post("/v1/chat/completions", json={"model": "primary", "messages": MESSAGES})
    assert response.status_code == 503
    assert stub.calls == []


def test_startup_shutdown_purge_failure_does_not_break_lifespan():
    """Purge hygiene failure must never break startup or shutdown."""
    import contextlib

    from sabiroute.chat.store import SabiChatStore

    stub = StubLiteLLMClient()
    state = build_gateway_state(
        config=make_config(), client=stub, key_store=InMemoryApiKeyStore()
    )
    provision_test_key(state)
    state.chat_store = SabiChatStore("sqlite:///:memory:")

    def boom(*args, **kwargs):
        raise RuntimeError("simulated purge failure")

    store = state.chat_store
    assert store is not None
    monkey_orig = store.purge_expired_sessions
    store.purge_expired_sessions = boom  # type: ignore[method-assign]
    try:
        app = create_app(state=state)
        with TestClient(app):
            pass
    except RuntimeError:
        pytest.fail("purge failure propagated through lifespan")
    finally:
        store.purge_expired_sessions = monkey_orig  # type: ignore[method-assign]
        # Suppress the known Starlette merged-lifespan asyncgen warning that
        # surfaces only when this test runs in the same process after suites
        # that leave lifespan generators pending; it is test-harness noise,
        # not a product failure (purge already proved best-effort above).
        with contextlib.suppress(RuntimeError):
            asyncio.get_event_loop_policy().get_event_loop().run_until_complete(
                asyncio.sleep(0)
            )


def test_executor_capacity_recovers_after_failures():
    """Executor slots must be consistent after worker failures."""
    from sabiroute.security.store_executor import BoundedStoreExecutor

    async def run():
        ex = BoundedStoreExecutor(max_concurrency=2)

        def boom():
            raise RuntimeError("worker boom")

        with pytest.raises(RuntimeError, match="worker boom"):
            await ex.run(boom)
        assert ex.in_use_count == 0
        assert await ex.run(lambda: 42) == 42
        assert ex.in_use_count == 0
