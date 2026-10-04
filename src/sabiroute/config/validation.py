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

    if config.litellm_settings.request_timeout <= 0:
        raise ConfigValidationError(
            "litellm_settings.request_timeout must be greater than zero."
        )

    return config
