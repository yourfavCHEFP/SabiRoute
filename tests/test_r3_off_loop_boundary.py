"""R3-S4 — the completion path keeps synchronous store I/O off the event loop.

The requirement: "where synchronous DB work exists behind async request paths,
verify the established off-loop/executor boundary ... prove actual behavior."

The *mechanism* is already proven in isolation (`test_store_executor.py`) and
on the admin routes (`test_admin_executor.py`). What was never proven is the
property R3 actually depends on: that a client completion request executes its
store work through that boundary, so one slow query cannot stall the loop that
serves every other request. That is what this file measures.

Two independent proofs:

1. **Thread identity.** A successful ``/v1/chat/completions`` request records
   the OS thread of every store call and compares it with the event-loop
   thread. The app is driven over ``httpx.ASGITransport``, so it runs in *this*
   test's loop — meaning an on-loop store call would report the loop's thread
   id and fail the assertion.
2. **Responsiveness.** With the credential read blocked on a worker thread, an
   unrelated request to ``/health/live`` must still complete. If the store call
   had run on the loop, that request could not be served.

Coordination is by ``asyncio.Event`` / ``threading.Event``; there are no
sleeps and no timing assumptions. The blocking read's bounded wait is a
hang-guard, not a scheduling device.

Labels: VERIFIED BY RUNTIME (stub provider, in-memory store, no network).
"""

from __future__ import annotations

import asyncio
import threading
from typing import Any

import httpx
from conftest import InMemoryApiKeyStore, make_config, provision_test_key

from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app

BODY = {"model": "fast", "messages": [{"role": "user", "content": "hello"}]}


class OkProviderStub:
    """Provider double that succeeds, so accounting finalization also runs."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    async def chat_completion(
        self, decision: Any, messages: Any, **extra: Any
    ) -> dict[str, Any]:
        self.calls.append(decision.deployment)
        return {
            "id": "chatcmpl-r3s4",
            "model": decision.deployment,
            "choices": [{"message": {"role": "assistant", "content": "ok"}}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2},
        }

    async def start_chat_completion_stream(
        self, decision: Any, messages: Any, **extra: Any
    ) -> Any:
        self.calls.append(decision.deployment)
        raise AssertionError("stream stub is not used at the boundary level")


class ThreadRecordingStore(InMemoryApiKeyStore):
    """Records the OS thread of each request-path store call."""

    def __init__(self) -> None:
        super().__init__()
        self.calls: list[tuple[str, int]] = []

    def get(self, key_id: str) -> Any:
        self.calls.append(("get", threading.get_ident()))
        return super().get(key_id)

    def get_budget(self, key_id: str) -> Any:
        self.calls.append(("get_budget", threading.get_ident()))
        return super().get_budget(key_id)

    def create_usage_event(self, event: Any) -> Any:
        self.calls.append(("create_usage_event", threading.get_ident()))
        return super().create_usage_event(event)


def _build(stub: Any, store: Any) -> tuple[Any, str]:
    state = build_gateway_state(config=make_config(), client=stub, key_store=store)
    key = provision_test_key(state)
    return state, key


async def test_completion_store_reads_run_off_the_event_loop() -> None:
    """Every store call on a completion request must run off the loop thread."""
    store = ThreadRecordingStore()
    stub = OkProviderStub()
    state, key = _build(stub, store)
    app = create_app(state=state)
    # Provisioning wrote through the store too; measure only the request.
    store.calls.clear()

    loop_thread = threading.get_ident()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {key}"},
    ) as client:
        resp = await client.post("/v1/chat/completions", json=BODY)

    assert resp.status_code == 200
    # The request really did exercise the store: authentication resolves the
    # credential record, and accounting records the admitted request.
    exercised = {name for name, _ in store.calls}
    assert "get" in exercised, "authentication did not read the store"
    assert "create_usage_event" in exercised, "accounting did not write"
    assert stub.calls == ["primary"]

    # The property under test: none of that work touched the loop thread.
    on_loop_thread = [name for name, tid in store.calls if tid == loop_thread]
    assert on_loop_thread == [], (
        f"store calls executed on the event-loop thread: {on_loop_thread}"
    )


async def test_blocking_store_read_does_not_stall_the_event_loop() -> None:
    """A blocked credential read must not freeze the server.

    If the store read ran on the loop, no other request could be served while
    it was blocked. Serving ``/health/live`` during the block is the proof.
    """
    store = InMemoryApiKeyStore()
    stub = OkProviderStub()
    state, key = _build(stub, store)
    app = create_app(state=state)

    loop = asyncio.get_running_loop()
    loop_thread = threading.get_ident()
    entered = asyncio.Event()
    release = threading.Event()
    original_get = store.get

    def blocking_get(key_id: str) -> Any:
        # Fail fast and precisely on the real invariant. An on-loop store read
        # would block the loop inside the wait below, so the event-ordering
        # assertions further down could not distinguish "served concurrently"
        # from "served after the block ended" — the queued ``entered.set``
        # callback would fire first either way. The thread check is the
        # discriminating one, so it comes first.
        if threading.get_ident() == loop_thread:
            raise AssertionError("store read executed on the event-loop thread")
        # Announce entry from the worker thread, then hold it until released.
        loop.call_soon_threadsafe(entered.set)
        assert release.wait(timeout=10), "the test never released the read"
        return original_get(key_id)

    store.get = blocking_get  # type: ignore[method-assign]

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {key}"},
    ) as client:
        request = asyncio.create_task(client.post("/v1/chat/completions", json=BODY))
        try:
            # Reaching this line means the loop ran while the read was blocked.
            await asyncio.wait_for(entered.wait(), timeout=5)
            assert not release.is_set()
            assert not request.done()
            # Authentication has not resolved, so nothing reached the provider.
            assert stub.calls == []

            live = await asyncio.wait_for(client.get("/health/live"), timeout=5)
            assert live.status_code == 200
            assert live.json() == {"status": "alive"}

            # Control: this coroutine is on the loop thread, and the read is
            # not — so the two are genuinely concurrent, not sequential.
            assert threading.get_ident() == loop_thread
        finally:
            release.set()

        resp = await asyncio.wait_for(request, timeout=5)

    assert resp.status_code == 200
    assert stub.calls == ["primary"]
