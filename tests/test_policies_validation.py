"""Validation tests for :mod:`sabiroute.routing.policies`.

``PolicyRegistry.from_directory`` is the guard that keeps a malformed route
file from reaching the router, so each rejection path is asserted with the
exact diagnostic it produces: unreadable directory, non-mapping YAML, bad
name, duplicate route, missing/blank/duplicate deployments, unsupported
strategy, non-integer or out-of-range max_attempts, and capability problems.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from sabiroute.routing import policies as policies_module
from sabiroute.routing.policies import PolicyRegistry


class _Registry:
    """Structural stand-in for ProviderRegistry.validate_candidates."""

    def __init__(self, known: set[str] | None = None) -> None:
        self.known = known if known is not None else {"dep-a", "dep-b"}
        self.validated: list[list[str]] = []

    def validate_candidates(self, candidates: list[str]) -> list[str]:
        self.validated.append(list(candidates))
        for candidate in candidates:
            if candidate not in self.known:
                raise KeyError(candidate)
        return list(candidates)


def _write(directory: Path, filename: str, body: str) -> Path:
    path = directory / filename
    path.write_text(body, encoding="utf-8")
    return path


def _load(directory: Path, registry: Any = None) -> PolicyRegistry:
    return PolicyRegistry.from_directory(directory, registry or _Registry())


def test_rejects_missing_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError) as excinfo:
        _load(tmp_path / "absent")

    assert "does not exist" in str(excinfo.value)


def test_rejects_yaml_that_is_not_a_mapping(tmp_path: Path) -> None:
    _write(tmp_path, "route.yaml", "- one\n- two\n")

    with pytest.raises(ValueError) as excinfo:
        _load(tmp_path)

    assert "must contain a YAML mapping" in str(excinfo.value)


def test_rejects_blank_route_name(tmp_path: Path) -> None:
    _write(tmp_path, "route.yaml", "name: '   '\ndeployments: [dep-a]\n")

    with pytest.raises(ValueError) as excinfo:
        _load(tmp_path)

    assert "non-empty string" in str(excinfo.value)


def test_rejects_duplicate_route_names(tmp_path: Path) -> None:
    body = "name: dup\ndeployments: [dep-a]\n"
    _write(tmp_path, "a.yaml", body)
    _write(tmp_path, "b.yaml", body)

    with pytest.raises(ValueError) as excinfo:
        _load(tmp_path)

    assert "Duplicate route name: dup" in str(excinfo.value)


def test_rejects_route_without_deployments(tmp_path: Path) -> None:
    _write(tmp_path, "route.yaml", "name: solo\n")

    with pytest.raises(ValueError) as excinfo:
        _load(tmp_path)

    assert "at least one deployment" in str(excinfo.value)


def test_rejects_blank_deployment_entry(tmp_path: Path) -> None:
    _write(tmp_path, "route.yaml", "name: r\ndeployments: [dep-a, '  ']\n")

    with pytest.raises(ValueError) as excinfo:
        _load(tmp_path)

    assert "invalid deployment name" in str(excinfo.value)


def test_rejects_duplicate_deployments(tmp_path: Path) -> None:
    _write(tmp_path, "route.yaml", "name: r\ndeployments: [dep-a, dep-a]\n")

    with pytest.raises(ValueError) as excinfo:
        _load(tmp_path)

    assert "duplicate deployments" in str(excinfo.value)


def test_rejects_unsupported_strategy(tmp_path: Path) -> None:
    _write(tmp_path, "route.yaml", "name: r\ndeployments: [dep-a]\nstrategy: magical\n")

    with pytest.raises(ValueError) as excinfo:
        _load(tmp_path)

    assert "unsupported strategy" in str(excinfo.value)


def test_rejects_boolean_max_attempts(tmp_path: Path) -> None:
    """``true`` parses as int in Python but must not be accepted as a count."""
    _write(tmp_path, "route.yaml", "name: r\ndeployments: [dep-a]\nmax_attempts: true\n")

    with pytest.raises(ValueError) as excinfo:
        _load(tmp_path)

    assert "max_attempts must be an integer" in str(excinfo.value)


def test_rejects_max_attempts_above_candidate_count(tmp_path: Path) -> None:
    _write(tmp_path, "route.yaml", "name: r\ndeployments: [dep-a]\nmax_attempts: 5\n")

    with pytest.raises(ValueError) as excinfo:
        _load(tmp_path)

    assert "between 1 and its candidate count" in str(excinfo.value)


def test_rejects_non_list_capabilities(tmp_path: Path) -> None:
    _write(tmp_path, "route.yaml", "name: r\ndeployments: [dep-a]\nrequired_capabilities: text\n")

    with pytest.raises(ValueError) as excinfo:
        _load(tmp_path)

    assert "required_capabilities must be a list" in str(excinfo.value)


def test_rejects_unknown_capability(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "route.yaml",
        "name: r\ndeployments: [dep-a]\nrequired_capabilities: [not-a-capability]\n",
    )

    with pytest.raises(ValueError) as excinfo:
        _load(tmp_path)

    assert "unknown required capability" in str(excinfo.value)


def test_rejects_repeated_capability(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Duplicate detection is independent of the enum's vocabulary."""
    monkeypatch.setattr(policies_module, "Capability", lambda value: value)
    _write(
        tmp_path,
        "route.yaml",
        "name: r\ndeployments: [dep-a]\nrequired_capabilities: [vision, vision]\n",
    )

    with pytest.raises(ValueError) as excinfo:
        _load(tmp_path)

    assert "repeats a required capability" in str(excinfo.value)


def test_rejects_directory_without_route_files(tmp_path: Path) -> None:
    with pytest.raises(ValueError) as excinfo:
        _load(tmp_path)

    assert "No route YAML files found" in str(excinfo.value)


def test_loads_valid_route_and_normalises_its_name(tmp_path: Path) -> None:
    registry = _Registry()
    _write(
        tmp_path,
        "route.yaml",
        "name: '  MiXeD  '\ndeployments: [dep-b, dep-a]\nmax_attempts: 1\n",
    )

    loaded = _load(tmp_path, registry)

    policy = loaded.get("mixed")
    assert policy.name == "mixed"
    assert policy.deployments == ["dep-b", "dep-a"]
    assert policy.strategy == "priority"
    assert policy.max_attempts == 1
    assert policy.required_capabilities == frozenset()
    assert registry.validated == [["dep-b", "dep-a"]]


def test_falls_back_to_the_file_stem_for_an_unnamed_route(tmp_path: Path) -> None:
    _write(tmp_path, "alpha.yaml", "deployments: [dep-a]\n")

    loaded = _load(tmp_path)

    assert [policy.name for policy in loaded.list()] == ["alpha"]


def test_rejects_deployment_unknown_to_the_registry(tmp_path: Path) -> None:
    _write(tmp_path, "route.yaml", "name: r\ndeployments: [ghost]\n")

    with pytest.raises(ValueError) as excinfo:
        _load(tmp_path)

    assert "Invalid deployment in route" in str(excinfo.value)


def test_get_raises_for_unknown_policy() -> None:
    registry = PolicyRegistry()

    with pytest.raises(ValueError) as excinfo:
        registry.get("does-not-exist")

    assert "Unknown routing policy: does-not-exist" in str(excinfo.value)


def test_register_adds_and_replaces_a_policy() -> None:
    registry = PolicyRegistry()
    first = policies_module.RoutingPolicy(name="custom", max_attempts=4)
    registry.register(first)

    assert registry.get("custom") is first

    replacement = policies_module.RoutingPolicy(name="custom", max_attempts=5)
    registry.register(replacement)

    assert registry.get("custom") is replacement
    assert len(registry.list()) == len(policies_module.DEFAULT_POLICIES) + 1
