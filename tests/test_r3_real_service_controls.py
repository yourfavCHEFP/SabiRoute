"""R3 — real-service controls: prove the real-service harness can fail.

This is a *control* suite, not another isolation suite. The R3 isolation
suites are only worth what their harness is worth, and that harness has three
ways to quietly prove nothing:

1. **Silent skip.** ``test_rate_limit_redis`` and the ``test_pg_*`` tests in
   ``test_user_quotas``/``test_shared_inference`` skip when their opt-in URL
   env var is unset. A green run then contains no real-service evidence at
   all, and nothing in the output distinguishes "passed" from "never ran".
2. **Hostile target.** A mis-pointed URL could aim the suite at a
   non-disposable server. ``test_rate_limit_redis`` guards this for Redis
   (``_checked_url``); the PostgreSQL opt-in path has no such guard, and a URL
   with no host/port silently resolves to the default Unix socket — a target
   nobody chose explicitly.
3. **Vacuous assertion.** A scoping assertion ("key A's bucket is unaffected
   by key B") is worthless if it would also pass against an unscoped
   implementation. Nothing currently demonstrates that it would not.

Owner decision D-R3-3 (tenant identity is a server-held fact) and Batch 3 gate
#2 ("confirm PostgreSQL and Redis are disposable and isolated ... if isolation
cannot be demonstrated, mark the relevant tests BLOCKED") both depend on the
harness being able to fail. So each control here is written to *detect
failure*, not to observe success:

* guard controls drive the SHIPPED Redis guard with hostile input and require
  it to refuse (``pytest.fail``), and this file's PostgreSQL guard likewise;
* a loud-failure control requires a configured-but-unreachable service to
  raise, never to skip;
* real-service controls re-run the isolation property against the actual
  Redis and PostgreSQL servers, so a divergence between the ``FakeRedis``
  model and the production Lua script, or between SQLite and real SQL, cannot
  hide behind an in-memory double;
* every real-service control deletes only its own uniquely-prefixed/tagged
  rows and then asserts no residue, so repeated runs cannot contaminate each
  other.

Secrets: a failing pytest frame renders that frame's locals, so a URL held in
a local variable leaks its password into CI output. ``_Endpoint`` therefore
wraps every service URL behind a redacted ``__repr__``, and
``test_endpoint_repr_hides_credentials`` pins that behaviour. No control
prints, logs or interpolates a raw credential anywhere.

Guards always run (they need no service). Only the real-service controls are
opt-in, via the same env vars the positive suites already use:
``SABIROUTE_TEST_REDIS_URL`` and ``SABIROUTE_TEST_PG_URL``.
"""

from __future__ import annotations

import os
import re
import uuid
from datetime import UTC, datetime
from urllib.parse import urlparse

import pytest
from redis.asyncio import Redis
from sqlalchemy import delete

# Imported deliberately without a try/except: if the shipped guard moves or is
# renamed, this control suite must fail loudly rather than skip. It is the
# behaviour of THAT function that these tests measure.
from test_rate_limit_redis import LOOPBACK_HOSTS, TEST_URL_ENV, _checked_url

from sabiroute.quotas import quota_window_start
from sabiroute.security.keys import ApiKeyRateLimit
from sabiroute.security.rate_limit import RedisTokenBucket
from sabiroute.security.store import (
    _QUOTA_RESERVATIONS,
    _QUOTA_WINDOWS,
    PostgresApiKeyStore,
    _connect,
)

PG_URL_ENV = "SABIROUTE_TEST_PG_URL"

#: Database names that are safe to mutate. The real PostgreSQL control deletes
#: rows, so the name must advertise itself as disposable.
_DISPOSABLE_DB = re.compile(
    r"(^|[_-])(test|tests|ci|scratch|tmp|temp|disposable|throwaway)([_-]|$)",
    re.IGNORECASE,
)

#: Names that are refused even if they also match the allowlist above.
_FORBIDDEN_DB = re.compile(r"(prod|production|live|customer)", re.IGNORECASE)


def _redact(url: str) -> str:
    """Render a URL for output: scheme/host/port/db only, no credentials."""
    parsed = urlparse(url)
    where = parsed.hostname or "<unix socket>"
    if parsed.port:
        where = f"{where}:{parsed.port}"
    return f"{parsed.scheme or '?'}://{where}{parsed.path or ''} (credentials withheld)"


class _Endpoint:
    """A service URL whose ``repr`` never contains the password.

    pytest renders a failing frame's locals, so a bare ``url`` string in a
    test body would publish its credential into the run log. Holding it here
    keeps diagnosis useful and the secret out of the output.
    """

    __slots__ = ("_url", "env_var")

    def __init__(self, env_var: str, url: str) -> None:
        self._url = url
        self.env_var = env_var

    def resolve(self) -> str:
        """The raw URL. Only ever passed straight into a client constructor."""
        return self._url

    def __repr__(self) -> str:
        return f"_Endpoint({self.env_var}={_redact(self._url)})"


# ---------------------------------------------------------------------------
# Control 1 — the SHIPPED Redis guard refuses hostile targets
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "hostile_url",
    [
        "redis://redis.example.com:6379/0",
        "redis://10.0.0.5:6379/0",
        "redis://db.internal:6379/0",
        "redis://0.0.0.0:6379/0",
        "redis://:topsecret@db.internal:6379/0",
    ],
)
def test_shipped_redis_guard_refuses_non_loopback_target(
    monkeypatch: pytest.MonkeyPatch, hostile_url: str
) -> None:
    """``_checked_url`` must FAIL on a non-loopback host, never proceed."""
    monkeypatch.setenv(TEST_URL_ENV, hostile_url)

    with pytest.raises(pytest.fail.Exception) as caught:
        _checked_url()

    message = str(caught.value)
    assert "Refusing" in message
    # The refusal names the offending host so an operator can diagnose it,
    # and must never echo a password.
    assert urlparse(hostile_url).hostname in message
    assert "loopback" in message.lower()
    assert "topsecret" not in message


@pytest.mark.parametrize(
    "loopback_url",
    [
        "redis://127.0.0.1:6399/0",
        "redis://localhost:6399/0",
        "redis://[::1]:6399/0",
        "redis://:secret@127.0.0.1:6400/1",
    ],
)
def test_shipped_redis_guard_accepts_loopback_and_returns_url_verbatim(
    monkeypatch: pytest.MonkeyPatch, loopback_url: str
) -> None:
    """Loopback targets pass through unmodified (no credential mangling)."""
    monkeypatch.setenv(TEST_URL_ENV, loopback_url)

    assert _checked_url() == loopback_url
    assert (urlparse(loopback_url).hostname or "").lower() in LOOPBACK_HOSTS


def test_shipped_redis_guard_covers_every_loopback_spelling() -> None:
    """Guards the guard: a narrowed allowlist would make acceptance vacuous."""
    assert {"127.0.0.1", "localhost", "::1"} <= LOOPBACK_HOSTS


# ---------------------------------------------------------------------------
# Control 2 — a configured-but-unreachable service FAILS, never skips
# ---------------------------------------------------------------------------


async def test_configured_but_unreachable_redis_fails_instead_of_skipping() -> None:
    """Opt-in means opt-in: a URL that is set and dead must error loudly.

    This is the failure mode that silently erodes real-service evidence — the
    env var is set, the runner believes integration was exercised, and a skip
    hides the fact that nothing connected.
    """
    # Port 1 on loopback is not a Redis server. Short timeout keeps the
    # control fast without changing what is being measured.
    client = Redis.from_url(
        "redis://127.0.0.1:1/0", socket_connect_timeout=2, socket_timeout=2
    )
    try:
        with pytest.raises(Exception) as caught:  # noqa: B017 - any loud failure
            await client.ping()
    finally:
        await client.aclose()

    assert not isinstance(caught.value, pytest.skip.Exception), (
        "an unreachable configured Redis must raise, not skip"
    )
    assert not isinstance(caught.value, pytest.xfail.Exception)


# ---------------------------------------------------------------------------
# Control 3 — this file's PostgreSQL guard refuses hostile targets
# ---------------------------------------------------------------------------


def _checked_pg_endpoint() -> _Endpoint:
    """Loopback-or-socket, disposable-name-only guard for this file.

    The shipped ``test_pg_*`` tests accept whatever ``SABIROUTE_TEST_PG_URL``
    contains; this file deletes rows, so it refuses to run anywhere that does
    not advertise itself as disposable locally.

    An empty host is accepted because it means "the default Unix socket",
    which is local by construction — but it is still not a *chosen* target, so
    the disposable-name rule applies just as strictly. Loopback and socket are
    the only two shapes permitted; anything routable is refused.
    """
    url = os.environ.get(PG_URL_ENV)
    if not url:
        pytest.fail(f"{PG_URL_ENV} is not set; real PostgreSQL controls cannot run")

    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    is_socket = host == ""
    if not is_socket and host not in LOOPBACK_HOSTS:
        pytest.fail(
            f"Refusing to run PostgreSQL controls against non-loopback host "
            f"{host!r} ({_redact(url)}); point {PG_URL_ENV} at 127.0.0.1 or "
            f"leave the host empty for the local Unix socket."
        )

    database = parsed.path.lstrip("/")
    if _FORBIDDEN_DB.search(database):
        pytest.fail(
            f"Refusing to run PostgreSQL controls against database "
            f"{database!r}: the name looks like a production database."
        )
    if not _DISPOSABLE_DB.search(database):
        pytest.fail(
            f"Refusing to run PostgreSQL controls against database "
            f"{database!r}: the name does not advertise itself as disposable "
            f"(expected e.g. '*_test')."
        )
    return _Endpoint(PG_URL_ENV, url)


@pytest.mark.parametrize(
    "hostile_url",
    [
        "postgresql://user:pw@db.example.com:5432/sabiroute_test",
        "postgresql://user:pw@10.1.2.3:5432/sabiroute_test",
        "postgresql://user:pw@postgres.internal:5432/sabiroute_stage0_test",
    ],
)
def test_pg_guard_refuses_non_loopback_target(
    monkeypatch: pytest.MonkeyPatch, hostile_url: str
) -> None:
    monkeypatch.setenv(PG_URL_ENV, hostile_url)

    with pytest.raises(pytest.fail.Exception) as caught:
        _checked_pg_endpoint()

    message = str(caught.value)
    assert "Refusing" in message
    assert urlparse(hostile_url).hostname in message
    # Credentials must never reach a failure message.
    assert "pw" not in message


@pytest.mark.parametrize(
    "database",
    ["sabiroute", "sabiroute_stage0", "sabiroute_prod_test", "sabiroute_live"],
)
def test_pg_guard_refuses_non_disposable_database_name(
    monkeypatch: pytest.MonkeyPatch, database: str
) -> None:
    """A loopback server is not enough: the database itself must be disposable."""
    monkeypatch.setenv(PG_URL_ENV, f"postgresql://user:secret@127.0.0.1:5433/{database}")

    with pytest.raises(pytest.fail.Exception) as caught:
        _checked_pg_endpoint()

    assert "Refusing" in str(caught.value)
    assert "secret" not in str(caught.value)


@pytest.mark.parametrize(
    "url",
    [
        "postgresql://user:secret@127.0.0.1:5433/sabiroute_stage0_test",
        "postgresql://user:secret@localhost:5433/sabiroute_ci",
        # The shape the project's .env actually uses: default Unix socket.
        "postgresql://user:secret@/sabiroute_stage0_test",
    ],
)
def test_pg_guard_accepts_disposable_local_database(
    monkeypatch: pytest.MonkeyPatch, url: str
) -> None:
    monkeypatch.setenv(PG_URL_ENV, url)

    endpoint = _checked_pg_endpoint()
    assert endpoint.resolve() == url


def test_pg_guard_still_enforces_disposable_name_over_unix_socket(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Accepting the socket shape must not bypass the database-name rule."""
    monkeypatch.setenv(PG_URL_ENV, "postgresql://user:secret@/sabiroute")

    with pytest.raises(pytest.fail.Exception):
        _checked_pg_endpoint()


def test_pg_guard_refuses_unset_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unset config is a FAIL here, not a skip: see Control 2's rationale."""
    monkeypatch.delenv(PG_URL_ENV, raising=False)

    with pytest.raises(pytest.fail.Exception) as caught:
        _checked_pg_endpoint()

    assert PG_URL_ENV in str(caught.value)


# ---------------------------------------------------------------------------
# Control 4 — redaction is real (a credential must not survive into output)
# ---------------------------------------------------------------------------


def test_redaction_hides_credentials() -> None:
    redacted = _redact("postgresql://user:topsecret@127.0.0.1:5433/sabiroute_test")

    assert "topsecret" not in redacted
    assert "user" not in redacted.split("://", 1)[1]
    assert "127.0.0.1:5433" in redacted
    assert "sabiroute_test" in redacted


def test_endpoint_repr_hides_credentials() -> None:
    """The leak this file was written to close: a failed frame's locals.

    If pytest ever renders an ``_Endpoint``, the password must not be in it.
    """
    endpoint = _Endpoint(
        PG_URL_ENV, "postgresql://user:topsecret@127.0.0.1:5433/sabiroute_test"
    )

    assert "topsecret" not in repr(endpoint)
    assert "topsecret" not in str(endpoint)
    assert "sabiroute_test" in repr(endpoint)


# ---------------------------------------------------------------------------
# Control 5 — the real Redis enforces per-key buckets (model vs Lua script)
# ---------------------------------------------------------------------------


async def test_real_redis_per_key_isolation_matches_fake_redis_model() -> None:
    """Draining key A on a REAL server must leave key B's burst untouched.

    ``test_r3_db_isolation`` proves this against ``FakeRedis``, which
    reimplements the bucket arithmetic. If the production Lua script diverged
    from that model, only a real server can tell. This control is that check.
    """
    if not os.environ.get(TEST_URL_ENV):
        pytest.skip(f"{TEST_URL_ENV} is not set; real Redis control skipped")
    # Reuse the shipped guard rather than a copy: this also proves the guard
    # passes a real, runnable target through untouched.
    endpoint = _Endpoint(TEST_URL_ENV, _checked_url())

    prefix = f"sabiroute:test-r3ctl:{uuid.uuid4().hex}"
    client = Redis.from_url(endpoint.resolve(), decode_responses=True)
    try:
        await client.ping()
    except Exception as exc:  # noqa: BLE001 - loud failure, never a skip
        await client.aclose()
        pytest.fail(
            f"real Redis control could not reach {endpoint}: "
            f"{type(exc).__name__}: {exc}"
        )

    bucket = RedisTokenBucket(client, key_prefix=prefix)
    limit = ApiKeyRateLimit(requests_per_minute=1, burst_capacity=2)
    try:
        assert (await bucket.admit("key-alpha", limit)).admitted
        assert (await bucket.admit("key-alpha", limit)).admitted
        # A is now exhausted; this is the control's premise, not its point.
        assert not (await bucket.admit("key-alpha", limit)).admitted

        # The point: B is untouched by A's exhaustion, on the real server.
        assert (await bucket.admit("key-beta", limit)).admitted

        # And the real server holds exactly the two scoped keys — a shared
        # counter could not have produced this pair.
        keys = sorted([key async for key in client.scan_iter(match=f"{prefix}*")])
        assert keys == [f"{prefix}:key-alpha", f"{prefix}:key-beta"]
    finally:
        try:
            leftovers = [key async for key in client.scan_iter(match=f"{prefix}*")]
            if leftovers:
                await client.delete(*leftovers)
            assert [key async for key in client.scan_iter(match=f"{prefix}*")] == [], (
                "real Redis control leaked keys"
            )
        finally:
            await client.aclose()


# ---------------------------------------------------------------------------
# Control 6 — the real PostgreSQL scopes by tenant, not by request id
# ---------------------------------------------------------------------------


def test_real_pg_same_request_id_under_two_tenants_is_independent() -> None:
    """One ``request_id`` shared by two tenants must be two reservations.

    This is the D-R3-3 property against a real server: SQLite can accept a
    predicate that PostgreSQL treats differently, and the quota ledger's
    portable upsert/savepoint path is explicitly engine-dependent. Both
    tenants are deleted afterwards, and the control then asserts that the
    deletion left nothing of its own behind.

    Layering note: the opt-in contract (unset -> skip, matching the positive
    suites so the default suite stays green) is decided by the caller. The
    guard is what refuses to *run* against an unset or hostile target once the
    caller has decided to run, and
    ``test_pg_guard_refuses_unset_configuration`` pins that refusal.
    """
    if not os.environ.get(PG_URL_ENV):
        pytest.skip(f"{PG_URL_ENV} is not set; real PostgreSQL control skipped")
    endpoint = _checked_pg_endpoint()

    window = quota_window_start(datetime.now(UTC))
    # user_id is String(36) in the ledger.
    tag_a = f"r3ctl{os.getpid()}a"[:36]
    tag_b = f"r3ctl{os.getpid()}b"[:36]
    shared_request = f"r3ctl{os.getpid()}r"[:36]

    store = PostgresApiKeyStore(endpoint.resolve())
    cleanup_engine = _connect(endpoint.resolve(), None)
    try:
        assert store.check_and_reserve_quota(tag_a, shared_request, 10000, window, 50000)
        # SAME request_id, different tenant: must be admitted independently.
        assert store.check_and_reserve_quota(tag_b, shared_request, 10000, window, 50000)

        usage_a = store.get_quota_usage(tag_a, window)
        usage_b = store.get_quota_usage(tag_b, window)
        assert usage_a["reserved_tokens"] == 10000
        assert usage_b["reserved_tokens"] == 10000, (
            "tenant B's reservation was collapsed into tenant A's by request_id"
        )

        # Releasing A must not touch B.
        store.release_quota(tag_a, shared_request)
        assert store.get_quota_usage(tag_a, window)["reserved_tokens"] == 0
        assert store.get_quota_usage(tag_b, window)["reserved_tokens"] == 10000, (
            "releasing tenant A's reservation settled tenant B's"
        )
    finally:
        try:
            with cleanup_engine.begin() as connection:
                for table in (_QUOTA_RESERVATIONS, _QUOTA_WINDOWS):
                    connection.execute(
                        delete(table).where(table.c.user_id.in_([tag_a, tag_b]))
                    )
            # Residue check: this control must leave the disposable database
            # exactly as it found it, or the next run is contaminated.
            with cleanup_engine.connect() as connection:
                for table in (_QUOTA_RESERVATIONS, _QUOTA_WINDOWS):
                    remaining = connection.execute(
                        table.select().where(table.c.user_id.in_([tag_a, tag_b]))
                    ).all()
                    assert remaining == [], (
                        f"real PostgreSQL control leaked rows in {table.name}"
                    )
        finally:
            store.close()
            cleanup_engine.dispose()
