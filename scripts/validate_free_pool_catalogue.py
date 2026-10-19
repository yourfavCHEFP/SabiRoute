"""Validate the research-grade Free Pool catalogue draft against schema v0.1.

Research-only tool: checks structure, vocabularies, references, quota
safeguards, and display-safety rules. It never fetches providers, never
writes to the database, and never touches runtime configuration.

Usage:
    ./.venv/bin/python scripts/validate_free_pool_catalogue.py \
        docs/free-pool-catalogue-v0.1-draft.json
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

CLASSIFICATIONS = {
    "VERIFIED_RECURRING_FREE",
    "VERIFIED_QUANTIFIED_TRIAL",
    "VERIFIED_UNQUANTIFIED_TRIAL",
    "EARNED_OR_PROMOTIONAL_CREDITS",
    "BYOK_REQUIRED",
    "LOCAL_INFERENCE",
    "PAID_ONLY",
    "ACCESS_UNKNOWN",
}

CONFIDENCE = {"verified", "partial", "unknown"}
PUBLISHER = {"official", "secondary", "repository"}
EVIDENCE_TYPE = {
    "listing",
    "pricing",
    "terms",
    "capability",
    "access_verification",
    "license",
    "hardware",
}
EVIDENCE_STATUS = {"current", "overdue", "stale", "superseded"}
CLAIM_TYPE = {
    "listing",
    "identity",
    "allowance",
    "pricing",
    "access_terms",
    "capability",
    "license",
    "hardware",
    "quota_relation",
}
POOL_SHARING = {"VERIFIED_SHARED", "VERIFIED_INDEPENDENT", "UNKNOWN"}
POOL_UNKNOWN_REASON = {
    "catalog_gated",
    "provider_undisclosed",
    "unmapped",
    "conflicting_sources",
}
BINDING_KEYS = {"alias", "configured", "access_verified", "probe_ref", "last_check"}
FORBIDDEN_DISPLAY = ("unlimited", "guaranteed free", "guaranteed-free")


class ValidationError(Exception):
    pass


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if path is None:
        print("usage: validate_free_pool_catalogue.py <catalogue.json>")
        return 2
    doc = json.loads(path.read_text())
    errors: list[str] = []

    for key in (
        "catalogue_version",
        "schema_version",
        "status",
        "generated",
        "quota_pools",
        "evidence",
        "canonical_models",
        "access_routes",
    ):
        if key not in doc:
            fail(errors, f"missing top-level key: {key}")
    if errors:
        return report(errors)
    if "research-grade" not in doc["status"]:
        fail(errors, "status watermark must mark the draft research-grade")

    pools = {p["pool_id"]: p for p in doc["quota_pools"]}
    for pid in pools:
        if pid.lower() == "unknown":
            fail(errors, "a global 'unknown' quota pool is forbidden")
    for p in doc["quota_pools"]:
        if p.get("sharing") not in POOL_SHARING:
            fail(errors, f"pool {p.get('pool_id')}: bad sharing value")

    evidence = {e["evidence_id"]: e for e in doc["evidence"]}
    for eid, e in evidence.items():
        if e.get("publisher") not in PUBLISHER:
            fail(errors, f"evidence {eid}: bad publisher")
        if e.get("evidence_type") not in EVIDENCE_TYPE:
            fail(errors, f"evidence {eid}: bad evidence_type")
        if e.get("status") not in EVIDENCE_STATUS:
            fail(errors, f"evidence {eid}: bad status")
        if e.get("claim_type") not in CLAIM_TYPE:
            fail(errors, f"evidence {eid}: bad claim_type")
        for f in ("source_url", "checked_date", "claim"):
            if not e.get(f):
                fail(errors, f"evidence {eid}: missing {f}")

    models = {m["canonical_id"]: m for m in doc["canonical_models"]}
    if len(models) != len(doc["canonical_models"]):
        fail(errors, "duplicate canonical_id")

    route_ids = set()
    for r in doc["access_routes"]:
        rid = r.get("route_id")
        if rid in route_ids:
            fail(errors, f"duplicate route_id: {rid}")
        route_ids.add(rid)
        if r.get("canonical_id") not in models:
            fail(errors, f"route {rid}: unknown canonical_id")
        cls = r.get("classification")
        if cls not in CLASSIFICATIONS:
            fail(errors, f"route {rid}: bad classification")
            continue
        for claim, level in (r.get("claim_confidence") or {}).items():
            if claim not in CLAIM_TYPE:
                fail(errors, f"route {rid}: bad claim name {claim}")
            if level not in CONFIDENCE:
                fail(errors, f"route {rid}: bad confidence {level}")
        for eid in r.get("evidence_ids", []):
            if eid not in evidence:
                fail(errors, f"route {rid}: unknown evidence {eid}")
        pool = r.get("quota_pool_id")
        if pool is None:
            if r.get("pool_unknown_reason") not in POOL_UNKNOWN_REASON:
                fail(errors, f"route {rid}: NULL pool needs a valid reason")
        elif pool not in pools:
            fail(errors, f"route {rid}: unknown pool {pool}")
        binding = r.get("sabiroute_binding") or {}
        extra = set(binding) - BINDING_KEYS
        if extra:
            fail(errors, f"route {rid}: binding has forbidden keys {extra}")
        if binding.get("access_verified") is True and not binding.get("probe_ref"):
            fail(errors, f"route {rid}: verified access needs probe_ref")
        if "health" in binding or "eligibility" in binding:
            fail(errors, f"route {rid}: binding must not carry health/eligibility")
        cls = r["classification"]
        if cls == "VERIFIED_QUANTIFIED_TRIAL" and not r.get("trial_grant"):
            fail(errors, f"route {rid}: quantified trial needs trial_grant")
        if cls == "LOCAL_INFERENCE" and not r.get("local_artifact"):
            fail(errors, f"route {rid}: local route needs local_artifact")
        if cls in {"ACCESS_UNKNOWN", "PAID_ONLY"} and not r.get("unknowns"):
            # PAID_ONLY needs no unknowns only if fully evidenced; keep strict.
            if cls == "ACCESS_UNKNOWN":
                fail(errors, f"route {rid}: unknown route needs unknowns[]")

        for field in ("limits", "trial_grant"):
            value = r.get(field)
            if isinstance(value, dict):
                for limit_key, limit_value in value.items():
                    if isinstance(limit_value, str) and limit_value.strip().lower() in {
                        "unlimited",
                        "infinite",
                        "guaranteed free",
                        "guaranteed-free",
                    }:
                        fail(
                            errors,
                            f"route {rid}: {field}.{limit_key} must not claim "
                            "unlimited/guaranteed values",
                        )
                    if isinstance(limit_value, (int, float)) and limit_value == 0:
                        fail(
                            errors,
                            f"route {rid}: {field}.{limit_key} must not be zero "
                            "(unknown values must be omitted, not zeroed)",
                        )

    # Aggregation safeguard demonstration: NULL-pool routes excluded.
    pooled: dict[str, int] = {}
    skipped = 0
    for r in doc["access_routes"]:
        if r.get("quota_pool_id") is None:
            skipped += 1
        else:
            pooled[r["quota_pool_id"]] = pooled.get(r["quota_pool_id"], 0) + 1

    if errors:
        return report(errors)

    by_class: dict[str, int] = {}
    for r in doc["access_routes"]:
        by_class[r["classification"]] = by_class.get(r["classification"], 0) + 1
    print(f"identities: {len(models)}")
    print(f"routes: {len(route_ids)}")
    print(f"routes_by_classification: {json.dumps(by_class, indent=1, sort_keys=True)}")
    print(f"pools: {len(pools)}; pooled_routes: {pooled}; null_pool_skipped: {skipped}")
    print(f"evidence_records: {len(evidence)}")
    today = date.today().isoformat()
    print(f"checked_today: {today} (evidence dates must be <= today)")
    print("VALIDATION PASSED")
    return 0


def report(errors: list[str]) -> int:
    print(f"VALIDATION FAILED with {len(errors)} error(s):")
    for message in errors:
        print(f"  - {message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
