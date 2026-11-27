"""Behavioural tests for :mod:`sabiroute.chat.store` persistence contracts."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from sabiroute.chat.store import DuplicateEmailError, SabiChatStore


@pytest.fixture()
def store(tmp_path: Path) -> SabiChatStore:
    return SabiChatStore(f"sqlite:///{tmp_path / 'chat.db'}")


def test_create_user_then_look_up_by_email(store: SabiChatStore) -> None:
    created = store.create_user("user@example.test", "hash")

    found = store.get_user_by_email("user@example.test")

    assert found is not None
    assert found.user_id == created.user_id
    assert found.disabled_at is None
    assert store.get_user(created.user_id) == found


def test_duplicate_email_is_rejected(store: SabiChatStore) -> None:
    store.create_user("dupe@example.test", "hash")

    with pytest.raises(DuplicateEmailError):
        store.create_user("dupe@example.test", "other-hash")


def test_disable_user_is_idempotent(store: SabiChatStore) -> None:
    user = store.create_user("d@example.test", "hash")

    assert store.disable_user(user.user_id) is True
    assert store.disable_user(user.user_id) is False
    assert store.get_user(user.user_id).disabled_at is not None  # type: ignore[union-attr]


def test_session_lifecycle_and_revoke(store: SabiChatStore) -> None:
    user = store.create_user("s@example.test", "hash")
    expires = datetime.now(UTC) + timedelta(days=1)

    session = store.create_session(user.user_id, "digest", expires)

    assert store.get_session("digest") == session
    assert store.revoke_session(session.session_id) is True
    assert store.revoke_session(session.session_id) is False
    assert store.get_session("digest").revoked_at is not None  # type: ignore[union-attr]


def test_conversations_are_owner_scoped(store: SabiChatStore) -> None:
    owner = store.create_user("owner@example.test", "hash")
    stranger = store.create_user("stranger@example.test", "hash")

    conversation = store.create_conversation(owner.user_id, "Title")

    assert store.get_conversation(conversation.conversation_id, owner.user_id) is not None
    assert store.get_conversation(conversation.conversation_id, stranger.user_id) is None


def test_purge_removes_expired_sessions_only(store: SabiChatStore) -> None:
    user = store.create_user("p@example.test", "hash")
    past = datetime.now(UTC) - timedelta(days=2)
    future = datetime.now(UTC) + timedelta(days=2)

    store.create_session(user.user_id, "old", past)
    store.create_session(user.user_id, "new", future)

    removed = store.purge_expired_sessions()

    assert removed == 1
    assert store.get_session("old") is None
    assert store.get_session("new") is not None
