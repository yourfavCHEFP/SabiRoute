"""Password hashing for SabiChat local accounts.

Choice, documented: stdlib ``hashlib.pbkdf2_hmac`` (PBKDF2-HMAC-SHA256,
600_000 iterations per current OWASP guidance, 128-bit random salt) with
``hmac.compare_digest`` verification. Rationale: no new dependency or native
extension for the project's pinned interpreter range; PBKDF2 is an approved
password scheme, and this module uses the primitive exactly as specified —
it is not custom cryptography. The modular ``$``-delimited format carries the
parameters so a future revision (higher work factor or a different scheme)
can be introduced with re-hash-on-login, without a flag day.

Never log, return, or persist anything but the modular hash string.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

ALGORITHM = "pbkdf2-sha256"
ITERATIONS = 600_000
SALT_BYTES = 16
MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 128


class PasswordPolicyError(ValueError):
    """Raised when a password fails shape validation before any hashing."""


def validate_password_shape(password: str) -> None:
    """Enforce length bounds before expensive hashing work."""
    if not isinstance(password, str):
        raise PasswordPolicyError("Password must be a string.")
    if len(password.encode("utf-8")) > 1024:
        raise PasswordPolicyError("Password is too long.")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise PasswordPolicyError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
        )
    if len(password) > MAX_PASSWORD_LENGTH:
        raise PasswordPolicyError(
            f"Password must be at most {MAX_PASSWORD_LENGTH} characters."
        )


def hash_password(password: str) -> str:
    """Hash a validated password into a modular ``$``-delimited string."""
    validate_password_shape(password)
    salt = secrets.token_bytes(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, ITERATIONS
    )
    return f"{ALGORITHM}${ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Verify against a modular hash; False for malformed stored values."""
    try:
        algorithm, raw_iterations, raw_salt, raw_digest = stored.split("$")
        iterations = int(raw_iterations)
        salt = bytes.fromhex(raw_salt)
        expected = bytes.fromhex(raw_digest)
    except (ValueError, AttributeError):
        return False
    if algorithm != ALGORITHM or iterations < 1 or not salt or not expected:
        return False
    candidate = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations
    )
    return hmac.compare_digest(candidate, expected)


def dummy_verify(password: str) -> None:
    """Burn comparable work for unknown accounts to narrow timing signals.

    Called on login attempts for emails with no record, so absent and present
    accounts cost the same order of work. The result is intentionally discarded.
    """
    salt = b"\x00" * SALT_BYTES
    hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
