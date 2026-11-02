"""F-06a literal-credential policy — config validation rules.

Lane ownership: R3 (core security / credential policy). Moved verbatim out of
``tests/test_request_limits.py`` so the R7 release-evidence package does not
carry another lane's evidence. Bodies are unchanged.

Scope: ``sabiroute.config.validation.validate_config`` accepting only an
``os.environ/`` reference or an explicitly marked test credential, rejecting
literal secrets without echoing the value, and rejecting whitespace-padded
values. These are the only tests covering this policy — the R3 leakage suite
covers redaction/egress, not config admission.
"""

from __future__ import annotations


def test_literal_secret_rejected_without_value_leak():
    from sabiroute.config.models import SabiRouteConfig
    from sabiroute.config.validation import ConfigValidationError, validate_config

    secret = "sk-live-REALISTIC-SECRET-abc123"
    try:
        validate_config(
            SabiRouteConfig.from_mapping(
                {
                    "model_list": [
                        {
                            "model_name": "prod",
                            "litellm_params": {
                                "model": "openai/gpt-4o-mini",
                                "api_key": secret,
                            },
                        }
                    ]
                }
            )
        )
    except ConfigValidationError as exc:
        assert "literal" in str(exc).lower()
        assert secret not in str(exc)
    else:
        raise AssertionError("literal secret was accepted")


def test_marked_test_credential_accepted():
    from sabiroute.config.models import SabiRouteConfig
    from sabiroute.config.validation import validate_config

    config = validate_config(
        SabiRouteConfig.from_mapping(
            {
                "model_list": [
                    {
                        "model_name": "t",
                        "litellm_params": {
                            "model": "openai/gpt-4o-mini",
                            "api_key": "sk-test-fixture-only",
                        },
                    }
                ]
            }
        )
    )
    assert config.model_list[0].litellm_params.api_key == "sk-test-fixture-only"


def test_allowlist_rejects_whitespace_padded_values():
    from sabiroute.config.models import SabiRouteConfig
    from sabiroute.config.validation import ConfigValidationError, validate_config

    for bad in (" sk-test-123", "sk-test-123 ", "sk-test-123\n"):
        try:
            validate_config(
                SabiRouteConfig.from_mapping(
                    {
                        "model_list": [
                            {
                                "model_name": "t",
                                "litellm_params": {
                                    "model": "openai/x",
                                    "api_key": bad,
                                },
                            }
                        ]
                    }
                )
            )
        except ConfigValidationError:
            pass
        else:
            raise AssertionError(f"whitespace-padded value accepted: {bad!r}")


def test_env_reference_accepted_and_missing_var_fails():
    from sabiroute.config.models import SabiRouteConfig
    from sabiroute.config.validation import validate_config

    config = validate_config(
        SabiRouteConfig.from_mapping(
            {
                "model_list": [
                    {
                        "model_name": "t",
                        "litellm_params": {
                            "model": "openai/gpt-4o-mini",
                            "api_key": "os.environ/OPENAI_API_KEY",
                        },
                    }
                ]
            }
        )
    )
    assert config.model_list[0].litellm_params.api_key == "os.environ/OPENAI_API_KEY"
    # Missing-variable behavior lives in the loader/resolver layer:
    from sabiroute.config.loader import ConfigLoadError, _resolve_os_environ_value

    try:
        _resolve_os_environ_value("os.environ/SABIROUTE_DEFINITELY_UNSET_VAR_XYZ")
    except ConfigLoadError as exc:
        assert "SABIROUTE_DEFINITELY_UNSET_VAR_XYZ" in str(exc)
    else:
        raise AssertionError("missing env var was accepted")
