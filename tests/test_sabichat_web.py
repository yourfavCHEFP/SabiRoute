"""Sprint 4: SabiChat static frontend — serving, contract parity, safety markers.

The UI is zero-build HTML/CSS/vanilla JS served by the app itself. These
tests prove serving, endpoint parity with the real route table, and static
safety properties (no secrets, no innerHTML, no persistent token storage,
no direct provider calls). Interactive browser behavior is covered by the
optional Playwright smoke procedure, not by this file.
"""

from __future__ import annotations

import re
from pathlib import Path

from conftest import InMemoryApiKeyStore, StubLiteLLMClient, make_config
from fastapi.testclient import TestClient

from sabiroute.chat.store import SabiChatStore
from sabiroute.freepool.eligibility import FreePoolPolicy
from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app

WEB_DIR = Path(__file__).resolve().parents[1] / "web"


def read_web(name):
    return (WEB_DIR / name).read_text(encoding="utf-8")


def make_client(tmp_path):
    state = build_gateway_state(
        config=make_config(),
        client=StubLiteLLMClient(),
        key_store=InMemoryApiKeyStore(),
        free_pool=FreePoolPolicy(),
        chat_store=SabiChatStore(f"sqlite:///{tmp_path / 'web.sqlite'}"),
    )
    return TestClient(create_app(state=state))


def test_web_files_served_with_correct_types(tmp_path):
    client = make_client(tmp_path)

    index = client.get("/app/")
    assert index.status_code == 200
    assert "text/html" in index.headers["content-type"]

    js = client.get("/app/app.js")
    assert js.status_code == 200
    assert "javascript" in js.headers["content-type"]

    css = client.get("/app/styles.css")
    assert css.status_code == 200
    assert "css" in css.headers["content-type"]


def test_mount_does_not_shadow_api(tmp_path):
    client = make_client(tmp_path)

    assert client.get("/v1/auth/me").status_code == 401
    assert client.get("/docs").status_code == 200


def test_auth_and_chat_landmarks_present():
    html = read_web("index.html")

    for element_id in (
        "view-auth",
        "view-app",
        "auth-form",
        "auth-email",
        "auth-password",
        "auth-submit",
        "conversation-list",
        "message-list",
        "composer",
        "composer-input",
        "send-button",
        "cancel-button",
        "banner",
        "sign-out",
        "new-chat",
    ):
        assert f'id="{element_id}"' in html, element_id
    assert "<html lang=" in html
    assert 'name="viewport"' in html
    assert "<label" in html
    assert "./app.js" in html
    assert "./styles.css" in html


def test_frontend_uses_only_sabichat_endpoints(tmp_path):
    js = read_web("app.js")
    referenced = set(re.findall(r"\"(/v1/[a-z/\-]+)", js))
    assert referenced, "expected fetch paths in app.js"

    client = make_client(tmp_path)
    routes = set()
    for route in client.app.routes:
        if hasattr(route, "path") and route.path:
            routes.add(route.path)
        original = getattr(route, "original_router", None)
        if original is not None:
            for inner in original.routes:
                if hasattr(inner, "path") and inner.path:
                    routes.add(inner.path)
    for path in referenced:
        assert path in routes, f"{path} has no backend route"

    assert "/v1/chat/completions" not in js
    assert "4000" not in js
    assert "localhost" not in js
    assert "127.0.0.1" not in js


def test_quota_meter_landmarks_present():
    html = read_web("index.html")

    for element_id in (
        "quota-meter",
        "quota-text",
        "quota-bar",
        "quota-fill",
        "quota-reset",
    ):
        assert f'id="{element_id}"' in html, element_id
    assert 'role="progressbar"' in html
    assert "aria-valuemin" in html
    assert "aria-valuemax" in html
    assert "aria-valuenow" in html
    assert "aria-live" in html


def test_quota_meter_uses_summary_endpoint():
    js = read_web("app.js")

    assert "/v1/chat/quota-summary" in js
    # Honest states: loading, unavailable, and stale are rendered, never
    # fabricated zeros; unenrolled hides the meter.
    assert "enrolled" in js
    assert "quota_unavailable" in js
    assert "refreshQuota" in js
    # Post-request refresh: the meter re-reads after a completed send.
    assert js.count("refreshQuota") >= 3
    # Quota exhaustion restores the optimistically cleared draft.
    assert "quota_exceeded" in js


    # Logout/account-switch must tear down the previous session's rendered
    # UI: messages, draft, and banner are account-scoped and must not
    # survive the transition to the authentication view.
    show_auth = js[js.index("function showAuth"):]
    show_auth = show_auth[: show_auth.index("\n  }\n")]
    assert "renderMessages([])" in show_auth
    assert 'composerInput.value = ""' in show_auth
    assert "hideBanner()" in show_auth


def test_frontend_parses_backend_error_envelope():
    js = read_web("app.js")
    assert "payload.detail" in js
    assert "detail.error" in js


def test_no_secrets_or_credentials_in_bundle():
    bundle = read_web("index.html") + read_web("app.js") + read_web("styles.css")

    assert "sr_live_" not in bundle
    assert "sk-" not in bundle
    assert "api_key" not in bundle
    assert "localStorage" not in bundle
    assert "sessionStorage" not in bundle
    assert "document.cookie" not in bundle


def test_safe_rendering_and_submission_guards():
    js = read_web("app.js")

    assert "innerHTML" not in js
    assert "outerHTML" not in js
    assert "document.write" not in js
    assert "textContent" in js
    assert "encodeURIComponent" in js

    # Double-submit and cross-conversation-leak guards (static markers;
    # behavior itself needs a browser).
    assert "AbortController" in js
    assert "pending" in js
    assert "requestSubmit" in js
