"""R3 — persistence-isolation regression suite (PostgreSQL/SQLite + Redis).

Owner decision D-R3-3: tenant identity is a *server-held* fact. Every write
and every read that the persistence layer performs on behalf of a tenant must
carry that tenant's identifier in its own SQL predicate or Redis key. A
lookup that is scoped only by a record identifier (``request_id``,
``conversation_id``) is one identifier-guess away from a cross-tenant read or
write, so nothing here may rely on "the caller already checked".

What this file proves, per store:

* Redis rate limiting — the token bucket key embeds the API key ID, so one
  key's admitted volume can never consume another key's budget.
* Budget ledger — reservations, reconciliation and release are key-scoped;
  the *same* ``request_id`` under two keys is two independent reservations
  and neither can settle or delete the other.
* Quota ledger — the same guarantee across users, plus window isolation.
* Usage telemetry — a key's event list never contains another key's rows,
  and finalization cannot be steered onto a foreign row.
* SabiChat conversations — owner-scoped reads, no existence oracle, and no
  message written into a conversation the caller does not own.

SQLite exercises the real SQL statements; PostgreSQL is not required. Every
assertion is VERIFIED BY RUNTIME against the production store classes.
"""

from __future__ import annotations

import math
import tempfile
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

import pytest
from conftest import InMemoryApiKeyStore, StubLiteLLMClient, enable_shared_inference, make_config
from fastapi.testclient import TestClient

from sabiroute.chat.store import SabiChatStore
from sabiroute.freepool.eligibility import FreePoolPolicy
from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app
from sabiroute.quotas import quota_window_start
from sabiroute.security.keys import (
    ApiKeyBudget,
    ApiKeyRateLimit,
    RequestUsageEvent,
    issue_api_key,
)
from sabiroute.security.rate_limit import RedisTokenBucket
from sabiroute.security.store import PostgresApiKeyStore, _connect, ensure_schema

WINDOW = quota_window_start(datetime.now(UTC))

USER_A = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
USER_B = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"


# ---------------------------------------------------------------------------
# Fixtures / harness
# ---------------------------------------------------------------------------


def _new_store() -> PostgresApiKeyStore:
    """A fresh, fully-migrated SQLite database behind the real store class."""
    directory = tempfile.mkdtemp()
    url = f"sqlite:///{directory}/isolation.db"
    engine = _connect(url, None)
    ensure_schema(engine, groups="full")
    return PostgresApiKeyStore(url, engine=engine)


def _new_chat_store() -> SabiChatStore:
    directory = tempfile.mkdtemp()
    url = f"sqlite:///{directory}/chat.db"
    engine = _connect(url, None)
    ensure_schema(engine, groups="full")
    return SabiChatStore(url, engine=engine)


class FakeRedis:
    """Stands in for ``redis.asyncio.Redis`` and models one bucket per key.

    It reimplements the token-bucket arithmetic from the production Lua
    script (*not* the key scoping, which is what these tests measure) so the
    rate-limit key chosen by ``RedisTokenBucket`` is observable from outside.
    """

    def __init__(self, *, now_ms: int = 1_700_000_000_000) -> None:
        self.keys: list[str] = []
        self._now_ms = now_ms
        self._buckets: dict[str, tuple[float, int]] = {}

    def advance(self, milliseconds: int) -> None:
        self._now_ms += milliseconds

    async def eval(  # noqa: A002 - mirrors the redis client signature
        self, script: str, numkeys: int, key: str, *args: Any
    ) -> list[int]:
        assert numkeys == 1
        assert "HGET" in script  # the real token-bucket script was passed
        self.keys.append(key)
        requests_per_minute = float(args[0])
        burst_capacity = float(args[1])
        tokens, last_ms = self._buckets.get(key, (burst_capacity, self._now_ms))
        now_ms = max(self._now_ms, last_ms)
        refill = (now_ms - last_ms) * (requests_per_minute / 60000)
        tokens = min(burst_capacity, tokens + refill)
        admitted = 0
        if tokens >= 1:
            tokens -= 1
            admitted = 1
        self._buckets[key] = (tokens, now_ms)
        retry_after_ms = 0
        if not admitted:
            retry_after_ms = math.ceil((1 - tokens) / (requests_per_minute / 60000))
        return [admitted, retry_after_ms]

    async def aclose(self) -> None:
        return None


# ---------------------------------------------------------------------------
# Redis — rate-limit bucket isolation
# ---------------------------------------------------------------------------


async def test_rate_limit_key_embeds_api_key_id() -> None:
    """The Redis key must carry the tenant identifier, not just a counter."""
    redis = FakeRedis()
    bucket = RedisTokenBucket(redis)  # type: ignore[arg-type]
    limit = ApiKeyRateLimit(requests_per_minute=60, burst_capacity=5)

    await bucket.admit("key-alpha", limit)
    await bucket.admit("key-beta", limit)

    assert redis.keys == [
        "sabiroute:rate:v1:key-alpha",
        "sabiroute:rate:v1:key-beta",
    ]


async def test_exhausted_key_never_consumes_another_keys_bucket() -> None:
    """Draining key A to rejection must leave key B at full burst."""
    redis = FakeRedis()
    bucket = RedisTokenBucket(redis)  # type: ignore[arg-type]
    limit = ApiKeyRateLimit(requests_per_minute=1, burst_capacity=2)

    assert (await bucket.admit("key-alpha", limit)).admitted
    assert (await bucket.admit("key-alpha", limit)).admitted
    denied = await bucket.admit("key-alpha", limit)
    assert denied.admitted is False
    assert denied.retry_after_seconds is not None

    # Key B has never been charged for A's traffic: full burst remains.
    assert (await bucket.admit("key-beta", limit)).admitted
    assert (await bucket.admit("key-beta", limit)).admitted
    assert (await bucket.admit("key-beta", limit)).admitted is False


async def test_rate_limit_state_is_shared_only_for_the_same_key() -> None:
    """Two gateway replicas share one key's bucket and no one else's."""
    redis = FakeRedis()
    replica_one = RedisTokenBucket(redis)  # type: ignore[arg-type]
    replica_two = RedisTokenBucket(redis)  # type: ignore[arg-type]
    limit = ApiKeyRateLimit(requests_per_minute=1, burst_capacity=2)

    assert (await replica_one.admit("key-alpha", limit)).admitted
    assert (await replica_two.admit("key-alpha", limit)).admitted
    assert (await replica_two.admit("key-alpha", limit)).admitted is False

    # The neighbouring key was untouched by both replicas.
    assert (await replica_one.admit("key-beta", limit)).admitted


class AuthRequiredRedis:
    """Client for a Redis that demands AUTH, as a secured server does.

    Models the real local instance, which answers ``NOAUTH Authentication
    required.`` to an unauthenticated connection. The property that matters
    is not the error text but where it lands: a failed AUTH must raise out of
    ``admit`` so the caller denies closed. A limiter that read it as "no
    tokens left" would deny for the wrong reason; one that read it as
    "allowed" would silently remove rate limiting entirely.
    """

    def __init__(self) -> None:
        self.calls = 0

    async def eval(self, *args: Any, **kwargs: Any) -> Any:
        self.calls += 1
        from redis.exceptions import ResponseError

        raise ResponseError("NOAUTH Authentication required.")

    async def aclose(self) -> None:
        return None


async def test_redis_auth_failure_is_never_admission() -> None:
    """D-R3-4: required Redis AUTH fails closed, never open."""
    from redis.exceptions import ResponseError

    redis = AuthRequiredRedis()
    bucket = RedisTokenBucket(redis)  # type: ignore[arg-type]
    limit = ApiKeyRateLimit(requests_per_minute=60, burst_capacity=5)

    with pytest.raises(ResponseError):
        await bucket.admit("key-alpha", limit)
    assert redis.calls == 1


# ---------------------------------------------------------------------------
# PostgreSQL — budget ledger isolation (key-scoped)
# ---------------------------------------------------------------------------


def _two_keys(store: PostgresApiKeyStore) -> tuple[str, str]:
    first, _ = issue_api_key(store, project_id="project-alpha", name="alpha")
    second, _ = issue_api_key(store, project_id="project-beta", name="beta")
    return first.key_id, second.key_id


def test_budget_reservation_is_invisible_to_another_key() -> None:
    store = _new_store()
    key_a, key_b = _two_keys(store)
    assert store.set_budget(key_a, ApiKeyBudget(daily_tokens=10_000))
    assert store.set_budget(key_b, ApiKeyBudget(daily_tokens=10_000))

    assert store.reserve_budget(key_a, "req-shared-1", 900, None, datetime.now(UTC)) is None

    usage_a = store.get_budget_usage(key_a, datetime.now(UTC))
    usage_b = store.get_budget_usage(key_b, datetime.now(UTC))
    assert usage_a["daily"]["tokens"] == 900
    assert usage_b["daily"]["tokens"] == 0


def test_same_request_id_under_two_keys_are_independent_reservations() -> None:
    store = _new_store()
    key_a, key_b = _two_keys(store)
    assert store.set_budget(key_a, ApiKeyBudget(daily_tokens=10_000))
    assert store.set_budget(key_b, ApiKeyBudget(daily_tokens=10_000))
    now = datetime.now(UTC)

    assert store.reserve_budget(key_a, "req-collide", 500, None, now) is None
    assert store.reserve_budget(key_b, "req-collide", 700, None, now) is None

    # Releasing B must not reach into A's ledger entry.
    store.release_budget(key_b, "req-collide")
    assert store.get_budget_usage(key_a, now)["daily"]["tokens"] == 500
    assert store.get_budget_usage(key_b, now)["daily"]["tokens"] == 0


def test_reconcile_cannot_settle_a_foreign_budget_reservation() -> None:
    store = _new_store()
    key_a, key_b = _two_keys(store)
    assert store.set_budget(key_a, ApiKeyBudget(daily_tokens=10_000))
    assert store.set_budget(key_b, ApiKeyBudget(daily_tokens=10_000))
    now = datetime.now(UTC)

    assert store.reserve_budget(key_a, "req-owned-by-a", 800, None, now) is None
    # B echoes A's request identifier: nothing of A's may move.
    store.reconcile_budget(key_b, "req-owned-by-a", 1, None)

    assert store.get_budget_usage(key_a, now)["daily"]["tokens"] == 800


def test_budget_exhaustion_for_one_key_does_not_deny_another() -> None:
    store = _new_store()
    key_a, key_b = _two_keys(store)
    assert store.set_budget(key_a, ApiKeyBudget(daily_tokens=1_000))
    assert store.set_budget(key_b, ApiKeyBudget(daily_tokens=1_000))
    now = datetime.now(UTC)

    assert store.reserve_budget(key_a, "req-fill", 1_000, None, now) is None
    assert store.reserve_budget(key_a, "req-over", 1, None, now) == "daily_tokens_exceeded"
    # The neighbouring tenant still has its full allowance.
    assert store.reserve_budget(key_b, "req-fill", 1_000, None, now) is None


# ---------------------------------------------------------------------------
# PostgreSQL — quota ledger isolation (user-scoped)
# ---------------------------------------------------------------------------


def test_quota_reservation_is_invisible_to_another_user() -> None:
    store = _new_store()
    assert store.check_and_reserve_quota(USER_A, "req-a-1", 4_000, WINDOW, 10_000)

    assert store.get_quota_usage(USER_A, WINDOW) == {
        "reserved_tokens": 4_000,
        "consumed_tokens": 0,
    }
    assert store.get_quota_usage(USER_B, WINDOW) == {
        "reserved_tokens": 0,
        "consumed_tokens": 0,
    }


def test_same_request_id_under_two_users_are_independent() -> None:
    store = _new_store()
    assert store.check_and_reserve_quota(USER_A, "req-collide", 3_000, WINDOW, 10_000)
    assert store.check_and_reserve_quota(USER_B, "req-collide", 5_000, WINDOW, 10_000)

    # B releasing its own reservation must not free A's identical request id.
    store.release_quota(USER_B, "req-collide")
    assert store.get_quota_usage(USER_A, WINDOW)["reserved_tokens"] == 3_000
    assert store.get_quota_usage(USER_B, WINDOW)["reserved_tokens"] == 0


def test_settle_cannot_consume_a_foreign_users_reservation() -> None:
    store = _new_store()
    assert store.check_and_reserve_quota(USER_A, "req-owned-by-a", 2_500, WINDOW, 10_000)

    store.settle_quota(USER_B, "req-owned-by-a", 2_500)

    assert store.get_quota_usage(USER_A, WINDOW) == {
        "reserved_tokens": 2_500,
        "consumed_tokens": 0,
    }
    assert store.get_quota_usage(USER_B, WINDOW) == {
        "reserved_tokens": 0,
        "consumed_tokens": 0,
    }


def test_quota_exhaustion_for_one_user_does_not_deny_another() -> None:
    store = _new_store()
    assert store.check_and_reserve_quota(USER_A, "req-fill", 10_000, WINDOW, 10_000)
    assert store.check_and_reserve_quota(USER_A, "req-over", 1, WINDOW, 10_000) is False
    assert store.check_and_reserve_quota(USER_B, "req-fill", 10_000, WINDOW, 10_000)


def test_quota_retry_is_idempotent_only_within_the_same_user() -> None:
    """A duplicate request id is a no-op for its owner, not for a stranger."""
    store = _new_store()
    assert store.check_and_reserve_quota(USER_A, "req-retry", 1_000, WINDOW, 10_000)
    assert store.check_and_reserve_quota(USER_A, "req-retry", 1_000, WINDOW, 10_000)
    assert store.get_quota_usage(USER_A, WINDOW)["reserved_tokens"] == 1_000

    # B reusing that identifier is a *new* reservation, admitted and charged.
    assert store.check_and_reserve_quota(USER_B, "req-retry", 1_000, WINDOW, 10_000)
    assert store.get_quota_usage(USER_B, WINDOW)["reserved_tokens"] == 1_000


# ---------------------------------------------------------------------------
# PostgreSQL — usage telemetry isolation
# ---------------------------------------------------------------------------


def _usage_event(request_id: str, key_id: str, project_id: str) -> RequestUsageEvent:
    return RequestUsageEvent(
        request_id=request_id,
        key_id=key_id,
        project_id=project_id,
        created_at=datetime.now(UTC),
        requested_alias="fast",
    )


def test_usage_event_list_is_scoped_to_one_key() -> None:
    store = _new_store()
    key_a, key_b = _two_keys(store)
    store.create_usage_event(_usage_event("r-a", key_a, "project-alpha"))
    store.create_usage_event(_usage_event("r-b", key_b, "project-beta"))

    events_a, total_a = store.list_usage_events(key_a, limit=50, offset=0)
    events_b, total_b = store.list_usage_events(key_b, limit=50, offset=0)

    assert [event.request_id for event in events_a] == ["r-a"]
    assert [event.request_id for event in events_b] == ["r-b"]
    assert (total_a, total_b) == (1, 1)


def test_finalize_cannot_target_a_foreign_usage_row() -> None:
    """Finalization is key-scoped: a mismatched key finalizes nothing."""
    store = _new_store()
    key_a, key_b = _two_keys(store)
    store.create_usage_event(_usage_event("r-owned-by-a", key_a, "project-alpha"))

    intruder = replace(
        _usage_event("r-owned-by-a", key_b, "project-beta"),
        final_status=200,
        final_deployment="stolen",
    )
    assert store.finalize_usage_event(intruder) is False

    # The owner's row is still pending and untouched.
    events_a, _ = store.list_usage_events(key_a, limit=50, offset=0)
    (row,) = events_a
    assert row.final_status is None
    assert row.final_deployment is None


def test_finalize_succeeds_for_the_row_owner() -> None:
    """The scoping above must not break the legitimate path."""
    store = _new_store()
    key_a, _ = _two_keys(store)
    store.create_usage_event(_usage_event("r-owner", key_a, "project-alpha"))
    owned = replace(
        _usage_event("r-owner", key_a, "project-alpha"),
        final_status=200,
        final_deployment="deployment-a",
    )
    assert store.finalize_usage_event(owned) is True

    events_a, _ = store.list_usage_events(key_a, limit=50, offset=0)
    assert events_a[0].final_status == 200


# ---------------------------------------------------------------------------
# SabiChat — conversation ownership
# ---------------------------------------------------------------------------


def test_conversation_read_is_owner_scoped_in_the_store() -> None:
    store = _new_chat_store()
    owner = store.create_user("owner@example.com", "hash")
    stranger = store.create_user("stranger@example.com", "hash")
    conversation = store.create_conversation(owner.user_id, "Owner only")

    assert store.get_conversation(conversation.conversation_id, owner.user_id) is not None
    assert store.get_conversation(conversation.conversation_id, stranger.user_id) is None

    listed_for_stranger, total = store.list_conversations(
        stranger.user_id, limit=20, offset=0
    )
    assert listed_for_stranger == []
    assert total == 0


def test_touch_conversation_by_a_stranger_does_not_mutate_the_row() -> None:
    store = _new_chat_store()
    owner = store.create_user("owner@example.com", "hash")
    stranger = store.create_user("stranger@example.com", "hash")
    conversation = store.create_conversation(owner.user_id, "Owner only")
    before = store.get_conversation(conversation.conversation_id, owner.user_id)
    assert before is not None

    store.touch_conversation(conversation.conversation_id, stranger.user_id)

    after = store.get_conversation(conversation.conversation_id, owner.user_id)
    assert after is not None
    assert after.updated_at == before.updated_at


_PASSWORD = "correct-horse-battery-99"


def _chat_client(tmp_path: Any) -> tuple[TestClient, Any]:
    policy = FreePoolPolicy(enabled=True, eligible_deployments=frozenset({"primary"}))
    store = SabiChatStore(f"sqlite:///{tmp_path / 'chat.sqlite'}")
    state = build_gateway_state(
        config=make_config(),
        client=StubLiteLLMClient(),
        key_store=InMemoryApiKeyStore(),
        free_pool=policy,
        chat_store=store,
    )
    enable_shared_inference(state)
    return TestClient(create_app(state=state)), state


def _register(client: TestClient, email: str) -> dict[str, str]:
    response = client.post(
        "/v1/auth/register", json={"email": email, "password": _PASSWORD}
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_foreign_conversation_is_indistinguishable_from_a_missing_one(
    tmp_path: Any,
) -> None:
    """No existence oracle: both 404s carry the same envelope and message."""
    client, _ = _chat_client(tmp_path)
    owner_headers = _register(client, "owner@example.com")
    stranger_headers = _register(client, "stranger@example.com")

    created = client.post("/v1/conversations", json={"title": "Owner only"}, headers=owner_headers)
    assert created.status_code == 201
    real_id = created.json()["conversation_id"]

    foreign = client.get(f"/v1/conversations/{real_id}", headers=stranger_headers)
    missing = client.get(
        "/v1/conversations/00000000-0000-4000-8000-000000000000",
        headers=stranger_headers,
    )

    assert foreign.status_code == missing.status_code == 404
    assert foreign.json() == missing.json()


def test_foreign_conversation_write_is_refused_before_persistence(tmp_path: Any) -> None:
    client, state = _chat_client(tmp_path)
    owner_headers = _register(client, "owner@example.com")
    stranger_headers = _register(client, "stranger@example.com")

    created = client.post("/v1/conversations", json={"title": "Owner only"}, headers=owner_headers)
    real_id = created.json()["conversation_id"]

    refused = client.post(
        f"/v1/conversations/{real_id}/messages",
        json={"content": "intruder message payload"},
        headers=stranger_headers,
    )
    assert refused.status_code == 404

    # The owner's history still holds exactly zero messages.
    history = client.get(f"/v1/conversations/{real_id}", headers=owner_headers)
    assert history.status_code == 200
    assert history.json()["messages"] == []
    assert state.chat_store is not None
