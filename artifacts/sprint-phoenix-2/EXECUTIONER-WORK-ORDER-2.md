# EXECUTIONER WORK ORDER 2 — R6.2 → R6.5, AND THE R7 OFFLINE ITEMS

**Issued:** 2026-11-17 · **Branch:** `sec/deps-nov` · **HEAD at issue:** `d115073`
**Supersedes:** `artifacts/sprint-phoenix/EXECUTIONER-WORK-ORDER.md` for R6.2–R6.5 scope. The R6.0/R6.1
order remains the historical record of that run and is not rewritten.
**Extends:** `artifacts/sprint-phoenix/R6-COMPLETION-PROMPT.md` (R6.0/R6.1 scope, now spent).
**Read with:** `R6.1-FOUNDATION-CONTRACT.md`, `BUILD-MAP-R6-TO-R8.md`, `OWNER-SIGNATURE-SHEET.md`.

---

## 0. THE CEILING — READ BEFORE ANYTHING ELSE

The owner asked for 100% in one run. **Four items cannot reach 100% by any agent act.** They are
listed first so no one discovers them at hour six and calls the run a failure.

| # | Item | Why no work order closes it |
|---|---|---|
| 1 | **R8 acceptance** | Requires a stable SHA → **T1/T8 by a fresh session with no prior context** → owner green. The author does not review its own work. An executioner verdict is not a verdict. |
| 2 | **WP-5 owner closure decision** | An owner act. `R6_SCORECARD.md` §1 records it NOT STARTED / BLOCKED. |
| 3 | **F-02 real genesis hash** | Permanently gated on the registration ledger (authorisation row 8 — **never**). Stays *accepted, unproven, not blocking*. |
| 4 | **R6.1 exit criterion 4** | The owner's review of the contract draft. |

**Therefore the honest maximum for this run is:**

- R6.2–R6.5 **built, tested, and shipped dark** (`enabled=false`) — implementation stops being 0%
- R6.6–R6.7 **specified**, not executed
- R7's **offline** items done; its infrastructure items remain blocked
- R8 **untouched and still BLOCKED**

**Do not report this run as "R6 complete".** Report it as *pipeline built, feature off, R8 still
blocked*. A run that claims more than this has inflated a label, and label inflation is the one
failure this repository has spent a sprint correcting.

---

## 1. OWNER AUTHORISATION — REQUIRED BEFORE STEP A1

This work order is **inert** until the owner grants the tranche. The executioner must not begin
Tranche B on the strength of this document alone.

The owner must state, in their own words, something equivalent to:

> I authorise tranche 2: R6.2, R6.3, R6.4 and R6.5, built dark with `enabled=false` as the default.
> I authorise the R7 offline items in Tranche D. I do not authorise R6.6–R6.7 execution, R8, the
> registration ledger, or any push.

Record the owner's words verbatim in the run report. If the grant is absent or narrower, **stop at
the boundary of what was granted** and say exactly which tranches were live.

---

## 2. TRANCHE A — VERIFY, THEN COMMIT (small; must pass before B)

### A1 — Verify the three baseline refs

`R6.1-FOUNDATION-CONTRACT.md` §2.1 declares every `:NNN` ref in the I1–I9 table `319a711`-relative
except the I9 window. Exactly one baseline ref has ever been checked (`:1311`). Three have not.

```bash
git show 319a711:src/sabiroute/api/completions.py | sed -n '915,925p;1162,1170p;1195,1203p'
```

For each of `:919` (claimed: `FrozenOriginal` construction), `:1166` (claimed: capability
eligibility), `:1199` (claimed: the reservation):

- **If it holds at `319a711`** — the label is earned. Leave it, and record the verification.
- **If it does not hold at `319a711` either** — **delete the ref**. A coordinate correct at neither
  commit is worse than no coordinate, because it invites trust. Do not replace it with a guess.

At HEAD these three are: `:919` a 404 unknown-model message, `:1166` quota-denial handling, `:1199`
a route-misconfiguration 503. The reservation is `store.reserve_budget` at `:1244`.

### A2 — Commit the contract

`R6.1-FOUNDATION-CONTRACT.md` is modified and unstaged. R6.1's exit criterion 2 is ticked inside an
uncommitted file, so the exit evidence currently exists only in the working tree.

Stage **by explicit path only**. Inspect `git diff --cached`. Commit. No `git add .`, no `-A`.

### A3 — Confirm the baseline is green before building on it

```
./.venv/bin/python -m ruff check src tests scripts config
./.venv/bin/python -m mypy src
./.venv/bin/python -m pytest -q
shasum -a 256 -c REPORTS-MANIFEST.sha256
```

Record the actual output. If any is red, **stop** — do not build a pipeline on a red tree.

---

## 3. TRANCHE B — R6.2 → R6.5, THE PIPELINE

**The seam is already defined.** `R6.1-FOUNDATION-CONTRACT.md` §2.2 fixes where each contract lands:

| Contract | Lands in |
|---|---|
| I1, I7, I9 | `src/sabiroute/api/completions.py` |
| I2, I3, I4, I8 | new `src/sabiroute/request_transform/` |
| I5 | **`src/sabiroute/config/validation.py` — Track A protected** |
| I6 | `request_transform/` + `capabilities.py` (read-only) |

**The I9 window at HEAD `d115073`: strictly after `:1337`, before `:1366`.** Note that `:1338`–`:1365`
is entirely the body of `_handle_attempt_loop_cancellation`; nothing in it executes. The operative
insertion point is **immediately before `:1366`**, after the nested def ends at `:1364`. Do not
insert inside the def.

### B1 — R6.2: immutable original, canonical form, metadata, validation

Build `src/sabiroute/request_transform/` with:

- **I1 `FrozenOriginal`** — a deep-frozen copy: a new list of new dicts, not a shallow copy of the
  client's. The current client shallow-copies. Byte-equality pre/post is a **test**, not an
  assumption.
- **I2 `CanonicalRequest`** — deterministic and idempotent. Same input → same bytes; canonicalising
  twice changes nothing. **Never expands** (output ≤ input). Unsupported shapes fail closed to
  `CanonicalisationError` → fail-to-original, **never a 4xx**.
- **I3 `EffectiveRequest`** — frozen; **one per logical request**. Re-derivation per attempt is
  forbidden. Monotone-shrink: output ≤ original. This is load-bearing for the reservation at
  `:1244`, which is taken on the original.
- **I4 `TransformationRecord`** — frozen tuple of ids, versions, counts, hashes, `fallback_reason`.
  **Never carries text.** Read-only to the API.
- **I8 `ValidatedEffective`** — failures degrade to the original, never a 4xx. Same caps as I1
  (256 msgs / 500k chars / 1 MiB).

**Exit:** unit tests for each contract, including the negative cases — non-idempotent input,
expansion attempt, oversized input, unsupported shape. Byte-equality test for I1.

### B2 — R6.3: the optimisation policy (I5)

Lands in `src/sabiroute/config/validation.py`. **This is a Track A protected file.** Read the
protection rule in `CLAUDE.md` before touching it, and state in the report exactly what you changed
and why the change is inside the grant.

- `OptimizationPolicy`: `enabled=false` **default**, `strategy`, `version`, `max_ratio`, per-route
  override.
- Loaded **once at startup**, frozen after load. A mid-request flip would split one reservation
  across two requests.
- Invalid config → **startup failure**, not a runtime degrade.
- `max_ratio` bounds shrinkage. **No expansion knob.**

**`max_ratio` direction, scope and range are an OWNER SLOT** (contract §4). Do not invent a value.
Ship the field, validate its type, and leave the number unset with a named default of `None`.

### B3 — R6.4: the compression reimplementation

**`litellm.compress()` is rejected** — build map §5.3, eight findings. Do not import it. Reimplement
the two ideas that are right:

1. **`get_protected_indices`** — system messages, last user message, last assistant message, and
   **every message up to and including the last Anthropic `cache_control` breakpoint**. That last
   one is load-bearing: rewriting a row inside a cached prefix turns the next request's cache *read*
   into a cache *write*, making compression actively more expensive.
2. **The atomic tool-exchange span** — preserve tool-call pairing. Never split a call from its
   result.

The four decisions in build map §5.4 must each be made **explicitly in code and in the report**:

| Decision | Do not default to |
|---|---|
| Granularity | whole messages (stock) — a constraint in a low-ranked message is deleted with it |
| Truncation safety | line-split 70/30 (stock) — on a JSON body this yields syntactically invalid content |
| Token accounting | the engine's estimator — two estimators means two "tokens saved" numbers |
| Bypass surface | protected indices only — needs a policy enum and request correlation |

**The I2 250 ms / 2× bytes budget is an OWNER SLOT** (contract §4). It is a **synchronous event-loop
stall**, not a wall-clock budget. Ship the check, leave the threshold unset, default the feature off.

**Exit:** tests proving a cached prefix is never rewritten, a tool exchange is never split, and
truncation never produces invalid JSON.

### B4 — R6.5: capability checks, bypass, fail-to-original

- **I6** — reuse the existing capability enum in `capabilities.py:11–60`. **No new enum.** Dropping
  `tool_use`, `structured_output`, `vision` or multimodal → **hard fail to original**.
- **I7 `BypassDecision`** — immutable per request, evaluated once, default-off. A malformed caller
  signal is **ignored** in favour of the operator default; it never errors.
- **I9** — the call-site guard, immediately before `:1366`. Swallows `Exception`, **never
  `BaseException`** — `CancelledError` must propagate. Logs once at warning with `redact_secrets`.

**Exit:** a test that a raised exception inside the transform leaves the original request intact and
the response unchanged; a test that `CancelledError` propagates; a test that a malformed bypass
signal falls back to the operator default.

### B5 — The whole pipeline ships dark

`enabled=false` is the default at every layer. The pipeline must be **inert** until the owner fills
the two slots and flips the flag. Prove it: a test that with `enabled=false` the bytes sent to the
provider are byte-identical to the pre-R6 path.

---

## 4. TRANCHE C — R6.6 / R6.7, SPECIFICATION ONLY

- **C1 — R6.6:** the validation and evidence specification. What evidence proves the pipeline works,
  in what environment, at what authority. **Specify; do not execute.**
- **C2 — R6.7:** the staged rollout design — stages, gates, rollback, kill switch. **Design; do not
  deploy.** No staging environment is authorised.

---

## 5. TRANCHE D — R7 OFFLINE ITEMS

Only the items that need no infrastructure and no push:

- **D1** — compose E2E definition (write it; do not run it against managed services)
- **D2** — backup/restore scripts and their tests against disposable local PostgreSQL
- **D3** — the GitHub workflow **file** (write it; **do not push**, so it never runs)

**Not in scope:** managed PostgreSQL, TLS/off-host transport, multi-instance Redis, staging, any GH
run. Those stay in R7's outstanding list.

---

## 6. HARD STOPS

- **No push.** No `git push` of any kind without a separate, explicit owner authorisation.
- **No `main`.** Never modify it.
- **No `git add .` or `git add -A`.** Explicit paths only; inspect `git diff --cached` every time.
- **No amend, reset, clean, stash, discard, merge, rebase, cherry-pick, force-push.**
- **No hand-editing `uv.lock`.** `uv` only; `./.venv/bin/python` for every command.
- **No reading or printing `.env` values.** Env-var secrets only.
- **Protected paths** — `.env`, `uv.lock`, `.github/**`, `.mcp.json`, `.claude/**`,
  `.playwright-cli/**`, `brag-output/**`, `reports/provider_verification.json`. `config/validation.py`
  is Track A: touch it only inside the B2 grant, and say so.
- **`training_authorized` stays `false`.** Phase 13 gate.
- **The registration ledger is permanently gated.** Never instantiate it.
- **Do not issue a T1/T8 verdict.** That is a fresh session's act, not yours.
- **Do not tick R6.1 criterion 4 or WP-5.** Owner acts.
- **Do not invent a threshold, budget or ratio.** The two slots stay slots.

---

## 7. REPORTING

Report in the `CLAUDE.md` §3 structure. Additionally:

- **Per tranche:** what was built, what was tested, what was **not** built and why.
- **Every claim labelled** `[M]` / `[R]` / `[I]` / `[?]`. Never upgrade a label without re-derivation.
- **The owner's authorisation words, verbatim.**
- **The two slots, restated as still open.**
- **A plain list of what you could not complete.** This is the most valuable section. A run that
  reports nothing incomplete has either done everything or is not looking.

**Do not write "Done."** State what is true, what is unproven, and what is blocked.

---

## 8. WHAT THIS ORDER CANNOT DELIVER

Restated because it will be asked again at the end of the run:

- **R8 stays BLOCKED.** Stable SHA → T1/T8 (fresh session) → owner green. None of those is yours.
- **WP-5 stays NOT STARTED.** Owner act.
- **F-02 stays accepted-unproven.** The real genesis hash needs the permanently-gated ledger.
- **R6.1 criterion 4 stays unticked.** Owner review.
- **R6.6–R6.7 are specified, not executed.**
- **R7's infrastructure items stay outstanding.**

The run's honest headline is: **the pipeline exists, it is tested, and it is off.**
