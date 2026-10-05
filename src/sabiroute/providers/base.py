from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

_ENV_PREFIX = "os.environ/"


class MissingCredentialError(RuntimeError):
    """Raised when a deployment's credential environment variable is not set."""


def _resolve_env_reference(value: Any) -> Any:
    """Resolve ``os.environ/NAME`` strings into their environment values."""

    if not isinstance(value, str) or not value.startswith(_ENV_PREFIX):
        return value

    name = value.removeprefix(_ENV_PREFIX)
    resolved = os.environ.get(name)
    if resolved is None:
        raise MissingCredentialError(f"Environment variable '{name}' is not set.")

    return resolved


@dataclass(frozen=True, slots=True)
class ProviderDeployment:
    """
    Immutable description of one LiteLLM-backed deployment.

    Credentials are stored as environment variable names and resolved
    lazily at the LiteLLM call boundary, keeping secrets out of config
    snapshots and logs. ``api_key`` holds a literal key only when the
    configuration did not use an environment reference.
    """

    name: str
    provider: str
    model: str
    api_key_env: str | None = None
    api_key: str | None = None
    api_base: str | None = None
    metadata: dict[str, Any] | None = None

    def as_litellm_params(self) -> dict[str, Any]:
        """
        Convert this deployment into LiteLLM SDK parameters.

        ``os.environ/NAME`` references are resolved here. That form is
        only meaningful in LiteLLM proxy config files — the SDK call
        itself must receive the real secret.
        """

        params: dict[str, Any] = {
            "model": self.model,
        }

        if self.api_key_env is not None:
            params["api_key"] = _resolve_env_reference(f"{_ENV_PREFIX}{self.api_key_env}")
        elif self.api_key is not None:
            params["api_key"] = self.api_key

        if self.api_base is not None:
            params["api_base"] = _resolve_env_reference(self.api_base)

        if self.metadata:
            for key, value in self.metadata.items():
                params[key] = _resolve_env_reference(value)

        return params


@dataclass(frozen=True, slots=True)
class ProviderInfo:
    """
    Metadata describing a provider.
    """

    name: str
    display_name: str
    native_litellm: bool = True
    enabled: bool = True
