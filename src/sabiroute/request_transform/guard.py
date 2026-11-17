"""I9 — fail-to-original.

The call-site guard. It swallows ``Exception`` and **never** ``BaseException``:
``asyncio.CancelledError`` derives from ``BaseException``, and the ledger compensation
path depends on it propagating. A guard that caught it would leak a reservation.

The guard logs once at warning, with the exception passed through ``redact_secrets`` so a
credential carried in an error message cannot reach the log.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TypeVar

from ..security.redaction import redact_secrets

T = TypeVar("T")


def fail_to_original(
    operation: Callable[[], T],
    original: T,
    *,
    logger: logging.Logger,
    request_id: str,
    reason: str,
) -> T:
    """Run ``operation``; on any ``Exception`` return ``original`` unchanged.

    ``CancelledError`` and every other ``BaseException`` propagate untouched.
    """
    try:
        return operation()
    except Exception as exc:  # noqa: BLE001 - deliberate: this is the degrade boundary
        logger.warning(
            "request transform degraded to original (request_id=%s reason=%s error=%s)",
            request_id,
            reason,
            redact_secrets(exc),
        )
        return original
