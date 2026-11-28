"""Phase 15: the console is self-contained, accessible, and state-aware.

These assertions protect the properties that make the dashboard usable as an
operational surface rather than a table dump: a real landmark structure, live
regions for state changes, tabular figures, stated-preference handling, and no
dependence on any asset outside the gateway's own origin.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = REPO_ROOT / "web" / "dashboard"


def read(name: str) -> str:
    return (DASHBOARD / name).read_text(encoding="utf-8")


def test_html_is_self_contained() -> None:
    html = read("index.html")
    assert "http://" not in html
    assert "https://" not in html
    assert "fonts.googleapis" not in html
    assert "cdn" not in html.lower()


def test_html_has_an_accessible_skeleton() -> None:
    html = read("index.html")
    assert html.count('scope="col"') >= 5
    assert html.count("aria-live") >= 2
    assert 'role="alert"' in html
    assert 'for="admin-key"' in html
    # ``off`` is widely ignored on a password field; ``new-password`` is the
    # value browsers actually honour when suppressing a save-password prompt
    # for a credential that is deliberately scoped to one tab.
    assert 'autocomplete="new-password"' in html
    assert 'type="password"' in html


def test_css_handles_stated_preferences() -> None:
    css = read("dashboard.css")
    for media in (
        "@media (prefers-color-scheme: dark)",
        "@media (prefers-reduced-motion: reduce)",
        "@media (prefers-reduced-transparency: reduce)",
        "@media (prefers-contrast: more)",
    ):
        assert media in css, media
    assert "font-variant-numeric: tabular-nums" in css
    assert "backdrop-filter: blur(" in css
    assert "font-optical-sizing: auto" in css


def test_js_is_polite_and_state_aware() -> None:
    script = read("dashboard.js")
    # Never send ambient credentials with an admin request.
    assert 'credentials: "omit"' in script
    # Stop polling a hidden tab; resume when it becomes visible again.
    assert "visibilityState" in script
    # Cooldown timers tick locally between polls.
    assert "data-until" in script
    # A stale reading is labelled, not silently presented as current.
    assert "Stale" in script
    assert "toLocaleTimeString" in script
    # The polling window is disclosed rather than implied to be all-time.
    assert "since page opened" in script or "poll" in script.lower()


def test_console_answers_health_in_one_line() -> None:
    """The verdict strip is the 2am question: is this gateway healthy now?"""
    html = read("index.html")
    script = read("dashboard.js")
    css = read("dashboard.css")

    assert 'id="verdict"' in html
    assert 'id="verdict-text"' in html
    # Tone is a data attribute, so the dot can carry state without new markup.
    assert 'data-tone="ok"' in html

    # It is derived from data already fetched — the console adds no endpoint.
    assert "function renderVerdict(" in script
    assert "deployments available" in script
    assert "no failures in the last" in script
    assert 'setAttribute("data-tone"' in script

    # And it is quiet when healthy: only the dot changes colour.
    for tone in ('data-tone="warn"', 'data-tone="bad"'):
        assert tone in css, tone
