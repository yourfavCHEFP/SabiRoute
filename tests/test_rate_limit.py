from __future__ import annotations

import asyncio
from threading import Lock
from typing import cast

import pytest
from redis.asyncio import Redis

from sabiroute.security.keys import ApiKeyRateLimit
from sabiroute.security.rate_limit import RedisTokenBucket


class MemoryRedis:
    """Atomic test double for the Lua token-bucket contract."""

    def __init__(self) -> None:
        self.now_ms = 0
        self.buckets: dict[str, tuple[float, int]] = {}
        self.lock = Lock()

    async def eval(
        self,
        script: str,
        numkeys: int,
        key: str,
        requests_per_minute: int,
        burst_capacity: int,
    ) -> list[int]:
        await asyncio.sleep(0)
        with self.lock:
            tokens, last_ms = self.buckets.get(key, (float(burst_capacity), self.now_ms))
            now_ms = max(self.now_ms, last_ms)
            tokens = min(
                float(burst_capacity),
                tokens + (now_ms - last_ms) * requests_per_minute / 60_000,
            )
            admitted = int(tokens >= 1)
            if admitted:
                tokens -= 1
            self.buckets[key] = (tokens, now_ms)
            retry_ms = 0
            if not admitted:
                retry_ms = int(
                    (1 - tokens) * 60_000 / requests_per_minute
                    + 0.999999999
                )
            return [admitted, retry_ms]

    async def aclose(self) -> None:
        return None

    def advance(self, milliseconds: int) -> None:
        self.now_ms += milliseconds


class BrokenRedis:
    async def eval(self, *args: object) -> list[int]:
        raise ConnectionError("redis unavailable")

    async def aclose(self) -> None:
        return None


def limiter_for(client: object) -> RedisTokenBucket:
    return RedisTokenBucket(cast(Redis, client))


@pytest.mark.asyncio
async def test_burst_below_at_and_above_limit_then_exact_refill_boundary() -> None:
    backend = MemoryRedis()
    limiter = limiter_for(backend)
    limit = ApiKeyRateLimit(requests_per_minute=60, burst_capacity=2)

    first = await limiter.admit("a" * 24, limit)
    second = await limiter.admit("a" * 24, limit)
    third = await limiter.admit("a" * 24, limit)

    assert first.admitted is True
    assert second.admitted is True
    assert third.admitted is False
    assert third.retry_after_seconds == 1

    backend.advance(999)
    assert (await limiter.admit("a" * 24, limit)).admitted is False
    backend.advance(1)
    assert (await limiter.admit("a" * 24, limit)).admitted is True


@pytest.mark.asyncio
async def test_refill_boundary_for_non_burst_rate_is_exact() -> None:
    backend = MemoryRedis()
    limiter = limiter_for(backend)
    limit = ApiKeyRateLimit(requests_per_minute=2, burst_capacity=1)

    assert (await limiter.admit("b" * 24, limit)).admitted is True
    backend.advance(29_999)
    assert (await limiter.admit("b" * 24, limit)).admitted is False
    backend.advance(1)
    assert (await limiter.admit("b" * 24, limit)).admitted is True


@pytest.mark.asyncio
async def test_concurrent_requests_cannot_exceed_burst_capacity() -> None:
    limiter = limiter_for(MemoryRedis())
    limit = ApiKeyRateLimit(requests_per_minute=10, burst_capacity=7)

    decisions = await asyncio.gather(
        *(limiter.admit("c" * 24, limit) for _ in range(40))
    )

    assert sum(decision.admitted for decision in decisions) == 7
    assert sum(not decision.admitted for decision in decisions) == 33


@pytest.mark.asyncio
async def test_distinct_api_keys_have_isolated_buckets() -> None:
    limiter = limiter_for(MemoryRedis())
    limit = ApiKeyRateLimit(requests_per_minute=1, burst_capacity=1)

    assert (await limiter.admit("d" * 24, limit)).admitted is True
    assert (await limiter.admit("d" * 24, limit)).admitted is False
    assert (await limiter.admit("e" * 24, limit)).admitted is True


@pytest.mark.asyncio
async def test_redis_error_is_not_converted_to_admission() -> None:
    limiter = limiter_for(BrokenRedis())

    with pytest.raises(ConnectionError, match="redis unavailable"):
        await limiter.admit(
            "f" * 24,
            ApiKeyRateLimit(requests_per_minute=10, burst_capacity=2),
        )


class GarbledRedis:
    async def eval(self, *args: object) -> list[int]:
        return [1]

    async def aclose(self) -> None:
        return None


@pytest.mark.asyncio
async def test_malformed_redis_reply_is_rejected_not_admitted() -> None:
    limiter = limiter_for(GarbledRedis())

    with pytest.raises(RuntimeError, match="invalid rate-limit result"):
        await limiter.admit(
            "g" * 24,
            ApiKeyRateLimit(requests_per_minute=10, burst_capacity=2),
        )


class SilentServer:
    """Accepts one connection and never replies: a deterministically wedged peer."""

    def __init__(self) -> None:
        import socket as _socket
        import threading as _threading

        self._sock = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
        self._sock.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, 1)
        self._sock.bind(("127.0.0.1", 0))
        self._sock.listen(1)
        self.port = self._sock.getsockname()[1]
        self._stop = _threading.Event()
        self._holder = _threading.Thread(target=self._hold, daemon=True)
        self._holder.start()

    def _hold(self) -> None:
        try:
            conn, _ = self._sock.accept()
            conn.settimeout(10)
            try:
                conn.recv(4096)
                # Hold the connection open without replying: the peer looks
                # wedged, so the client must time out rather than observe
                # a close.
                self._stop.wait(timeout=10)
            except OSError:
                pass
            finally:
                try:
                    conn.close()
                except OSError:
                    pass
        except OSError:
            pass

    def close(self) -> None:
        self._stop.set()
        try:
            self._sock.close()
        except OSError:
            pass
        self._holder.join(timeout=5)


@pytest.mark.asyncio
async def test_wedged_redis_raises_timeout_instead_of_hanging() -> None:
    import redis.exceptions
    from redis.asyncio import Redis as AsyncRedis

    server = SilentServer()
    try:
        client = AsyncRedis.from_url(
            f"redis://127.0.0.1:{server.port}/15"
            "?socket_timeout=0.3&socket_connect_timeout=0.3",
            decode_responses=True,
        )
        try:
            limiter = RedisTokenBucket(client)
            with pytest.raises(redis.exceptions.TimeoutError):
                await limiter.admit(
                    "h" * 24,
                    ApiKeyRateLimit(requests_per_minute=10, burst_capacity=2),
                )
        finally:
            await client.aclose()
    finally:
        server.close()
