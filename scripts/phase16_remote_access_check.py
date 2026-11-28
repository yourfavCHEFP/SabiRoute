#!/usr/bin/env python3
"""Read-only Phase 16 posture check.

Reports whether this machine is in the remote-access posture the decision
record requires: a loopback listener, and a private tailnet in front of it.
It never changes serve or funnel configuration, never starts anything, and
never reads a credential.

    ./.venv/bin/python scripts/phase16_remote_access_check.py

Exit codes: 0 when every check passes, 1 when any check fails, 2 when the
tailnet checks cannot run because the CLI is absent.

Reading the result:

* PASS on bind, FAIL elsewhere  -> the app is safe; the tailnet is not set up.
* FAIL on bind                 -> fix this first. The listener is wider than
                                  the decision allows.
* Any PASS with "Funnel"       -> stop. Funnel publishes to the public
                                  internet and Phase 20 gates that.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from sabiroute.config.remote_access import (  # noqa: E402
    DEFAULT_HOST,
    HOST_ENV,
    OPT_IN_ENV,
    InsecureBindError,
    resolve_bind_host,
)

EXPECTED_TARGET = "http://127.0.0.1:8000"
PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, timeout=20, check=False)


def check_bind(environ: dict[str, str]) -> tuple[str, str]:
    requested = environ.get(HOST_ENV, DEFAULT_HOST)
    try:
        resolved = resolve_bind_host(environ=environ)
    except InsecureBindError as error:
        return FAIL, f"requested {requested}: {error}"
    note = "default" if requested == DEFAULT_HOST else f"from {HOST_ENV}"
    if environ.get(OPT_IN_ENV):
        note += f", opt-in {OPT_IN_ENV} is set"
    return PASS, f"listener {resolved} ({note})"


def check_cli(tailscale: str | None) -> tuple[str, str]:
    if not tailscale:
        return SKIP, "tailscale CLI not on PATH"
    result = _run([tailscale, "version"])
    if result.returncode != 0:
        return FAIL, (result.stderr or result.stdout).strip().splitlines()[0]
    return PASS, result.stdout.strip().splitlines()[0]


def check_identity(tailscale: str | None) -> tuple[str, str]:
    if not tailscale:
        return SKIP, "tailscale CLI not on PATH"
    result = _run([tailscale, "status", "--json"])
    if result.returncode != 0:
        return FAIL, "tailscale status failed; is the daemon running and logged in?"
    try:
        status = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return FAIL, "tailscale status did not return JSON"
    backend = status.get("BackendState") or "unknown"
    self_node = status.get("Self") or {}
    name = self_node.get("DNSName") or self_node.get("HostName") or "unnamed"
    if backend != "Running":
        return FAIL, f"backend {backend}; node {name}"
    return PASS, f"node {name}"


def check_serve(tailscale: str | None) -> tuple[str, str]:
    if not tailscale:
        return SKIP, "tailscale CLI not on PATH"
    result = _run([tailscale, "serve", "status"])
    if result.returncode != 0:
        return FAIL, "serve status failed"
    output = (result.stdout or "").strip()
    if not output or "No serve config" in output:
        return FAIL, (
            "no serve config; run: tailscale serve --bg --https=443 "
            + EXPECTED_TARGET
        )
    if EXPECTED_TARGET not in output:
        return FAIL, f"serve config does not proxy {EXPECTED_TARGET}"
    return PASS, f"proxying {EXPECTED_TARGET} on the tailnet"


def check_funnel(tailscale: str | None) -> tuple[str, str]:
    if not tailscale:
        return SKIP, "tailscale CLI not on PATH"
    result = _run([tailscale, "funnel", "status"])
    output = (result.stdout or "") + (result.stderr or "")
    lowered = output.lower()
    if "funnel on" in lowered or "https://" in lowered:
        return FAIL, (
            "public ingress is configured. Disable it with "
            "`tailscale serve reset` and re-run this check."
        )
    return PASS, "no public ingress"


def main() -> int:
    tailscale = shutil.which("tailscale")
    environ = dict(os.environ)
    checks = [
        ("bind", *check_bind(environ)),
        ("cli", *check_cli(tailscale)),
        ("identity", *check_identity(tailscale)),
        ("serve", *check_serve(tailscale)),
        ("funnel", *check_funnel(tailscale)),
    ]

    width = max(len(name) for name, _, _ in checks)
    failed = 0
    skipped = 0
    for name, verdict, detail in checks:
        print(f"{name.ljust(width)}  {verdict}  {detail}")
        if verdict == FAIL:
            failed += 1
        elif verdict == SKIP:
            skipped += 1

    if failed:
        print(f"\n{failed} check(s) failed. See docs/remote-access.md for the runbook.")
        return 1
    if skipped == len(checks):
        print("\nNothing could be checked on this machine.")
        return 2
    print("\nPosture matches ADR-010: loopback listener, tailnet-only proxy, no funnel.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
