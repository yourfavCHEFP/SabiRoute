# SPRINT PHOENIX — PH-0 and PH-3 EXECUTION REPORT

**Date:** 2026-11-16 · **Actor:** Claude Code (executioner)
**Branch:** `sec/deps-nov` @ `1e69ada9` · **HEAD unchanged**
**Scope executed:** PH-0.1, PH-0.2, PH-0.3, PH-3
**Scope NOT executed:** PH-2 (gate failed — see §6)

Evidence labels per `CLAUDE.md` §2: `[M]` measured this session · `[R]` reported by
another actor · `[I]` inferred · `[?]` unverified.

---

## 0. Drift check before any edit

All four anchors matched the brief exactly `[M]`. I was where the brief said.

| Artifact | Bytes | Lines | SHA-256 (prefix) | Verdict |
|---|---:|---:|---|---|
| `docs/r6-t16-r6-decision-option-register.md` | 52,782 | 633 | `43c7331c8045026f` | MATCH |
| `docs/r6-registration-protocol-03b-r1.md` | 14,620 | 384 | `d3125df37b745356` | MATCH |
| `…-owner-parameter-addendum.md` | 39,784 | 661 | `9a817f6dec3bb01f` | MATCH |
| `…WP2_Owner_Decision_Record_Part_4.txt` | 18,710 | 258 | `50251c079b6ac2cb` | MATCH |

Addendum O5 anchors confirmed before editing `[M]`: `:528`, `:533`, `:644`, `:646`
(four occurrences); `:538` = `PARAM-B.5` `(O4)`; `:539` = `PARAM-B.6` `(O1)`.

---

## 1. F-03 — protocol `:213` reads `VER:v1`

**What was wrong.** Two things, and they are different. First, the finding's cited
line is stale: in the 384-line protocol, `:213` is "3. Apply Unicode NFC
normalization" — §8 hash normalization. The `VER:v1` token is at `:155` (§6) and
`:248` (§10 step 8) `[M]`. Second, the token itself is **not** a defect to be
fixed: Part 4 §14.1 records the retire-or-retain question as **OPEN**, the
correction **DEFERRED**, and states that no other decision in that record silently
resolves it. The deferred sixth has no owner code.

**What I changed.** Appended §18 "Dated provenance notes" to the protocol. No
normative text was altered and the token was **not** retired.

**Before / after.** The protocol's final line was unchanged; the note is appended
after it:

```
**DRAFT — OWNER-APPROVED PROTOCOL DECISIONS, NOT YET REGISTERED OR EXECUTED.**
```

now followed by §18, which records: the token's true loci (`:155`, `:248`); that
`:213` is stale; that the token is retained by deferral per Part 4 §14.1; and the
recorded status **"`VER:v1` token — RETAINED, question OPEN, correction DEFERRED."**

**New digest.** 15,898 B / 410 L / `59643d242effe3bca2a50ae4e52e86d28d9b5105465c446cab87e38fc69a6590` `[M]`

**Re-verified after all edits** `[M]`: `grep -n 'VER:v1'` returns `:155`, `:248`
and the §18 note only; `:213` is NFC normalization; the note is present once.

---

## 2. F-04 — correction proposal `:885` "NOT OWNER-APPROVED"

**What was wrong.** The document contradicts itself. Its `:3` banner, updated under
WP2-D12, reads *"PROPOSAL — OWNER-ADOPTED IN PART (WP2-D2 · WP2-D11); INCORPORATED
BY THE WP-2 EDIT PASS — NOT EXECUTED"*. Its closing banner at `:885` still reads
*"PROPOSAL — NOT OWNER-APPROVED — NOT INCORPORATED — NOT EXECUTED"*, and `:882-883`
still says "Nothing in this document is incorporated. Nothing is approved." `[M]`

**What I changed.** Appended a dated provenance note. `:885` and `:882-883` are
retained verbatim and superseded in place, not rewritten.

**Before / after.** `:885` is unchanged:

```
**PROPOSAL — NOT OWNER-APPROVED — NOT INCORPORATED — NOT EXECUTED**
```

The note after it records that the `:3` D12 banner governs, that the WP-2 edit pass
did incorporate the accepted corrections, and that the proposal remains **NOT
EXECUTED** and is **not an approval** — "owner-adopted in part" is narrower than
"owner-approved", and `PARAM-F.3` independent verification is still outstanding.

**New digest.** 49,995 B / 910 L / `b3acfcb3481a2adb67f2ac7b346d3c1df0279851571cbcfc8f6d2274cd891414` `[M]`

**Re-verified** `[M]`: the note is present once; `:885` still carries the old
banner, now explicitly superseded.

---

## 3. F-05 — Parts 1–3 stale measurements

**What was wrong.** Parts 1 and 2 carry byte counts and digests that describe
pre-edit files, with no supersession note. Part 2 `:318` additionally asserts the
addendum "contains **zero** occurrences of `O5`" — live is **four** `[M]`. Part 3
was checked and carries no stale figures of this class `[M]`.

**What I changed.** Appended a dated supersession note to Part 1 and to Part 2.
Every original row is retained verbatim.

**Before / after — Part 1:**

| Locus | Superseded | Live |
|---|---|---|
| `:101` | correction proposal `48,596 B` | **49,995 B**; `b3acfcb3…cd891414` |
| `:102` | protocol `12,619 B`; `3a003632…cd512b` | **15,898 B**; `59643d24…69a6590` |
| `:103` | addendum `38,603 B`; `69166509…3399a6` | **42,917 B**; `601a27a3…a51c49f5` |

Re-measured and still correct: `:100` owner decision pack `39,580 B`; `:104` T16
`52,782 B` `[M]`.

**Before / after — Part 2:** `:73` (12,619 B / `3a003632…`), `:219` (`(348 lines`),
`:220` (embedded `3a003632…`), `:223` ("348 lines and `3a003632…`"), `:229`
("addendum still reads `348 lines`"), and `:318` ("zero occurrences of `O5`") are
each superseded with the live value. The `:318` paragraph's addendum anchors
`:537`/`:538` are also recorded as stale by one — live `:538`/`:539`.

**Re-verified** `[M]`: one F-05 note in each of Part 1 and Part 2; the `:318` claim
is superseded and the live count is four.

---

## 4. F-06 — addendum §12 stale protocol anchors

**What was wrong.** The addendum cites protocol line anchors that no longer
resolve, because the protocol grew 348 → 384 lines in the WP-2 edit pass and
384 → 410 lines in this pass (F-03's §18 note). Named in the finding: `:337`
(blank), `§8:171–185`, `:208–214`, `:130–135`, `:212–214`, `:325` `[M]`.

**What I changed.** Re-derived **15** anchors by locating the cited *content* in
the current protocol — not by applying a fixed offset — and corrected them in
place across §3, §12.1 and §12.2. Added addendum §13 recording every old → new
mapping so the superseded values survive as history.

| Locus | Superseded | Current | Content reached |
|---|---|---|---|
| §3/§12.1 `PARAM-A.3` | `:208-214` | `:238-253` | §10 REGISTER procedure |
| §3/§12.1 `PARAM-A.4` | `§6:130-135` | `§6:157-161` | §6 "independently confirms…" |
| §3/§12.1 `PARAM-A.4` | `§10 step 8:212-214` | `§10 step 8:248-250` | §10 step 8 |
| §3/§12.1 `PARAM-A.4` | `§15:282-300` | `§15:318-336` | §15 read-back |
| §3/§12.1 `PARAM-A.6` | `:325` | `:357-382` | §17 exclusions |
| §3/§12.1 `PARAM-A.1` | `:337` | `:373` | §17 issue 1 |
| §12.1 `PARAM-B.1` | `§8:171-185` | `§8:207-221` | §8 normalization |
| §12.1 `PARAM-E.6` | `:338-339` | `:374-375` | §17 issue 2 |
| §12.2 disposition ×7 | `:337`,`:338-339`,`:340-341`,`:342`,`:343`,`:344`,`:345-346` | `:373`,`:374-375`,`:376-377`,`:378`,`:379`,`:380`,`:381-382` | §17 issues 1–7 |

`03B-R1:58-60` was re-measured and still resolves; unchanged.

**Also corrected:** the addendum's own embedded protocol reference at `:11-12`
(384 lines / `d3125df3…` → 410 lines / `59643d24…`) and §12.3's copy of the same.

**Deliberately NOT corrected, and named in addendum §13:** `:267` and `:402` (both
§8) cite `03B-R1:340-341` / `:338-339` / `:344` for §17 issues 3, 2 and 6. They
carry the same staleness but sit outside F-06's recorded §12 scope. Correct
targets are `:376-377`, `:374-375`, `:380`. Left stale and recorded rather than
silently half-corrected.

**New digest.** 42,917 B / 710 L / `601a27a36e1fc4ed25de0ef45ced6afec67ea61f45a12f12ecf352eaa51c49f5` `[M]`

**Re-verified** `[M]`: every corrected anchor was re-read after the final edit and
lands on the content named above; no stale pattern survives as a live citation
outside the §13 historical table.

---

## 5. PH-3 — synthetic genesis-hash proof

**What I added.** One test, `test_ph3_genesis_entry_hash_is_deterministic_total_and_field_sensitive`,
in `tests/test_r6_registration_digest_conformance.py` (Group 5, beside the existing
genesis fixtures). It **instantiates nothing**: no ledger file, no REG record, no
VER record, no chain head, no real entry. The fixture is decision pack §3.6's
synthetic nine-field preimage, which is explicitly not the real chain head.

It proves three properties:

1. **Determinism** — same fixture, same digest on every call; the canonical form is
   a fixed point, so hashing is independent of the starting representation.
2. **Totality** — defined over the whole nine-field fixture; the digest is always
   64 lowercase hex characters.
3. **Per-field sensitivity** — each of the nine fields is perturbed individually;
   all nine mutations produce well-formed digests, no two collide with each other,
   and none collides with the unmutated fixture.

**F-02 disposition: PARTIALLY PROVEN — never "closed".** The live test
`test_u11_genesis_entry_hash_is_computable` **stays skipped** at `:570`. The
arithmetic is proven; the real genesis hash is not, and remains gated on WP-5.

---

## 6. PH-2 — NOT EXECUTED (gate failed)

The PH-2 gate requires, among other things, **ruff clean** and **mypy clean**.
Neither holds `[M]`:

```text
$ ./.venv/bin/python -m ruff check .
Found 350 errors.
[*] 124 fixable with the `--fix` option (11 hidden fixes can be enabled with the `--unsafe-fixes` option).

$ ./.venv/bin/python -m mypy .
artifacts/sprint13-policy-experiment/stub_server.py: error: Duplicate module named "stub_server" (also at "./artifacts/sprint13-429-drill/stub_server.py")
Found 1 error in 1 file (errors prevented further checking)
```

Both are **pre-existing** and unrelated to this pass. Scoped to the changed file:

```text
$ ./.venv/bin/python -m ruff check tests/test_r6_registration_digest_conformance.py
Found 1 error.        # E731 at :877, a pre-existing `h = lambda` in _genesis_line

$ ./.venv/bin/python -m mypy tests/test_r6_registration_digest_conformance.py
Found 87 errors in 1 file (checked 1 source file)   # all pre-existing missing annotations
```

This session introduced **zero** new ruff or mypy errors: the one mypy error my new
test initially added (a missing return annotation) was fixed by annotating it
`-> None`, taking the file from 88 to 87.

**Decision.** The gate says "If any is false: STOP. Report. Do not commit." I took
that literally rather than reading "clean" charitably as "no new errors", because
the charitable reading is exactly the reading that lets the run keep going. **No
commit was made.** PH-2.1–PH-2.6 were not started; no corpus manifest was written,
nothing was staged.

> ### CORRECTION — 2026-11-16 (same day), added after the fact
>
> **The two gate commands above were run at the wrong scope, and the conclusion
> followed from the wrong command.** `CLAUDE.md` §11 scopes the quality bar to
> `src tests scripts config` for ruff and to `src` for mypy. It does not extend to
> `artifacts/`. Both commands were run repo-wide, so the 350 ruff errors and the
> duplicate-module mypy error are **`artifacts/` scratch-script noise**, not findings
> about the codebase. The "duplicate module" is two `stub_server.py` files in
> `artifacts/sprint13-*` colliding — a type check never ran at all.
>
> Re-run at the gate's actual scope `[M]`, **before** any fix was applied:
>
> ```text
> $ ./.venv/bin/ruff check src tests scripts config
> tests/test_r6_registration_digest_conformance.py:877:5: E731 Do not assign a lambda expression
> Found 1 error.
>
> $ ./.venv/bin/mypy src
> Success: no issues found in 49 source files
> ```
>
> The real blocker was **one pre-existing E731** — `h = lambda s: ...` inside
> `_genesis_line()` — a one-line fix, not a 350-error remediation pass. That fix has
> since been applied (`def h(s: str) -> str:`), after which `[M]`:
>
> ```text
> $ ./.venv/bin/ruff check src tests scripts config
> All checks passed!
>
> $ ./.venv/bin/mypy src
> Success: no issues found in 49 source files
> ```
>
> **What was right and what was wrong.** Stopping and reporting rather than re-reading
> "clean" charitably was the correct instinct, and §6's refusal to make the gate mean
> what convenience wanted is the strongest part of this report. What was wrong is that
> the report never ran the command the gate actually names; it had the scoped figure
> for the changed file (§6 shows `1 error # E731 at :877`) and generalised from
> repo-wide output it had not scoped. The NEXT section below therefore recommended
> "authorise a lint/type remediation pass" — a step that did not exist and would have
> spent owner time on 350 `artifacts/` warnings. **The correct next step was one line.**

---

## 7. PH-0.2 — suites, literal commands and trailing output

```text
$ ./.venv/bin/python -m pytest tests/test_r6_registration_digest_conformance.py -q
SKIPPED [1] tests/test_r6_registration_digest_conformance.py:570: awaiting authorised ledger instantiation
105 passed, 1 skipped in 0.28s

$ ./.venv/bin/python -m pytest tests/test_r6_settlement_integrity.py -q
6 passed in 0.42s

$ ./.venv/bin/python -m pytest -q
774 passed, 10 skipped in 21.74s
```

The conformance count rose 104 → 105 because PH-3 added one test. The single skip
is unchanged and is a **finding, not a pass**. The other nine skips are
environment-gated integration tests (`SABIROUTE_TEST_REDIS_URL` /
`SABIROUTE_TEST_PG_URL` unset) and are unrelated to R6.

---

## 8. PH-0.3 — baseline re-measurement

| Artifact | Old | New | Label |
|---|---|---|---|
| `docs/r6-t16-r6-decision-option-register.md` | 52,782 / 633 / `43c7331c…` | unchanged | `[M]` |
| `docs/r6-registration-protocol-03b-r1.md` | 14,620 / 384 / `d3125df3…` | **15,898 / 410 / `59643d24…`** | `[M]` |
| `…-owner-parameter-addendum.md` | 39,784 / 661 / `9a817f6d…` | **42,917 / 710 / `601a27a3…`** | `[M]` |
| `…u1-u3-correction-proposal-2026-11-07.md` | 48,634 / 885 / `61c68807…` | **49,995 / 910 / `b3acfcb3…`** | `[M]` |
| `…WP2_Owner_Decision_Record_Part_4.txt` | 18,710 / 258 / `50251c07…` | unchanged | `[M]` |
| `REPORTS-MANIFEST.sha256` | 13 entries, all verify `[R]` | 13/13 verify `OK` | `[M]` |
| `docs/r6-*.md` inventory | 42 | **42** | `[M]` |

Promoted `[R]` → `[M]` only for the manifest and the test baseline, both of which I
re-derived this session. The four artifact rows were already `[M]` and were
re-measured rather than assumed.

---

## 9. Contradictions found and how they were handled

1. **F-03 vs Part 4 §14.1.** PH-0.1 authorises "correcting" F-03; Part 4 §14.1
   forbids resolving the `VER:v1` question without an owner decision. Resolved by
   taking "correct by dated supersession" to mean *record the true state*, not
   *change the token*. The token is untouched. If the owner intended retirement,
   that is a separate decision and is not made here.
2. **Build Map §6 ledger vs §6.1 prose.** The ledger table still shows rows 1, 2
   and 7 as "No", while §6.1 states "Rows 1, 2, 6 and 7 are now granted". The
   prompt independently grants all four, so I proceeded on the prompt's authority
   and record the table/prose mismatch here rather than editing the map.
3. **F-06 scope.** The stale-anchor class is wider than the six anchors the finding
   names. I corrected the whole of §12 (15 anchors) and named the two remaining §8
   loci rather than leaving the class half-fixed or silently expanding scope.

---

## 10. Working tree

Intended edits only. **Zero git operations performed** — no add, commit, push,
merge, rebase, reset, stash, checkout or branch op.

| File | Change |
|---|---|
| `docs/r6-registration-protocol-03b-r1.md` | §18 dated note appended (F-03) |
| `docs/…-owner-parameter-addendum.md` | 15 anchors + `:11-12` + §12.3 digest; §13 note (F-06) |
| `docs/…u1-u3-correction-proposal-2026-11-07.md` | dated note appended (F-04) |
| `artifacts/r6-closure/WP2_Owner_Decision_Record_Part_1.txt` | dated supersession (F-05) |
| `artifacts/r6-closure/WP2_Owner_Decision_Record_Part_2.txt` | dated supersession (F-05) |
| `artifacts/r6-closure/R6_SCORECARD.md` | §5 baseline, F-02…F-06, §7 log, status block |
| `tests/test_r6_registration_digest_conformance.py` | 2 vectors refreshed; PH-3 test added |
| `artifacts/sprint-phoenix/PH0-PH3-EXECUTION-REPORT.md` | this report |

`docs/r6-*.md` count: **42** `[M]`. No 43rd document created.

---

## PROVEN / UNPROVEN / BLOCKED BY / NEXT

**PROVEN** `[M]`
- F-03, F-04, F-05, F-06 corrected by dated supersession and each re-verified after
  the final edit.
- F-02 → PARTIALLY PROVEN; `:570` still skipped.
- Conformance 105 passed / 1 skipped · settlement 6 passed · full suite 774 passed /
  10 skipped / 0 failed.
- 3/3 U2 vectors reproduce; 13/13 manifest entries verify; 42-document inventory
  intact.
- Zero new ruff or mypy errors introduced.

**UNPROVEN**
- The real genesis hash — gated on WP-5, not on this pass.
- O6–O8 content; ledger absence.
- Untracked drift 146 → 147 → 149 attribution.
- ~~Corpus durability — still 0 of 42 tracked.~~ **Closed 2026-11-16 — 42 of 42 tracked.**

**BLOCKED BY**
- ~~PH-2: ruff (350 errors) and mypy (1 blocking error) are not clean. Pre-existing,
  but the gate is literal.~~ **Withdrawn — wrong command scope; see the §6 correction.**
- F-01 / D-2: registration locus for O1–O5 undefined.
- D-5 / D-6: BL-22 unsigned, G7 not granted.

**NEXT**
- ~~Owner decision on the ruff/mypy gate: either accept "no new errors" as the
  standard, or authorise a lint/type remediation pass. Only then can PH-2 run.~~ **No such decision is needed** — the only blocker was one
E731, now fixed; scoped ruff and mypy are both clean.
- ~~After PH-2: WP-5 owner closure decision pack.~~ **PH-2 has since run** — see below.

**PH-2 HAS SINCE RUN (2026-11-16, same day).** The 42-document corpus was staged by
explicit path, the staged diff inspected (0 paths outside `docs/r6-*.md`), and committed
as `e0530e5`. Re-derived after the commit: **42 of 42 tracked** `[M]`;
`REPORTS-MANIFEST.sha256` **13/13 verify** `[M]`. **F-09 is CLOSED.**

**STILL BLOCKED — owner acts, not execution:**

- **PH-1** — authorisation rows 3, 4, 5: registration locus (D-2), U4 reading R-A,
  `marker_sha256` / O3. All still `No`.
- **PH-4** — authorisation rows 9, 10, 11: BL-22 (D-5), G7 (D-6), R6.1 (D-7). All still `No`.

**AT THE TIME OF THIS REPORT: NOTHING COMMITTED · NOTHING STAGED · NOTHING PUSHED · BL-22 UNSIGNED · G7 NOT GRANTED**

**SINCE THEN (2026-11-16): `e0530e5` committed — the 42-document corpus only. Nothing
else staged, nothing pushed. BL-22 still unsigned, G7 still not granted.**
