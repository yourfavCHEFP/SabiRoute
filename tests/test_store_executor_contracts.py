"""Contract coverage for :mod:`sabiroute.security.store_executor`.

The executor keeps blocking store calls off the event loop. Existing tests
cover the happy path, cancellation and exception propagation; what follows
pins the three seams that only a hand-built schedule reaches: the advertised
concurrency ceiling, the orphaned-waiter recovery that returns a slot when a
waiter leaves between grant and wake-up, and the exactly-once capacity release
that stops a slot leaking when a completion is delivered twice.
"""
from __future__ import annotations

import asyncio
from typing import Any

import pytest

from sabiroute.security import store_executor as executor_module
from sabiroute.security.store_executor import BoundedStoreExecutor, _LoopSemaphore


class _LockedFuture:
    """Reports itself un-done but refuses a result, like a cancelled future."""

    def __init__(self) -> None:
        self.result_attempts = 0

    def done(self) -> bool:
        return False

    def set_result(self, _value: Any) -> None:
        self.result_attempts += 1
        raise asyncio.InvalidStateError("future is already cancelled")


class _RecordingLoop:
    """Delegates to a real loop but remembers completions it was handed."""

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self.settles: list[tuple[Any, tuple[Any, ...]]] = []

    def __getattr__(self, name: str) -> Any:
        return getattr(self._loop, name)

    def call_soon_threadsafe(
        self, callback: Any, *args: Any
    ) -> asyncio.Handle:
        if args:
            self.settles.append((callback, args))
        return self._loop.call_soon_threadsafe(callback, *args)


def test_concurrency_ceiling_is_exposed() -> None:
    assert BoundedStoreExecutor(4).max_concurrency == 4
    assert BoundedStoreExecutor().max_concurrency == 32


def test_a_waiter_that_leaves_after_its_grant_returns_the_slot() -> None:
    async def scenario() -> tuple[int, int]:
        # Capacity is zero because the queued waiter was already charged for
        # the slot it is waiting on; recovery must hand that slot back.
        semaphore = _LoopSemaphore(0)
        loop = asyncio.get_running_loop()
        orphan = _LockedFuture()
        with semaphore._guard:
            semaphore._waiters.append((loop, orphan))  # type: ignore[arg-type]

        semaphore.release()
        await asyncio.sleep(0)

        return semaphore._slots, orphan.result_attempts

    slots, attempts = asyncio.run(scenario())

    assert attempts == 1
    assert slots == 1


def test_a_duplicate_completion_releases_the_slot_only_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def scenario() -> tuple[BoundedStoreExecutor, str, _RecordingLoop]:
        executor = BoundedStoreExecutor(1)
        recorder = _RecordingLoop(asyncio.get_running_loop())
        monkeypatch.setattr(executor_module, "asyncio", _Proxy(recorder))

        result = await executor.run(lambda: "done")
        return executor, result, recorder

    executor, result, recorder = asyncio.run(scenario())

    assert result == "done"
    assert executor.in_use_count == 0
    assert len(recorder.settles) == 1

    settle, args = recorder.settles[0]
    with pytest.raises(asyncio.InvalidStateError):
        settle(*args)

    # The idempotency guard means a second delivery cannot decrement twice.
    assert executor.in_use_count == 0


class _Proxy:
    """Stands in for the ``asyncio`` module inside ``store_executor``."""

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def __getattr__(self, name: str) -> Any:
        return getattr(asyncio, name)

    def get_running_loop(self) -> asyncio.AbstractEventLoop:
        return self._loop  # type: ignore[return-value]
