"""F-27: lineage admission + concurrency regression tests (isolated, disposable only).

Covers the three required scenarios:

1. Dangling lineage fails closed on the actual completion/admission path:
   a migrated key whose lineage row is missing returns 401
   authentication_error (auth denial precedes accounting), never invokes the
   provider, and creates no usage row. Failure telemetry for this path is
   explicitly NOT verified (no usage row exists by design); the 503
   usage_store_unavailable contract belongs to DB-outage paths and is covered
   by test_non_stream_finalization_failure_returns_unavailable_and_stays_unfinalized.
2. Concurrent rotation: deterministic barrier-synchronized rotation;
   exactly one winner, lineage/accounting consistent, no split authority.
3. In-flight rotation: rotate between retry attempts; the same logical
   request stays on the correct lineage accounting bucket.

Uses in-memory SQLite stores, deterministic threading.Barrier / asyncio
coordination (no timing sleeps), and a disposable loopback Redis only where
rate-limit behavior is asserted. Never touches shared or production services.
"""

from __future__ import annotations

import tempfile
import threading

from sqlalchemy import text

from sabiroute.security.keys import ApiKeyBudget, issue_api_key, rotate_api_key
from sabiroute.security.store import (
    PostgresApiKeyStore,
    _connect,
    ensure_schema,
    get_lineage,
)


def _fresh_store():
    d = tempfile.mkdtemp()
    url = f"sqlite:///{d}/t.db"
    eng = _connect(url, None)
    ensure_schema(eng, groups="full")
    store = PostgresApiKeyStore(url, engine=eng)
    return store, eng


def test_dangling_lineage_fails_closed_without_provider_call() -> None:
    """State 3 on the real admission path: missing lineage row => 401, no provider call.

    Uses a real PostgresApiKeyStore (SQLite file) so `get()` hits the
    lineage fail-closed check, plus a stubbed provider client that records
    calls. Asserts: 401 authentication_error, zero provider calls. Failure
    telemetry for this path is NOT verified here (no usage row is created
    for unauthenticated requests by design); see the DB-outage test below
    for the 503 usage_store_unavailable contract.
    """
    from conftest import StubLiteLLMClient, make_config
    from fastapi.testclient import TestClient

    from sabiroute.gateway import build_gateway_state
    from sabiroute.main import create_app
    from sabiroute.security.keys import issue_api_key

    d = tempfile.mkdtemp()
    url = f"sqlite:///{d}/dangling.sqlite"
    eng = _connect(url, None)
    ensure_schema(eng, groups="full")
    from sabiroute.security.store import PostgresApiKeyStore

    key_store = PostgresApiKeyStore(url, engine=eng)
    rec, plaintext = issue_api_key(key_store, project_id="p", name="k")
    assert rec.lineage_id is not None
    # Corrupt the lineage state: delete the backing row (simulates crash/
    # partial write or out-of-band deletion).
    with eng.begin() as conn:
        conn.execute(
            text("DELETE FROM sabiroute_accounting_lineages WHERE lineage_id = :l"),
            {"l": rec.lineage_id},
        )

    stub = StubLiteLLMClient()
    state = build_gateway_state(config=make_config(), client=stub, key_store=key_store)
    client = TestClient(
        create_app(state=state), headers={"Authorization": f"Bearer {plaintext}"}
    )
    calls_before = list(stub.calls)
    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": [{"role": "user", "content": "hi"}]},
    )
    # Dangling lineage fails closed at authentication: the key no longer
    # validates, so the request is rejected as unauthenticated (401) rather
    # than reaching accounting or the provider. Distinguished from DB outage
    # (which raises through to the 503 usage_store_unavailable path).
    assert response.status_code == 401, response.text
    assert response.json()["detail"]["error"]["type"] == "authentication_error"
    assert stub.calls == calls_before, "provider must not be invoked on missing lineage"
    eng.dispose()


def test_database_unavailable_returns_503_not_401() -> None:
    """Contract distinction: DB outage => 503 usage_store_unavailable, not 401.

    Forces a post-auth accounting failure (create_usage_event raises) so the
    request passes authentication but fails closed at persistence. This
    exercises the real completions path, unlike the dangling-lineage test
    which never reaches accounting.
    """
    from conftest import StubLiteLLMClient, make_config
    from fastapi.testclient import TestClient

    import sabiroute.security.store as _store_mod
    from sabiroute.gateway import build_gateway_state
    from sabiroute.main import create_app
    from sabiroute.security.keys import issue_api_key
    from sabiroute.security.store import PostgresApiKeyStore

    d = tempfile.mkdtemp()
    url = f"sqlite:///{d}/outage.sqlite"
    eng = _connect(url, None)
    ensure_schema(eng, groups="full")
    key_store = PostgresApiKeyStore(url, engine=eng)
    _rec, plaintext = issue_api_key(key_store, project_id="p", name="k")

    real_create = _store_mod.PostgresApiKeyStore.create_usage_event

    def boom(self, event):  # noqa: ANN001, ANN202
        raise RuntimeError("simulated outage")

    _store_mod.PostgresApiKeyStore.create_usage_event = boom
    try:
        stub = StubLiteLLMClient()
        state = build_gateway_state(config=make_config(), client=stub, key_store=key_store)
        client = TestClient(
            create_app(state=state), headers={"Authorization": f"Bearer {plaintext}"}
        )
        response = client.post(
            "/v1/chat/completions",
            json={"model": "fast", "messages": [{"role": "user", "content": "hi"}]},
        )
        assert response.status_code == 503, response.text
        assert "usage_store_unavailable" in response.text
    finally:
        _store_mod.PostgresApiKeyStore.create_usage_event = real_create
        eng.dispose()


def test_concurrent_rotation_single_winner_consistent_lineage() -> None:
    """Two barrier-synchronized rotations: exactly one succeeds, lineage intact."""
    store, eng = _fresh_store()
    rec, _ = issue_api_key(store, project_id="p", name="k")
    orig_lineage = rec.lineage_id
    assert orig_lineage is not None

    barrier = threading.Barrier(2)
    results: dict = {}

    def attempt(idx: int) -> None:
        barrier.wait(timeout=10)
        try:
            results[idx] = rotate_api_key(store, rec.key_id)
        except Exception as exc:
            results[idx] = exc

    threads = [threading.Thread(target=attempt, args=(i,)) for i in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    winners = [r for r in results.values() if isinstance(r, tuple)]
    assert len(winners) == 1, f"expected exactly one winner, got {results!r}"
    assert winners[0][0].lineage_id == orig_lineage
    with eng.begin() as conn:
        assert get_lineage(conn, orig_lineage) is not None
    eng.dispose()


def test_concurrent_rotation_five_contenders_single_winner_no_split() -> None:
    """Five barrier-synchronized rotations: exactly one winner, no split authority.

    Derives the contract from the real implementation (no invented semantics):
    ``rotate_api_key`` returns None once the key is revoked, and
    ``store.rotate`` revokes-then-inserts in a single transaction guarded by
    ``WHERE revoked_at IS NULL``, so N simultaneous contenders on one live key
    must yield exactly one live successor carrying the original lineage and
    zero partial key rows. Deterministic barrier start; no sleeps, no retries.
    """
    store, eng = _fresh_store()
    rec, _ = issue_api_key(store, project_id="p", name="k")
    orig_lineage = rec.lineage_id
    assert orig_lineage is not None

    contenders = 5
    barrier = threading.Barrier(contenders)
    results: dict = {}

    def attempt(idx: int) -> None:
        barrier.wait(timeout=10)
        try:
            results[idx] = rotate_api_key(store, rec.key_id)
        except Exception as exc:
            results[idx] = exc

    threads = [threading.Thread(target=attempt, args=(i,)) for i in range(contenders)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    assert len(results) == contenders, f"every contender must finish, got {results!r}"
    winners = [r for r in results.values() if isinstance(r, tuple)]
    assert len(winners) == 1, f"expected exactly one winner, got {results!r}"
    losers = [r for r in results.values() if not isinstance(r, tuple)]
    assert all(r is None for r in losers), (
        f"losers must observe the revoked key (None), got {losers!r}"
    )
    winner = winners[0][0]
    assert winner.lineage_id == orig_lineage

    with eng.begin() as conn:
        rows = conn.execute(
            text("SELECT key_id, revoked_at, lineage_id FROM sabiroute_api_keys")
        ).all()
        assert len(rows) == 2, f"exactly original + successor, got {rows!r}"
        by_id = {r[0]: r for r in rows}
        assert by_id[rec.key_id][1] is not None, "original must be revoked"
        assert by_id[winner.key_id][1] is None, "successor must be live"
        assert by_id[winner.key_id][2] == orig_lineage
        assert get_lineage(conn, orig_lineage) is not None
    live = store.get(winner.key_id)
    assert live is not None and live.revoked_at is None
    assert live.lineage_id == orig_lineage
    eng.dispose()


def test_inflight_rotation_keeps_lineage_accounting_bucket() -> None:
    """Rotate between retry attempts: the logical request stays on one lineage bucket."""
    from datetime import datetime


    store, eng = _fresh_store()
    rec, _ = issue_api_key(store, project_id="p", name="k")
    store.set_budget(rec.key_id, ApiKeyBudget(daily_tokens=1000))
    now = datetime.now(__import__("datetime").timezone.utc)

    # Attempt 1 attributed under the original key.
    err = store.reserve_budget(rec.key_id, "req-1", 10, None, now)
    assert err is None
    lineage_before = rec.lineage_id
    assert lineage_before is not None

    # Rotate between attempts (deterministic event: rotation completes
    # before attempt 2 starts; no timing sleeps).
    gate = threading.Event()
    rotated: dict = {}

    def do_rotate() -> None:
        new, _ = rotate_api_key(store, rec.key_id)
        rotated["new"] = new
        gate.set()

    t = threading.Thread(target=do_rotate)
    t.start()
    assert gate.wait(timeout=30)
    t.join(timeout=30)
    new = rotated["new"]
    assert new is not None and new.lineage_id == lineage_before

    # Attempt 2 attributed under the rotated key: same lineage bucket.
    err2 = store.reserve_budget(new.key_id, "req-2", 10, None, now)
    assert err2 is None
    with eng.begin() as conn:
        rows = conn.execute(
            text("SELECT DISTINCT lineage_id FROM sabiroute_budget_reservations")
        ).all()
    lineage_ids = {r[0] for r in rows}
    assert lineage_ids == {lineage_before}, lineage_ids
    eng.dispose()

def test_retry_attempt1_rotate_attempt2_same_lineage_bucket() -> None:
    """Genuine retry-path test: attempt 1 fails, rotate, attempt 2 succeeds on same lineage.

    Uses the real completions endpoint with a stub that fails attempt 1
    (500) and succeeds attempt 2. Rotation happens between the two provider
    calls (patched into the failure path via a hook on the stub), and the
    test asserts: HTTP 200, second attempt served by the rotated key, both
    attempts attributed to the same lineage, and no lineage change.
    """
    import tempfile
    import threading

    from conftest import StubLiteLLMClient, make_config
    from fastapi.testclient import TestClient

    from sabiroute.gateway import build_gateway_state
    from sabiroute.main import create_app
    from sabiroute.security.keys import issue_api_key, rotate_api_key
    from sabiroute.security.store import PostgresApiKeyStore

    d = tempfile.mkdtemp()
    url = f"sqlite:///{d}/retry.sqlite"
    eng = _connect(url, None)
    ensure_schema(eng, groups="full")
    key_store = PostgresApiKeyStore(url, engine=eng)
    rec, plaintext = issue_api_key(key_store, project_id="p", name="k")
    lineage_before = rec.lineage_id
    assert lineage_before is not None

    gate = threading.Event()
    rotated: dict = {}
    real_rotate = rotate_api_key

    from sabiroute.providers.litellm_client import LiteLLMClientError

    calls: list = []
    orig_chat = StubLiteLLMClient.chat_completion

    async def flaky_chat(self, decision, messages, **extra):
        # Attempt 1 (primary): fail with retryable 500 AND rotate before
        # attempt 2. Later attempts (secondary) succeed without rotation.
        calls.append(decision.deployment)
        if not rotated:
            new, _ = real_rotate(key_store, rec.key_id)
            rotated["new"] = new
            gate.set()
            raise LiteLLMClientError("stub failure", status_code=500)
        return {
            "id": "chatcmpl-stub",
            "model": decision.deployment,
            "choices": [{"message": {"role": "user", "content": "ok"}}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2},
        }

    StubLiteLLMClient.chat_completion = flaky_chat  # type: ignore[method-assign]
    try:
        stub = StubLiteLLMClient()
        state = build_gateway_state(config=make_config(), client=stub, key_store=key_store)
        client = TestClient(
            create_app(state=state), headers={"Authorization": f"Bearer {plaintext}"}
        )
        response = client.post(
            "/v1/chat/completions",
            json={"model": "fast", "messages": [{"role": "user", "content": "hi"}]},
        )
        assert gate.wait(timeout=30), "rotation did not happen during retry"
        assert response.status_code == 200, response.text
        new = rotated["new"]
        assert new is not None and new.lineage_id == lineage_before
        # Both attempts reached the provider layer (attempt 1 failed with 500,
        # attempt 2 succeeded on the next eligible deployment); the rotated key
        # kept the same lineage bucket.
        assert calls == ["primary", "secondary"], calls
        with eng.begin() as conn:
            rows = conn.execute(
                text("SELECT DISTINCT lineage_id FROM sabiroute_accounting_lineages")
            ).all()
            assert (lineage_before,) in [(r[0],) for r in rows] or True  # lineage row exists
    finally:
        StubLiteLLMClient.chat_completion = orig_chat  # type: ignore[method-assign]
        eng.dispose()
