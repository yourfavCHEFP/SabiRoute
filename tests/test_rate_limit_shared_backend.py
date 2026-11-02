"""F-08 multi-instance shared enforcement — deterministic bucket doubles.

Lane ownership: rate limiting (F-08). Moved verbatim out of
``tests/test_request_limits.py`` so the R7 release-evidence package does not
carry another lane's evidence. Bodies are unchanged.

Scope: two limiter instances sharing one backend consume one shared allowance,
and distinct key prefixes do not share it.

Honest caveat: these exercise ``_ScriptlessBucket``, a local dict-backed
*double*, not the shipped ``RedisTokenBucket``. The real multi-instance proof
lives in ``tests/test_rate_limit_redis.py`` (same Redis, two clients). These
doubles add prefix-isolation coverage only; they are not release evidence.
"""

from __future__ import annotations


class _ScriptlessBucket:
    """Minimal RedisTokenBucket-shaped double sharing one dict backend."""

    def __init__(self, backend: dict, prefix: str = "t"):
        self._backend = backend
        self._prefix = prefix

    async def admit(self, key_id: str, limit) -> object:
        import time as _time

        now_ms = int(_time.time() * 1000)
        window_ms = 60_000
        key = f"{self._prefix}:{key_id}"
        state = self._backend.setdefault(
            key, {"tokens": limit.burst_capacity, "last": now_ms}
        )
        elapsed = now_ms - state["last"]
        refill = elapsed * limit.requests_per_minute / window_ms
        state["tokens"] = min(limit.burst_capacity, state["tokens"] + refill)
        state["last"] = now_ms
        from types import SimpleNamespace

        if state["tokens"] >= 1:
            state["tokens"] -= 1
            return SimpleNamespace(admitted=True, retry_after_seconds=None)
        return SimpleNamespace(admitted=False, retry_after_seconds=1)

    def key(self, key_id: str) -> str:
        return f"{self._prefix}:{key_id}"


def test_two_instances_share_one_backend_allowance():
    import asyncio

    from sabiroute.security.keys import ApiKeyRateLimit

    backend: dict = {}
    a = _ScriptlessBucket(backend, prefix="shared")
    b = _ScriptlessBucket(backend, prefix="shared")
    limit = ApiKeyRateLimit(requests_per_minute=60, burst_capacity=3)

    async def run():
        r1 = await a.admit("k", limit)
        r2 = await b.admit("k", limit)
        r3 = await a.admit("k", limit)
        r4 = await b.admit("k", limit)
        return [r.admitted for r in (r1, r2, r3, r4)]

    assert asyncio.run(run()) == [True, True, True, False]


def test_distinct_prefixes_do_not_share_allowance():
    import asyncio

    from sabiroute.security.keys import ApiKeyRateLimit

    backend: dict = {}
    a = _ScriptlessBucket(backend, prefix="one")
    b = _ScriptlessBucket(backend, prefix="two")
    limit = ApiKeyRateLimit(requests_per_minute=60, burst_capacity=1)

    async def run():
        return [(await a.admit("k", limit)).admitted, (await b.admit("k", limit)).admitted]

    assert asyncio.run(run()) == [True, True]
