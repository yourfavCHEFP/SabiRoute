# R2 — live provider matrix gate

**Recorded:** 2026-11-18 · **Branch:** `sec/deps-nov` · **HEAD at observation:** `fb7583b`
**Status:** `BLOCKED — NOT DONE`. This record does not close R2.

## 1. Why this record exists

`reports/my_scorecard.md:87` records R2 as unit-tested with a live matrix absent:
`0 live calls`, one historical `0/1 AUTH_FAIL` result. No live-provider matrix file exists
in the tree. A tree search for provider-matrix and live-provider artefacts found only
`reports/provider_verification.json`.

## 2. Evidence

| Claim | Evidence | Label |
|---|---|---|
| Offline provider harness is green | `tests/test_provider_harness.py` 6/6 in the scorecard row; code mapping of 14 aliases and 19 model YAMLs inspected | `[VERIFIED BY INSPECTION]` |
| Only historical live result is one failed call | `reports/provider_verification.json` — generated `2026-10-10T10:46:30.661837+00:00`, `total: 1`, `passed: 0`, `failed: 1`, `error_type: AUTHENTICATION_ERROR` | `[VERIFIED BY INSPECTION]` |
| No provider credential is set in this process environment | Set/empty status check only: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `TOGETHERAI_API_KEY`, `DEEPINFRA_API_KEY`, `MOONSHOT_API_KEY`, `MINIMAX_API_KEY`, `CLOUDFLARE_API_KEY`, `OPENROUTER_API_KEY`, `CEREBRAS_API_KEY`, `NVIDIA_NIM_API_KEY`, `COHERE_API_KEY`, `POLLINATION_API_KEY`, `QODER_API_KEY` all `EMPTY`; no value was read or printed | `[VERIFIED BY RUNTIME]` |
| No new live call was made here | No provider request was issued; `scripts/test_providers.py` was inspected but not executed | `[VERIFIED BY INSPECTION]` |

`.env` was not read or printed. Credential status above refers only to the process environment
used for this observation.

## 3. Exact gate

A live matrix requires a fresh, explicit owner row naming:

1. the provider aliases to exercise;
2. the credential source, with values never printed or committed;
3. a spend ceiling and non-stream/stream scope;
4. the accepted outcome taxonomy, including authentication failure and rate limit;
5. authority to write the resulting matrix into `reports/`.

`OFFICIAL_SABIROUTE_ENGINEERING_TEAM_MOBILIZATION_ORDER.md` §7 places external provider
spending, unapproved provider requests, credential changes, and live provider execution
without explicit authorization outside autonomous scope. That gate has not been issued here.

## 4. Frozen boundary

The C11 `--max-tokens` provider-harness feature must not be amended, extended, re-committed, or
absorbed into another commit. This record changes no harness code and no configuration.

## 5. Position

`R2: OFFLINE HARNESS GREEN · LIVE MATRIX ABSENT · 0 AUTHORIZED LIVE CALLS · BLOCKED`

The matrix cannot honestly be marked DONE from configuration presence, prior mapping, or a
historical `AUTH_FAIL`. No status is upgraded by this record.
