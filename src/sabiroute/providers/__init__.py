"""Provider integrations and deployment registry."""

from .base import ProviderDeployment, ProviderInfo
from .registry import ProviderRegistry, registry_from_config

__all__ = [
    "LiteLLMClient",
    "LiteLLMClientError",
    "ProviderDeployment",
    "ProviderInfo",
    "ProviderRegistry",
    "registry_from_config",
]


def __getattr__(name: str):
    if name in {"LiteLLMClient", "LiteLLMClientError"}:
        from .litellm_client import LiteLLMClient, LiteLLMClientError

        if name == "LiteLLMClient":
            return LiteLLMClient
        return LiteLLMClientError
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
