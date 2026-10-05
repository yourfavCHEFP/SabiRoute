from __future__ import annotations

import pytest

from sabiroute.config.loader import load_config, load_raw_config
from sabiroute.config.validation import ConfigValidationError

CONFIG_YAML = """\
model_list:
  - model_name: openai-test
    litellm_params:
      model: openai/gpt-4o-mini
      api_key: os.environ/OPENAI_API_KEY
"""


def _write_config(tmp_path, content: str = CONFIG_YAML):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(content, encoding="utf-8")
    return config_file


def test_env_references_preserved_by_default(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-123")

    config = load_config(_write_config(tmp_path))

    assert config.model_list[0].litellm_params.api_key == "os.environ/OPENAI_API_KEY"


def test_resolve_env_true_resolves_eagerly(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-123")

    raw = load_raw_config(_write_config(tmp_path), resolve_env=True)

    key = raw["model_list"][0]["litellm_params"]["api_key"]
    assert key == "sk-test-123"


def test_missing_env_var_does_not_block_loading(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    config = load_config(_write_config(tmp_path))

    assert config.model_list[0].litellm_params.api_key == "os.environ/OPENAI_API_KEY"


def test_malformed_env_reference_rejected(tmp_path):
    bad = CONFIG_YAML.replace("OPENAI_API_KEY", "1BAD_NAME")
    config_file = _write_config(tmp_path, bad)

    with pytest.raises(ConfigValidationError):
        load_config(config_file)
