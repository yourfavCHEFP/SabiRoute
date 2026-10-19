from __future__ import annotations

import re

from .models import SabiRouteConfig

_ENV_REFERENCE_PATTERN = re.compile(r"^os\.environ/[A-Za-z_][A-Za-z0-9_]*$")


class ConfigValidationError(ValueError):
    """Raised when SabiRoute configuration fails semantic validation."""


def validate_config(config: SabiRouteConfig) -> SabiRouteConfig:
    """
    Validate SabiRoute configuration after Pydantic parsing.

    This function performs semantic checks that are more specific
    to SabiRoute than basic Pydantic type validation.
    """

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
        elif api_key is not None and not _is_test_credential(api_key):
            # Production configuration must not embed literal provider
            # secrets. Only explicitly marked test credentials are
            # accepted; everything else must be an os.environ/ reference.
            # The offending value is never echoed (name only).
            raise ConfigValidationError(
                f"Deployment {deployment.model_name!r} embeds a literal "
                f"api_key; use an 'os.environ/VAR_NAME' reference instead."
            )

    if config.litellm_settings.request_timeout <= 0:
        raise ConfigValidationError(
            "litellm_settings.request_timeout must be greater than zero."
        )

    return config


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
