"""Behavioural tests for :mod:`sabiroute.chat.passwords`."""
from __future__ import annotations

import pytest

from sabiroute.chat import passwords


def test_shape_rejects_non_string() -> None:
    with pytest.raises(passwords.PasswordPolicyError):
        passwords.validate_password_shape(123456789012)  # type: ignore[arg-type]


def test_shape_enforces_the_minimum_length() -> None:
    with pytest.raises(passwords.PasswordPolicyError) as excinfo:
        passwords.validate_password_shape("a" * (passwords.MIN_PASSWORD_LENGTH - 1))

    assert "at least" in str(excinfo.value)


def test_shape_enforces_the_maximum_length() -> None:
    with pytest.raises(passwords.PasswordPolicyError) as excinfo:
        passwords.validate_password_shape("a" * (passwords.MAX_PASSWORD_LENGTH + 1))

    assert "at most" in str(excinfo.value)


def test_shape_enforces_the_absolute_byte_ceiling_first() -> None:
    with pytest.raises(passwords.PasswordPolicyError) as excinfo:
        passwords.validate_password_shape("a" * 1025)

    assert "too long" in str(excinfo.value)


def test_shape_accepts_a_boundary_length_password() -> None:
    passwords.validate_password_shape("a" * passwords.MIN_PASSWORD_LENGTH)


def test_hash_is_modular_and_verifies(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(passwords, "ITERATIONS", 1_000)
    secret = "correct horse battery"

    stored = passwords.hash_password(secret)

    algorithm, iterations, salt, digest = stored.split("$")
    assert algorithm == passwords.ALGORITHM
    assert int(iterations) == 1_000
    assert len(bytes.fromhex(salt)) == passwords.SALT_BYTES
    assert bytes.fromhex(digest)
    assert passwords.verify_password(secret, stored) is True
    assert passwords.verify_password("wrong password!", stored) is False


def test_verify_rejects_malformed_or_foreign_hashes() -> None:
    assert passwords.verify_password("whatever", "not-a-modular-hash") is False
    assert passwords.verify_password("whatever", "pbkdf2-sha256$0$aabb$ccdd") is False
    assert passwords.verify_password("whatever", "md5$1000$aabb$ccdd") is False
    assert passwords.verify_password("whatever", "pbkdf2-sha256$x$aabb$ccdd") is False
    assert passwords.verify_password("whatever", "pbkdf2-sha256$1000$$ccdd") is False


def test_dummy_verify_burns_work_and_returns_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(passwords, "ITERATIONS", 10)

    assert passwords.dummy_verify("unknown-account-password") is None
