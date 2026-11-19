"""R3 — secret-leakage regression suite (owner decision D-R3-3).

D-R3-3: secrets must not appear in logs, telemetry, error messages, or audit
output. This file proves that property for the paths an attacker or an operator
actually observes:

* client-facing error bodies (non-streaming and streaming),
* the administrative telemetry snapshots (``/admin/errors``, ``/admin/usage``,
  ``/admin/metrics``),
* application logging captured through ``caplog``.

It also pins two authentication guardrails that keep the admin boundary
separate: the admin secret may not be the internal LiteLLM master key, and may
not be a client-key-shaped value.

Labels: VERIFIED BY RUNTIME (fresh local run, stub provider, no real calls).
No live credential is used anywhere; the canary is a synthetic literal.
"""

from __future__ import annotations

import logging
from typing import Any

import pytest
from conftest import InMemoryApiKeyStore, make_config, provision_test_key
from fastapi.testclient import TestClient

from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app
from sabiroute.providers.litellm_client import LiteLLMClientError

MESSAGES = [{"role": "user", "content": "hello"}]

#: Synthetic credential. If this string appears in a response, log, or admin
#: snapshot, a real provider key would have leaked by the same path.
CANARY = "sk-R3-LOG-CANARY-4d1c88"

ADMIN_SECRET = "r3-admin-secret-not-a-real-key"


class LeakyProviderStub:
    """Provider double that echoes a credential inside its error text.

    This models the worst realistic case: an upstream that reflects the
    credential it was given back in a 401 body.
    """

    def __init__(self, *, stream: bool = False) -> None:
        self.calls: list[str] = []
        self.stream = stream

    async def chat_completion(
        self, decision: Any, messages: Any, **extra: Any
    ) -> dict[str, Any]:
        self.calls.append(decision.deployment)
        raise LiteLLMClientError(
            f"LiteLLM gateway returned HTTP 401: Incorrect API key provided: {CANARY}",
            status_code=401,
            response_body={"error": {"message": f"Incorrect API key provided: {CANARY}"}},
        )

    async def start_chat_completion_stream(
        self, decision: Any, messages: Any, **extra: Any
    ) -> Any:
        self.calls.append(decision.deployment)
        raise LiteLLMClientError(
            f"LiteLLM gateway returned HTTP 401: Incorrect API key provided: {CANARY}",
            status_code=401,
            response_body={"error": {"message": f"Incorrect API key provided: {CANARY}"}},
        )


class OkProviderStub:
    """Provider double that succeeds, so accounting finalization actually runs."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    async def chat_completion(
        self, decision: Any, messages: Any, **extra: Any
    ) -> dict[str, Any]:
        self.calls.append(decision.deployment)
        return {
            "id": "chatcmpl-ok",
            "model": decision.deployment,
            "choices": [{"message": {"role": "assistant", "content": "ok"}}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2},
        }

    async def start_chat_completion_stream(
        self, decision: Any, messages: Any, **extra: Any
    ) -> Any:
        self.calls.append(decision.deployment)
        raise AssertionError("stream stub not used here")


def make_client(*, stub: Any | None = None) -> tuple[TestClient, Any, Any]:
    stub = stub if stub is not None else LeakyProviderStub()
    state = build_gateway_state(
        config=make_config(), client=stub, key_store=InMemoryApiKeyStore()
    )
    key = provision_test_key(state)
    client = TestClient(
        create_app(state=state), headers={"Authorization": f"Bearer {key}"}
    )
    return client, state, stub


def _admin_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {ADMIN_SECRET}"}


@pytest.fixture(autouse=True)
def _admin_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SABIROUTE_ADMIN_KEY", ADMIN_SECRET)


def test_provider_error_body_does_not_return_credential() -> None:
    """A provider echoing a key must not reach the client."""
    client, state, stub = make_client()
    resp = client.post(
        "/v1/chat/completions", json={"model": "fast", "messages": MESSAGES}
    )
    assert resp.status_code == 502
    assert stub.calls, "provider should have been attempted"
    assert CANARY not in resp.text
    assert "Incorrect API key" not in resp.text
    # The client learns the failure class, not the upstream detail.
    assert resp.json()["error"]["type"] == "sabiroute_upstream_error"


def test_provider_error_absent_from_admin_error_snapshot() -> None:
    client, state, stub = make_client()
    client.post("/v1/chat/completions", json={"model": "fast", "messages": MESSAGES})
    snap = client.get("/admin/errors", headers=_admin_headers())
    assert snap.status_code == 200
    assert CANARY not in snap.text
    assert "Incorrect API key" not in snap.text


def test_provider_error_stored_in_telemetry_is_redacted() -> None:
    """The endpoint exposes counts only, so assert on what is *stored*.

    ``/admin/errors`` returns ``counts()`` and never the message, which is why
    the endpoint-level test above cannot see this: the raw provider text sat in
    ``ErrorTracker.records[].message`` unmasked, one future debug endpoint away
    from being served. D-R3-3 covers telemetry and provider errors directly.
    """
    client, state, stub = make_client()
    client.post("/v1/chat/completions", json={"model": "fast", "messages": MESSAGES})

    records = state.errors.records
    assert records, "the provider failure was not recorded, so this proves nothing"
    stored = " | ".join(record.message for record in records)

    assert CANARY not in stored, "provider-echoed credential persisted in telemetry"
    # Redaction preserves surrounding prose so the record stays diagnosable;
    # the masked carrier being present proves the message really was stored
    # and that redaction — not an empty field — is what removed the canary.
    assert "sk-***" in stored


def test_provider_error_absent_from_application_logs(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """D-R3-3: application-controlled logging must not carry the raw secret."""
    caplog.set_level(logging.DEBUG)
    client, state, stub = make_client()
    client.post("/v1/chat/completions", json={"model": "fast", "messages": MESSAGES})
    assert CANARY not in caplog.text, "provider-echoed credential reached the logs"


def test_streaming_provider_failure_does_not_return_credential(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    client, state, stub = make_client(stub=LeakyProviderStub(stream=True))
    resp = client.post(
        "/v1/chat/completions", json={"model": "fast", "messages": MESSAGES, "stream": True}
    )
    assert CANARY not in resp.text
    assert CANARY not in caplog.text


def test_store_failure_does_not_return_credential() -> None:
    """A store exception whose text embeds a DSN secret stays internal."""
    client, state, stub = make_client()
    store = state.key_store

    def boom(_key_id: str) -> Any:
        raise RuntimeError(
            f"could not connect: postgresql://user:{CANARY}@db.internal:5432/sabiroute"
        )

    store.get_budget = boom  # type: ignore[method-assign]
    resp = client.post(
        "/v1/chat/completions", json={"model": "fast", "messages": MESSAGES}
    )
    assert resp.status_code == 503
    assert CANARY not in resp.text


def test_auth_store_failure_denies_typed_without_credential_or_provider_call(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """R3-S5 fail-closed + R3-S3 leakage, on the FIRST store read of the path.

    Authentication resolves the credential record before any other work. If
    that fault escapes, the client still gets no service — but it becomes an
    unhandled 500 whose full traceback the ASGI server logs, and a driver
    failure carries the DSN (password included) in its message. So this path
    must map the fault to the established typed 503, must not echo the secret,
    and must never reach the provider.
    """
    client, state, stub = make_client()

    def boom(_key_id: str) -> Any:
        raise RuntimeError(
            f"could not connect: postgresql://user:{CANARY}@db.internal:5432/sabiroute"
        )

    # authenticate_api_key() resolves the record through store.get(key_id).
    state.key_store.get = boom  # type: ignore[method-assign]

    with caplog.at_level(logging.INFO):
        resp = client.post(
            "/v1/chat/completions", json={"model": "fast", "messages": MESSAGES}
        )

    # Fail closed, in the shape the rest of the boundary already uses.
    assert resp.status_code == 503
    assert resp.json()["detail"]["error"]["type"] == "authentication_unavailable"
    # No credential material in the response or the logs.
    assert CANARY not in resp.text
    assert CANARY not in caplog.text
    # Authentication never succeeded, so no provider call was fabricated.
    assert stub.calls == []


def test_admin_snapshot_endpoints_carry_no_credential_material() -> None:
    """Telemetry snapshots expose aggregates, never credentials."""
    client, state, stub = make_client()
    client.post("/v1/chat/completions", json={"model": "fast", "messages": MESSAGES})
    for path in ("/admin/errors", "/admin/usage", "/admin/metrics", "/admin/latency"):
        resp = client.get(path, headers=_admin_headers())
        assert resp.status_code == 200, path
        assert CANARY not in resp.text, path
        assert "sk-" not in resp.text, f"{path} emitted credential-shaped text"


def test_issued_plaintext_absent_from_read_endpoints() -> None:
    """The one-time issuance response is the only place a plaintext key appears."""
    client, state, stub = make_client()
    created = client.post(
        "/admin/api-keys",
        json={"project_id": "p", "name": "k"},
        headers=_admin_headers(),
    )
    assert created.status_code == 201
    issued = created.json()
    plaintext = issued.get("api_key") or issued.get("key") or issued.get("plaintext")
    assert plaintext, f"issuance response shape changed: {sorted(issued)}"
    key_id = issued["id"]

    for path in (
        f"/admin/api-keys/{key_id}/usage",
        f"/admin/api-keys/{key_id}/budget",
        f"/admin/api-keys/{key_id}/rate-limit",
        "/admin/usage",
    ):
        resp = client.get(path, headers=_admin_headers())
        assert resp.status_code == 200, path
        assert plaintext not in resp.text, f"{path} returned the plaintext key"


def test_admin_secret_cannot_be_litellm_master_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The admin boundary must not collapse into the internal provider key."""
    monkeypatch.setenv("LITELLM_MASTER_KEY", CANARY)
    monkeypatch.setenv("SABIROUTE_ADMIN_KEY", CANARY)
    client, state, stub = make_client()
    resp = client.get("/admin/errors", headers={"Authorization": f"Bearer {CANARY}"})
    assert resp.status_code == 503
    assert resp.json()["detail"]["error"]["type"] == "authentication_unavailable"
    assert CANARY not in resp.text


def test_admin_secret_cannot_be_client_key_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A client-issued key shape may never satisfy the admin boundary."""
    shape = "sr_live_r3_canary_shape"
    monkeypatch.setenv("SABIROUTE_ADMIN_KEY", shape)
    client, state, stub = make_client()
    resp = client.get("/admin/errors", headers={"Authorization": f"Bearer {shape}"})
    assert resp.status_code == 503
    assert resp.json()["detail"]["error"]["type"] == "authentication_unavailable"
    assert shape not in resp.text


def test_client_key_cannot_reach_admin_endpoints() -> None:
    """A valid client credential is not an admin credential."""
    client, state, stub = make_client()
    resp = client.get("/admin/errors")  # client bearer, not admin
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Store-exception log hygiene (regression).
#
# The accounting finalizer logs the text of an exception raised by a store
# call (``logger.error("...: %s", exc)``). Store exceptions are exactly the
# class of error whose message can embed a connection URI, and a URI carries
# the password. The existing test above proves the *response* stays clean;
# these prove the *log* does too.
# ---------------------------------------------------------------------------

DSN_LEAK = f"postgresql://sabiroute:{CANARY}@db.internal:5432/sabiroute"


def _budgeted_client(monkeypatch: pytest.MonkeyPatch) -> tuple[TestClient, Any, Any]:
    """Client whose key has a budget, so finalization reconciles on success."""
    from sabiroute.security.keys import ApiKeyBudget

    client, state, stub = make_client(stub=OkProviderStub())
    store = state.key_store
    for record in store.records.values():
        store.set_budget(record.key_id, ApiKeyBudget(daily_tokens=1_000))
    assert store.budgets, "budget fixture was not applied"
    return client, state, stub


def test_store_exception_dsn_absent_from_logs_on_reconcile_failure(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A DSN-bearing store failure during reconciliation must not be logged raw."""
    caplog.set_level(logging.DEBUG)
    client, state, stub = _budgeted_client(monkeypatch)

    def boom(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError(f"could not connect: {DSN_LEAK}")

    state.key_store.reconcile_budget = boom  # type: ignore[method-assign]
    resp = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES, "max_tokens": 16},
    )
    assert stub.calls, "provider should have been attempted"
    # Explicit failure semantics, not silent success.
    assert resp.status_code == 503
    assert resp.json()["error"]["type"] == "budget_store_unavailable"
    # Neither the response nor the log may carry the credential.
    assert CANARY not in resp.text
    assert CANARY not in caplog.text, "store DSN credential reached the logs"


def test_store_exception_dsn_absent_from_logs_on_release_failure(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The pre-attempt release path must be equally clean."""
    caplog.set_level(logging.DEBUG)
    client, state, stub = _budgeted_client(monkeypatch)

    def boom(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError(f"could not connect: {DSN_LEAK}")

    state.key_store.release_budget = boom  # type: ignore[method-assign]
    # Reserve, then fail routing before any attempt: the exact path where
    # finish() releases the reservation (``release_budget=not attempted``).
    from sabiroute.routing.router import NoHealthyDeploymentError

    def no_route(*args: Any, **kwargs: Any) -> Any:
        raise NoHealthyDeploymentError("no healthy deployment")

    state.router.choose_deployment = no_route  # type: ignore[method-assign]
    resp = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES, "max_tokens": 16},
    )
    # Release failure is surfaced as an explicit store-unavailable, never as
    # a silent success or a provider-route outcome.
    assert resp.status_code == 503
    assert resp.json()["error"]["type"] == "budget_store_unavailable"
    assert stub.calls == [], "no provider attempt should have been made"
    assert CANARY not in resp.text
    assert CANARY not in caplog.text, "store DSN credential reached the logs"


# ---------------------------------------------------------------------------
# Redaction primitive (unit).
#
# The log sites above are only safe while ``redact_secrets`` keeps matching.
# A silently-broken pattern would leave every call site looking protected
# while writing raw credentials to disk, so the carriers are pinned here.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw, leaked, must_keep",
    [
        (
            "could not connect: postgresql://sabiroute:hunter2@db.internal:5432/x",
            "hunter2",
            ["postgresql://", "sabiroute:", "db.internal"],
        ),
        (
            "redis://default:s3cr3t-pass@cache.internal:6379/0 refused",
            "s3cr3t-pass",
            ["redis://", "cache.internal"],
        ),
        ("Authorization: Bearer abcdef0123456789abcdef", "abcdef0123456789abcdef", ["Bearer"]),
        ("upstream said sk-proj-ZZZZ9999 rejected", "ZZZZ9999", []),
        ("issued sr_live_abcdef0123456789 to project", "abcdef0123456789", []),
    ],
)
def test_redact_secrets_masks_carriers_but_keeps_diagnostics(
    raw: str, leaked: str, must_keep: list[str]
) -> None:
    from sabiroute.security.redaction import redact_secrets

    masked = redact_secrets(raw)
    assert leaked not in masked, f"redaction missed {leaked!r}"
    for fragment in must_keep:
        assert fragment in masked, f"redaction destroyed context {fragment!r}"


@pytest.mark.parametrize(
    ("raw", "canary", "expected"),
    [
        pytest.param(
            "could not connect: postgresql://f6_user:f6_uri_pw_9f2c@db.internal:5432/x",
            "f6_uri_pw_9f2c",
            "could not connect: postgresql://f6_user:***@db.internal:5432/x",
            id="uri-userinfo-password",
        ),
        pytest.param(
            "Authorization: Bearer f6BearerCanary9f2c",
            "f6BearerCanary9f2c",
            "Authorization: Bearer ***",
            id="bearer-token",
        ),
        pytest.param(
            "issued sr_live_f6client9f2c to project",
            "f6client9f2c",
            "issued sr_live_*** to project",
            id="sr-live-client-key",
        ),
        pytest.param(
            "issued sr_test_f6client9f2c to project",
            "f6client9f2c",
            "issued sr_live_*** to project",
            id="sr-test-client-key",
        ),
        pytest.param(
            "upstream said sk-f6skcanary9f2c rejected",
            "f6skcanary9f2c",
            "upstream said sk-*** rejected",
            id="provider-key",
        ),
    ],
)
def test_redact_secrets_masks_documented_carriers(
    raw: str, canary: str, expected: str
) -> None:
    """S6-F6: each carrier named in redaction.py masks to its observed shape.

    The ``sr_test_`` case pins the current substitution, which rewrites both
    issued-key prefixes to ``sr_live_***``; this is not a claim about any
    other key shape.
    """
    from sabiroute.security.redaction import redact_secrets

    masked = redact_secrets(raw)
    assert canary not in masked
    assert masked == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        pytest.param(
            "operator password f6_bare_pw_9f2c was quoted in prose",
            "operator password f6_bare_pw_9f2c was quoted in prose",
            id="bare-password-in-prose",
        ),
        pytest.param(
            "postgresql://f6_user:f6_at_pw@tail@db.internal:5432/x",
            "postgresql://f6_user:***@tail@db.internal:5432/x",
            id="unencoded-at-in-password",
        ),
    ],
)
def test_redact_secrets_documents_residual_boundaries(
    raw: str, expected: str
) -> None:
    """Pin shapes the pattern-based primitive does not fully mask.

    A bare password in prose has no recognized carrier. The unencoded ``@``
    ends the URI password match, so the tail after that ``@`` stays visible.
    Neither case is a claim about secrets in other shapes.
    """
    from sabiroute.security.redaction import redact_secrets

    assert redact_secrets(raw) == expected


def test_redact_secrets_is_idempotent_and_never_raises() -> None:
    from sabiroute.security.redaction import redact_secrets

    once = redact_secrets("postgresql://u:p@h/db")
    assert redact_secrets(once) == once

    class Hostile:
        def __str__(self) -> str:
            raise RuntimeError("cannot render")

    assert redact_secrets(Hostile()) == "<unprintable>"
    assert redact_secrets(None) == "None"


# ---------------------------------------------------------------------------
# Startup and schema-check log hygiene (regression).
#
# ``redact_secrets`` was wired into the accounting finalizer's log sites but
# **not** into the startup or schema-compatibility paths. Those are the most
# likely leak sites of all: ``build_gateway_state`` and ``check_schema`` are
# what open the PostgreSQL connection, and a driver's connect failure embeds
# the DSN -- the exact channel ``redaction.py`` names in its own docstring.
# A failed boot therefore wrote the password to disk in cleartext, on the same
# class of exception the finalizer already masked.
# ---------------------------------------------------------------------------


def test_gateway_startup_failure_dsn_absent_from_logs(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A startup failure whose text embeds a DSN must not be logged raw."""
    import sabiroute.main as main_module

    caplog.set_level(logging.DEBUG)

    def boom() -> Any:
        raise RuntimeError(f"could not connect: {DSN_LEAK}")

    monkeypatch.setattr(main_module, "build_gateway_state", boom)
    app = main_module.create_app()
    with TestClient(app):
        pass

    # The line must actually have been emitted, or absence proves nothing.
    assert "Gateway startup failed" in caplog.text
    assert CANARY not in caplog.text, "startup DSN credential reached the logs"
    assert CANARY not in str(app.state.gateway.startup_error)


def test_schema_incompatible_dsn_absent_from_logs(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The injected-state schema check is the same credential channel."""
    import sabiroute.main as main_module

    caplog.set_level(logging.DEBUG)
    state = build_gateway_state(
        config=make_config(), client=OkProviderStub(), key_store=InMemoryApiKeyStore()
    )
    provision_test_key(state)
    state.key_store._engine = object()  # makes the schema branch reachable

    def boom(_engine: Any) -> None:
        raise RuntimeError(f"could not connect: {DSN_LEAK}")

    monkeypatch.setattr(main_module, "check_schema", boom)
    app = main_module.create_app(state=state)
    with TestClient(app):
        pass

    assert "Gateway schema incompatible" in caplog.text
    assert CANARY not in caplog.text, "schema-check DSN credential reached the logs"
    assert CANARY not in str(state.startup_error)


def test_readiness_schema_recheck_does_not_store_credential(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``/health/ready`` re-checks the schema; its error text must stay masked."""
    import sabiroute.api.health as health_module
    import sabiroute.main as main_module

    state = build_gateway_state(
        config=make_config(), client=OkProviderStub(), key_store=InMemoryApiKeyStore()
    )
    key = provision_test_key(state)
    state.key_store._engine = object()

    def boom(_engine: Any) -> None:
        raise RuntimeError(f"could not connect: {DSN_LEAK}")

    # Patch both bindings so neither the probe nor a lifespan re-check can
    # surface the raw text, whichever one runs first.
    monkeypatch.setattr(health_module, "check_schema", boom)
    monkeypatch.setattr(main_module, "check_schema", boom)

    client = TestClient(
        create_app(state=state), headers={"Authorization": f"Bearer {key}"}
    )
    resp = client.get("/health/ready")

    assert resp.status_code == 503
    # The 503 plus a null startup_error proves the re-check failed only for
    # this response, without poisoning shared gateway state.
    assert state.startup_error is None
    assert CANARY not in resp.text
    assert CANARY not in str(state.startup_error)


def test_snapshot_cleanup_budget_release_dsn_absent_from_logs(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A release failure during snapshot cleanup must not log its raw text.

    This is the same ``store.release_budget`` exception the reconcile path
    already redacts; the snapshot-cleanup branch is a separate handler.
    """
    from sabiroute.security.keys import ApiKeyBudget

    caplog.set_level(logging.DEBUG)
    client, state, stub = make_client(stub=OkProviderStub())
    store = state.key_store
    for record in store.records.values():
        store.set_budget(record.key_id, ApiKeyBudget(daily_tokens=1_000))
    assert store.budgets, "budget fixture was not applied"
    store.fail_feature_snapshot_writes = True

    def boom(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError(f"could not connect: {DSN_LEAK}")

    store.release_budget = boom  # type: ignore[method-assign]
    resp = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES, "max_tokens": 16},
    )

    assert resp.status_code == 503
    assert "snapshot persistence error" in caplog.text
    assert CANARY not in resp.text
    assert CANARY not in caplog.text, "snapshot-cleanup DSN reached the logs"


# ---------------------------------------------------------------------------
# Quota-gated and cancellation variants of the same class of log site.
# The four handlers below are separate branches of ``finish``/the reserve
# gates, so covering only the reconcile path left them unproven.
# ---------------------------------------------------------------------------

QUOTA_USER = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


def _quota_client(stub: Any) -> tuple[TestClient, Any]:
    """Client for a pilot Sabi user, so the quota gate really reserves."""
    from conftest import enable_shared_inference

    from sabiroute.freepool.eligibility import FreePoolPolicy
    from sabiroute.quotas import QuotaPolicy
    from sabiroute.security.keys import issue_api_key

    store = InMemoryApiKeyStore()
    state = build_gateway_state(
        config=make_config(),
        client=stub,
        key_store=store,
        free_pool=FreePoolPolicy(
            enabled=True, eligible_deployments=frozenset({"primary"})
        ),
        quota_policy=QuotaPolicy(pilot_users=frozenset({QUOTA_USER})),
    )
    # The Sabi user identity is honoured only when the request bears the
    # server-held service credential, so this client must present it.
    service_record, service_plaintext = issue_api_key(
        store, project_id="sabichat-service", name="sabichat-service"
    )
    state.sabichat_service_key_id = service_record.key_id
    enable_shared_inference(state)
    client = TestClient(
        create_app(state=state),
        headers={"Authorization": f"Bearer {service_plaintext}"},
    )
    return client, state


def _quota_body() -> dict[str, Any]:
    from sabiroute.security.keys import SABI_USER_ID_FIELD

    return {
        "model": "primary",
        "messages": MESSAGES,
        "sabi_route_free_chat": True,
        "max_tokens": 16,
        SABI_USER_ID_FIELD: QUOTA_USER,
    }


def test_snapshot_cleanup_quota_release_dsn_absent_from_logs(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The quota sibling of the budget snapshot-cleanup handler."""
    caplog.set_level(logging.DEBUG)
    client, state = _quota_client(OkProviderStub())
    state.key_store.fail_feature_snapshot_writes = True

    def boom(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError(f"could not connect: {DSN_LEAK}")

    state.key_store.release_quota = boom  # type: ignore[method-assign]
    resp = client.post("/v1/chat/completions", json=_quota_body())

    assert resp.status_code == 503
    assert "snapshot persistence error" in caplog.text
    assert CANARY not in resp.text
    assert CANARY not in caplog.text, "quota snapshot-cleanup DSN reached the logs"


def _direct_request(state: Any) -> Any:
    """Build a ``Request`` carrying a valid client identity, as FastAPI would."""
    from starlette.requests import Request

    from sabiroute.security.keys import ApiKeyIdentity

    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    # Prefer the service credential: quota identity is gated on it, and
    # relying on dict insertion order would make this test silently vacuous.
    service_id = getattr(state, "sabichat_service_key_id", None)
    record = store.records[service_id] if service_id else next(iter(store.records.values()))
    return Request(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/v1/chat/completions",
            "raw_path": b"/v1/chat/completions",
            "query_string": b"",
            "root_path": "",
            "headers": [],
            "client": ("127.0.0.1", 12345),
            "server": ("test", 80),
            "app": create_app(state=state),
            "state": {
                "api_identity": ApiKeyIdentity(
                    key_id=record.key_id, project_id=record.project_id
                )
            },
        }
    )


def test_cancellation_release_dsn_absent_from_logs(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Both release handlers on the pre-dispatch cancellation path.

    A cancelled admission compensates idempotently by releasing the budget and
    the quota reservation. Those two handlers logged the raw store exception;
    a store that is failing *because* it cannot reach PostgreSQL is exactly
    the case where the exception text carries the DSN.
    """
    import asyncio

    from sabiroute.api.completions import ChatCompletionRequest, chat_completions
    from sabiroute.security.keys import SABI_USER_ID_FIELD, ApiKeyBudget

    caplog.set_level(logging.DEBUG)
    _client, state = _quota_client(OkProviderStub())
    store = state.key_store
    for record in store.records.values():
        store.set_budget(record.key_id, ApiKeyBudget(daily_tokens=1_000))
    assert store.budgets, "budget fixture was not applied"

    def cancelled(*args: Any, **kwargs: Any) -> Any:
        # Synchronous, like the real store method: an ``async def`` would
        # return a coroutine and never raise.
        raise asyncio.CancelledError

    def boom(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError(f"could not connect: {DSN_LEAK}")

    store.reserve_budget = cancelled  # type: ignore[method-assign]
    store.release_budget = boom  # type: ignore[method-assign]
    store.release_quota = boom  # type: ignore[method-assign]

    payload = ChatCompletionRequest(
        model="primary",
        messages=MESSAGES,
        sabi_route_free_chat=True,
        max_tokens=16,
        **{SABI_USER_ID_FIELD: QUOTA_USER},
    )
    response = asyncio.run(chat_completions(payload, _direct_request(state)))

    assert response.status_code == 499
    assert "release failed after cancellation" in caplog.text
    assert CANARY not in caplog.text, "cancellation-path DSN reached the logs"
