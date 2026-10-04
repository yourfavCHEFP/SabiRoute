"""Typed configuration models for SabiRoute and LiteLLM."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


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
    model_config = ConfigDict(extra="allow", frozen=True)


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


class SabiRouteConfig(BaseModel):
    """The full configuration shape used by SabiRoute."""

    model_list: list[DeploymentConfig] = Field(default_factory=list)
    litellm_settings: LiteLLMSettings = Field(default_factory=LiteLLMSettings)
    general_settings: GeneralSettings = Field(default_factory=GeneralSettings)
    model_config = ConfigDict(extra="allow", frozen=True)

    @classmethod
    def from_mapping(cls, raw: dict[str, Any]) -> SabiRouteConfig:
        """Create a typed config object from a plain Python mapping."""

        return cls.model_validate(raw)
