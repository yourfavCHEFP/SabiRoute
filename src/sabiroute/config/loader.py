"""Utilities for loading and validating the SabiRoute configuration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import find_dotenv, load_dotenv

from .models import SabiRouteConfig
from .validation import ConfigValidationError, validate_config

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "config.yaml"
DEFAULT_ENV_PATH = REPO_ROOT / ".env"


class ConfigLoadError(ValueError):
    """Raised when a configuration file cannot be loaded or parsed."""


def _load_environment_file() -> None:
    """Load environment variables from the project root .env file when present."""

    env_path = DEFAULT_ENV_PATH
    if env_path.exists():
        load_dotenv(env_path, override=False)
        return

    dotenv_path = find_dotenv(usecwd=True)
    if dotenv_path:
        load_dotenv(dotenv_path, override=False)


def _resolve_os_environ_value(value: Any) -> Any:
    """Convert strings like 'os.environ/OPENAI_API_KEY' into the real value."""

    if not isinstance(value, str):
        return value

    prefix = "os.environ/"
    if not value.startswith(prefix):
        return value

    env_name = value.removeprefix(prefix)
    if not env_name:
        raise ConfigLoadError("Environment references must include a variable name.")

    resolved = os.getenv(env_name)
    if resolved is None:
        raise ConfigLoadError(
            f"Environment variable '{env_name}' is not set but is required by the config."
        )

    return resolved


def _resolve_environment_variables(value: Any) -> Any:
    """Recursively resolve environment-variable references in config mappings."""

    if isinstance(value, dict):
        return {
            key: _resolve_environment_variables(item) for key, item in value.items()
        }

    if isinstance(value, list):
        return [_resolve_environment_variables(item) for item in value]

    if isinstance(value, tuple):
        return tuple(_resolve_environment_variables(item) for item in value)

    return _resolve_os_environ_value(value)


def load_raw_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load a raw YAML config file and return the parsed mapping."""

    _load_environment_file()

    config_file = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
    if not config_file.exists():
        raise ConfigLoadError(f"Configuration file not found: {config_file}")

    with config_file.open("r", encoding="utf-8") as file:
        raw_config = yaml.safe_load(file) or {}

    if not isinstance(raw_config, dict):
        raise ConfigLoadError(
            "Configuration file must contain a YAML mapping at the root."
        )

    return _resolve_environment_variables(raw_config)


def load_config(config_path: str | Path | None = None) -> SabiRouteConfig:
    """Load and validate the application config from YAML."""

    raw_config = load_raw_config(config_path)
    config = SabiRouteConfig.from_mapping(raw_config)
    return validate_config(config)


__all__ = [
    "ConfigLoadError",
    "ConfigValidationError",
    "DEFAULT_CONFIG_PATH",
    "REPO_ROOT",
    "load_config",
    "load_raw_config",
]
