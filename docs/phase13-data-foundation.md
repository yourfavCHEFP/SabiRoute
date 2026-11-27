# Phase 13.1 — Routing data foundation

SabiRoute persists a versioned, content-free `pre_routing_features` snapshot for
each deployment decision. The snapshot is constructed before provider execution
and stored separately from the ordered `routing_decisions` outcome records on
the same logical-request usage row. Both arrays use the same attempt order.
`feature_schema_version` identifies the current schema as `1.1`; existing
schema `1.0` rows remain legacy records and are not assigned fabricated
temporal provenance.

The snapshot is an explicit allowlist. It includes the logical request ID,
attempt number, decision time, request classification, requested route/policy,
candidate and eligible sets, required capabilities, request-shape flags, safe
size/token estimates, output cap, routing strategy/version, measured score
context, and optional experiment/propensity fields. The prompt, completion,
tools payload, response schema, credentials, API key, and user identity are not
copied into the snapshot. Unsupported/multimodal token estimation remains null.
No selection-propensity mechanism currently exists, so those fields remain null.

Outcome records retain attempt outcome, HTTP status when known, failure
category, latency, provider-reported usage, and cost only when calculable from
configured pricing. These are labels/evaluation outcomes, not that attempt's
features.

## Audit and export

Run a read-only database audit:

```sh
PYTHONPATH=src .venv/bin/python scripts/audit_routing_dataset.py
```

Optionally write an explicitly diagnostic-only export. It retains unmatched
records with exclusion reasons and cannot be treated as a training dataset:

```sh
PYTHONPATH=src .venv/bin/python scripts/audit_routing_dataset.py \
  --diagnostic-export work/routing-dataset-diagnostic.json
```

The audit script only reflects and selects from `sabiroute_request_usage`; it
does not call the application store initializer, create tables, alter schema,
or train a model. Diagnostic records keep pre-routing features and
post-execution outcomes in separate objects, omit API key/project identifiers,
and mark unmatched, malformed, ineligible, or provenance-deficient rows with
inspectable exclusion reasons. These records are diagnostic only.

The separate `--export` option writes a candidate JSON envelope for human
review. It refuses to write when readiness is `BLOCKED`, any attempt is
unmatched or invalid, selected-deployment eligibility is not verified, or
temporal provenance is incomplete. Even a successful candidate has
`training_authorized: false` and requires human review. It does not authorize
model training.

The report preserves the source and meaning of decision, attempt-start,
attempt-completion, and outcome-recording timestamps. It distinguishes stored,
missing, unavailable, invalid/timezone-unknown, and legacy/unknown-schema
values. An outcome-recording timestamp is the time the outcome object is
assembled, not a database commit timestamp.

The report also includes `phase13_readiness`: explicit pairing, request/attempt
consistency, schema compatibility, provenance and leakage issues,
label-variation, and chronological-split blockers. It applies no minimum
row-count threshold. A structurally clear dataset advances only to human
review; the report never authorizes training.

`chronological_split` partitions on logical request groups so all fallback
attempts from a request remain together. The audit flags the data as
observational: an unselected but eligible deployment has no counterfactual
outcome. Do not interpret missing outcomes as failures or successes.

No universal sample-adequacy threshold is assumed. The audit reports counts,
coverage, missingness, time range, class balance, and deployment observations;
an optional threshold is only descriptive when explicitly supplied by the
operator.

## Phase 13.2 — Runtime verification

The current checkout was verified in an isolated local SabiRoute instance
against the existing PostgreSQL and LiteLLM services. One bounded non-streaming
request through the measured `research` policy selected OpenRouter, and one
bounded streaming request selected Groq, whose `streaming: true` declaration is
explicitly verified in configuration. Both requests completed successfully.

Both persisted records contain schema `1.1` feature snapshots and attempt
outcomes associated with the same logical request. Their historical-summary
cutoffs are present and match their decision timestamps; attempt start,
completion, and outcome-recording timestamps are ordered. Each new request
passes the per-request dataset integrity audit. The streaming response delivered
20 SSE data frames and terminated with `[DONE]`. The temporary verification key
was revoked.

The aggregate audit remains invalid because it still contains one older
attempt without a feature snapshot and legacy rows without temporal provenance.
Those records remain visible as integrity issues and were not rewritten. The
current telemetry path is verified; the dataset is still insufficient for
Phase 13.3 because all six recorded provider attempts are successful and there
is no outcome variation. The chronological split is also unavailable because
the existing unmatched attempt has no decision timestamp. Phase 13.3 remains
locked.

The read-only PostgreSQL audit after the live requests found 7 logical requests,
6 provider attempts, 5 requests with feature snapshots, and 6 labeled outcomes.
Stored feature-schema counts are 2 records at `1.1`, 3 at `1.0`, and 2 without
a schema version. Only 2 attempts have verifiable `1.1` temporal provenance;
4 attempt records have legacy or unavailable provenance, including the
unmatched historical attempt. The aggregate audit reports one feature/outcome
count mismatch and one outcome without a feature snapshot. Latency and provider
usage are present on all 6 attempts; actual cost is unavailable on all 6.

### Historical unmatched record

The fresh read-only database query identified request
`c43966db-759c-464c-9bd6-39d7c4ae065e`, created at
`2026-10-09 07:57:11.933178+01:00`. Its logical-request row exists with
`final_status: 200` and one successful `sabiroute-groq` provider-attempt
outcome. The attempt's `request_id` and `logical_request_id` match the row.
The row currently has zero feature snapshots; both feature and attempt schema
versions and all three attempt timestamps are absent. The usage table does not
retain prior row versions, so it cannot establish whether a feature snapshot
ever existed or why it is missing.

No repair was made. Preserve the outcome and keep the aggregate integrity check
failed. Do not invent a feature snapshot or timestamps. A future training export
must exclude this unmatched observation unless an authoritative original
snapshot is recovered; deleting the outcome would conceal rather than resolve
the audit finding.

The isolated Gateway process began without prior in-memory reliability or
latency observations: neither live snapshot contained a latest historical
observation timestamp. Its recorded as-of cutoff therefore establishes the
decision-time boundary, but does not provide a historical signal or prove the
provenance of older aggregate history. Across the persisted snapshots, request
shape is narrow (chat only; no tools, response-format variation, or multimodal
requests). Groq and OpenRouter were jointly eligible twice, while Gemini had
one eligible observation. Outcomes exist only for selected deployments, so
this remains observational data with selection bias and no counterfactual
labels. The full dataset still cannot be chronologically split because at least
one exported attempt has no decision timestamp.

## Phase status and next gate

Keep these statuses separate:

- **Implementation:** the Phase 13.1 feature snapshot and read-only audit
  implementation are present in the working tree; they are not yet isolated in
  a Phase 13 commit.
- **Live verification:** the current telemetry path passed one bounded
  non-streaming and one bounded streaming request.
- **Phase 13.2 closure:** pending. The live-runtime subgate passed, but the
  aggregate dataset-integrity acceptance criterion has not passed.
- **Aggregate integrity:** failed; one historical feature/outcome mismatch and
  one outcome without a feature snapshot remain. No historical records were
  repaired or inferred.
- **Phase 13.3 training readiness:** blocked by the integrity mismatch,
  incomplete temporal provenance, no outcome variation, and unavailable
  chronological split. Training is not authorized.

The read-only readiness result is a screening aid, not a statistical adequacy
claim. It does not set a universal observation threshold and cannot establish
that a model will outperform deterministic-v1.

## Safe observation collection

Let normal, authorized SabiRoute traffic generate observations over time. Do
not send extra traffic just to increase row counts, randomize provider
selection, or deliberately cause provider failures. Keep API-level rejections
separate from provider-attempt outcomes. Record outcomes only for deployments
that actually ran; an eligible but unselected deployment has no outcome label.
Review the read-only audit periodically and preserve legacy integrity issues as
issues. Consider Phase 13.3 only after the pairing and temporal gates pass, a
leakage-safe chronological split is possible, and observed labels have useful
variation for the approved target. Passing those checks still requires a
separate human review of dataset coverage and evaluation design.

## Scope

This phase adds telemetry and offline audit utilities only. It does not change
deterministic-v1, capability or health semantics, fallback behavior, provider
configuration, model selection, or provider execution. No ML dependency or
training code is added.
