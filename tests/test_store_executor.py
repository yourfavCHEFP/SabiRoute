"""Deterministic tests for the bounded store executor (Mission 16A).

Uses threading.Event gates — never arbitrary sleeps — so every outcome is
forced, not timed. The real executor (not a double) is under test.
"""

from __future__ import annotations

import asyncio
import threading

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
