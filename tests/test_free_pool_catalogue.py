"""Offline regression tests for the Free Pool catalogue evidence audit.

These tests never fetch providers and never touch runtime configuration:
they load the research-grade draft JSON and assert the structural validator
passes plus the stale-precision corrections from the 2026-10-11 evidence
audit (exact-count brittleness in E07/E10, rerank-generation drift in E25,
top-up wording in E28).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOGUE_PATH = REPO_ROOT / "docs" / "free-pool-catalogue-v0.1-draft.json"
VALIDATOR_PATH = REPO_ROOT / "scripts" / "validate_free_pool_catalogue.py"


def load_catalogue() -> dict:
    return json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))


def evidence_by_id(doc: dict) -> dict[str, dict]:
    return {e["evidence_id"]: e for e in doc["evidence"]}


def run_validator() -> int:
    spec = importlib.util.spec_from_file_location(
        "sabiroute_free_pool_validator", VALIDATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["sabiroute_free_pool_validator"] = module
    spec.loader.exec_module(module)
    argv = sys.argv
    sys.argv = ["validate_free_pool_catalogue.py", str(CATALOGUE_PATH)]
    try:
        return int(module.main())
    finally:
        sys.argv = argv


def test_catalogue_validator_passes() -> None:
    assert run_validator() == 0


def test_e07_asserts_no_fixed_model_total() -> None:
    claim = evidence_by_id(load_catalogue())["E07"]["claim"]
    assert "345-model" not in claim


def test_e10_does_not_assert_exact_count() -> None:
    claim = evidence_by_id(load_catalogue())["E10"]["claim"]
    assert "36 text-catalog" not in claim


def test_e25_does_not_present_rerank_2x_as_current() -> None:
    claim = evidence_by_id(load_catalogue())["E25"]["claim"]
    assert "rerank-2.x" not in claim


def test_e28_does_not_require_top_up() -> None:
    claim = evidence_by_id(load_catalogue())["E28"]["claim"]
    assert "top-up balance required" not in claim


@pytest.mark.parametrize("evidence_id", ["E07", "E10", "E25", "E28"])
def test_corrected_records_carry_audit_date(evidence_id: str) -> None:
    record = evidence_by_id(load_catalogue())[evidence_id]
    assert record["checked_date"] == "2026-10-11"
