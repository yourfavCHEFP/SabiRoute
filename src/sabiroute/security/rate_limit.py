"""Atomic per-key request admission backed by Redis token buckets."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from redis.asyncio import Redis

from .keys import ApiKeyRateLimit

_TOKEN_BUCKET_SCRIPT = r"""
local key = KEYS[1]
local requests_per_minute = tonumber(ARGV[1])
local burst_capacity = tonumber(ARGV[2])
local time_parts = redis.call('TIME')
local now_ms = tonumber(time_parts[1]) * 1000 + math.floor(tonumber(time_parts[2]) / 1000)
local tokens = tonumber(redis.call('HGET', key, 'tokens'))
local last_ms = tonumber(redis.call('HGET', key, 'last_ms'))
if tokens == nil then tokens = burst_capacity end
if last_ms == nil then last_ms = now_ms end
now_ms = math.max(now_ms, last_ms)
local elapsed_ms = math.max(0, now_ms - last_ms)
local refill_rate_per_ms = requests_per_minute / 60000
tokens = math.min(burst_capacity, tokens + elapsed_ms * refill_rate_per_ms)
local admitted = 0
if tokens >= 1 then
    tokens = tokens - 1
    admitted = 1
end
redis.call('HSET', key, 'tokens', tokens, 'last_ms', now_ms)
local ttl_ms = math.max(60000, math.ceil((burst_capacity / refill_rate_per_ms) * 2))
redis.call('PEXPIRE', key, ttl_ms)
local retry_after_ms = 0
if admitted == 0 then
    retry_after_ms = math.ceil((1 - tokens) / refill_rate_per_ms)
end
return {admitted, retry_after_ms}
"""


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    """The atomic outcome for one user-facing request admission."""

    admitted: bool
    retry_after_seconds: int | None = None


class RedisTokenBucket:
    """Redis Lua token bucket; one consumed token represents one API request.

    Rejections update the refill timestamp but do not consume a token. The
    Redis server clock is used so app-server clock skew cannot split a key's
    effective rate across SabiRoute instances.
    """

    def __init__(self, client: Redis, *, key_prefix: str = "sabiroute:rate:v1") -> None:
        self._client = client
        self._key_prefix = key_prefix

    async def admit(self, key_id: str, limit: ApiKeyRateLimit) -> RateLimitDecision:
        result: Any = await self._client.eval(
            _TOKEN_BUCKET_SCRIPT,
            1,
            f"{self._key_prefix}:{key_id}",
            limit.requests_per_minute,
            limit.burst_capacity,
        )
        if not isinstance(result, (list, tuple)) or len(result) != 2:
            raise RuntimeError("Redis returned an invalid rate-limit result.")
        admitted = bool(int(result[0]))
        retry_after_ms = int(result[1])
        if admitted:
            return RateLimitDecision(admitted=True)
        return RateLimitDecision(
            admitted=False,
            retry_after_seconds=max(1, math.ceil(retry_after_ms / 1000)),
        )

    async def close(self) -> None:
        await self._client.aclose()
