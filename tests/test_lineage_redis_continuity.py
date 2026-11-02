"""F-27 Gap A: rotation preserves the Redis lineage bucket; no fresh allowance.

Proves the real runtime invariant through actual Redis behavior (not source
inspection, string equality, or mocks):

1. Key A is issued with a lineage identity and a Redis-backed rate limit.
2. Key A's burst allowance is consumed via the real ``RedisTokenBucket``.
3. Key A is rotated to Key B; Key B retains the same lineage.
4. Admitting Key B's lineage bucket through the real Redis path does NOT
   behave like a fresh bucket (the prior consumption is still visible).
5. A genuinely fresh lineage is still admitted (control: the limiter works).

Isolation: spawns a disposable ``redis-server`` bound to 127.0.0.1 on an
ephemeral port (never the shared/default Redis at 6379, never touched), uses
a unique key prefix per test, deletes only its own keys on teardown (never
FLUSHDB), and terminates the server. The key store is a disposable SQLite
tempfile. Skips cleanly only if the ``redis-server`` binary is unavailable.
"""

from __future__ import annotations

import asyncio
import shutil
import socket
import subprocess
import tempfile
import uuid

import pytest
from redis.asyncio import Redis

from sabiroute.security.keys import ApiKeyRateLimit, issue_api_key, rotate_api_key
from sabiroute.security.rate_limit import RedisTokenBucket
from sabiroute.security.store import PostgresApiKeyStore, _connect, ensure_schema


@pytest.fixture()
async def disposable_redis():
    """Ephemeral loopback redis-server with self-owned-prefix cleanup."""
    binary = shutil.which("redis-server")
    if binary is None:
        pytest.skip("redis-server binary unavailable; cannot prove Redis continuity")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    assert port != 6379, "must never use the shared/default Redis port"
    proc = subprocess.Popen(
        [
            binary,
            "--port",
            str(port),
            "--bind",
            "127.0.0.1",
            "--save",
            "",
            "--appendonly",
            "no",
            "--protected-mode",
            "yes",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    client = Redis.from_url(f"redis://127.0.0.1:{port}/0", decode_responses=True)
    prefix = f"sabiroute:test-lineage-redis:{uuid.uuid4().hex}:"
    try:
        for _ in range(100):
            try:
                await client.ping()
                break
            except Exception:
                await asyncio.sleep(0.05)
        else:
            pytest.fail("disposable redis-server did not become ready")
        yield RedisTokenBucket(client, key_prefix=prefix.rstrip(":")), client, prefix
    finally:
        try:
            leftovers = [key async for key in client.scan_iter(match=f"{prefix}*")]
            if leftovers:
                await client.delete(*leftovers)
            remaining = [key async for key in client.scan_iter(match=f"{prefix}*")]
            assert remaining == [], f"test Redis keys leaked: {remaining}"
        finally:
            await client.aclose()
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=10)


async def test_rotation_keeps_lineage_bucket_without_fresh_allowance(
    disposable_redis,
) -> None:
    """Exhaust burst on key A, rotate, prove key B shares the spent bucket."""
    limiter, client, prefix = disposable_redis

    d = tempfile.mkdtemp()
    eng = _connect(f"sqlite:///{d}/redis-continuity.db", None)
    ensure_schema(eng, groups="full")
    store = PostgresApiKeyStore(f"sqlite:///{d}/redis-continuity.db", engine=eng)
    try:
        # A. Key A has a lineage identity.
        rec_a, _ = issue_api_key(store, project_id="p", name="k")
        assert rec_a.lineage_id is not None
        # requests_per_minute=1 keeps refill negligible (~1.7e-5 tokens/ms),
        # so exhaustion observed below cannot refill mid-test.
        limit = ApiKeyRateLimit(requests_per_minute=1, burst_capacity=3)
        assert store.set_rate_limit(rec_a.key_id, limit) is True

        # B. Consume the whole burst through the real Redis-backed mechanism.
        bucket_a = rec_a.lineage_id or rec_a.key_id
        assert bucket_a == rec_a.lineage_id
        for _ in range(3):
            assert (await limiter.admit(bucket_a, limit)).admitted is True
        assert (await limiter.admit(bucket_a, limit)).admitted is False

        # C. Rotate; D. the rotated key retains the same lineage authority.
        rotated = rotate_api_key(store, rec_a.key_id)
        assert rotated is not None
        rec_b, _ = rotated
        assert rec_b.lineage_id == rec_a.lineage_id
        limit_b = store.get_rate_limit(rec_b.key_id)
        assert limit_b is not None
        # Same derivation rule as api/completions.py rate-limit admission.
        bucket_b = rec_b.lineage_id or rec_b.key_id
        assert bucket_b == bucket_a

        # E/F. No fresh allowance: the shared bucket is still exhausted in
        # real Redis. A fresh bucket would admit here.
        assert (await limiter.admit(bucket_b, limit_b)).admitted is False

        # Control: a genuinely fresh lineage is admitted, proving the denial
        # above is bucket exhaustion rather than a broken limiter.
        rec_c, _ = issue_api_key(store, project_id="p", name="fresh")
        assert rec_c.lineage_id is not None
        assert rec_c.lineage_id != rec_a.lineage_id
        assert (await limiter.admit(rec_c.lineage_id, limit)).admitted is True

        # Only self-owned prefixed keys exist on the disposable server.
        keys = [key async for key in client.scan_iter(match="*")]
        assert keys != []
        assert all(key.startswith(prefix) for key in keys), keys
    finally:
        eng.dispose()
