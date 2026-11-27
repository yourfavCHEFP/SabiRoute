"""Remote-access posture for SabiRoute (Phase 16).

SabiRoute is local-first. The only supported way to reach this process from
another device is a private tailnet through ``tailscale serve``, which
terminates TLS on the tailnet and proxies to a loopback listener. Public
ingress is not supported: not Tailscale Funnel, not a LAN bind, not a router
port forward. Phase 20's review gates public exposure, and a gate that lives
only in a runbook is a gate that gets skipped at 2am.

This module therefore polices exactly one thing: the address the process
binds. It does not attempt to inspect firewalls, container networks, or
upstream proxies, and it does not claim to. If the process listens on a
loopback address, the only reachable path is one an operator deliberately
created (a tailnet, an SSH tunnel, a local browser).
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Final

DEFAULT_HOST: Final[str] = "127.0.0.1"
OPT_IN_ENV: Final[str] = "SABIROUTE_ALLOW_NON_LOOPBACK_BIND"
HOST_ENV: Final[str] = "SABIROUTE_HOST"

LOOPBACK_HOSTS: Final[frozenset[str]] = frozenset(
    {"127.0.0.1", "localhost", "::1", "[::1]"}
)


class InsecureBindError(RuntimeError):
    """Raised when the API is asked to listen beyond this machine.

    The error is intentional and terminal: a process that cannot honour the
    posture must not start quietly in a wider posture.
    """


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def is_loopback(host: str) -> bool:
    """Return whether ``host`` names this machine only."""
    return host.strip() in LOOPBACK_HOSTS


def non_loopback_allowed(environ: Mapping[str, str] | None = None) -> bool:
    """Return whether the operator opted into a wider bind explicitly."""
    source = os.environ if environ is None else environ
    return _truthy(source.get(OPT_IN_ENV))


def resolve_bind_host(
    host: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> str:
    """Resolve the listener address, refusing anything beyond loopback.

    ``host`` wins when supplied; otherwise ``SABIROUTE_HOST`` is read, and
    ``127.0.0.1`` is the default. A non-loopback address is refused unless
    ``SABIROUTE_ALLOW_NON_LOOPBACK_BIND`` is set, which is the documented
    escape hatch for a container network that already sits behind a private
    interface. That flag is an acknowledgement, not a recommendation.
    """
    source = os.environ if environ is None else environ
    candidate = host if host is not None else source.get(HOST_ENV, DEFAULT_HOST)
    resolved = (candidate or DEFAULT_HOST).strip()

    if is_loopback(resolved):
        return resolved
    if non_loopback_allowed(source):
        return resolved

    raise InsecureBindError(
        f"Refusing to bind {resolved!r}: SabiRoute listens on loopback only. "
        "Reach it from another device through a private tailnet "
        "(`tailscale serve --bg --https=443 http://127.0.0.1:8000`) or an SSH "
        "tunnel. Public ingress (Tailscale Funnel, a LAN bind, a forwarded "
        "port) is gated behind the Phase 20 review. If this bind is deliberate "
        f"and already private, set {OPT_IN_ENV}=1 and restart."
    )
