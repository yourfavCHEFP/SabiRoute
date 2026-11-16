from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

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
            # accepted; everything else is treated as a secret.
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


# --- R6.3 / I5: the optimisation policy -------------------------------------
#
# Track A protected file. This addition is inside the B2 grant of
# EXECUTIONER-WORK-ORDER-2 (owner authorisation, tranche 2). Nothing above this
# line was changed; the existing validators are untouched.
#
# ``max_ratio`` is an OWNER SLOT. The field ships, its type and range are
# validated, and its value is left unset (``None``). No number is chosen here:
# choosing one would be inventing evidence.

class OptimizationPolicy(BaseModel):
    """The optimisation policy, loaded once at startup and frozen after load.

    A mid-request flip would split one reservation across two requests, so the
    object is frozen and is never re-read during a request.
    """

    enabled: bool = False
    strategy: str = "none"
    version: int = Field(default=1, ge=1)
    max_ratio: float | None = None
    model_config = ConfigDict(extra="forbid", frozen=True)

    @field_validator("max_ratio")
    @classmethod
    def _validate_max_ratio(cls, value: float | None) -> float | None:
        if value is None:
            return value
        # Bounds shrinkage only. There is no expansion knob.
        if not 0.0 < value <= 1.0:
            raise ValueError("max_ratio must be greater than 0 and at most 1")
        return value

class RouteOptimizationOverride(BaseModel):
    """A per-route override of the global optimisation policy."""

    enabled: bool | None = None
    strategy: str | None = None
    max_ratio: float | None = None
    model_config = ConfigDict(extra="forbid", frozen=True)

    @field_validator("max_ratio")
    @classmethod
    def _validate_max_ratio(cls, value: float | None) -> float | None:
        if value is None:
            return value
        if not 0.0 < value <= 1.0:
            raise ValueError("max_ratio must be greater than 0 and at most 1")
        return value

class OptimizationSettings(BaseModel):
    """The global policy plus any per-route overrides."""

    policy: OptimizationPolicy = Field(default_factory=OptimizationPolicy)
    routes: dict[str, RouteOptimizationOverride] = Field(default_factory=dict)
    model_config = ConfigDict(extra="forbid", frozen=True)

def load_optimization_settings(raw: object) -> OptimizationSettings:
    """Parse and validate optimisation settings.

    Invalid configuration is a **startup failure**, not a runtime degrade: a
    policy that cannot be understood must not silently become "off" at request
    time, because that would hide a misconfiguration behind a working service.
    """
    if raw is None:
        return OptimizationSettings()
    if not isinstance(raw, dict):
        raise ConfigValidationError("optimization settings must be a mapping")
    try:
        return OptimizationSettings.model_validate(raw)
    except Exception as exc:  # pydantic ValidationError and friends
        raise ConfigValidationError(f"invalid optimization settings: {exc}") from exc

def resolve_optimization_policy(
    settings: OptimizationSettings, route: str | None
) -> OptimizationPolicy:
    """Return the effective policy for one route, applying any override."""
    base = settings.policy
    if route is None or route not in settings.routes:
        return base
    override = settings.routes[route]
    return OptimizationPolicy(
        enabled=base.enabled if override.enabled is None else override.enabled,
        strategy=base.strategy if override.strategy is None else override.strategy,
        version=base.version,
        max_ratio=base.max_ratio if override.max_ratio is None else override.max_ratio,
    )
