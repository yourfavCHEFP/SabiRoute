"""Bounded off-thread execution for synchronous store operations."""

from __future__ import annotations

import asyncio
import collections
import threading
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

DEFAULT_MAX_STORE_CONCURRENCY = 32


class _LoopSemaphore:
    """Fair counting semaphore usable from multiple event loops.

    Slot accounting lives behind a threading lock; waiters are woken via
    their own loop's ``call_soon_threadsafe``. New arrivals never barge
    ahead of queued waiters. Waiter entries are removed on grant or on
    cancellation, so no per-loop state accumulates: sharing one executor
    across test harnesses (or any loop topology) stays correct, and in a
    single-loop deployment it behaves exactly like a bounded semaphore.
    """

    def __init__(self, value: int) -> None:
        self._guard = threading.Lock()
        self._slots = value
        self._waiters: collections.deque[
            tuple[asyncio.AbstractEventLoop, asyncio.Future[None]]
        ] = collections.deque()

    async def acquire(self) -> None:
        loop = asyncio.get_running_loop()
        with self._guard:
            if self._slots > 0 and not self._waiters:
                self._slots -= 1
                return
            future: asyncio.Future[None] = loop.create_future()
            self._waiters.append((loop, future))
        try:
            await future
        except BaseException:
            # Cancelled (or failed) while queued: withdraw so the slot can
            # never be granted to a waiter that already left.
            with self._guard:
                for entry in list(self._waiters):
                    if entry[1] is future:
                        self._waiters.remove(entry)
                        break
            raise

    def release(self) -> None:
        with self._guard:
            while self._waiters:
                waiter_loop, waiter_future = self._waiters.popleft()
                if not waiter_future.done():
                    break
            else:
                self._slots += 1
                return

            def _wake() -> None:
                if waiter_future.done():
                    # Left between pop and wake: hand the slot back.
                    with self._guard:
                        self._slots += 1
                    return
                try:
                    waiter_future.set_result(None)
                except asyncio.InvalidStateError:
                    with self._guard:
                        self._slots += 1

            try:
                waiter_loop.call_soon_threadsafe(_wake)
            except RuntimeError:
                # Owning loop is gone; the waiter is gone with it.
                with self._guard:
                    self._slots += 1


class BoundedStoreExecutor:
    """Run blocking store callables on worker threads with bounded concurrency.

    Capacity accounting tracks started-but-unfinished worker operations:

    - Waiting for capacity is cancellable and starts nothing.
    - Cancelling while waiting never starts the operation.
    - Cancelling while the worker runs does NOT free the slot early; the
      slot releases only when the worker function actually returns. The
      worker keeps running to completion: cancellation is not preemption,
      and a timed-out caller must not imply the database work stopped.
    - Results and worker exceptions propagate to the waiter that is still
      awaiting. A waiter that already left observes its own cancellation.

    At most ``max_concurrency`` worker operations are active at once; each
    runs on a daemon thread that exits when its call returns. SQLAlchemy
    sessions/connections must stay inside a single worker call: the current
    store methods open short-lived ``engine.begin()`` blocks, which
    satisfies this constraint.
    """

    def __init__(self, max_concurrency: int = DEFAULT_MAX_STORE_CONCURRENCY) -> None:
        if max_concurrency < 1:
            raise ValueError("Store executor concurrency must be positive.")
        self._max_concurrency = max_concurrency
        self._semaphore = _LoopSemaphore(max_concurrency)
        self._in_use = 0

    @property
    def max_concurrency(self) -> int:
        return self._max_concurrency

    @property
    def in_use_count(self) -> int:
        """Worker operations currently holding capacity (test seam)."""
        return self._in_use

    async def run(self, func: Callable[P, R], /, *args: P.args, **kwargs: P.kwargs) -> R:
        await self._semaphore.acquire()
        self._in_use += 1
        loop = asyncio.get_running_loop()
        finished: asyncio.Future[R] = loop.create_future()

        def _settle(outcome: tuple[str, Any]) -> None:
            try:
                if finished.cancelled():
                    # The waiter already left (cancelled/timed out). Do not
                    # deliver into it; still release the slot below.
                    return
                kind, value = outcome
                if kind == "ok":
                    finished.set_result(value)
                else:
                    finished.set_exception(value)
            finally:
                # Released only when the worker actually finished, even if
                # the waiter is long gone.
                self._in_use -= 1
                self._semaphore.release()

        def _invoke() -> None:
            try:
                outcome: tuple[str, Any] = ("ok", func(*args, **kwargs))
            except BaseException as exc:
                outcome = ("err", exc)
            loop.call_soon_threadsafe(_settle, outcome)

        threading.Thread(
            target=_invoke, daemon=True, name="sabiroute-store-worker"
        ).start()
        return await finished
