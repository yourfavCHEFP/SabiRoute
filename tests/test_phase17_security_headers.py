"""Phase 17 F-13: security response headers and CSP compatibility of the UIs.

The policy is same-origin only, so these tests prove (a) the three headers are
on ordinary responses, (b) the policy permits same-origin script and style,
and (c) the two shipped UIs actually load their assets same-origin and use no
inline script/style or framework features the policy would block.
"""

from __future__ import annotations

from pathlib import Path

from conftest import InMemoryApiKeyStore, StubLiteLLMClient, make_config
from fastapi.testclient import TestClient

from sabiroute.gateway import build_gateway_state, empty_gateway_state
from sabiroute.main import (
    CONTENT_SECURITY_POLICY,
    STRICT_TRANSPORT_SECURITY,
    create_app,
)

WEB_DIR = Path(__file__).resolve().parents[1] / "web"


def _client() -> TestClient:
    state = build_gateway_state(
        config=make_config(),
        client=StubLiteLLMClient(),
        key_store=InMemoryApiKeyStore(),
    )
    return TestClient(create_app(state=state))


def _directives(policy: str) -> dict[str, list[str]]:
    directives: dict[str, list[str]] = {}
    for directive in policy.split(";"):
        parts = directive.split()
        if parts:
            directives[parts[0]] = parts[1:]
    return directives


def test_headers_present_on_a_normal_response() -> None:
    with _client() as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["strict-transport-security"] == STRICT_TRANSPORT_SECURITY
    assert response.headers["content-security-policy"] == CONTENT_SECURITY_POLICY


def test_headers_present_on_a_readiness_failure() -> None:
    with TestClient(create_app(state=empty_gateway_state())) as client:
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["content-security-policy"] == CONTENT_SECURITY_POLICY


def test_csp_permits_same_origin_script_and_style() -> None:
    directives = _directives(CONTENT_SECURITY_POLICY)

    for name in ("default-src", "script-src", "style-src", "connect-src"):
        assert "'self'" in directives[name], name

    # No inline or eval allowance was introduced to make the pages work.
    assert "'unsafe-inline'" not in CONTENT_SECURITY_POLICY
    assert "'unsafe-eval'" not in CONTENT_SECURITY_POLICY
    assert "*" not in CONTENT_SECURITY_POLICY
    # Both pages declare a `data:` favicon.
    assert "data:" in directives["img-src"]
    assert directives["frame-ancestors"] == ["'none'"]


def test_served_uis_carry_the_same_policy() -> None:
    with _client() as client:
        for path in (
            "/app/",
            "/app/app.js",
            "/app/styles.css",
            "/admin/dashboard/",
            "/admin/dashboard/dashboard.js",
            "/admin/dashboard/dashboard.css",
        ):
            response = client.get(path)
            assert response.status_code == 200, path
            assert (
                response.headers["content-security-policy"]
                == CONTENT_SECURITY_POLICY
            ), path
            assert response.headers["x-content-type-options"] == "nosniff", path


def test_static_ui_assets_are_same_origin_and_csp_safe() -> None:
    """The policy is safe only if the pages load assets from their own mount."""
    sabichat = (WEB_DIR / "index.html").read_text(encoding="utf-8")
    dashboard = (WEB_DIR / "dashboard" / "index.html").read_text(encoding="utf-8")

    # Same-origin, relative assets: permitted by script-src/style-src 'self'.
    assert '<script src="./app.js"' in sabichat
    assert '<link rel="stylesheet" href="./styles.css"' in sabichat
    assert '<script src="./dashboard.js"' in dashboard
    assert '<link rel="stylesheet" href="./dashboard.css"' in dashboard

    for markup in (sabichat, dashboard):
        lowered = markup.lower()
        # Nothing the strict policy would block.
        assert "<style" not in lowered
        assert "style=" not in lowered
        assert "onclick=" not in lowered
        assert "onload=" not in lowered
        assert "onerror=" not in lowered
        # The only non-'self' image source is the inline favicon.
        assert 'href="data:,' in lowered


def test_ui_javascript_uses_no_csp_blocked_constructs() -> None:
    for name in ("app.js", "dashboard/dashboard.js"):
        source = (WEB_DIR / name).read_text(encoding="utf-8")
        assert "eval(" not in source, name
        assert "new Function" not in source, name
        assert "innerHTML" not in source, name
        assert "document.write" not in source, name


def test_opt_in_docs_are_exempt_from_the_strict_policy(monkeypatch) -> None:
    # Swagger UI and ReDoc bootstrap from a CDN with an inline script, which
    # the strict policy would block. They are opt-in developer docs.
    monkeypatch.setenv("SABIROUTE_DOCS_ENABLED", "1")
    with _client() as client:
        response = client.get("/docs")

    assert response.status_code == 200
    assert "content-security-policy" not in response.headers
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["strict-transport-security"] == STRICT_TRANSPORT_SECURITY
