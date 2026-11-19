# Competitive Evidence Matrix — draft

**Status:** evidence-index draft only. No competitor is ranked, no comparative
performance figure is asserted, and the OmniRoute same-workload benchmark is
**not done**. This draft upgrades no S18 gate.

**Compiled at:** branch `sec/deps-nov`, HEAD `df2acac3be6e84e1702f1f67f969cf732745d8be`.
**Sources consulted:** `SabiRoute-Master-Build-Checklist-v1.2-CANDIDATE.md:673-682`;
`reports/pre-roadmap-audit.md:107-127`;
`artifacts/sprint-phoenix-2/R2-LIVE-PROVIDER-MATRIX-GATE.md:1-48`;
`artifacts/sprint-phoenix-2/S1-S18-ACCEPTANCE-CROSSWALK.md:16-25`;
`docs/build-map.md:167-181,320-351`; `README.md:352-374`;
`docs/phase13-data-foundation.md:102-109`.

## Reading rule

A row records what a cited source establishes and what remains untested. A local
configuration, an offline harness result, a historical failed call, or an
absence of claims is not a comparative measurement. `[VERIFIED BY INSPECTION]`

## Matrix

| Dimension | SabiRoute evidence status | Comparator evidence status | Untested / remaining gate | Evidence label |
|---|---|---|---|---|
| Provider alias coverage | Offline harness is green; 14 aliases are mapped in configuration. No live matrix exists and the recorded authorized live-call count is zero. | No current OpenRouter or other provider comparison exists in the cited anchors. | Fresh owner-named live matrix: aliases, credential source, spend ceiling, non-stream/stream scope, outcome taxonomy, and report write authority. | VERIFIED BY INSPECTION |
| Historical provider result | `reports/provider_verification.json` records one historical result: `total: 1`, `passed: 0`, `failed: 1`, `error_type: AUTHENTICATION_ERROR`. | No comparator result is paired with it. | Do not treat a historical auth failure as provider performance evidence. No new live call was made for this draft. | VERIFIED BY INSPECTION |
| Coding-agent compatibility | S18 asks for expansion based on demand; the S1–S18 crosswalk records no such comparative evidence. | None supplied in the cited anchors. | Demand definition, agent list, test protocol, and owner review. | VERIFIED BY INSPECTION; UNVERIFIED |
| MCP / A2A integrations | S18 asks for evaluation where appropriate; no integration comparison is recorded in the cited anchors. | None supplied. | Scope decision, protocol fixtures, and measured outcomes. | VERIFIED BY INSPECTION; UNVERIFIED |
| Same-workload OmniRoute benchmark | Checklist S18 requires the same workload and environment. The crosswalk records same-workload benchmark evidence as absent; `reports/pre-roadmap-audit.md:123-124` records that no comparative claims are made or supported. | No OmniRoute result is present. | **NOT DONE.** Requires an authorized benchmark specification, matched workload/environment, reproducible runs, and owner scorecard review. No ranking is inferred. | VERIFIED BY INSPECTION; UNVERIFIED |
| Scorecard strengths, weaknesses, exclusions | The audit states that no differentiator comparison is supported anywhere in the repository. The S18 scorecard update remains a checklist item. | No comparator scorecard exists in the cited anchors. | Owner review of strengths, weaknesses, deliberately excluded features, and release planning from evidence rather than feature counts. | VERIFIED BY INSPECTION |
| Cost / usage economics | The audit records that no metering exists and unit economics are unmodelled. The Phase 13 audit records provider usage on all six attempts but actual cost unavailable on all six. | No comparator cost model is present. | Metering design, cost evidence, and matched-workload cost comparison. | VERIFIED BY INSPECTION; UNVERIFIED |
| Local operational evidence | Local disposable PostgreSQL backup/restore and D1 controlled replay have runtime records in the S1–S18 crosswalk. | No managed or deployed comparator operation is recorded. | Managed PG/TLS, managed backup/restore, hosted CI, compose-up E2E, staging, and production-like rollback/incident evidence. | VERIFIED BY RUNTIME; VERIFIED BY INSPECTION |
| Deliberately empty / blocked surface | `docs/build-map.md:167-181` names zero-byte files that must remain empty and `docs/build-map.md:326-351` names blocked work. | No comparator inventory was collected. | Do not fill placeholders to make a matrix look complete; do not infer competitor feature counts. | VERIFIED BY INSPECTION |

## Explicitly not claimed

- No SabiRoute-versus-competitor performance ranking.
- No borrowed competitor percentage or quality figure.
- No statement that a historical `AUTH_FAIL` measures provider reliability.
- No claim that offline mapping, configuration presence, or a local disposable
  replay is live-provider evidence.
- No claim that the OmniRoute benchmark has run or that S18 is complete.

`SabiRoute-Master-Build-Checklist-v1.2-CANDIDATE.md:673-682` and
`artifacts/sprint-phoenix-2/S1-S18-ACCEPTANCE-CROSSWALK.md:25`
`[VERIFIED BY INSPECTION]`

## Position

`S18: evidence matrix drafted · live provider matrix absent · comparable workload benchmark absent · no rankings asserted · owner scorecard review remains open`
