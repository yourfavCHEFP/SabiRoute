"""PostgreSQL persistence for SabiRoute-owned API-key records."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    create_engine,
    delete,
    func,
    insert,
    select,
    update,
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from .keys import (
    ApiKeyBudget,
    ApiKeyRateLimit,
    ApiKeyRecord,
    RequestUsageEvent,
    validate_pre_routing_feature_snapshot,
    validate_usage_event_finalization,
)

_METADATA = MetaData()
_API_KEYS = Table(
    "sabiroute_api_keys",
    _METADATA,
    Column("key_id", String(24), primary_key=True),
    Column("key_hash", String(64), nullable=False),
    Column("project_id", String(128), nullable=False, index=True),
    Column("name", String(128), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("revoked_at", DateTime(timezone=True), nullable=True),
    Column("metadata_json", JSON, nullable=False, default=dict),
)
_API_KEY_RATE_LIMITS = Table(
    "sabiroute_api_key_rate_limits",
    _METADATA,
    Column("key_id", String(24), ForeignKey("sabiroute_api_keys.key_id"), primary_key=True),
    Column("requests_per_minute", Integer, nullable=False),
    Column("burst_capacity", Integer, nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)
_REQUEST_USAGE = Table(
    "sabiroute_request_usage",
    _METADATA,
    Column("request_id", String(36), primary_key=True),
    Column("key_id", String(24), ForeignKey("sabiroute_api_keys.key_id"), nullable=False),
    Column("project_id", String(128), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("requested_alias", String(256), nullable=True),
    Column("final_deployment", String(256), nullable=True),
    Column("final_status", Integer, nullable=True),
    Column("prompt_tokens", Integer, nullable=True),
    Column("completion_tokens", Integer, nullable=True),
    Column("total_tokens", Integer, nullable=True),
    Column("failure_category", String(64), nullable=True),
    Column("estimated_input_tokens", Integer, nullable=True),
    Column("reserved_tokens", Integer, nullable=True),
    Column("estimated_cost_usd", Numeric(20, 10), nullable=True),
    Column("actual_cost_usd", Numeric(20, 10), nullable=True),
    Column("routing_decisions", JSON, nullable=False, default=list),
    Column("feature_schema_version", String(16), nullable=True, default="1.0"),
    Column("pre_routing_features", JSON, nullable=False, default=list),
    Column("usage_source", String(16), nullable=True),
)
Index("ix_sabiroute_request_usage_key_time", _REQUEST_USAGE.c.key_id, _REQUEST_USAGE.c.created_at)
_SCHEMA_VERSIONS = Table(
    "sabiroute_schema_versions",
    _METADATA,
    Column("revision", String(64), primary_key=True),
    Column("description", String(256), nullable=False),
    Column("applied_at", DateTime(timezone=True), nullable=False),
)
#: Ordered schema revisions. Each revision must be idempotent and purely
#: additive: existing tables and rows are never rewritten or dropped.
#: Application order is the list order; applied revisions are recorded in
#: ``sabiroute_schema_versions`` so re-running is a no-op.
_SHARED_INFERENCE = Table(
    "sabiroute_shared_inference_policy",
    _METADATA,
    Column("id", String(16), primary_key=True),
    Column("enabled", Boolean, nullable=True),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("updated_by", String(128), nullable=False),
)
_QUOTA_WINDOWS = Table(
    "sabichat_quota_windows",
    _METADATA,
    Column("user_id", String(36), primary_key=True),
    Column("window_start", DateTime(timezone=True), primary_key=True),
    Column("reserved_tokens", Integer, nullable=False, default=0),
    Column("consumed_tokens", Integer, nullable=False, default=0),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)
_QUOTA_RESERVATIONS = Table(
    "sabichat_quota_reservations",
    _METADATA,
    Column("user_id", String(36), primary_key=True),
    Column("request_id", String(36), primary_key=True),
    Column("window_start", DateTime(timezone=True), nullable=False),
    Column("estimated_tokens", Integer, nullable=False),
    Column("status", String(16), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)
SCHEMA_MIGRATIONS: tuple[tuple[str, str], ...] = (
    ("0001-usage-source", "Add nullable sabiroute_request_usage.usage_source."),
    ("0002-sabichat-backend", "Add sabichat_users/sessions/conversations/messages."),
    ("0003-shared-inference-switch", "Add sabiroute_shared_inference_policy."),
    ("0004-user-quota-ledger", "Add sabichat_quota_windows/reservations."),
)


def _connect(database_url: str, engine: Engine | None) -> Engine:
    """Build a SQLAlchemy engine with the project's URL conventions."""
    if engine is not None:
        return engine
    url = database_url
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url.removeprefix("postgresql://")
    elif url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url.removeprefix("postgres://")
    return create_engine(url, pool_pre_ping=True)


def migrate_usage_columns(engine: Engine) -> None:
    """Add nullable accounting and routing telemetry fields to usage tables."""
    from sqlalchemy import inspect

    existing = {
        column["name"] for column in inspect(engine).get_columns(_REQUEST_USAGE.name)
    }
    additions = {
        "estimated_input_tokens": "INTEGER",
        "reserved_tokens": "INTEGER",
        "estimated_cost_usd": "NUMERIC(20, 10)",
        "actual_cost_usd": "NUMERIC(20, 10)",
        "routing_decisions": "JSON",
        "feature_schema_version": "VARCHAR(16)",
        "pre_routing_features": "JSON NOT NULL DEFAULT '[]'",
        "usage_source": "VARCHAR(16)",
    }
    dialect = engine.dialect.name
    with engine.begin() as connection:
        for name, sql_type in additions.items():
            if name not in existing:
                if dialect == "postgresql":
                    connection.exec_driver_sql(
                        f"ALTER TABLE {_REQUEST_USAGE.name} ADD COLUMN IF NOT EXISTS "
                        f"{name} {sql_type}"
                    )
                    continue
                connection.exec_driver_sql(
                    f"ALTER TABLE {_REQUEST_USAGE.name} ADD COLUMN {name} {sql_type}"
                )


def apply_schema_migrations(engine: Engine) -> None:
    """Record ordered schema revisions idempotently.

    Column changes themselves are applied by ``create_all`` (fresh installs)
    and ``migrate_usage_columns`` (existing databases); this ledger only
    records *which* revisions the database has seen, in order, so application
    order is explicit and re-running is a no-op. Rollback is out of scope by
    design: every revision is additive, so a downgrade is at most an ignored
    column, never lost rows.
    """
    with engine.begin() as connection:
        applied = {
            row[0] for row in connection.execute(select(_SCHEMA_VERSIONS.c.revision))
        }
        for revision, description in SCHEMA_MIGRATIONS:
            if revision in applied:
                continue
            connection.execute(
                insert(_SCHEMA_VERSIONS).values(
                    revision=revision,
                    description=description,
                    applied_at=datetime.now(UTC),
                )
            )


def applied_schema_revisions(engine: Engine) -> list[str]:
    """Revisions recorded in application order (by applied timestamp)."""
    with engine.begin() as connection:
        rows = connection.execute(
            select(_SCHEMA_VERSIONS.c.revision).order_by(
                _SCHEMA_VERSIONS.c.applied_at, _SCHEMA_VERSIONS.c.revision
            )
        )
        return [row[0] for row in rows]


def ensure_schema(engine: Engine) -> None:
    """Bring one database to the current schema: tables, columns, ledger.

    Shared by every store entry point so initialization order never matters:
    whichever store opens the database first performs the full upgrade.
    """
    _METADATA.create_all(
        engine,
        tables=[
            _API_KEYS,
            _API_KEY_RATE_LIMITS,
            _REQUEST_USAGE,
            _API_KEY_BUDGETS,
            _BUDGET_RESERVATIONS,
            _SCHEMA_VERSIONS,
            _SABICHAT_USERS,
            _SABICHAT_SESSIONS,
            _SABICHAT_CONVERSATIONS,
            _SABICHAT_MESSAGES,
            _SHARED_INFERENCE,
            _QUOTA_WINDOWS,
            _QUOTA_RESERVATIONS,
        ],
    )
    migrate_usage_columns(engine)
    apply_schema_migrations(engine)
_API_KEY_BUDGETS = Table(
    "sabiroute_api_key_budgets",
    _METADATA,
    Column("key_id", String(24), ForeignKey("sabiroute_api_keys.key_id"), primary_key=True),
    Column("daily_tokens", Integer, nullable=True),
    Column("monthly_tokens", Integer, nullable=True),
    Column("daily_cost_usd", Numeric(20, 10), nullable=True),
    Column("monthly_cost_usd", Numeric(20, 10), nullable=True),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)
_BUDGET_RESERVATIONS = Table(
    "sabiroute_budget_reservations",
    _METADATA,
    Column("request_id", String(36), primary_key=True),
    Column("key_id", String(24), ForeignKey("sabiroute_api_keys.key_id"), primary_key=True),
    Column("window_kind", String(8), primary_key=True),
    Column("window_start", DateTime(timezone=True), primary_key=True),
    Column("reserved_tokens", Integer, nullable=False),
    Column("accounted_tokens", Integer, nullable=False),
    Column("estimated_cost_usd", Numeric(20, 10), nullable=True),
    Column("accounted_cost_usd", Numeric(20, 10), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)
_SABICHAT_USERS = Table(
    "sabichat_users",
    _METADATA,
    Column("user_id", String(36), primary_key=True),
    Column("email", String(320), nullable=False, unique=True),
    Column("password_hash", String(256), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
)
_SABICHAT_SESSIONS = Table(
    "sabichat_sessions",
    _METADATA,
    Column("session_id", String(36), primary_key=True),
    Column("user_id", String(36), ForeignKey("sabichat_users.user_id"), nullable=False),
    Column("token_hash", String(64), nullable=False, unique=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("revoked_at", DateTime(timezone=True), nullable=True),
)
_SABICHAT_CONVERSATIONS = Table(
    "sabichat_conversations",
    _METADATA,
    Column("conversation_id", String(36), primary_key=True),
    Column("user_id", String(36), ForeignKey("sabichat_users.user_id"), nullable=False),
    Column("title", String(120), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)
_SABICHAT_MESSAGES = Table(
    "sabichat_messages",
    _METADATA,
    Column("message_id", String(36), primary_key=True),
    Column(
        "conversation_id",
        String(36),
        ForeignKey("sabichat_conversations.conversation_id"),
        nullable=False,
    ),
    Column("role", String(16), nullable=False),
    Column("content", String(8000), nullable=False),
    Column("model", String(256), nullable=True),
    Column("deployment", String(256), nullable=True),
    Column("error_type", String(64), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)
Index(
    "ix_sabichat_messages_conversation_time",
    _SABICHAT_MESSAGES.c.conversation_id,
    _SABICHAT_MESSAGES.c.created_at,
)
Index(
    "ix_sabichat_conversations_user_time",
    _SABICHAT_CONVERSATIONS.c.user_id,
    _SABICHAT_CONVERSATIONS.c.created_at,
)


class PostgresApiKeyStore:
    """SabiRoute-owned table in the configured PostgreSQL database.

    ``create_all`` is used because this repository has no migration framework or
    existing SabiRoute schema. The table name is namespaced and does not touch
    LiteLLM's tables.
    """

    def __init__(self, database_url: str, *, engine: Engine | None = None) -> None:
        if not database_url:
            raise ValueError("DATABASE_URL is required for API-key persistence.")
        if engine is None:
            url = database_url
            if url.startswith("postgresql://"):
                url = "postgresql+psycopg://" + url.removeprefix("postgresql://")
            elif url.startswith("postgres://"):
                url = "postgresql+psycopg://" + url.removeprefix("postgres://")
            engine = create_engine(url, pool_pre_ping=True)
        self._engine = engine
        # New tables and nullable telemetry columns are additive; create_all
        # does not alter existing tables.
        _METADATA.create_all(
            self._engine,
            tables=[
                _API_KEYS,
                _API_KEY_RATE_LIMITS,
                _REQUEST_USAGE,
                _API_KEY_BUDGETS,
                _BUDGET_RESERVATIONS,
                _SCHEMA_VERSIONS,
                _SABICHAT_USERS,
                _SABICHAT_SESSIONS,
                _SABICHAT_CONVERSATIONS,
                _SABICHAT_MESSAGES,
                _SHARED_INFERENCE,
                _QUOTA_WINDOWS,
                _QUOTA_RESERVATIONS,
            ],
        )
        self._migrate_usage_columns()
        self._apply_schema_migrations()

    def _migrate_usage_columns(self) -> None:
        """Add nullable accounting and routing telemetry fields to usage tables."""
        migrate_usage_columns(self._engine)

    def _apply_schema_migrations(self) -> None:
        """Record ordered schema revisions idempotently (see module runner)."""
        apply_schema_migrations(self._engine)

    def applied_revisions(self) -> list[str]:
        """Revisions recorded in application order (by applied timestamp)."""
        return applied_schema_revisions(self._engine)

    def create(self, record: ApiKeyRecord) -> None:
        with self._engine.begin() as connection:
            connection.execute(insert(_API_KEYS).values(**_record_values(record)))

    def get(self, key_id: str) -> ApiKeyRecord | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(select(_API_KEYS).where(_API_KEYS.c.key_id == key_id))
                .mappings()
                .first()
            )
        return _from_row(row) if row is not None else None

    def revoke(self, key_id: str, at: datetime) -> bool:
        with self._engine.begin() as connection:
            result = connection.execute(
                update(_API_KEYS)
                .where(_API_KEYS.c.key_id == key_id, _API_KEYS.c.revoked_at.is_(None))
                .values(revoked_at=at)
            )
        return result.rowcount == 1

    def rotate(self, old_key_id: str, new_record: ApiKeyRecord, at: datetime) -> bool:
        with self._engine.begin() as connection:
            old_limit = (
                connection.execute(
                    select(_API_KEY_RATE_LIMITS).where(_API_KEY_RATE_LIMITS.c.key_id == old_key_id)
                )
                .mappings()
                .first()
            )
            old_budget = (
                connection.execute(
                    select(_API_KEY_BUDGETS).where(_API_KEY_BUDGETS.c.key_id == old_key_id)
                )
                .mappings()
                .first()
            )
            result = connection.execute(
                update(_API_KEYS)
                .where(_API_KEYS.c.key_id == old_key_id, _API_KEYS.c.revoked_at.is_(None))
                .values(revoked_at=at)
            )
            if result.rowcount != 1:
                return False
            connection.execute(insert(_API_KEYS).values(**_record_values(new_record)))
            if old_limit is not None:
                connection.execute(
                    insert(_API_KEY_RATE_LIMITS).values(
                        key_id=new_record.key_id,
                        requests_per_minute=old_limit["requests_per_minute"],
                        burst_capacity=old_limit["burst_capacity"],
                        updated_at=at,
                    )
                )
            if old_budget is not None:
                connection.execute(
                    insert(_API_KEY_BUDGETS).values(
                        key_id=new_record.key_id,
                        daily_tokens=old_budget["daily_tokens"],
                        monthly_tokens=old_budget["monthly_tokens"],
                        daily_cost_usd=old_budget["daily_cost_usd"],
                        monthly_cost_usd=old_budget["monthly_cost_usd"],
                        updated_at=at,
                    )
                )
        return True

    def get_rate_limit(self, key_id: str) -> ApiKeyRateLimit | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(_API_KEY_RATE_LIMITS).where(_API_KEY_RATE_LIMITS.c.key_id == key_id)
                )
                .mappings()
                .first()
            )
        if row is None:
            return None
        return ApiKeyRateLimit(
            requests_per_minute=row["requests_per_minute"],
            burst_capacity=row["burst_capacity"],
        )

    def set_rate_limit(self, key_id: str, limit: ApiKeyRateLimit | None) -> bool:
        with self._engine.begin() as connection:
            active_key = connection.execute(
                select(_API_KEYS.c.key_id)
                .where(
                    _API_KEYS.c.key_id == key_id,
                    _API_KEYS.c.revoked_at.is_(None),
                )
                .with_for_update()
            ).first()
            if active_key is None:
                return False
            if limit is None:
                connection.execute(
                    delete(_API_KEY_RATE_LIMITS).where(_API_KEY_RATE_LIMITS.c.key_id == key_id)
                )
                return True
            updated_at = datetime.now(UTC)
            result = connection.execute(
                update(_API_KEY_RATE_LIMITS)
                .where(_API_KEY_RATE_LIMITS.c.key_id == key_id)
                .values(
                    requests_per_minute=limit.requests_per_minute,
                    burst_capacity=limit.burst_capacity,
                    updated_at=updated_at,
                )
            )
            if result.rowcount == 0:
                connection.execute(
                    insert(_API_KEY_RATE_LIMITS).values(
                        key_id=key_id,
                        requests_per_minute=limit.requests_per_minute,
                        burst_capacity=limit.burst_capacity,
                        updated_at=updated_at,
                    )
                )
        return True

    def get_shared_inference(self) -> bool | None:
        """Read the shared-inference kill-switch state.

        Returns True only when an administrator explicitly enabled it, False
        when explicitly disabled, and None when no valid record exists.
        Callers treat anything but True as disabled (fail closed).
        """
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(_SHARED_INFERENCE).where(_SHARED_INFERENCE.c.id == "shared")
                )
                .mappings()
                .first()
            )
        if row is None:
            return None
        value = row["enabled"]
        return value if isinstance(value, bool) else None

    def set_shared_inference(self, enabled: bool, actor: str) -> None:
        """Upsert the kill-switch state with audit metadata (no secrets)."""
        now = datetime.now(UTC)
        with self._engine.begin() as connection:
            result = connection.execute(
                update(_SHARED_INFERENCE)
                .where(_SHARED_INFERENCE.c.id == "shared")
                .values(enabled=enabled, updated_at=now, updated_by=actor[:128])
            )
            if result.rowcount == 0:
                connection.execute(
                    insert(_SHARED_INFERENCE).values(
                        id="shared",
                        enabled=enabled,
                        updated_at=now,
                        updated_by=actor[:128],
                    )
                )

    def shared_inference_status(self) -> dict[str, Any]:
        """Safe status snapshot for the admin endpoint (no secrets)."""
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(_SHARED_INFERENCE).where(_SHARED_INFERENCE.c.id == "shared")
                )
                .mappings()
                .first()
            )
        if row is None:
            return {"enabled": False, "configured": False, "updated_at": None, "updated_by": None}
        value = row["enabled"]
        return {
            "enabled": value is True,
            "configured": isinstance(value, bool),
            "updated_at": row["updated_at"],
            "updated_by": row["updated_by"],
        }

    def get_budget(self, key_id: str) -> ApiKeyBudget | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(_API_KEY_BUDGETS).where(_API_KEY_BUDGETS.c.key_id == key_id)
                )
                .mappings()
                .first()
            )
        if row is None:
            return None
        return ApiKeyBudget(
            daily_tokens=row["daily_tokens"],
            monthly_tokens=row["monthly_tokens"],
            daily_cost_usd=row["daily_cost_usd"],
            monthly_cost_usd=row["monthly_cost_usd"],
        )

    def set_budget(self, key_id: str, budget: ApiKeyBudget | None) -> bool:
        with self._engine.begin() as connection:
            active = connection.execute(
                select(_API_KEYS.c.key_id)
                .where(_API_KEYS.c.key_id == key_id, _API_KEYS.c.revoked_at.is_(None))
                .with_for_update()
            ).first()
            if active is None:
                return False
            if budget is None:
                connection.execute(
                    delete(_API_KEY_BUDGETS).where(_API_KEY_BUDGETS.c.key_id == key_id)
                )
                return True
            values = {
                "daily_tokens": budget.daily_tokens,
                "monthly_tokens": budget.monthly_tokens,
                "daily_cost_usd": budget.daily_cost_usd,
                "monthly_cost_usd": budget.monthly_cost_usd,
                "updated_at": datetime.now(UTC),
            }
            result = connection.execute(
                update(_API_KEY_BUDGETS).where(_API_KEY_BUDGETS.c.key_id == key_id).values(**values)
            )
            if result.rowcount == 0:
                connection.execute(insert(_API_KEY_BUDGETS).values(key_id=key_id, **values))
        return True

    def get_budget_usage(self, key_id: str, now: datetime) -> dict[str, dict[str, Any]]:
        utc_now = now.astimezone(UTC)
        windows = {
            "daily": datetime(utc_now.year, utc_now.month, utc_now.day, tzinfo=UTC),
            "monthly": datetime(utc_now.year, utc_now.month, 1, tzinfo=UTC),
        }
        result: dict[str, dict[str, Any]] = {}
        with self._engine.connect() as connection:
            for kind, start in windows.items():
                row = connection.execute(
                    select(
                        func.coalesce(func.sum(_BUDGET_RESERVATIONS.c.accounted_tokens), 0),
                        func.coalesce(func.sum(_BUDGET_RESERVATIONS.c.accounted_cost_usd), 0),
                    ).where(
                        _BUDGET_RESERVATIONS.c.key_id == key_id,
                        _BUDGET_RESERVATIONS.c.window_kind == kind,
                        _BUDGET_RESERVATIONS.c.window_start == start,
                    )
                ).one()
                result[kind] = {"tokens": row[0], "cost_usd": row[1]}
        return result

    def reserve_budget(
        self,
        key_id: str,
        request_id: str,
        estimated_tokens: int,
        estimated_cost_usd: Decimal | None,
        now: datetime,
    ) -> str | None:
        """Atomically reserve one logical request against configured UTC windows."""
        with self._engine.begin() as connection:
            budget_row = (
                connection.execute(
                    select(_API_KEY_BUDGETS)
                    .where(_API_KEY_BUDGETS.c.key_id == key_id)
                    .with_for_update()
                )
                .mappings()
                .first()
            )
            if budget_row is None:
                return "budget_changed"
            windows = []
            utc_now = now.astimezone(UTC)
            windows.append(
                ("daily", datetime(utc_now.year, utc_now.month, utc_now.day, tzinfo=UTC))
            )
            windows.append(("monthly", datetime(utc_now.year, utc_now.month, 1, tzinfo=UTC)))
            pending_rows: list[dict[str, Any]] = []
            for kind, start in windows:
                token_limit = budget_row[f"{kind}_tokens"]
                cost_limit = budget_row[f"{kind}_cost_usd"]
                if token_limit is None and cost_limit is None:
                    continue
                if cost_limit is not None and estimated_cost_usd is None:
                    return f"{kind}_pricing_unknown"
                totals = connection.execute(
                    select(
                        func.coalesce(func.sum(_BUDGET_RESERVATIONS.c.accounted_tokens), 0),
                        func.coalesce(func.sum(_BUDGET_RESERVATIONS.c.accounted_cost_usd), 0),
                    ).where(
                        _BUDGET_RESERVATIONS.c.key_id == key_id,
                        _BUDGET_RESERVATIONS.c.window_kind == kind,
                        _BUDGET_RESERVATIONS.c.window_start == start,
                    )
                ).one()
                if token_limit is not None and totals[0] + estimated_tokens > token_limit:
                    return f"{kind}_tokens_exceeded"
                if cost_limit is not None and totals[1] + estimated_cost_usd > cost_limit:
                    return f"{kind}_cost_exceeded"
                pending_rows.append(
                    dict(
                        request_id=request_id,
                        key_id=key_id,
                        window_kind=kind,
                        window_start=start,
                        reserved_tokens=estimated_tokens,
                        accounted_tokens=estimated_tokens,
                        estimated_cost_usd=estimated_cost_usd,
                        accounted_cost_usd=estimated_cost_usd,
                        created_at=now,
                    )
                )
            if pending_rows:
                connection.execute(insert(_BUDGET_RESERVATIONS), pending_rows)
        return None

    def reconcile_budget(
        self,
        key_id: str,
        request_id: str,
        actual_tokens: int | None,
        actual_cost_usd: Decimal | None,
    ) -> None:
        with self._engine.begin() as connection:
            rows = (
                connection.execute(
                    select(_BUDGET_RESERVATIONS).where(
                        _BUDGET_RESERVATIONS.c.key_id == key_id,
                        _BUDGET_RESERVATIONS.c.request_id == request_id,
                    )
                )
                .mappings()
                .all()
            )
            for row in rows:
                values: dict[str, Any] = {}
                if actual_tokens is not None:
                    values["accounted_tokens"] = actual_tokens
                if actual_cost_usd is not None:
                    values["accounted_cost_usd"] = actual_cost_usd
                if values:
                    connection.execute(
                        update(_BUDGET_RESERVATIONS)
                        .where(
                            _BUDGET_RESERVATIONS.c.key_id == key_id,
                            _BUDGET_RESERVATIONS.c.request_id == request_id,
                            _BUDGET_RESERVATIONS.c.window_kind == row["window_kind"],
                            _BUDGET_RESERVATIONS.c.window_start == row["window_start"],
                        )
                        .values(**values)
                    )

    def release_budget(self, key_id: str, request_id: str) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                delete(_BUDGET_RESERVATIONS).where(
                    _BUDGET_RESERVATIONS.c.key_id == key_id,
                    _BUDGET_RESERVATIONS.c.request_id == request_id,
                )
            )

    def check_and_reserve_quota(
        self,
        user_id: str,
        request_id: str,
        estimate: int,
        window_start: datetime,
        quota: int,
    ) -> bool:
        """Atomically verify allowance and reserve estimate for one request.

        Single transaction: upsert the day aggregate, lock it, deny when
        consumed + reserved + estimate exceeds the quota, otherwise bump the
        reservation and record this request. Returns True when admitted.
        A repeated call with the same ``request_id`` is a no-op success
        (already counted), so retries of the admission itself cannot
        double-charge. Non-positive estimates are rejected by the caller;
        a non-positive estimate here admits nothing and reserves nothing.
        """
        if estimate < 1 or quota < 1:
            return False
        now = datetime.now(UTC)
        with self._engine.begin() as connection:
            # Portable upsert: the savepoint keeps the outer transaction
            # alive on PostgreSQL when the row already exists (a bare failing
            # INSERT would abort it); SQLite takes the same path.
            try:
                with connection.begin_nested():
                    connection.execute(
                        insert(_QUOTA_WINDOWS).values(
                            user_id=user_id,
                            window_start=window_start,
                            reserved_tokens=0,
                            consumed_tokens=0,
                            updated_at=now,
                        )
                    )
            except IntegrityError:
                pass
            window = (
                connection.execute(
                    select(_QUOTA_WINDOWS)
                    .where(
                        _QUOTA_WINDOWS.c.user_id == user_id,
                        _QUOTA_WINDOWS.c.window_start == window_start,
                    )
                    .with_for_update()
                )
                .mappings()
                .one()
            )
            existing = connection.execute(
                select(_QUOTA_RESERVATIONS.c.status).where(
                    _QUOTA_RESERVATIONS.c.user_id == user_id,
                    _QUOTA_RESERVATIONS.c.request_id == request_id,
                )
            ).first()
            if existing is not None:
                # Same logical request admitted before: no-op success so a
                # retry of the admission itself cannot double-charge.
                return True
            if window["reserved_tokens"] + window["consumed_tokens"] + estimate > quota:
                return False
            connection.execute(
                update(_QUOTA_WINDOWS)
                .where(
                    _QUOTA_WINDOWS.c.user_id == user_id,
                    _QUOTA_WINDOWS.c.window_start == window_start,
                )
                .values(
                    reserved_tokens=_QUOTA_WINDOWS.c.reserved_tokens + estimate,
                    updated_at=now,
                )
            )
            connection.execute(
                insert(_QUOTA_RESERVATIONS).values(
                    user_id=user_id,
                    request_id=request_id,
                    window_start=window_start,
                    estimated_tokens=estimate,
                    status="reserved",
                    created_at=now,
                )
            )
            return True

    def settle_quota(
        self, user_id: str, request_id: str, actual_tokens: int | None
    ) -> None:
        """Settle one reservation exactly once (idempotent).

        With actuals, consumed grows by actuals and the estimate is released
        from reserved. Without actuals (unknown provider usage), the estimate
        moves reserved → consumed so the capacity stays conservatively held —
        never silently freed, never assumed zero.
        """
        with self._engine.begin() as connection:
            row = (
                connection.execute(
                    select(_QUOTA_RESERVATIONS).where(
                        _QUOTA_RESERVATIONS.c.user_id == user_id,
                        _QUOTA_RESERVATIONS.c.request_id == request_id,
                        _QUOTA_RESERVATIONS.c.status == "reserved",
                    )
                    .with_for_update()
                )
                .mappings()
                .first()
            )
            if row is None:
                return
            estimate = row["estimated_tokens"]
            settled = actual_tokens if actual_tokens is not None else estimate
            connection.execute(
                update(_QUOTA_WINDOWS)
                .where(
                    _QUOTA_WINDOWS.c.user_id == user_id,
                    _QUOTA_WINDOWS.c.window_start == row["window_start"],
                )
                .values(
                    reserved_tokens=_QUOTA_WINDOWS.c.reserved_tokens - estimate,
                    consumed_tokens=_QUOTA_WINDOWS.c.consumed_tokens + settled,
                    updated_at=datetime.now(UTC),
                )
            )
            connection.execute(
                update(_QUOTA_RESERVATIONS)
                .where(
                    _QUOTA_RESERVATIONS.c.user_id == user_id,
                    _QUOTA_RESERVATIONS.c.request_id == request_id,
                    _QUOTA_RESERVATIONS.c.status == "reserved",
                )
                .values(status="settled")
            )

    def release_quota(self, user_id: str, request_id: str) -> None:
        """Release a reservation that never executed (idempotent).

        Only ``reserved`` rows convert; settled rows are never touched, so a
        release racing a settle cannot erase consumed usage.
        """
        with self._engine.begin() as connection:
            row = (
                connection.execute(
                    select(_QUOTA_RESERVATIONS).where(
                        _QUOTA_RESERVATIONS.c.user_id == user_id,
                        _QUOTA_RESERVATIONS.c.request_id == request_id,
                        _QUOTA_RESERVATIONS.c.status == "reserved",
                    )
                    .with_for_update()
                )
                .mappings()
                .first()
            )
            if row is None:
                return
            connection.execute(
                update(_QUOTA_WINDOWS)
                .where(
                    _QUOTA_WINDOWS.c.user_id == user_id,
                    _QUOTA_WINDOWS.c.window_start == row["window_start"],
                )
                .values(
                    reserved_tokens=_QUOTA_WINDOWS.c.reserved_tokens - row["estimated_tokens"],
                    updated_at=datetime.now(UTC),
                )
            )
            connection.execute(
                update(_QUOTA_RESERVATIONS)
                .where(
                    _QUOTA_RESERVATIONS.c.user_id == user_id,
                    _QUOTA_RESERVATIONS.c.request_id == request_id,
                    _QUOTA_RESERVATIONS.c.status == "reserved",
                )
                .values(status="released")
            )

    def get_quota_usage(self, user_id: str, window_start: datetime) -> dict[str, int]:
        """Current reserved/consumed totals for one user-day (tests/admin)."""
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(
                        _QUOTA_WINDOWS.c.reserved_tokens,
                        _QUOTA_WINDOWS.c.consumed_tokens,
                    ).where(
                        _QUOTA_WINDOWS.c.user_id == user_id,
                        _QUOTA_WINDOWS.c.window_start == window_start,
                    )
                )
                .mappings()
                .first()
            )
        if row is None:
            return {"reserved_tokens": 0, "consumed_tokens": 0}
        return {
            "reserved_tokens": row["reserved_tokens"],
            "consumed_tokens": row["consumed_tokens"],
        }

    def create_usage_event(self, event: RequestUsageEvent) -> None:
        with self._engine.begin() as connection:
            connection.execute(insert(_REQUEST_USAGE).values(**_usage_values(event)))

    def append_pre_routing_feature_snapshot(
        self, request_id: str, snapshot: Mapping[str, Any]
    ) -> bool:
        with self._engine.begin() as connection:
            row = (
                connection.execute(
                    select(
                        _REQUEST_USAGE.c.final_status,
                        _REQUEST_USAGE.c.feature_schema_version,
                        _REQUEST_USAGE.c.pre_routing_features,
                    )
                    .where(_REQUEST_USAGE.c.request_id == request_id)
                    .with_for_update()
                )
                .mappings()
                .first()
            )
            if row is None or row["final_status"] is not None:
                return False
            features = list(row["pre_routing_features"] or [])
            schema_version = snapshot.get("feature_schema_version")
            validate_pre_routing_feature_snapshot(
                request_id,
                len(features) + 1,
                snapshot,
                row["feature_schema_version"],
            )
            result = connection.execute(
                update(_REQUEST_USAGE)
                .where(
                    _REQUEST_USAGE.c.request_id == request_id,
                    _REQUEST_USAGE.c.final_status.is_(None),
                )
                .values(
                    pre_routing_features=features + [dict(snapshot)],
                    feature_schema_version=schema_version,
                )
            )
            return result.rowcount == 1

    def finalize_usage_event(self, event: RequestUsageEvent) -> bool:
        validate_usage_event_finalization(event)
        values = _usage_values(event)
        values.pop("request_id")
        values.pop("key_id")
        values.pop("project_id")
        values.pop("created_at")
        with self._engine.begin() as connection:
            result = connection.execute(
                update(_REQUEST_USAGE)
                .where(
                    _REQUEST_USAGE.c.request_id == event.request_id,
                    _REQUEST_USAGE.c.final_status.is_(None),
                )
                .values(**values)
            )
        return result.rowcount == 1

    def list_usage_events(
        self, key_id: str, *, limit: int, offset: int
    ) -> tuple[list[RequestUsageEvent], int]:
        with self._engine.connect() as connection:
            total = connection.execute(
                select(func.count())
                .select_from(_REQUEST_USAGE)
                .where(_REQUEST_USAGE.c.key_id == key_id)
            ).scalar_one()
            rows = (
                connection.execute(
                    select(_REQUEST_USAGE)
                    .where(_REQUEST_USAGE.c.key_id == key_id)
                    .order_by(
                        _REQUEST_USAGE.c.created_at.desc(), _REQUEST_USAGE.c.request_id.desc()
                    )
                    .limit(limit)
                    .offset(offset)
                )
                .mappings()
                .all()
            )
        return [_usage_from_row(row) for row in rows], int(total)

    def close(self) -> None:
        self._engine.dispose()


def _record_values(record: ApiKeyRecord) -> dict[str, Any]:
    return {
        "key_id": record.key_id,
        "key_hash": record.key_hash,
        "project_id": record.project_id,
        "name": record.name,
        "created_at": record.created_at,
        "revoked_at": record.revoked_at,
        "metadata_json": record.metadata or {},
    }


def _usage_values(event: RequestUsageEvent) -> dict[str, Any]:
    return {
        "request_id": event.request_id,
        "key_id": event.key_id,
        "project_id": event.project_id,
        "created_at": event.created_at,
        "requested_alias": event.requested_alias,
        "final_deployment": event.final_deployment,
        "final_status": event.final_status,
        "prompt_tokens": event.prompt_tokens,
        "completion_tokens": event.completion_tokens,
        "total_tokens": event.total_tokens,
        "failure_category": event.failure_category,
        "estimated_input_tokens": event.estimated_input_tokens,
        "reserved_tokens": event.reserved_tokens,
        "estimated_cost_usd": event.estimated_cost_usd,
        "actual_cost_usd": event.actual_cost_usd,
        "routing_decisions": list(event.routing_decisions),
        "feature_schema_version": event.feature_schema_version,
        "pre_routing_features": list(event.pre_routing_features),
        "usage_source": event.usage_source,
    }


def _usage_from_row(row: Any) -> RequestUsageEvent:
    return RequestUsageEvent(
        request_id=row["request_id"],
        key_id=row["key_id"],
        project_id=row["project_id"],
        created_at=row["created_at"],
        requested_alias=row["requested_alias"],
        final_deployment=row["final_deployment"],
        final_status=row["final_status"],
        prompt_tokens=row["prompt_tokens"],
        completion_tokens=row["completion_tokens"],
        total_tokens=row["total_tokens"],
        failure_category=row["failure_category"],
        estimated_input_tokens=row["estimated_input_tokens"],
        reserved_tokens=row["reserved_tokens"],
        estimated_cost_usd=row["estimated_cost_usd"],
        actual_cost_usd=row["actual_cost_usd"],
        routing_decisions=tuple(row.get("routing_decisions") or ()),
        feature_schema_version=row.get("feature_schema_version"),
        pre_routing_features=tuple(row.get("pre_routing_features") or ()),
        # Legacy rows predate the column (NULL): they stay "unknown".
        # Attribution is never backfilled or invented.
        usage_source=row.get("usage_source") or "unknown",
    )


def _from_row(row: Any) -> ApiKeyRecord:
    return ApiKeyRecord(
        key_id=row["key_id"],
        key_hash=row["key_hash"],
        project_id=row["project_id"],
        name=row["name"],
        created_at=row["created_at"],
        revoked_at=row["revoked_at"],
        metadata=row["metadata_json"] or {},
    )
