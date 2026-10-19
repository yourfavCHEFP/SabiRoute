"""Deterministic tests for the bounded store executor (Mission 16A).

Uses threading.Event gates — never arbitrary sleeps — so every outcome is
forced, not timed. The real executor (not a double) is under test.
"""

from __future__ import annotations

import asyncio
import threading
from typing import Any

import pytest

from sabiroute.security.store_executor import BoundedStoreExecutor


def test_blocked_operation_does_not_stall_unrelated_work() -> None:
    async def main() -> str:
        executor = BoundedStoreExecutor(max_concurrency=4)
        gate = threading.Event()

        async def blocked() -> str:
            return await executor.run(gate.wait)

        async def fast() -> str:
            await asyncio.sleep(0)
            return "fast-done"

        task = asyncio.ensure_future(blocked())
        try:
            await asyncio.sleep(0)
            assert await fast() == "fast-done"
            assert executor.in_use_count == 1
            return "unblocked"
        finally:
            gate.set()
            assert await task is True

    assert asyncio.run(main()) == "unblocked"


def test_concurrency_limit_is_exact() -> None:
    async def main() -> None:
        executor = BoundedStoreExecutor(max_concurrency=2)
        entered: list[str] = []
        release = threading.Event()

        async def op(name: str) -> str:
            def _work() -> str:
                entered.append(name)
                assert release.wait(timeout=10)
                return name

            return await executor.run(_work)

        tasks = [asyncio.ensure_future(op(f"op-{i}")) for i in range(4)]
        try:
            await asyncio.sleep(0.05)
            # Exactly two started; the rest queue without starting.
            assert sorted(entered) == ["op-0", "op-1"]
            assert executor.in_use_count == 2
        finally:
            release.set()
        assert sorted(await asyncio.gather(*tasks)) == [f"op-{i}" for i in range(4)]
        assert executor.in_use_count == 0

    asyncio.run(main())


def test_cancel_while_queued_starts_nothing() -> None:
    async def main() -> None:
        executor = BoundedStoreExecutor(max_concurrency=1)
        gate = threading.Event()
        started: list[str] = []

        async def holder() -> str:
            return await executor.run(gate.wait)

        async def queued() -> str:
            def _work() -> str:
                started.append("queued-ran")
                return "queued-ran"

            return await executor.run(_work)

        hold = asyncio.ensure_future(holder())
        await asyncio.sleep(0)
        waiter = asyncio.ensure_future(queued())
        await asyncio.sleep(0)
        waiter.cancel()
        with pytest.raises(asyncio.CancelledError):
            await waiter
        assert started == []
        assert executor.in_use_count == 1
        gate.set()
        assert await hold is True
        assert executor.in_use_count == 0

    asyncio.run(main())


def test_cancel_while_running_keeps_slot_until_worker_finishes() -> None:
    async def main() -> None:
        executor = BoundedStoreExecutor(max_concurrency=1)
        release = threading.Event()
        gate_b = threading.Event()

        async def op_a() -> str:
            return await executor.run(lambda: (release.wait(timeout=10), "a")[1])

        async def op_b() -> str:
            def _work() -> str:
                gate_b.set()
                return "b"

            return await executor.run(_work)

        task_a = asyncio.ensure_future(op_a())
        await asyncio.sleep(0)
        waiter_b = asyncio.ensure_future(op_b())
        await asyncio.sleep(0)
        # B is queued behind A. Cancelling B must not free A's slot early:
        # a further operation must still wait.
        waiter_b.cancel()
        with pytest.raises(asyncio.CancelledError):
            await waiter_b
        assert executor.in_use_count == 1
        late = asyncio.ensure_future(op_b())
        await asyncio.sleep(0.05)
        assert not late.done()
        assert gate_b.is_set() is False
        release.set()
        assert await task_a == "a"
        assert await late == "b"
        assert executor.in_use_count == 0

    asyncio.run(main())


def test_results_and_exceptions_propagate() -> None:
    async def main() -> None:
        executor = BoundedStoreExecutor(max_concurrency=2)

        def boom() -> None:
            raise RuntimeError("worker failure")

        assert await executor.run(lambda: 40 + 2) == 42
        with pytest.raises(RuntimeError, match="worker failure"):
            await executor.run(boom)

    asyncio.run(main())


def test_deadline_timeout_leaves_worker_and_slot_consistent() -> None:
    async def main() -> None:
        executor = BoundedStoreExecutor(max_concurrency=1)
        release = threading.Event()

        async def blocked() -> str:
            return await executor.run(lambda: release.wait(timeout=10) and "done")

        with pytest.raises(TimeoutError):
            await asyncio.wait_for(blocked(), timeout=0.05)
        # The waiter left, but the worker still holds the slot.
        assert executor.in_use_count == 1
        release.set()
        # Slot frees only when the worker actually finishes.
        for _ in range(100):
            if executor.in_use_count == 0:
                break
            await asyncio.sleep(0.01)
        assert executor.in_use_count == 0

    asyncio.run(main())


def test_executor_rejects_nonpositive_capacity() -> None:
    with pytest.raises(ValueError):
        BoundedStoreExecutor(max_concurrency=0)


def test_executor_usable_across_sequential_loops() -> None:
    # Test harnesses (TestClient portals, asyncio.run per call) use several
    # loops against one gateway state; capacity must survive loop changes.
    executor = BoundedStoreExecutor(max_concurrency=1)

    async def once(value: int) -> int:
        return await executor.run(lambda: value)

    assert asyncio.run(once(1)) == 1
    assert asyncio.run(once(2)) == 2
    assert executor.in_use_count == 0


def test_invalid_deadline_env_rejected() -> None:
    # Cross-check shipped alongside the executor: invalid budgets fail loud.
    import os

    from sabiroute.api.deadline import request_deadline_seconds

    old = os.environ.get("SABIROUTE_REQUEST_DEADLINE_SECONDS")
    os.environ["SABIROUTE_REQUEST_DEADLINE_SECONDS"] = "soon"
    try:
        with pytest.raises(ValueError):
            request_deadline_seconds()
    finally:
        if old is None:
            del os.environ["SABIROUTE_REQUEST_DEADLINE_SECONDS"]
        else:
            os.environ["SABIROUTE_REQUEST_DEADLINE_SECONDS"] = old


def test_worker_completion_after_event_loop_closed_releases_capacity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executor = BoundedStoreExecutor(max_concurrency=1)
    worker_entered = threading.Event()
    worker_release = threading.Event()
    worker_exited = threading.Event()
    thread_exceptions: list[BaseException] = []
    orig_excepthook = threading.excepthook

    def capture_excepthook(args: threading.ExceptHookArgs) -> None:
        if args.exc_value is not None:
            thread_exceptions.append(args.exc_value)
        orig_excepthook(args)

    monkeypatch.setattr(threading, "excepthook", capture_excepthook)

    def blocked_worker() -> str:
        worker_entered.set()
        assert worker_release.wait(timeout=5.0)
        worker_exited.set()
        return "finished-after-close"

    loop1 = asyncio.new_event_loop()
    try:
        async def start_and_cancel() -> None:
            task = loop1.create_task(executor.run(blocked_worker))
            assert await loop1.run_in_executor(None, worker_entered.wait, 5.0)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

        loop1.run_until_complete(start_and_cancel())
        assert executor.in_use_count == 1
    finally:
        loop1.close()

    # Release the worker after its originating event loop is already closed.
    worker_release.set()
    assert worker_exited.wait(timeout=5.0)
    for _ in range(100):
        if executor.in_use_count == 0:
            break
        threading.Event().wait(0.01)

    assert thread_exceptions == []
    assert executor.in_use_count == 0
    assert asyncio.run(executor.run(lambda: "recovered")) == "recovered"
    assert executor.in_use_count == 0


def test_waiter_cancelled_between_selection_and_wake_hands_off_to_next_waiter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Part 1: Waiter A is popped by release(), then cancelled before its _wake
    # callback executes on the event loop, while Waiter B remains queued.
    async def run_cancel_before_wake() -> None:
        executor = BoundedStoreExecutor(max_concurrency=1)
        loop = asyncio.get_running_loop()
        holder_entered = threading.Event()
        holder_release = threading.Event()
        a_runs = 0
        b_runs = 0

        def hold_slot() -> str:
            holder_entered.set()
            assert holder_release.wait(timeout=5.0)
            return "holder"

        def work_a() -> str:
            nonlocal a_runs
            a_runs += 1
            return "a"

        def work_b() -> str:
            nonlocal b_runs
            b_runs += 1
            return "b-completed"

        holder_task = asyncio.create_task(executor.run(hold_slot))
        assert await asyncio.to_thread(holder_entered.wait, 5.0)

        task_a = asyncio.create_task(executor.run(work_a))
        while len(executor._semaphore._waiters) < 1:
            await asyncio.sleep(0)
        waiter_a_future = executor._semaphore._waiters[0][1]

        task_b = asyncio.create_task(executor.run(work_b))
        while len(executor._semaphore._waiters) < 2:
            await asyncio.sleep(0)

        orig_call_soon_threadsafe = loop.call_soon_threadsafe
        intercepted_a_wake = False

        def cancel_a_before_wake(
            callback: Any, *args: Any, **kwargs: Any
        ) -> Any:
            nonlocal intercepted_a_wake
            if (
                not intercepted_a_wake
                and getattr(callback, "__name__", "") == "_wake"
            ):
                intercepted_a_wake = True

                def cancel_then_wake() -> None:
                    # Waiter A has already been popped by release(), leaving
                    # only Waiter B in _waiters. Cancel Waiter A right before
                    # _wake inspects target_future.done().
                    assert len(executor._semaphore._waiters) == 1
                    waiter_a_future.cancel()
                    callback(*args, **kwargs)

                return orig_call_soon_threadsafe(cancel_then_wake)
            return orig_call_soon_threadsafe(callback, *args, **kwargs)

        monkeypatch.setattr(loop, "call_soon_threadsafe", cancel_a_before_wake)

        holder_release.set()
        assert await holder_task == "holder"
        with pytest.raises(asyncio.CancelledError):
            await task_a
        assert await task_b == "b-completed"

        assert intercepted_a_wake is True
        assert a_runs == 0
        assert b_runs == 1
        assert executor.in_use_count == 0
        assert executor._semaphore._slots == 1
        assert len(executor._semaphore._waiters) == 0
        assert await executor.run(lambda: "post-check") == "post-check"
        assert executor._semaphore._slots == 1

    asyncio.run(run_cancel_before_wake())

    # Part 2: _wake() grants the slot via set_result(None), and Task A is
    # cancelled in the same loop turn before acquire() resumes, while Waiter B
    # remains queued.
    async def run_cancel_after_wake_grant() -> None:
        executor = BoundedStoreExecutor(max_concurrency=1)
        loop = asyncio.get_running_loop()
        holder_entered = threading.Event()
        holder_release = threading.Event()
        a_runs = 0
        b_runs = 0

        def hold_slot() -> str:
            holder_entered.set()
            assert holder_release.wait(timeout=5.0)
            return "holder"

        def work_a() -> str:
            nonlocal a_runs
            a_runs += 1
            return "a"

        def work_b() -> str:
            nonlocal b_runs
            b_runs += 1
            return "b-after-grant-cancel"

        holder_task = asyncio.create_task(executor.run(hold_slot))
        assert await asyncio.to_thread(holder_entered.wait, 5.0)

        task_a = asyncio.create_task(executor.run(work_a))
        while len(executor._semaphore._waiters) < 1:
            await asyncio.sleep(0)
        task_b = asyncio.create_task(executor.run(work_b))
        while len(executor._semaphore._waiters) < 2:
            await asyncio.sleep(0)

        orig_call_soon_threadsafe = loop.call_soon_threadsafe
        intercepted_a_wake = False

        def wake_then_cancel_task_a(
            callback: Any, *args: Any, **kwargs: Any
        ) -> Any:
            nonlocal intercepted_a_wake
            if (
                not intercepted_a_wake
                and getattr(callback, "__name__", "") == "_wake"
            ):
                intercepted_a_wake = True

                def grant_then_cancel_task() -> None:
                    # _wake grants the slot to Waiter A's future first
                    # (set_result(None) succeeds), then task_a.cancel() marks
                    # task_a for cancellation before acquire() resumes.
                    callback(*args, **kwargs)
                    task_a.cancel()

                return orig_call_soon_threadsafe(grant_then_cancel_task)
            return orig_call_soon_threadsafe(callback, *args, **kwargs)

        monkeypatch.setattr(loop, "call_soon_threadsafe", wake_then_cancel_task_a)

        holder_release.set()
        assert await holder_task == "holder"
        with pytest.raises(asyncio.CancelledError):
            await task_a
        assert await task_b == "b-after-grant-cancel"

        assert intercepted_a_wake is True
        assert a_runs == 0
        assert b_runs == 1
        assert executor.in_use_count == 0
        assert executor._semaphore._slots == 1
        assert len(executor._semaphore._waiters) == 0

    asyncio.run(run_cancel_after_wake_grant())


def test_closed_loop_waiter_preceding_live_waiter_hands_off_and_preserves_capacity() -> None:
    executor = BoundedStoreExecutor(max_concurrency=1)
    holder_entered = threading.Event()
    holder_release = threading.Event()
    order: list[str] = []

    def hold_slot() -> str:
        holder_entered.set()
        assert holder_release.wait(timeout=5.0)
        return "holder"

    # Case 1: A waiter whose loop is already closed sits at the head of _waiters,
    # and a second waiter whose loop closes right when call_soon_threadsafe(_wake)
    # is invoked sits second, both ahead of live Waiter B and Waiter C.
    closed_loop = asyncio.new_event_loop()
    closed_future = closed_loop.create_future()
    closed_loop.close()

    class _RaceClosedLoop:
        def is_closed(self) -> bool:
            # Simulates a loop that is still open during the _guard check and
            # closes right before call_soon_threadsafe(_wake) is called.
            return False

        def call_soon_threadsafe(self, callback: Any, *args: Any) -> Any:
            raise RuntimeError("Event loop is closed")

    race_loop = asyncio.new_event_loop()
    race_future = race_loop.create_future()
    race_loop.close()

    async def run_live_waiters() -> None:
        holder_task = asyncio.create_task(executor.run(hold_slot))
        assert await asyncio.to_thread(holder_entered.wait, 5.0)
        assert executor.in_use_count == 1
        assert executor._semaphore._slots == 0

        # Enqueue two unusable closed-loop waiters ahead of live Waiters B and C.
        with executor._semaphore._guard:
            executor._semaphore._waiters.append((closed_loop, closed_future))
            executor._semaphore._waiters.append(
                (_RaceClosedLoop(), race_future)  # type: ignore[arg-type]
            )

        def work_b() -> str:
            order.append("b")
            return "b"

        def work_c() -> str:
            order.append("c")
            return "c"

        task_b = asyncio.create_task(executor.run(work_b))
        while len(executor._semaphore._waiters) < 3:
            await asyncio.sleep(0)
        task_c = asyncio.create_task(executor.run(work_c))
        while len(executor._semaphore._waiters) < 4:
            await asyncio.sleep(0)

        holder_release.set()
        assert await holder_task == "holder"
        assert await task_b == "b"
        assert await task_c == "c"

        assert order == ["b", "c"]
        assert executor.in_use_count == 0
        assert executor._semaphore._slots == 1
        assert len(executor._semaphore._waiters) == 0

    asyncio.run(run_live_waiters())


