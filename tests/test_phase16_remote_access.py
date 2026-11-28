"""Phase 16: the remote-access posture is enforced, not just documented.

The invariant under test: SabiRoute listens on loopback unless an operator
opts in explicitly, and the only documented way off this machine is a private
tailnet proxy. Funnel and plain LAN binds are refused rather than forgotten.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from sabiroute.config.remote_access import (
    DEFAULT_HOST,
    OPT_IN_ENV,
    InsecureBindError,
    is_loopback,
    non_loopback_allowed,
    resolve_bind_host,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_default_listener_is_loopback() -> None:
    assert DEFAULT_HOST == "127.0.0.1"
    assert resolve_bind_host(environ={}) == "127.0.0.1"


def test_host_env_is_read() -> None:
    assert resolve_bind_host(environ={"SABIROUTE_HOST": "localhost"}) == "localhost"


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "::1", "[::1]"])
def test_loopback_hosts_are_accepted(host: str) -> None:
    assert is_loopback(host)
    assert resolve_bind_host(host, environ={}) == host


@pytest.mark.parametrize(
    "host", ["0.0.0.0", "::", "192.168.1.20", "10.0.0.7", "gateway.example.ts.net"]
)
def test_wider_binds_are_refused_by_default(host: str) -> None:
    with pytest.raises(InsecureBindError) as raised:
        resolve_bind_host(host, environ={})

    message = str(raised.value)
    assert "loopback" in message
    assert "tailscale serve" in message
    assert "Funnel" in message
    assert OPT_IN_ENV in message


def test_explicit_opt_in_permits_a_wider_bind() -> None:
    assert resolve_bind_host("0.0.0.0", environ={OPT_IN_ENV: "1"}) == "0.0.0.0"
    assert non_loopback_allowed({OPT_IN_ENV: "yes"})
    assert not non_loopback_allowed({OPT_IN_ENV: "0"})
    assert not non_loopback_allowed({})


def test_compose_publishes_on_loopback_only() -> None:
    compose = (REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    entries = re.findall(r'^\s*-\s*"([^"]+)"', compose, re.MULTILINE)
    published = [entry for entry in entries if entry.count(":") >= 2]
    assert published, "docker-compose.yml publishes no ports; the assertion is stale"
    for mapping in published:
        assert mapping.startswith("127.0.0.1:"), mapping


def test_remote_access_runbook_records_the_decision() -> None:
    document = (REPO_ROOT / "docs" / "remote-access.md").read_text(encoding="utf-8")
    lowered = document.lower()
    for required in (
        "tailscale serve",
        "funnel",
        "127.0.0.1",
        "admin key",
        "rollback",
    ):
        assert required in lowered, required
    assert "adr-010" in lowered


def test_decision_record_carries_adr_010() -> None:
    record = (REPO_ROOT / "docs" / "architecture-decision-record.md").read_text(
        encoding="utf-8"
    )
    assert "### ADR-010" in record
    assert "tailscale" in record.lower()


def test_checker_script_never_enables_public_ingress() -> None:
    script = (REPO_ROOT / "scripts" / "phase16_remote_access_check.py").read_text(
        encoding="utf-8"
    )
    # The checker may mention Funnel and may inspect its status, but every
    # subprocess it runs must be read-only. Parse the argument lists rather
    # than the prose, which necessarily contains the word "funnel".
    assert "funnel" in script.lower()
    calls = re.findall(r"_run\(\[([^\]]*)\]\)", script)
    assert calls, "the checker runs no subprocesses; the assertion is stale"
    for call in calls:
        for mutating in ('"--bg"', '"on"', '"up"', '"reset"'):
            assert mutating not in call, call
    assert '"funnel", "status"' in script.replace("'", '"')
