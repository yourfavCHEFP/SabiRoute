# Phase 13 natural-observation specification v0.1 (2026-10-11)

Status: specification only. No training is authorized by this document.
Training remains blocked until every gate below passes AND a human review
approves. Implementation: `src/sabiroute/intelligence/dataset.py`;
pipeline narrative: `docs/phase13-data-foundation.md`.

## 1. Separating collection, validity, and readiness

- **Collection:** are observations being recorded? (Snapshots persisted
  before execution; outcomes recorded per attempt; see `make_pre_routing_snapshot`,
  `_routing_attempt_event`, `finalize_usage_event`.)
- **Validity:** are they internally consistent and trustworthy?
  (`audit_dataset`: feature/outcome pairing, schema enforcement, temporal
  provenance, eligibility re-checks, quarantine of unmatched rows.)
- **Readiness:** is there enough valid, representative evidence for an
  experiment? (`chronological_split` + `assess_phase13_readiness`.)
  Success at one stage never implies the next.

## 2. Natural-observation definitions

1. **Logical request:** one client call admitted to the gateway, identified
   by a UUID `request_id` created before admission checks.
2. **Provider attempt:** one `LiteLLMClient` execution for that request,
   numbered sequentially from 1; retries, fallback, and streaming frames
   share the request identity.
3. **Feature snapshot:** the `PreRoutingFeatureSnapshot` (schema 1.1,
   allowlisted, extra-forbidden) persisted BEFORE its attempt executes;
   snapshot failure blocks execution (fail-closed).
4. **Terminal outcome:** the finalized `RequestUsageEvent`
   (`final_status` + per-attempt outcome/failure-category/http-status).
   Unfinalized events (`final_status None`) are incomplete records, never
   outcomes.
5. **Timestamps/provenance:** timezone-aware `decision_timestamp`,
   `attempt_started/completed_at`, `outcome_recorded_at`; verified only
   when all required stamps exist, are aware, and order correctly.
   Naive or future-dated stamps are quarantined, never repaired.
6. **Failed/incomplete records:** failed attempts are valid outcomes;
   unfinalized, unpaired, or schema-rejected rows are quarantined as
   `diagnostic_only`, visible to audits, excluded from training rows.
7. **Missing costs/usage:** represented as null (`usage: None`,
   `actual_cost_usd: None`, `total_tokens: None`); estimates are never
   substituted, and totals are sums of observed parts only.
8. **Selected vs unselected:** labels exist ONLY for attempted
   deployments. Unselected candidates receive no outcomes, no
   counterfactuals — selection bias is reported, not corrected by
   invention.
9. **Selection bias:** measured and communicated via attempt/coverage
   counts per deployment and policy; `selection_propensity` stays null
   unless a real randomized logging policy produces it.
10. **Chronological boundaries:** `chronological_split` groups by logical
    request on integrity-eligible, temporally verified rows; fallback
    attempts in one request never straddle train/eval.
11. **Integrity/variation assessment:** `audit_dataset` (pairing, schema,
    provenance, eligibility) plus `len(observed_outcomes) > 1`.
12. **Training authorization:** blockers (`feature_outcome_integrity_failed`,
    `temporal_provenance_incomplete`, `no_outcome_variation`,
    `chronological_split_unavailable`) must ALL clear, yielding
    `READY_FOR_HUMAN_REVIEW` — which authorizes review, not training.

## 3. Non-fabrication rule

Natural observations originate ONLY from genuine gateway execution.
Forbidden as training input: synthetic failures, artificial traffic,
invented timestamps/costs/propensities, reconstructed decision-time
features, counterfactual labels, repaired provenance. Synthetic data is
permitted solely in explicitly labeled unit tests and must never enter
`diagnostic_export` training rows (quarantine dispositions enforce this).

## 4. Gap analysis (what natural traffic must still supply)

- Outcome variation across deployments (currently all-success histories).
- Sufficient temporally verified rows for a defensible chronological
  split with multiple logical requests per side.
- Complete provenance on every included row (no naive stamps).
- Real `selection_propensity` values if any future selector randomizes;
  otherwise propensity-aware methods stay out of scope.
- Observed (not estimated) costs where monetary budgets apply.

Until then: `training_authorized` stays false, and every readiness report
must keep saying BLOCKED with the specific unmet conditions.
