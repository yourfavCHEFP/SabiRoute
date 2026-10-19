"""Typed configuration models for SabiRoute and LiteLLM."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..capabilities import Capability, CapabilityDeclaration


class LiteLLMParams(BaseModel):
    """Parameters for one LiteLLM model deployment."""

    model: str
    api_key: str | None = None
    api_base: str | None = None
    account_id: str | None = None
    model_config = ConfigDict(extra="allow", frozen=True)


class DeploymentConfig(BaseModel):
    """One public provider alias and the LiteLLM route behind it."""

    model_name: str
    litellm_params: LiteLLMParams
    input_cost_per_million_tokens: Decimal | None = Field(default=None, ge=0)
    output_cost_per_million_tokens: Decimal | None = Field(default=None, ge=0)
    capabilities: dict[Capability, CapabilityDeclaration] | None = None
    model_config = ConfigDict(extra="allow", frozen=True)

    @field_validator("capabilities", mode="before")
    @classmethod
    def validate_capability_declarations(cls, value: Any) -> Any:
        if value is None:
            return value
        if not isinstance(value, dict):
            raise ValueError(
                "capabilities must map each capability to true, false, or unknown"
            )
        if any(
            not isinstance(declaration, bool)
            and declaration != "unknown"
            for declaration in value.values()
        ):
            raise ValueError("capability declarations must be true, false, or unknown")
        return value


class LiteLLMSettings(BaseModel):
    """General LiteLLM proxy tuning settings."""

    request_timeout: int = 120
    drop_params: bool = True
    set_verbose: bool = False
    model_config = ConfigDict(extra="allow", frozen=True)


class GeneralSettings(BaseModel):
    """Top-level gateway settings loaded from the config file."""

    master_key: str | None = None
    model_config = ConfigDict(extra="allow", frozen=True)


class RoutingScoringConfig(BaseModel):
    """Versioned weights and freshness requirements for measured routing."""

    policy_version: str = "deterministic-v1"
    reliability_weight: float = Field(default=0.7, ge=0, le=1)
    latency_weight: float = Field(default=0.3, ge=0, le=1)
    minimum_samples: int = Field(default=5, ge=1)
    max_signal_age_seconds: int = Field(default=3600, ge=1)
    model_config = ConfigDict(extra="forbid", frozen=True)

    @field_validator("policy_version")
    @classmethod
    def validate_policy_version(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("policy_version must not be empty")
        return value

    @model_validator(mode="after")
    def validate_weights(self) -> RoutingScoringConfig:
        if abs(self.reliability_weight + self.latency_weight - 1.0) > 1e-9:
            raise ValueError("routing scoring weights must sum to 1")
        return self


class SabiRouteConfig(BaseModel):
    """The full configuration shape used by SabiRoute."""

    model_list: list[DeploymentConfig] = Field(default_factory=list)
    litellm_settings: LiteLLMSettings = Field(default_factory=LiteLLMSettings)
    general_settings: GeneralSettings = Field(default_factory=GeneralSettings)
    routing_scoring: RoutingScoringConfig = Field(default_factory=RoutingScoringConfig)
    model_config = ConfigDict(extra="allow", frozen=True)

    @classmethod
    def from_mapping(cls, raw: dict[str, Any]) -> SabiRouteConfig:
        """Create a typed config object from a plain Python mapping."""

        return cls.model_validate(raw)
