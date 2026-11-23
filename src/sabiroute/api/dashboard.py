"""Phase 15 admin dashboard: a read-only static frontend over the admin API.

The dashboard is a zero-build HTML/CSS/vanilla-JS page served by the
application itself, exactly like the SabiChat UI mounted at ``/app``. It adds
no data surface and no authority: every figure it shows comes from the five
already-authenticated ``/admin`` read endpoints (``health``, ``metrics``,
``latency``, ``errors``, ``usage``), and the page itself carries no
credential.

The operator pastes their admin key into the page; the page keeps it in this
tab's ``sessionStorage`` only and sends it as the normal ``Authorization:
Bearer`` header on each fetch. The mount is intentionally unauthenticated
because it is a secret-free static shell -- the data it requests stays behind
``require_admin_key`` on the admin router, so admin authentication is neither
weakened nor bypassed.

The mount lives at ``/admin/dashboard`` rather than ``/admin`` so it can never
shadow the admin API routes. The admin router is registered before this mount,
and the two path spaces do not overlap.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

DASHBOARD_MOUNT_PATH = "/admin/dashboard"
DASHBOARD_MOUNT_NAME = "admin-dashboard"


def dashboard_dir(web_dir: Path | None) -> Path | None:
    """Return the dashboard asset directory, or ``None`` when it is absent."""
    if web_dir is None:
        return None
    candidate = web_dir / "dashboard"
    return candidate if candidate.is_dir() else None


def mount_dashboard(app: FastAPI, web_dir: Path | None) -> bool:
    """Mount the read-only dashboard under ``/admin/dashboard``.

    Returns ``True`` when the mount was added. The mount is unauthenticated on
    purpose: the page is static and secret-free, and every data request it
    makes still passes through ``require_admin_key`` on the admin router.
    """
    directory = dashboard_dir(web_dir)
    if directory is None:
        return False
    app.mount(
        DASHBOARD_MOUNT_PATH,
        StaticFiles(directory=directory, html=True),
        name=DASHBOARD_MOUNT_NAME,
    )
    return True
