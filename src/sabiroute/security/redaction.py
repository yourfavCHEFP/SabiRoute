"""Credential redaction for application-controlled log output.

Owner decision D-R3-3: secrets must not appear in logs, telemetry, error
messages, or audit output.

Persistence layers routinely embed the connection URI they failed on in the
exception text (``could not connect: postgresql://user:pw@host/db``), and a
URI carries the credential. Logging such an exception verbatim therefore
writes a live password to disk, where it outlives the request and travels to
whatever collects the logs.

This module masks the credential *carriers* that realistically appear in
error text while preserving enough of the message to stay diagnosable:

* URI userinfo passwords — ``scheme://user:secret@host``
* ``Bearer`` tokens — ``Authorization: Bearer <token>``
* issued SabiRoute client keys — ``sr_live_...`` / ``sr_test_...``
* provider key shapes — ``sk-...``

Residual risk, stated honestly: this is pattern-based. A secret appearing in
none of these shapes (for example a bare password quoted in prose) is not
masked. Callers that must guarantee zero leak should log the exception class
name only. Redaction is idempotent and never raises.
"""

from __future__ import annotations

import re

REDACTED = "***"

#: ``scheme://user:password@host`` — mask the password, keep scheme/user/host.
_URI_USERINFO = re.compile(
    r"(?P<scheme>[A-Za-z][A-Za-z0-9+.\-]*://)"
    r"(?P<user>[^:/@\s]+):"
    r"(?P<secret>[^@/\s]*)@"
)

#: ``Bearer <token>`` — keep the scheme word, mask the token.
_BEARER = re.compile(r"(?i)\b(bearer\s+)([A-Za-z0-9._\-+/=]{8,})")

#: SabiRoute-issued client keys and OpenAI-style provider keys.
_CLIENT_KEY = re.compile(r"\bsr_(?:live|test)_[A-Za-z0-9_\-]{8,}")
_PROVIDER_KEY = re.compile(r"\bsk-[A-Za-z0-9_\-]{6,}")


def redact_secrets(value: object) -> str:
    """Return ``value`` as text with recognized credential carriers masked.

    Accepts any object (an exception is the intended argument) and never
    raises: formatting a log message must not itself become a failure path.
    """
    try:
        text = str(value)
    except Exception:
        return "<unprintable>"

    text = _URI_USERINFO.sub(
        lambda match: f"{match.group('scheme')}{match.group('user')}:{REDACTED}@", text
    )
    text = _BEARER.sub(lambda match: f"{match.group(1)}{REDACTED}", text)
    text = _CLIENT_KEY.sub(f"sr_live_{REDACTED}", text)
    text = _PROVIDER_KEY.sub(f"sk-{REDACTED}", text)
    return text
