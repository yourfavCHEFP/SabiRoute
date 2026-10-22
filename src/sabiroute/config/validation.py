from __future__ import annotations

import os
import re

from .models import SabiRouteConfig

_ENV_REFERENCE_PATTERN = re.compile(r"^os\.environ/[A-Za-z_][A-Za-z0-9_]*$")

# Explicit, default-off opt-in that permits literal *marked test*
# credentials in configuration. It exists for controlled local testing
# only. It never authorises an arbitrary literal provider credential.
TEST_CREDENTIAL_OPT_IN_ENV_VAR = "SABIROUTE_ALLOW_TEST_CREDENTIALS"

_TEST_CREDENTIAL_OPT_IN_ENABLED = {"1", "true", "yes", "on"}
_TEST_CREDENTIAL_OPT_IN_DISABLED = {"0", "false", "no", "off"}


class ConfigValidationError(ValueError):
    """Raised when SabiRoute configuration fails semantic validation."""


def validate_config(
    config: SabiRouteConfig,
    *,
    allow_test_credentials: bool | None = None,
) -> SabiRouteConfig:
    """
    Validate SabiRoute configuration after Pydantic parsing.

    This function performs semantic checks that are more specific
    to SabiRoute than basic Pydantic type validation.

    ``allow_test_credentials`` selects whether literal *marked test*
    credentials are accepted. ``None`` (the default) resolves the opt-in
    from the ``SABIROUTE_ALLOW_TEST_CREDENTIALS`` environment variable,
    which is off unless explicitly enabled.
    """

    allow_test = (
        _allow_test_credentials_from_env()
        if allow_test_credentials is None
        else allow_test_credentials
    )

    if not config.model_list:
        raise ConfigValidationError("model_list must contain at least one deployment.")

    aliases: set[str] = set()

    for deployment in config.model_list:
        if not deployment.model_name.strip():
            raise ConfigValidationError(
                "Every deployment must have a non-empty model_name."
            )

        if deployment.model_name in aliases:
            raise ConfigValidationError(
                f"Duplicate model_name detected: {deployment.model_name!r}"
            )

        aliases.add(deployment.model_name)

        model = deployment.litellm_params.model.strip()

        if not model:
            raise ConfigValidationError(
                f"Deployment {deployment.model_name!r} has an empty LiteLLM model."
            )

        api_key = deployment.litellm_params.api_key

        if api_key is not None and api_key.startswith("os.environ/"):
            if not _ENV_REFERENCE_PATTERN.match(api_key):
                raise ConfigValidationError(
                    f"Invalid environment reference in "
                    f"{deployment.model_name!r}: {api_key!r}"
                )
        elif api_key is not None:
            # Production configuration must not embed literal provider
            # secrets. Marked test credentials are accepted only behind the
            # explicit opt-in; every other literal must be an os.environ/
            # reference. The offending value is never echoed (name only).
            if _is_test_credential(api_key):
                if not allow_test:
                    raise ConfigValidationError(
                        f"Deployment {deployment.model_name!r} embeds a literal "
                        f"test credential; literal test credentials are disabled "
                        f"by default. Set {TEST_CREDENTIAL_OPT_IN_ENV_VAR}=1 to "
                        f"allow them for controlled local testing only, or use "
                        f"an 'os.environ/VAR_NAME' reference instead."
                    )
            else:
                raise ConfigValidationError(
                    f"Deployment {deployment.model_name!r} embeds a literal "
                    f"api_key; use an 'os.environ/VAR_NAME' reference instead."
                )

    if config.litellm_settings.request_timeout <= 0:
        raise ConfigValidationError(
            "litellm_settings.request_timeout must be greater than zero."
        )

    return config


def _allow_test_credentials_from_env(raw: str | None = None) -> bool:
    """Resolve the literal test-credential opt-in from the environment.

    Unset or blank means disabled. ``1``/``true``/``yes``/``on`` enable it
    and ``0``/``false``/``no``/``off`` disable it. Any other value is a
    configuration error and fails loudly rather than silently defaulting.
    The raw value is never echoed, so a value pasted into the wrong
    variable cannot leak into logs or error text.
    """

    value = os.environ.get(TEST_CREDENTIAL_OPT_IN_ENV_VAR) if raw is None else raw

    if value is None:
        return False

    token = value.strip().lower()

    if not token:
        return False

    if token in _TEST_CREDENTIAL_OPT_IN_ENABLED:
        return True

    if token in _TEST_CREDENTIAL_OPT_IN_DISABLED:
        return False

    raise ConfigValidationError(
        f"{TEST_CREDENTIAL_OPT_IN_ENV_VAR} must be one of '1', 'true', 'yes', "
        f"'on', '0', 'false', 'no', 'off' (case-insensitive); got an "
        f"unrecognized value."
    )


def _is_test_credential(value: str) -> bool:
    """Recognize explicitly marked non-secret test credentials.

    Only values that cannot be confused with a real provider secret are
    accepted: the ``sk-test-`` / ``sk-literal-test`` prefixes used by this
    repository's own test suite. Anything else is treated as a secret.
    """
    candidate = value.strip()
    if candidate != value:
        return False
    return candidate.startswith(("sk-test-", "sk-test_", "sk-literal-test"))
