"""Phase 15 admin dashboard — static-content safety and contract.

These are reading-level assertions over the shipped dashboard assets. They
prove the page is read-only, keeps the operator's key in session storage only,
never injects HTML strings, references exactly the five admin endpoints, and
embeds no credential. Runtime serving and the auth boundary live in
``test_phase15_dashboard_serving.py``.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

DASHBOARD_DIR = Path(__file__).resolve().parents[1] / "web" / "dashboard"

ADMIN_ENDPOINTS = (
    "/admin/health",
    "/admin/metrics",
    "/admin/latency",
    "/admin/errors",
    "/admin/usage",
)

MUTATING_VERBS = re.compile(r"\b(POST|PUT|PATCH|DELETE)\b")


def read(name: str) -> str:
    return (DASHBOARD_DIR / name).read_text(encoding="utf-8")


def test_dashboard_assets_exist():
    for name in ("index.html", "dashboard.js", "dashboard.css"):
        assert (DASHBOARD_DIR / name).is_file(), name


def test_dashboard_references_the_five_admin_endpoints():
    js = read("dashboard.js")
    for path in ADMIN_ENDPOINTS:
        assert path in js, path


def test_dashboard_files_embed_no_secret():
    bundle = read("index.html") + read("dashboard.js") + read("dashboard.css")
    for marker in (
        "sr_live_",
        "sk-",
        "api_key",
        "SABIROUTE_ADMIN_KEY",
        "LITELLM_MASTER_KEY",
    ):
        assert marker not in bundle, marker


def test_dashboard_keeps_the_key_in_session_storage_only():
    js = read("dashboard.js")
    assert "sessionStorage" in js
    assert "localStorage" not in js
    assert "document.cookie" not in js


def test_dashboard_issues_no_mutating_requests():
    js = read("dashboard.js")
    assert MUTATING_VERBS.search(js) is None
    # Every fetch is an explicit GET.
    assert 'method: "GET"' in js


def test_dashboard_sends_the_bearer_header():
    js = read("dashboard.js")
    assert "Authorization" in js
    assert "Bearer " in js


def test_dashboard_handles_401_with_a_key_prompt():
    js = read("dashboard.js")
    html = read("index.html")
    assert "401" in js
    assert "admin key" in js.lower()
    assert 'id="auth-panel"' in html
    assert 'id="admin-key"' in html
    assert 'id="auth-form"' in html


def test_dashboard_renders_without_html_injection():
    js = read("dashboard.js")
    for marker in (
        "innerHTML",
        "outerHTML",
        "insertAdjacentHTML",
        "document.write",
    ):
        assert marker not in js, marker
    assert "textContent" in js
    assert "createElement" in js


def test_dashboard_html_landmarks():
    html = read("index.html")
    for element_id in (
        "auth-panel",
        "auth-form",
        "admin-key",
        "data-view",
        "status-banner",
        "stat-total",
        "stat-success",
        "stat-failed",
        "stat-rate-limited",
        "by-model-body",
        "health-body",
        "latency-body",
        "errors-body",
        "usage-body",
        "refresh",
        "sign-out",
    ):
        assert f'id="{element_id}"' in html, element_id
    assert "<html lang=" in html
    assert 'name="viewport"' in html
    assert "./dashboard.js" in html
    assert "./dashboard.css" in html


def test_dashboard_js_passes_node_check():
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    result = subprocess.run(
        [node, "--check", str(DASHBOARD_DIR / "dashboard.js")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
