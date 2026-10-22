from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Any, cast

from ..capabilities import DeploymentCapabilities
from ..config.models import SabiRouteConfig
from .base import ProviderDeployment, ProviderInfo


class ProviderRegistry:
    """Central registry for SabiRoute providers and model deployments.

    This class owns metadata and lookup only. It never executes model requests.
    LiteLLM remains responsible for provider execution, retries, cooldowns,
    load balancing, and provider-level fallbacks.
    """

    def __init__(
        self,
        deployments: Iterable[ProviderDeployment] | None = None,
        providers: Iterable[ProviderInfo] | None = None,
    ) -> None:
        self._deployments: dict[str, ProviderDeployment] = {}
        self._providers: dict[str, ProviderInfo] = {}

        for provider in providers or ():
            self.register_provider(provider)

        for deployment in deployments or ():
            self.register(deployment)

    def register_provider(self, provider: ProviderInfo) -> None:
        key = self._normalize_name(provider.name)
        if not key:
            raise ValueError("Provider name cannot be empty.")
        if key in self._providers:
            raise ValueError(f"Provider already registered: {provider.name}")
        self._providers[key] = provider

    def register(self, deployment: ProviderDeployment) -> None:
        name = deployment.name.strip()
        if not name:
            raise ValueError("Deployment name cannot be empty.")
        if name in self._deployments:
            raise ValueError(f"Deployment already registered: {name}")

        provider_key = self._normalize_name(deployment.provider)
        if not provider_key:
            raise ValueError(f"Deployment {name!r} has an empty provider.")
        if provider_key not in self._providers:
            raise ValueError(f"Provider {deployment.provider!r} is not registered.")

        self._deployments[name] = deployment

    def get(self, name: str) -> ProviderDeployment:
        key = name.strip()
        try:
            return self._deployments[key]
        except KeyError as exc:
            raise KeyError(f"Unknown deployment: {name}") from exc

    def get_provider(self, name: str) -> ProviderInfo:
        key = self._normalize_name(name)
        try:
            return self._providers[key]
        except KeyError as exc:
            raise KeyError(f"Unknown provider: {name}") from exc

    def has_deployment(self, name: str) -> bool:
        return name.strip() in self._deployments

    def has_provider(self, name: str) -> bool:
        return self._normalize_name(name) in self._providers

    def list_deployments(self) -> list[ProviderDeployment]:
        return list(self._deployments.values())

    def list_providers(self) -> list[ProviderInfo]:
        return list(self._providers.values())

    def provider_deployments(self, provider: str) -> list[ProviderDeployment]:
        provider_key = self._normalize_name(provider)
        return [
            deployment
            for deployment in self._deployments.values()
            if self._normalize_name(deployment.provider) == provider_key
        ]

    def validate_candidates(self, candidates: Iterable[str]) -> list[str]:
        """Validate deployment names while preserving caller order."""
        validated: list[str] = []
        seen: set[str] = set()

        for candidate in candidates:
            name = candidate.strip()
            if not name:
                raise ValueError("Routing candidate cannot be empty.")
            if name in seen:
                continue
            if not self.has_deployment(name):
                raise KeyError(f"Unknown routing deployment: {name}")
            validated.append(name)
            seen.add(name)

        return validated

    def __iter__(self) -> Iterator[ProviderDeployment]:
        return iter(self._deployments.values())

    def __len__(self) -> int:
        return len(self._deployments)

    @staticmethod
    def _normalize_name(value: str) -> str:
        return value.strip().lower()


def registry_from_config(config: SabiRouteConfig) -> ProviderRegistry:
    """Build the registry from the canonical SabiRoute configuration.

    Secret values remain environment references. Provider-specific LiteLLM
    parameters are preserved in deployment.metadata instead of being dropped.
    """
    registry = ProviderRegistry()
    providers_seen: set[str] = set()

    for model_entry in config.model_list:
        params = model_entry.litellm_params
        litellm_model = params.model.strip()

        if not litellm_model:
            raise ValueError(
                f"Deployment {model_entry.model_name!r} has no LiteLLM model."
            )

        provider = _provider_from_model(litellm_model)
        provider_key = provider.lower()

        if provider_key not in providers_seen:
            registry.register_provider(
                ProviderInfo(
                    name=provider,
                    display_name=provider.replace("_", " ").title(),
                )
            )
            providers_seen.add(provider_key)

        raw_params = _model_dump(params)
        api_key = raw_params.get("api_key")

        api_key_env = _environment_reference_name(api_key)
        api_key_literal = api_key if api_key_env is None else None
        api_base = raw_params.get("api_base")

        metadata = {
            key: value
            for key, value in raw_params.items()
            if key not in {"model", "api_key", "api_base"}
            and value is not None
        }

        registry.register(
            ProviderDeployment(
                name=model_entry.model_name,
                provider=provider,
                model=litellm_model,
                api_key_env=api_key_env,
                api_key=api_key_literal,
                api_base=api_base,
                metadata=metadata or None,
                input_cost_per_million_tokens=model_entry.input_cost_per_million_tokens,
                output_cost_per_million_tokens=model_entry.output_cost_per_million_tokens,
                capabilities=DeploymentCapabilities(
                    supported=frozenset(
                        capability
                        for capability, declaration in (model_entry.capabilities or {}).items()
                        if declaration is True
                    ),
                    unsupported=frozenset(
                        capability
                        for capability, declaration in (model_entry.capabilities or {}).items()
                        if declaration is False
                    ),
                ),
            )
        )

    return registry


def _provider_from_model(model: str) -> str:
    provider, separator, _ = model.partition("/")
    if not separator or not provider.strip():
        raise ValueError(
            f"Invalid LiteLLM model {model!r}; expected 'provider/model'."
        )
    return provider.strip()


def _environment_reference_name(value: Any) -> str | None:
    if not isinstance(value, str):
        return None

    prefix = "os.environ/"
    if not value.startswith(prefix):
        return None

    name = value.removeprefix(prefix).strip()
    return name or None


def _model_dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return cast(dict[str, Any], value.model_dump(exclude_none=False))

    if isinstance(value, dict):
        return dict(value)

    raise TypeError(
        "litellm_params must be a Pydantic model or mapping-compatible object."
    )
