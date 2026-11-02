"""Focused tests for read-only schema validators (Stage 0)."""

from __future__ import annotations

from sqlalchemy import create_engine, inspect, text

from sabiroute.security.store import (
    check_quota_schema,
    check_sabichat_schema,
    check_schema,
    check_shared_inference_schema,
)


def _create_core_tables(engine, *, missing_col=None, missing_table=None):
    tables = {
        "sabiroute_api_keys": "CREATE TABLE sabiroute_api_keys (key_id VARCHAR(24) PRIMARY KEY, key_hash VARCHAR(64), project_id VARCHAR(128), name VARCHAR(128), created_at DATETIME, revoked_at DATETIME)",  # noqa: E501
        "sabiroute_api_key_budgets": "CREATE TABLE sabiroute_api_key_budgets (key_id VARCHAR(24) PRIMARY KEY, updated_at DATETIME)",  # noqa: E501
        "sabiroute_budget_reservations": "CREATE TABLE sabiroute_budget_reservations (key_id VARCHAR(24), request_id VARCHAR(36), window_kind VARCHAR(8), window_start DATETIME, reserved_tokens INTEGER, accounted_tokens INTEGER, created_at DATETIME, PRIMARY KEY(key_id,request_id,window_kind,window_start))",  # noqa: E501
        "sabiroute_schema_versions": "CREATE TABLE sabiroute_schema_versions (revision VARCHAR(64) PRIMARY KEY, description VARCHAR(256), applied_at DATETIME)",  # noqa: E501
        "sabiroute_request_usage": "CREATE TABLE sabiroute_request_usage (request_id VARCHAR(36) PRIMARY KEY, key_id VARCHAR(24), project_id VARCHAR(128), created_at DATETIME, final_status INTEGER)",  # noqa: E501
        # Required by the accounting contract (F2): budget/quota settlement
        # writes lineage rows, so a database without this table is
        # schema-incompatible. It is part of the Core inventory.
        "sabiroute_accounting_lineages": "CREATE TABLE sabiroute_accounting_lineages (lineage_id VARCHAR(36) PRIMARY KEY, created_at DATETIME, superseded_by VARCHAR(36), status VARCHAR(16), archived_at DATETIME)",  # noqa: E501
    }
    with engine.begin() as conn:
        for name, ddl in tables.items():
            if missing_table == name:
                continue
            if missing_col and missing_col[0] == name:
                token = missing_col[1]
                ddl = ddl.replace(", " + token, "").replace(token + ", ", "")
            conn.execute(text(ddl))


def test_check_schema_valid():
    eng = create_engine("sqlite:///:memory:")
    _create_core_tables(eng)
    check_schema(eng)  # no exception
    eng.dispose()


def test_check_schema_missing_table():
    eng = create_engine("sqlite:///:memory:")
    _create_core_tables(eng, missing_table="sabiroute_schema_versions")
    try:
        check_schema(eng)
        raise AssertionError("expected ValueError")
    except ValueError as e:
        assert "missing tables" in str(e)
        assert "sabiroute_schema_versions" in str(e)
    eng.dispose()


def test_check_schema_missing_column():
    eng = create_engine("sqlite:///:memory:")
    _create_core_tables(eng, missing_col=("sabiroute_api_keys", "revoked_at DATETIME"))
    try:
        check_schema(eng)
        raise AssertionError("expected ValueError")
    except ValueError as e:
        assert "missing columns" in str(e)
        assert "revoked_at" in str(e)
    eng.dispose()


def test_check_schema_missing_accounting_lineages_fails_closed():
    """F2: every other core table present, only the lineage table absent."""
    eng = create_engine("sqlite:///:memory:")
    _create_core_tables(eng, missing_table="sabiroute_accounting_lineages")
    present = set(inspect(eng).get_table_names())
    # The state is genuinely "everything except lineages", not "empty".
    assert "sabiroute_api_keys" in present
    assert "sabiroute_accounting_lineages" not in present
    try:
        check_schema(eng)
        raise AssertionError("expected ValueError")
    except ValueError as e:
        assert "missing tables" in str(e)
        assert "sabiroute_accounting_lineages" in str(e)
    eng.dispose()


def test_check_schema_missing_accounting_lineage_column_fails_closed():
    """The required-column contract for the lineage table is live too."""
    eng = create_engine("sqlite:///:memory:")
    _create_core_tables(eng)
    with eng.begin() as conn:
        conn.execute(text("DROP TABLE sabiroute_accounting_lineages"))
        conn.execute(
            text(
                "CREATE TABLE sabiroute_accounting_lineages "
                "(lineage_id VARCHAR(36) PRIMARY KEY, created_at DATETIME)"
            )
        )
    try:
        check_schema(eng)
        raise AssertionError("expected ValueError")
    except ValueError as e:
        assert "missing columns" in str(e)
        assert "status" in str(e)
    eng.dispose()


def test_check_schema_readonly():
    eng = create_engine("sqlite:///:memory:")
    _create_core_tables(eng, missing_col=("sabiroute_api_keys", "revoked_at DATETIME"))
    with eng.connect():
        before = {t: {col["name"] for col in inspect(eng).get_columns(t)} for t in inspect(eng).get_table_names()}  # noqa: E501
    try:
        check_schema(eng)
    except ValueError:
        pass
    with eng.connect():
        after = {t: {col["name"] for col in inspect(eng).get_columns(t)} for t in inspect(eng).get_table_names()}  # noqa: E501
    assert before == after
    eng.dispose()


def _create_sabichat_tables(engine, *, missing_table=None, missing_col=None):
    tables = {
        "sabichat_users": "CREATE TABLE sabichat_users (user_id VARCHAR(36) PRIMARY KEY, email VARCHAR(320), password_hash VARCHAR(256), created_at DATETIME, disabled_at DATETIME)",  # noqa: E501
        "sabichat_sessions": "CREATE TABLE sabichat_sessions (session_id VARCHAR(36) PRIMARY KEY, user_id VARCHAR(36), token_hash VARCHAR(64), expires_at DATETIME, revoked_at DATETIME)",  # noqa: E501
        "sabichat_conversations": "CREATE TABLE sabichat_conversations (conversation_id VARCHAR(36) PRIMARY KEY, user_id VARCHAR(36), title VARCHAR(120), created_at DATETIME, updated_at DATETIME)",  # noqa: E501
        "sabichat_messages": "CREATE TABLE sabichat_messages (message_id VARCHAR(36) PRIMARY KEY, conversation_id VARCHAR(36), created_at DATETIME)",  # noqa: E501
    }
    with engine.begin() as conn:
        for name, ddl in tables.items():
            if missing_table == name:
                continue
            if missing_col and missing_col[0] == name:
                token = missing_col[1]
                ddl = ddl.replace(", " + token, "").replace(token + ", ", "")
            conn.execute(text(ddl))


def test_check_sabichat_valid():
    eng = create_engine("sqlite:///:memory:")
    _create_sabichat_tables(eng)
    check_sabichat_schema(eng)
    eng.dispose()


def test_check_sabichat_missing_table():
    eng = create_engine("sqlite:///:memory:")
    _create_sabichat_tables(eng, missing_table="sabichat_messages")
    try:
        check_sabichat_schema(eng)
        raise AssertionError("expected ValueError")
    except ValueError as e:
        assert "missing tables" in str(e)
    eng.dispose()


def test_check_sabichat_missing_column():
    eng = create_engine("sqlite:///:memory:")
    _create_sabichat_tables(eng, missing_col=("sabichat_users", "password_hash VARCHAR(256)"))
    try:
        check_sabichat_schema(eng)
        raise AssertionError("expected ValueError")
    except ValueError as e:
        assert "missing columns" in str(e)
        assert "password_hash" in str(e)
    eng.dispose()


def test_check_sabichat_readonly():
    eng = create_engine("sqlite:///:memory:")
    _create_sabichat_tables(eng, missing_col=("sabichat_users", "password_hash VARCHAR(256)"))
    before = {t: {col["name"] for col in inspect(eng).get_columns(t)} for t in inspect(eng).get_table_names()}  # noqa: E501
    try:
        check_sabichat_schema(eng)
    except ValueError:
        pass
    after = {t: {col["name"] for col in inspect(eng).get_columns(t)} for t in inspect(eng).get_table_names()}  # noqa: E501
    assert before == after
    eng.dispose()


def test_check_quota_valid():
    eng = create_engine("sqlite:///:memory:")
    with eng.begin() as conn:
        conn.execute(text("CREATE TABLE sabichat_quota_windows (user_id VARCHAR(36), window_start DATETIME, reserved_tokens INTEGER, consumed_tokens INTEGER, updated_at DATETIME, PRIMARY KEY(user_id, window_start))"))  # noqa: E501
        conn.execute(text("CREATE TABLE sabichat_quota_reservations (user_id VARCHAR(36), request_id VARCHAR(36), window_start DATETIME, estimated_tokens INTEGER, status VARCHAR(16), created_at DATETIME, PRIMARY KEY(user_id, request_id))"))  # noqa: E501
    check_quota_schema(eng)
    eng.dispose()


def test_check_quota_missing_table():
    eng = create_engine("sqlite:///:memory:")
    with eng.begin() as conn:
        conn.execute(text("CREATE TABLE sabichat_quota_windows (user_id VARCHAR(36), window_start DATETIME, PRIMARY KEY(user_id, window_start))"))  # noqa: E501
    try:
        check_quota_schema(eng)
        raise AssertionError("expected ValueError")
    except ValueError as e:
        assert "missing tables" in str(e)
    eng.dispose()


def test_check_shared_inference_valid():
    eng = create_engine("sqlite:///:memory:")
    with eng.begin() as conn:
        conn.execute(text("CREATE TABLE sabiroute_shared_inference_policy (id VARCHAR(16) PRIMARY KEY, enabled BOOLEAN, updated_at DATETIME, updated_by VARCHAR(128))"))  # noqa: E501
    check_shared_inference_schema(eng)
    eng.dispose()


def test_check_shared_inference_missing_table():
    eng = create_engine("sqlite:///:memory:")
    try:
        check_shared_inference_schema(eng)
        raise AssertionError("expected ValueError")
    except ValueError as e:
        assert "missing table" in str(e)
    eng.dispose()


def test_od3_core_inventory_matches_contract():
    from sabiroute.security.store import (
        core_table_names,
        sabichat_product_table_names,
    )

    assert core_table_names() == {
        "sabiroute_api_keys",
        "sabiroute_api_key_rate_limits",
        "sabiroute_request_usage",
        "sabiroute_api_key_budgets",
        "sabiroute_budget_reservations",
        "sabiroute_schema_versions",
        "sabiroute_shared_inference_policy",
        "sabichat_quota_windows",
        "sabichat_quota_reservations",
        "sabiroute_accounting_lineages",
    }
    assert sabichat_product_table_names() == {
        "sabichat_users",
        "sabichat_sessions",
        "sabichat_conversations",
        "sabichat_messages",
    }
    # Ownership is by declared inventory, not by prefix: the two quota
    # tables are Core-owned despite the sabichat_ prefix.
    assert "sabichat_quota_windows" in core_table_names()
    assert "sabichat_quota_reservations" in core_table_names()
    assert core_table_names().isdisjoint(sabichat_product_table_names())


def test_od3_core_validation_independent_of_product_tables():
    from sabiroute.security.store import check_schema

    eng = create_engine("sqlite:///:memory:")
    _create_core_tables(eng)
    # No SabiChat product tables present: Core validation still passes.
    check_schema(eng)
    eng.dispose()


def test_od3_sabichat_validation_independent_of_core_tables():
    from sabiroute.security.store import check_sabichat_schema

    eng = create_engine("sqlite:///:memory:")
    _create_sabichat_tables(eng)
    # No Core tables present: SabiChat validation still passes.
    check_sabichat_schema(eng)
    eng.dispose()
