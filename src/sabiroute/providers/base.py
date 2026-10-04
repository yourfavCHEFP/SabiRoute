from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ProviderDeployment:
    """
    Immutable description of one LiteLLM-backed deployment.
    """

    name: str
    provider: str
    model: str
    api_key_env: str | None = None
    api_base: str | None = None
    metadata: dict[str, Any] | None = None

    def as_litellm_params(self) -> dict[str, Any]:
        """
        Convert this deployment into LiteLLM-compatible parameters.
        """
        params: dict[str, Any] = {
            "model": self.model,
        }

        if self.api_key_env:
            params["api_key"] = f"os.environ/{self.api_key_env}"

        if self.api_base:
            params["api_base"] = self.api_base

        if self.metadata:
            params.update(self.metadata)

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
