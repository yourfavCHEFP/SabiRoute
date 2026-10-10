"""Offline tests for the provider verification harness's max_tokens support.

These tests never call a real provider: litellm.completion is mocked and
argument parsing is exercised in-process.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

HARNESS_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "test_providers.py"
)


def load_harness() -> object:
    spec = importlib.util.spec_from_file_location(
        "sabiroute_test_providers_harness", HARNESS_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Register before exec so dataclasses can resolve string annotations
    # via sys.modules during module execution.
    sys.modules["sabiroute_test_providers_harness"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def harness() -> object:
    return load_harness()


def _ok_response() -> SimpleNamespace:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))]
    )


def test_non_streaming_passes_max_tokens(harness: object) -> None:
    with mock.patch("litellm.completion", return_value=_ok_response()) as call:
        status, _, _, _ = harness.test_non_streaming(
            model="test/model", timeout=60, max_tokens=32
        )
    assert status == "PASS"
    assert call.call_count == 1
    assert call.call_args.kwargs["max_tokens"] == 32


def test_streaming_passes_max_tokens(harness: object) -> None:
    chunks = [SimpleNamespace(choices=[])]
    with mock.patch("litellm.completion", return_value=iter(chunks)) as call:
        status, _, _, _ = harness.test_streaming(
            model="test/model", timeout=60, max_tokens=16
        )
    assert status == "PASS"
    assert call.call_count == 1
    assert call.call_args.kwargs["max_tokens"] == 16


def test_limit_omitted_preserves_previous_behavior(harness: object) -> None:
    with mock.patch("litellm.completion", return_value=_ok_response()) as call:
        status, _, _, _ = harness.test_non_streaming(
            model="test/model", timeout=60
        )
    assert status == "PASS"
    assert "max_tokens" not in call.call_args.kwargs

    chunks = [SimpleNamespace(choices=[])]
    with mock.patch("litellm.completion", return_value=iter(chunks)) as call:
        status, _, _, _ = harness.test_streaming(model="test/model", timeout=60)
    assert status == "PASS"
    assert "max_tokens" not in call.call_args.kwargs


def test_deployment_propagates_max_tokens(harness: object) -> None:
    deployment = {"model_name": "sabiroute-test", "litellm_params": {"model": "test/model"}}
    with mock.patch("litellm.completion", return_value=_ok_response()) as call:
        result = harness.test_deployment(
            deployment=deployment,
            timeout=60,
            test_stream=False,
            max_tokens=24,
        )
    assert result.status == "PASS"
    assert result.credential_status == "PRESENT"
    assert call.call_count == 1
    assert call.call_args.kwargs["max_tokens"] == 24


def test_max_tokens_rejects_non_positive(harness: object) -> None:
    for bad in ("0", "-5"):
        with mock.patch.object(
            sys, "argv", ["test_providers.py", "--max-tokens", bad]
        ):
            with pytest.raises(SystemExit):
                harness.parse_args()


def test_max_tokens_defaults_to_none(harness: object) -> None:
    with mock.patch.object(sys, "argv", ["test_providers.py"]):
        args = harness.parse_args()
    assert args.max_tokens is None
