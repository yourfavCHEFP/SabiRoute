"""Path and shape tests for :mod:`sabiroute.config.loader`.

Covers the branches that decide where configuration comes from and what
happens when it is malformed: the dotenv discovery fallback, non-string
values passing through untouched, an ``os.environ/`` reference with no
variable name, tuple recursion, a missing config file, a YAML root that is
not a mapping, and a resolved config that stops being a mapping.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from sabiroute.config import loader


def test_non_string_values_pass_through_untouched() -> None:
    assert loader._resolve_os_environ_value(42) == 42
    assert loader._resolve_os_environ_value(None) is None
    assert loader._resolve_os_environ_value(["os.environ/HOME"]) == ["os.environ/HOME"]


def test_environment_reference_without_a_name_is_rejected() -> None:
    with pytest.raises(loader.ConfigLoadError) as excinfo:
        loader._resolve_os_environ_value("os.environ/")

    assert "must include a variable name" in str(excinfo.value)


def test_resolves_references_inside_tuples(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SABI_TEST_TOKEN", "tok")

    resolved = loader._resolve_environment_variables(
        ("os.environ/SABI_TEST_TOKEN", 5, {"nested": "os.environ/SABI_TEST_TOKEN"})
    )

    assert resolved == ("tok", 5, {"nested": "tok"})


def test_environment_file_falls_back_to_discovered_dotenv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    discovered = tmp_path / "discovered.env"
    discovered.write_text("SABI_TEST_FALLBACK=1\n", encoding="utf-8")
    monkeypatch.setattr(loader, "DEFAULT_ENV_PATH", tmp_path / "absent.env")
    monkeypatch.setattr(loader, "find_dotenv", lambda usecwd=False: str(discovered))
    loaded: list[tuple[str, bool]] = []
    monkeypatch.setattr(
        loader,
        "load_dotenv",
        lambda path, override=False: loaded.append((str(path), override)),
    )

    loader._load_environment_file()

    assert loaded == [(str(discovered), False)]


def test_environment_file_is_skipped_when_nothing_is_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(loader, "DEFAULT_ENV_PATH", tmp_path / "absent.env")
    monkeypatch.setattr(loader, "find_dotenv", lambda usecwd=False: "")
    loaded: list[str] = []
    monkeypatch.setattr(
        loader, "load_dotenv", lambda path, override=False: loaded.append(str(path))
    )

    loader._load_environment_file()

    assert loaded == []


def test_missing_config_file_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(loader, "_load_environment_file", lambda: None)

    with pytest.raises(loader.ConfigLoadError) as excinfo:
        loader.load_raw_config(tmp_path / "absent.yaml")

    assert "Configuration file not found" in str(excinfo.value)


def test_yaml_root_must_be_a_mapping(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(loader, "_load_environment_file", lambda: None)
    path = tmp_path / "list.yaml"
    path.write_text("- a\n- b\n", encoding="utf-8")

    with pytest.raises(loader.ConfigLoadError) as excinfo:
        loader.load_raw_config(path)

    assert "YAML mapping at the root" in str(excinfo.value)


def test_resolved_configuration_must_remain_a_mapping(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(loader, "_load_environment_file", lambda: None)
    monkeypatch.setattr(
        loader,
        "_resolve_environment_variables",
        lambda value: ["no", "longer", "a", "mapping"],
    )
    path = tmp_path / "config.yaml"
    path.write_text("key: value\n", encoding="utf-8")

    with pytest.raises(loader.ConfigLoadError) as excinfo:
        loader.load_raw_config(path, resolve_env=True)

    assert "must remain a mapping" in str(excinfo.value)


def test_references_are_preserved_without_resolve_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Default behaviour must hand ``os.environ/NAME`` through untouched."""
    monkeypatch.setattr(loader, "_load_environment_file", lambda: None)
    path = tmp_path / "config.yaml"
    path.write_text("api_key: os.environ/SABI_TEST_UNSET\n", encoding="utf-8")

    raw: dict[str, Any] = loader.load_raw_config(path)

    assert raw["api_key"] == "os.environ/SABI_TEST_UNSET"


def test_unset_referenced_variable_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SABI_TEST_DEFINITELY_UNSET", raising=False)

    with pytest.raises(loader.ConfigLoadError) as excinfo:
        loader._resolve_os_environ_value("os.environ/SABI_TEST_DEFINITELY_UNSET")

    assert "is not set but is required" in str(excinfo.value)


def test_resolves_references_inside_lists(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SABI_TEST_TOKEN", "tok")

    assert loader._resolve_environment_variables(
        ["os.environ/SABI_TEST_TOKEN", 1]
    ) == ["tok", 1]


def test_resolve_env_returns_a_mapping_when_resolution_succeeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(loader, "_load_environment_file", lambda: None)
    monkeypatch.setenv("SABI_TEST_TOKEN", "tok")
    path = tmp_path / "config.yaml"
    path.write_text("api_key: os.environ/SABI_TEST_TOKEN\n", encoding="utf-8")

    resolved = loader.load_raw_config(path, resolve_env=True)

    assert resolved == {"api_key": "tok"}


def test_load_config_composes_parsing_then_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw = {"model_list": []}

    class _StubConfig:
        @staticmethod
        def from_mapping(mapping: Any) -> tuple[str, Any]:
            return ("mapped", mapping)

    monkeypatch.setattr(loader, "load_raw_config", lambda path=None: raw)
    monkeypatch.setattr(loader, "SabiRouteConfig", _StubConfig)
    monkeypatch.setattr(loader, "validate_config", lambda config: ("validated", config))

    assert loader.load_config(tmp_path / "ignored.yaml") == ("validated", ("mapped", raw))


def test_plain_strings_are_not_treated_as_references() -> None:
    assert loader._resolve_os_environ_value("plain-value") == "plain-value"


def test_primary_env_file_is_used_when_it_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    present = tmp_path / "present.env"
    present.write_text("X=1\n", encoding="utf-8")
    monkeypatch.setattr(loader, "DEFAULT_ENV_PATH", present)
    discovered: list[bool] = []
    monkeypatch.setattr(
        loader, "find_dotenv", lambda usecwd=False: discovered.append(True) or ""
    )
    loaded: list[tuple[str, bool]] = []
    monkeypatch.setattr(
        loader,
        "load_dotenv",
        lambda path, override=False: loaded.append((str(path), override)),
    )

    loader._load_environment_file()

    assert loaded == [(str(present), False)]
    assert discovered == []
