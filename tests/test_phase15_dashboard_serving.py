"""Phase 15 admin dashboard — serving and the admin authentication boundary.

The dashboard is a read-only static page over the five already-authenticated
``/admin`` read endpoints. These tests prove the app serves it, that the mount
does not shadow the admin API, and that admin authentication is neither
weakened nor bypassed. Static-content safety (no secrets, session storage,
read-only requests) lives in ``test_phase15_dashboard_static.py``.
"""

from __future__ import annotations

from conftest import (
    InMemoryApiKeyStore,
    StubLiteLLMClient,
    make_config,
    provision_test_key,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient

from sabiroute.api.dashboard import (
    DASHBOARD_MOUNT_NAME,
    DASHBOARD_MOUNT_PATH,
    dashboard_dir,
    mount_dashboard,
)
from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app

ADMIN_KEY = "phase15-admin-secret-not-a-real-credential"
ADMIN_ENDPOINTS = (
    "/admin/health",
    "/admin/metrics",
    "/admin/latency",
    "/admin/errors",
    "/admin/usage",
)


def build_app(monkeypatch, *, with_client_key: bool = False):
    monkeypatch.setenv("SABIROUTE_ADMIN_KEY", ADMIN_KEY)
    state = build_gateway_state(
        config=make_config(),
        client=StubLiteLLMClient(),
        key_store=InMemoryApiKeyStore(),
    )
    client_key = provision_test_key(state) if with_client_key else None
    return create_app(state=state), client_key


def test_dashboard_served_with_correct_content_types(monkeypatch):
    client = TestClient(build_app(monkeypatch)[0])

    index = client.get(f"{DASHBOARD_MOUNT_PATH}/")
    assert index.status_code == 200
    assert "text/html" in index.headers["content-type"]

    js = client.get(f"{DASHBOARD_MOUNT_PATH}/dashboard.js")
    assert js.status_code == 200
    assert "javascript" in js.headers["content-type"]

    css = client.get(f"{DASHBOARD_MOUNT_PATH}/dashboard.css")
    assert css.status_code == 200
    assert "css" in css.headers["content-type"]


def test_served_dashboard_js_references_the_five_endpoints(monkeypatch):
    client = TestClient(build_app(monkeypatch)[0])
    js = client.get(f"{DASHBOARD_MOUNT_PATH}/dashboard.js").text
    for path in ADMIN_ENDPOINTS:
        assert path in js, path


def test_dashboard_bare_path_redirects_to_trailing_slash(monkeypatch):
    client = TestClient(build_app(monkeypatch)[0])
    response = client.get(DASHBOARD_MOUNT_PATH, follow_redirects=False)
    assert response.status_code in (307, 308)
    assert response.headers["location"].endswith(f"{DASHBOARD_MOUNT_PATH}/")


def test_dashboard_mount_is_registered(monkeypatch):
    app = build_app(monkeypatch)[0]
    names = {getattr(route, "name", None) for route in app.routes}
    assert DASHBOARD_MOUNT_NAME in names


def test_dashboard_mount_does_not_shadow_admin_api(monkeypatch):
    """Every admin path still reaches the admin router, not the static mount."""
    client = TestClient(build_app(monkeypatch)[0])
    headers = {"Authorization": f"Bearer {ADMIN_KEY}"}

    for path in ADMIN_ENDPOINTS:
        response = client.get(path, headers=headers)
        assert response.status_code == 200, path
        # The admin endpoints return JSON, never the dashboard HTML shell.
        assert "application/json" in response.headers["content-type"], path


def test_admin_authentication_is_unchanged(monkeypatch):
    """Prove the dashboard did not loosen the admin boundary.

    Missing key → 401. Wrong admin key → 401. A valid *client* key → 401
    (the admin secret is a separate authority). The correct admin key → 200.
    """
    app, client_key = build_app(monkeypatch, with_client_key=True)
    assert client_key is not None
    client = TestClient(app)

    for path in ADMIN_ENDPOINTS:
        assert client.get(path).status_code == 401, path
        assert (
            client.get(path, headers={"Authorization": "Bearer wrong-secret"}).status_code
            == 401
        ), path
        assert (
            client.get(path, headers={"Authorization": f"Bearer {client_key}"}).status_code
            == 401
        ), path
        assert (
            client.get(path, headers={"Authorization": f"Bearer {ADMIN_KEY}"}).status_code
            == 200
        ), path


def test_admin_endpoints_fail_closed_when_secret_is_unconfigured(monkeypatch):
    """No configured admin secret must deny every admin route (503), never open."""
    monkeypatch.delenv("SABIROUTE_ADMIN_KEY", raising=False)
    state = build_gateway_state(
        config=make_config(),
        client=StubLiteLLMClient(),
        key_store=InMemoryApiKeyStore(),
    )
    client = TestClient(create_app(state=state))
    for path in ADMIN_ENDPOINTS:
        response = client.get(path, headers={"Authorization": "Bearer anything"})
        assert response.status_code == 503, path
        assert response.json()["detail"]["error"]["type"] == "authentication_unavailable"


def test_served_page_contains_no_admin_key(monkeypatch):
    client = TestClient(build_app(monkeypatch)[0])
    body = client.get(f"{DASHBOARD_MOUNT_PATH}/").text
    assert ADMIN_KEY not in body
    assert "SABIROUTE_ADMIN_KEY" not in body


def test_dashboard_dir_is_none_without_a_web_dir():
    assert dashboard_dir(None) is None


def test_dashboard_dir_is_none_when_assets_are_absent(tmp_path):
    assert dashboard_dir(tmp_path) is None


def test_mount_dashboard_returns_false_without_assets(tmp_path):
    app = FastAPI()
    assert mount_dashboard(app, tmp_path) is False
