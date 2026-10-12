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


ROUTE_YAML = """\
name: testroute
deployments:
  - sabiroute-openai
strategy: priority
max_attempts: 1
"""


def _gateway_state_with_env():
    from sabiroute.gateway import build_gateway_state

    return build_gateway_state()


def test_blank_routes_path_selects_repo_default_not_cwd(tmp_path, monkeypatch):
    from sabiroute.gateway import DEFAULT_ROUTES_PATH

    routes_dir = tmp_path / "routes"
    routes_dir.mkdir()
    (routes_dir / "testroute.yaml").write_text(ROUTE_YAML, encoding="utf-8")

    monkeypatch.setenv("SABIROUTE_ROUTES_PATH", str(routes_dir))
    overridden = _gateway_state_with_env()
    assert overridden.policies.get("testroute").deployments == ["sabiroute-openai"]
    with pytest.raises(ValueError, match="Unknown routing policy"):
        overridden.policies.get("fast")

    for blank in ("", "   "):
        monkeypatch.setenv("SABIROUTE_ROUTES_PATH", blank)
        state = _gateway_state_with_env()
        assert state.policies.get("fast").name == "fast"
        with pytest.raises(ValueError, match="Unknown routing policy"):
            state.policies.get("testroute")

    monkeypatch.delenv("SABIROUTE_ROUTES_PATH", raising=False)
    defaulted = _gateway_state_with_env()
    assert defaulted.policies.get("fast").name == "fast"
    assert str(DEFAULT_ROUTES_PATH).endswith("config/routes")


def test_blank_litellm_url_selects_default_without_network(monkeypatch):
    from sabiroute.gateway import DEFAULT_PROXY_URL, build_gateway_state

    for blank in ("", "   "):
        monkeypatch.setenv("SABIROUTE_LITELLM_URL", blank)
        state = build_gateway_state()
        assert state.client.base_url == DEFAULT_PROXY_URL == "http://127.0.0.1:4000"

    monkeypatch.delenv("SABIROUTE_LITELLM_URL", raising=False)
    assert build_gateway_state().client.base_url == DEFAULT_PROXY_URL

    monkeypatch.setenv("SABIROUTE_LITELLM_URL", "http://127.0.0.1:4123/")
    assert build_gateway_state().client.base_url == "http://127.0.0.1:4123"


def _rate_limiter_db(state) -> int | None:
    client = state.rate_limiter._client  # type: ignore[union-attr]
    return client.connection_pool.connection_kwargs.get("db")


def _rate_limiter_port(state) -> int | None:
    client = state.rate_limiter._client  # type: ignore[union-attr]
    return client.connection_pool.connection_kwargs.get("port")


@pytest.mark.parametrize("blank", ["", "   "])
def test_blank_redis_db_and_port_use_defaults(monkeypatch, blank):
    from sabiroute.gateway import build_gateway_state

    # Blank URL keeps the host branch selected: config loading injects the
    # repository .env for unset vars, so deleting is not enough to isolate.
    monkeypatch.setenv("REDIS_URL", "")
    monkeypatch.setenv("REDIS_HOST", "127.0.0.1")
    monkeypatch.setenv("REDIS_DB", blank)
    monkeypatch.setenv("REDIS_PORT", blank)

    state = build_gateway_state()

    assert state.rate_limiter is not None
    assert _rate_limiter_db(state) == 0
    assert _rate_limiter_port(state) == 6379


def test_explicit_redis_db_and_port_preserved(monkeypatch):
    from sabiroute.gateway import build_gateway_state

    # Blank URL keeps the host branch selected: config loading injects the
    # repository .env for unset vars, so deleting is not enough to isolate.
    monkeypatch.setenv("REDIS_URL", "")
    monkeypatch.setenv("REDIS_HOST", "127.0.0.1")
    monkeypatch.setenv("REDIS_DB", "3")
    monkeypatch.setenv("REDIS_PORT", "6380")

    state = build_gateway_state()

    assert _rate_limiter_db(state) == 3
    assert _rate_limiter_port(state) == 6380


@pytest.mark.parametrize("var,value", [("REDIS_DB", "abc"), ("REDIS_PORT", "abc")])
def test_invalid_redis_numbers_still_fail_loudly(monkeypatch, var, value):
    from sabiroute.gateway import build_gateway_state

    # Blank URL keeps the host branch selected: config loading injects the
    # repository .env for unset vars, so deleting is not enough to isolate.
    monkeypatch.setenv("REDIS_URL", "")
    monkeypatch.setenv("REDIS_HOST", "127.0.0.1")
    monkeypatch.setenv(var, value)

    with pytest.raises(ValueError):
        build_gateway_state()
