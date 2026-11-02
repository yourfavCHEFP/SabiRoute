"""F-07 lifespan-owned session cleanup (SabiChat hygiene).

Lane ownership: SabiChat / lifespan hygiene (adjacent to R5). Moved verbatim
out of ``tests/test_request_limits.py`` so the R7 release-evidence package does
not carry another lane's evidence. Bodies are unchanged.

Scope: ``sabiroute.chat.store.SabiChatStore.purge_expired_sessions`` and the
startup/shutdown lifespan hook that calls it — expired sessions are removed,
revoked sessions past retention are removed, recent ones are kept, and a purge
failure is hygiene noise that must never break startup.

Known overlap: ``tests/test_recovery_shutdown.py::
test_startup_shutdown_purge_failure_does_not_break_lifespan`` injects the same
purge failure and asserts the same "startup survives" property. Recorded in the
R7 ownership map rather than silently merged or duplicated.
"""

from __future__ import annotations

from conftest import InMemoryApiKeyStore, StubLiteLLMClient, make_config
from fastapi.testclient import TestClient

from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app


def test_startup_purges_expired_sessions_only(tmp_path):
    from datetime import UTC, datetime, timedelta

    from sabiroute.chat.store import SabiChatStore

    store = SabiChatStore(f"sqlite:///{tmp_path / 'purge.sqlite'}")
    now = datetime.now(UTC)
    uid = store.create_user("purge@example.com", "hashed").user_id
    # expired session
    store.create_session(uid, "a" * 64, now - timedelta(days=1))
    # live session
    store.create_session(uid, "b" * 64, now + timedelta(days=7))
    assert store.purge_expired_sessions(now) == 1
    # idempotent re-run removes nothing
    assert store.purge_expired_sessions(now) == 0


def test_lifespan_purge_runs_and_never_breaks_startup(tmp_path):
    from datetime import UTC, datetime, timedelta

    from sabiroute.chat.store import SabiChatStore

    store = SabiChatStore(f"sqlite:///{tmp_path / 'lifespan-purge.sqlite'}")
    now = datetime.now(UTC)
    uid = store.create_user("life@example.com", "hashed").user_id
    store.create_session(uid, "c" * 64, now - timedelta(days=1))
    state = build_gateway_state(
        config=make_config(), client=StubLiteLLMClient(), key_store=InMemoryApiKeyStore(),
        chat_store=store,
    )
    with TestClient(create_app(state=state)):
        pass
    # expired row removed by lifespan purge; live path unaffected
    assert store.purge_expired_sessions(now) == 0
    ready = TestClient(create_app(state=state)).get("/health/ready")
    assert ready.status_code == 200


def test_purge_failure_is_hygiene_not_outage(tmp_path, monkeypatch):
    from sabiroute.chat.store import SabiChatStore

    store = SabiChatStore(f"sqlite:///{tmp_path / 'purge-fail.sqlite'}")

    def boom(*a, **k):
        raise RuntimeError("store down")

    monkeypatch.setattr(store, "purge_expired_sessions", boom)
    state = build_gateway_state(
        config=make_config(), client=StubLiteLLMClient(), key_store=InMemoryApiKeyStore(),
        chat_store=store,
    )
    with TestClient(create_app(state=state)) as client:
        assert client.get("/health/live").status_code == 200


def test_purge_removes_revoked_past_retention_keeps_recent(tmp_path):
    from datetime import UTC, datetime, timedelta

    from sabiroute.chat.store import SabiChatStore

    store = SabiChatStore(f"sqlite:///{tmp_path / 'revoked.sqlite'}")
    now = datetime.now(UTC)
    uid = store.create_user("rev@example.com", "h").user_id
    # old revoked (40 days ago) -> purged; recent revoked -> kept; live -> kept
    s_old = store.create_session(uid, "o" * 64, now + timedelta(days=7))
    s_new = store.create_session(uid, "n" * 64, now + timedelta(days=7))
    store.create_session(uid, "l" * 64, now + timedelta(days=7))
    # backdate revoked_at via direct SQL (store API stamps now)
    from sqlalchemy import update

    from sabiroute.chat.store import _SABICHAT_SESSIONS

    with store._engine.begin() as conn:
        conn.execute(
            update(_SABICHAT_SESSIONS)
            .where(_SABICHAT_SESSIONS.c.session_id == s_old.session_id)
            .values(revoked_at=now - timedelta(days=40))
        )
    store.revoke_session(s_new.session_id)
    removed = store.purge_expired_sessions(now)
    assert removed == 1
    assert store.get_session("o" * 64) is None
    assert store.get_session("n" * 64) is not None
    assert store.get_session("l" * 64) is not None
