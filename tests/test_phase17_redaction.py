"""Phase 17 F-07: redaction covers the HuggingFace, Google and JWT shapes.

Provider error text is persisted after ``redact_secrets`` runs
(``api/completions.py``), so an unmasked credential shape in an upstream error
body would be written to the error tracker. These tests pin each new carrier,
prove ordinary text is left alone, and prove the pre-existing carriers were
not weakened.
"""

from __future__ import annotations

import pytest

from sabiroute.security.redaction import redact_secrets

HF_TOKEN = "hf_aBcDeFgHiJkLmNoPqRsTuVwXyZ012345"
GOOGLE_KEY = "AIzaSyD-1234567890abcdefghijklmnopqrs"
JWT = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4ifQ"
    ".SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
)


@pytest.mark.parametrize(
    ("raw", "secret", "carrier"),
    [
        pytest.param(f"huggingface said {HF_TOKEN} is invalid", HF_TOKEN, "hf_", id="hf"),
        pytest.param(f"google said {GOOGLE_KEY} is invalid", GOOGLE_KEY, "AIza", id="aiza"),
        pytest.param(f"upstream echoed {JWT} as auth", JWT, None, id="jwt"),
    ],
)
def test_new_carriers_are_masked(
    raw: str, secret: str, carrier: str | None
) -> None:
    masked = redact_secrets(raw)
    assert secret not in masked
    if carrier is not None:
        # The carrier prefix survives, so the log stays diagnosable.
        assert carrier in masked


def test_jwt_is_masked_whole() -> None:
    masked = redact_secrets(f"auth={JWT}")
    assert masked == "auth=***"
    for segment in JWT.split("."):
        assert segment not in masked


@pytest.mark.parametrize(
    "ordinary",
    [
        "the hf_ prefix names a HuggingFace token",
        "AIza is the Google key prefix",
        "JWT means JSON Web Token",
        "the header of a JWT is base64url of a JSON object",
        "sk-learn is a machine-learning library",
        "postgresql client error at db.internal:5432",
    ],
)
def test_ordinary_text_is_untouched(ordinary: str) -> None:
    assert redact_secrets(ordinary) == ordinary


def test_existing_patterns_are_not_weakened() -> None:
    raw = (
        "postgresql://user:hunter2@db.internal/x sk-proj-ZZZZ9999 "
        "sr_live_abcdef0123456789 Bearer abcdef0123456789"
    )
    masked = redact_secrets(raw)

    for leaked in ("hunter2", "ZZZZ9999", "abcdef0123456789"):
        assert leaked not in masked
    assert "postgresql://user:***@db.internal/x" in masked
    assert "sk-***" in masked
    assert "sr_live_***" in masked
    assert "Bearer ***" in masked


def test_new_patterns_are_idempotent() -> None:
    once = redact_secrets(f"{HF_TOKEN} {GOOGLE_KEY} {JWT}")
    assert redact_secrets(once) == once
