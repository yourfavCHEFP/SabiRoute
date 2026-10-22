"""Integration tests for the Redis Lua token bucket (Sprint 6, Task B).

These tests exercise the EXISTING RedisTokenBucket implementation against a
real Redis server. They prove what the MemoryRedis double cannot: the actual
Lua script's admit/deny accounting, server-side atomicity under contention,
and key expiry.

Opt-in only, via SABIROUTE_TEST_REDIS_URL:
- unset   -> all tests skip cleanly (default suite stays Redis-free);
- set     -> tests run against that instance;
- unreachable -> tests FAIL clearly (never silent-pass);
- non-loopback host -> fixture refuses (pytest.fail, never runs).

Safety: loopback-only targets, unique key prefix per session, per-test
cleanup that deletes only keys under that prefix (never FLUSHDB), and no
credentials in code or output.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from urllib.parse import urlparse

import pytest
from redis.asyncio import Redis

from sabiroute.security.keys import ApiKeyRateLimit
from sabiroute.security.rate_limit import RedisTokenBucket

TEST_URL_ENV = "SABIROUTE_TEST_REDIS_URL"
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}

pytestmark = pytest.mark.skipif(
    not os.environ.get(TEST_URL_ENV),
    reason=f"{TEST_URL_ENV} is not set; Redis integration tests skipped",
)


def _checked_url() -> str:
    url = os.environ[TEST_URL_ENV]
    host = (urlparse(url).hostname or "").lower()
    if host not in LOOPBACK_HOSTS:
        pytest.fail(
            f"Refusing to run Redis integration tests against non-loopback "
            f"host {host!r}; set {TEST_URL_ENV} to a 127.0.0.1/localhost URL."
        )
    return url


@pytest.fixture()
async def bucket():
    url = _checked_url()
    prefix = f"sabiroute:test-rate:{uuid.uuid4().hex}:"
    client = Redis.from_url(url, decode_responses=True)
    try:
        await client.ping()
    except Exception as exc:
        await client.aclose()
        pytest.fail(f"Cannot reach test Redis at loopback URL: {exc}")
    try:
        yield RedisTokenBucket(client, key_prefix=prefix.rstrip(":")), client, prefix
    finally:
        try:
            leftovers: list[str] = []
            async for key in client.scan_iter(match=f"{prefix}*"):
                leftovers.append(key)
            if leftovers:
                await client.delete(*leftovers)
            remaining = [key async for key in client.scan_iter(match=f"{prefix}*")]
            assert remaining == [], f"test keys leaked: {remaining}"
        finally:
            await client.aclose()


def _limit(rpm: int, burst: int) -> ApiKeyRateLimit:
    return ApiKeyRateLimit(requests_per_minute=rpm, burst_capacity=burst)


async def test_burst_enforced_then_denied_with_retry_after(bucket) -> None:
    limiter, _, _ = bucket
    limit = _limit(60, 3)

    results = [await limiter.admit("key-burst", limit) for _ in range(4)]

    assert [d.admitted for d in results] == [True, True, True, False]
    assert results[3].retry_after_seconds is not None
    assert results[3].retry_after_seconds >= 1


async def test_concurrent_admissions_capped_at_burst(bucket) -> None:
    limiter, _, _ = bucket
    limit = _limit(60, 5)

    decisions = await asyncio.gather(
        *(limiter.admit("key-race", limit) for _ in range(50))
    )

    assert sum(1 for d in decisions if d.admitted) == 5


async def test_distinct_keys_have_isolated_buckets(bucket) -> None:
    limiter, _, _ = bucket
    limit = _limit(60, 2)

    assert (await limiter.admit("key-a", limit)).admitted is True
    assert (await limiter.admit("key-a", limit)).admitted is True
    assert (await limiter.admit("key-a", limit)).admitted is False
    assert (await limiter.admit("key-b", limit)).admitted is True
    assert (await limiter.admit("key-b", limit)).admitted is True


async def test_bucket_key_carries_expiry(bucket) -> None:
    limiter, client, prefix = bucket
    key_id = "key-ttl"

    assert (await limiter.admit(key_id, _limit(60, 2))).admitted is True

    # Bucket key is f"{key_prefix}:{key_id}" with the trailing ":" stripped.
    ttl_ms = await client.pttl(f"{prefix.rstrip(':')}:{key_id}")
    assert ttl_ms > 0
