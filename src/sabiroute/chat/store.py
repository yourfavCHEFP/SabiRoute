"""SabiChat persistence: users, sessions, conversations, messages.

Conventions follow ``security/store.py``: SQLAlchemy Core tables, synchronous
methods (callers run them via ``BoundedStoreExecutor``), one shared schema
initialized through ``ensure_schema`` so store entry-point order never
matters. Session bearer tokens are never persisted — only their SHA-256
digest. Passwords are never persisted — only the modular hash string.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from ..security.store import (
    _SABICHAT_CONVERSATIONS,
    _SABICHAT_MESSAGES,
    _SABICHAT_SESSIONS,
    _SABICHAT_USERS,
    _connect,
    ensure_schema,
)


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _at(value: datetime) -> datetime:
    """Normalize a stored timestamp to tz-aware UTC.

    PostgreSQL returns aware datetimes; SQLite returns naive ones. All
    session-expiry comparisons require aware values, so the boundary
    normalizes naive timestamps as UTC rather than failing at comparison.
    """
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def digest_token(token: str) -> str:
    """One-way digest for persisted session tokens."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class SabiChatUser:
    user_id: str
    email: str
    password_hash: str
    created_at: datetime
    disabled_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class SabiChatSession:
    session_id: str
    user_id: str
    token_hash: str
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class SabiChatConversation:
    conversation_id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class SabiChatMessage:
    message_id: str
    conversation_id: str
    role: str
    content: str
    model: str | None = None
    deployment: str | None = None
    error_type: str | None = None
    created_at: datetime | None = None


class DuplicateEmailError(ValueError):
    """Raised when registration uses an already-registered email."""


class SabiChatStore:
    """Synchronous SabiChat persistence. Run methods via the store executor."""

    def __init__(self, database_url: str, *, engine: Engine | None = None) -> None:
        if not database_url:
            raise ValueError("DATABASE_URL is required for SabiChat persistence.")
        self._engine = _connect(database_url, engine)
        ensure_schema(self._engine)

    # -- users ---------------------------------------------------------

    def create_user(self, email: str, password_hash: str) -> SabiChatUser:
        user = SabiChatUser(
            user_id=str(uuid4()),
            email=email,
            password_hash=password_hash,
            created_at=_utcnow(),
        )
        try:
            with self._engine.begin() as connection:
                connection.execute(
                    insert(_SABICHAT_USERS).values(
                        user_id=user.user_id,
                        email=user.email,
                        password_hash=user.password_hash,
                        created_at=user.created_at,
                        disabled_at=None,
                    )
                )
        except IntegrityError as exc:
            raise DuplicateEmailError("Email is already registered.") from exc
        return user

    def get_user_by_email(self, email: str) -> SabiChatUser | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                select(_SABICHAT_USERS).where(_SABICHAT_USERS.c.email == email)
            ).mappings().first()
        return _user_from_row(row) if row is not None else None

    def get_user(self, user_id: str) -> SabiChatUser | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                select(_SABICHAT_USERS).where(_SABICHAT_USERS.c.user_id == user_id)
            ).mappings().first()
        return _user_from_row(row) if row is not None else None

    def disable_user(self, user_id: str) -> bool:
        with self._engine.begin() as connection:
            result = connection.execute(
                update(_SABICHAT_USERS)
                .where(
                    _SABICHAT_USERS.c.user_id == user_id,
                    _SABICHAT_USERS.c.disabled_at.is_(None),
                )
                .values(disabled_at=_utcnow())
            )
        return result.rowcount == 1

    # -- sessions ------------------------------------------------------

    def create_session(
        self, user_id: str, token_hash: str, expires_at: datetime
    ) -> SabiChatSession:
        session = SabiChatSession(
            session_id=str(uuid4()),
            user_id=user_id,
            token_hash=token_hash,
            created_at=_utcnow(),
            expires_at=expires_at,
        )
        with self._engine.begin() as connection:
            connection.execute(
                insert(_SABICHAT_SESSIONS).values(
                    session_id=session.session_id,
                    user_id=session.user_id,
                    token_hash=session.token_hash,
                    created_at=session.created_at,
                    expires_at=session.expires_at,
                    revoked_at=None,
                )
            )
        return session

    def get_session(self, token_hash: str) -> SabiChatSession | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                select(_SABICHAT_SESSIONS).where(
                    _SABICHAT_SESSIONS.c.token_hash == token_hash
                )
            ).mappings().first()
        return _session_from_row(row) if row is not None else None

    def revoke_session(self, session_id: str) -> bool:
        with self._engine.begin() as connection:
            result = connection.execute(
                update(_SABICHAT_SESSIONS)
                .where(
                    _SABICHAT_SESSIONS.c.session_id == session_id,
                    _SABICHAT_SESSIONS.c.revoked_at.is_(None),
                )
                .values(revoked_at=_utcnow())
            )
        return result.rowcount == 1

    def revoke_user_sessions(self, user_id: str) -> int:
        with self._engine.begin() as connection:
            result = connection.execute(
                update(_SABICHAT_SESSIONS)
                .where(
                    _SABICHAT_SESSIONS.c.user_id == user_id,
                    _SABICHAT_SESSIONS.c.revoked_at.is_(None),
                )
                .values(revoked_at=_utcnow())
            )
        return result.rowcount

    def purge_expired_sessions(self, now: datetime | None = None) -> int:
        """Delete sessions past expiry. Returns rows removed; safe to re-run."""
        cutoff = now or _utcnow()
        with self._engine.begin() as connection:
            result = connection.execute(
                delete(_SABICHAT_SESSIONS).where(_SABICHAT_SESSIONS.c.expires_at < cutoff)
            )
        return result.rowcount

    # -- conversations -------------------------------------------------

    def create_conversation(self, user_id: str, title: str) -> SabiChatConversation:
        now = _utcnow()
        conversation = SabiChatConversation(
            conversation_id=str(uuid4()),
            user_id=user_id,
            title=title,
            created_at=now,
            updated_at=now,
        )
        with self._engine.begin() as connection:
            connection.execute(
                insert(_SABICHAT_CONVERSATIONS).values(
                    conversation_id=conversation.conversation_id,
                    user_id=conversation.user_id,
                    title=conversation.title,
                    created_at=conversation.created_at,
                    updated_at=conversation.updated_at,
                )
            )
        return conversation

    def get_conversation(
        self, conversation_id: str, user_id: str
    ) -> SabiChatConversation | None:
        """Owner-scoped read: any user_id mismatch returns None (no leak)."""
        with self._engine.connect() as connection:
            row = connection.execute(
                select(_SABICHAT_CONVERSATIONS).where(
                    _SABICHAT_CONVERSATIONS.c.conversation_id == conversation_id,
                    _SABICHAT_CONVERSATIONS.c.user_id == user_id,
                )
            ).mappings().first()
        return _conversation_from_row(row) if row is not None else None

    def list_conversations(
        self, user_id: str, *, limit: int, offset: int
    ) -> tuple[list[SabiChatConversation], int]:
        with self._engine.connect() as connection:
            total = connection.execute(
                select(func.count())
                .select_from(_SABICHAT_CONVERSATIONS)
                .where(_SABICHAT_CONVERSATIONS.c.user_id == user_id)
            ).scalar_one()
            rows = connection.execute(
                select(_SABICHAT_CONVERSATIONS)
                .where(_SABICHAT_CONVERSATIONS.c.user_id == user_id)
                .order_by(
                    _SABICHAT_CONVERSATIONS.c.created_at.desc(),
                    _SABICHAT_CONVERSATIONS.c.conversation_id.desc(),
                )
                .limit(limit)
                .offset(offset)
            ).mappings().all()
        return [_conversation_from_row(row) for row in rows], total

    def touch_conversation(self, conversation_id: str, user_id: str) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                update(_SABICHAT_CONVERSATIONS)
                .where(
                    _SABICHAT_CONVERSATIONS.c.conversation_id == conversation_id,
                    _SABICHAT_CONVERSATIONS.c.user_id == user_id,
                )
                .values(updated_at=_utcnow())
            )

    # -- messages ------------------------------------------------------

    def create_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        *,
        model: str | None = None,
        deployment: str | None = None,
        error_type: str | None = None,
    ) -> SabiChatMessage:
        message = SabiChatMessage(
            message_id=str(uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
            model=model,
            deployment=deployment,
            error_type=error_type,
            created_at=_utcnow(),
        )
        with self._engine.begin() as connection:
            connection.execute(
                insert(_SABICHAT_MESSAGES).values(
                    message_id=message.message_id,
                    conversation_id=message.conversation_id,
                    role=message.role,
                    content=message.content,
                    model=message.model,
                    deployment=message.deployment,
                    error_type=message.error_type,
                    created_at=message.created_at,
                )
            )
        return message

    def list_messages(
        self, conversation_id: str, *, limit: int, offset: int = 0
    ) -> list[SabiChatMessage]:
        """Oldest-first page. Callers must owner-check the conversation first."""
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(_SABICHAT_MESSAGES)
                .where(_SABICHAT_MESSAGES.c.conversation_id == conversation_id)
                .order_by(
                    _SABICHAT_MESSAGES.c.created_at,
                    _SABICHAT_MESSAGES.c.message_id,
                )
                .limit(limit)
                .offset(offset)
            ).mappings().all()
        return [_message_from_row(row) for row in rows]

    def close(self) -> None:
        self._engine.dispose()


def _user_from_row(row: Any) -> SabiChatUser:
    disabled_at = row["disabled_at"]
    return SabiChatUser(
        user_id=row["user_id"],
        email=row["email"],
        password_hash=row["password_hash"],
        created_at=_at(row["created_at"]),
        disabled_at=_at(disabled_at) if disabled_at is not None else None,
    )


def _session_from_row(row: Any) -> SabiChatSession:
    revoked_at = row["revoked_at"]
    return SabiChatSession(
        session_id=row["session_id"],
        user_id=row["user_id"],
        token_hash=row["token_hash"],
        created_at=_at(row["created_at"]),
        expires_at=_at(row["expires_at"]),
        revoked_at=_at(revoked_at) if revoked_at is not None else None,
    )


def _conversation_from_row(row: Any) -> SabiChatConversation:
    return SabiChatConversation(
        conversation_id=row["conversation_id"],
        user_id=row["user_id"],
        title=row["title"],
        created_at=_at(row["created_at"]),
        updated_at=_at(row["updated_at"]),
    )


def _message_from_row(row: Any) -> SabiChatMessage:
    return SabiChatMessage(
        message_id=row["message_id"],
        conversation_id=row["conversation_id"],
        role=row["role"],
        content=row["content"],
        model=row["model"],
        deployment=row["deployment"],
        error_type=row["error_type"],
        created_at=_at(row["created_at"]) if row["created_at"] is not None else None,
    )
