# R6-CLOSE-FINAL-05 — Independent Verification of the R6.0-D Evidence Manifest

**Status:** EVIDENCE — **NOT EXECUTED**. This document tracks nothing, stages
nothing, commits nothing, pushes nothing, and creates no REG or VER record,
ledger, key, signature or checkpoint.

**Date:** 2026-11-07 (UTC)

**Repository baseline:** `feat/sabiroute-routing-foundation` @
`08201da8013a58b486d5fa2d6c46b36588a27781`.

**Subject:** independent re-derivation of the claims in
`docs/r6-close-final-04-r6.0-d-evidence-manifest-and-privacy-review-2026-11-07.md`
(FINAL-04), performed with independent tooling and independently authored
detection patterns.

---

## 1. Method

Every claim in FINAL-04 was recomputed from the working tree rather than read
from the document. The privacy scan used a separately written scanner with its
own pattern set, not the author's. Digest comparisons were byte-exact against the
raw file bytes with no normalisation.

---

## 2. Baseline Git state

| Fact | Observed |
|---|---|
| `HEAD` | `08201da8013a58b486d5fa2d6c46b36588a27781` |
| Branch | `feat/sabiroute-routing-foundation` |
| `git ls-files docs` | **16** tracked files |
| `git ls-files 'docs/r6-*'` | **0** — the R6 governance corpus is entirely untracked |
| Modified tracked files | **2** (`src/sabiroute/api/completions.py`, `tests/test_r6_settlement_integrity.py`) |
| Staged files | **0** |

Both modified files are preserved and were not altered by this verification.
`completions.py` carries comment-only reflow; `test_r6_settlement_integrity.py`
is purely additive (+161, −0).

---

## 3. Manifest verification — 38 rows (as then constituted)

All **38** rows of FINAL-04 §2 were recomputed. For every file the SHA-256, the
byte size and the line count reproduce exactly.

**Row-count correction (C-2, verified 2026-11-08).** **38 rows were present at
verification time** — this report could not be one of them. FINAL-04 §2 was
afterwards revised to 39 rows, adding this report as row 7; the other 38 are
unchanged. Current manifest total: **39** rows. The `0 mismatches` result above
is the measurement over the 38 rows then present, not a claim about the 39th.

**Result: 0 mismatches across 38 files × 3 attributes.**

The three U2-bound digests are unchanged and reproduce:

| File | SHA-256 |
|---|---|
| `docs/r6-t16-r6-decision-option-register.md` | `43c7331c8045026fb57695b74230897d0efcf1952e1fc1c337149e2a202c558c` |
| `docs/r6-registration-protocol-03b-r1.md` | `3a00363278de1427945a8ab7f77870f3a10f07b1acd09031c6f174e9c3cd512b` |
| `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md` | `2ff885e32ffbcc90c7dc7d49631b28b7eafa49b46958de6d01c17f3789fee14f` |

---

## 4. O3 / O4 vectors reproduced

Recomputed from the exact T16 bytes (`docs/r6-t16-r6-decision-option-register.md:163-164`)
applying 03B-R1 §8, and from the decision pack §3.5/§3.6 reference computation.

| Vector | Bytes | SHA-256 | Result |
|---|---:|---|---|
| O3 Alt-1 (value only, `A3: ` retained, LF preserved) | 163 | `97dc52a6b4880c53a9da4e84219c37b3cfda3070d52ff3cc287e87e64fbff149` | PASS |
| O3 Alt-1b (`A3: ` stripped) | 159 | `e067ed95785ab190ca658cf1b05e9576d74c98e1b340da421a2fce046e769098` | PASS |
| O3 Alt-2 (label + space + value) | 183 | `35de850fa80b00ecbe2c03b7846b489f3247c251351f53a9456f19176d926ccb` | PASS |
| O3 hazard (hard-break spaces stripped — negative vector) | 161 | `fc16e6d2ffd7d6fc19ad683816fb22aae7f89c336d14caf6c043761729a233d6` | PASS (must not equal Alt-1) |
| O4 genesis `prev` constant | — | `e893bd2cea4dfaa0db92c7343038d85c1cc50995d08bb5f1bdfbf38cba66d307` | PASS |
| O4 worked example, canonical line (no LF) | 508 | `ad1484b0758f0accfd9986ed6f2d5f8fac1ded3a83d95974ed58af7fc74caf28` | PASS |
| O4 worked example, line + LF | 509 | `452a05bb8c241e46b3e86851821dd3daa604e478baad6ed41354e0dda592bbbe` | PASS |

**Negative control.** Hashing proposal §3.2's placeholder line yields
`f7749d467829f5fcfeb3613b32f6987712e62879704d3b2f4cf80c706a8c2e9b`, **not**
`ad1484b0…`. This is the mechanical basis of finding F1.

---

## 5. Privacy scan

Independently written scanner; patterns for AWS access keys, private-key blocks,
GitHub and Slack tokens, JWTs, bearer tokens, generic `key/secret/token/password`
assignments, email addresses, absolute home paths and IPv4 addresses.

**Result: 1 finding, low severity. No credentials.**

| File | Line | Class | Severity |
|---|---:|---|---|
| `docs/r6-registration-protocol-03b-r1-u1-u3-verification-report.md` | 229 | absolute home path (discloses OS username) | **Low** |

No AWS key, private key, GitHub or Slack token, JWT, bearer token, generic secret
assignment, email address or IPv4 address was found in any corpus file.

**Limitation.** The scan is heuristic. It detects the listed patterns; it does not
prove the absence of every possible secret.

---

## 6. Conformance suite

```
python3 -m pytest tests/test_r6_registration_digest_conformance.py -q
67 passed, 2 skipped
```

The two skips are the executable form of the open decisions: `T10` (BLOCKED on
O3) and `T11` (BLOCKED on O4/O5). They remain skipped because the canonical
documents are unchanged.

---

## 7. Findings and disposition

| # | Finding | Severity | Owner disposition |
|---|---|---|---|
| **F1** | C-7 cited proposal §3.2, whose worked example retains placeholders the O4 decision forbids as test inputs; the placeholder line hashes to `f7749d46…`, not the published `ad1484b0…`. | **Material** | **Accepted — remediated.** C-7 now names decision pack §3.5/§3.6 as the normative worked example with its exact 508-byte line and digest; proposal §3.2's example is marked illustrative and non-normative. Schema and canonicalisation unchanged. |
| **F2** | C-6 appended a prospective single-line owner-response rule not authorised by the O3 decision. | Low | **Not approved as written — remediated.** The rule is removed from C-6. The Alt-1 exact-response-value boundary is retained. O3 is not reinterpreted as Alt-3. |
| **F3** | Decision pack §2.1 cited the A3 response at `T16:165-166`; it is at `163-164`. | Low | **Accepted — corrected.** Citation fixed. The addendum's `T16:165` references point at the A3 *provenance* line and are accurate; they were not changed. |
| **F4** | FINAL-04's privacy review covers only the 38 manifest files and never scans itself. | Informational | **Accepted — clarified.** FINAL-04 now states explicitly that it inventories the corpus while excluding its own file from its own digest table, and this report is included in the revised manifest. |

---

## 8. What this report does not do

- It does not apply canonical corrections C-1…C-7. **The canonical documents
  remain unmodified and the corrections remain unapplied.**
- It does not modify `docs/r6-registration-protocol-03b-r1.md` or
  `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md`.
- It does not create a REG or VER record, a ledger, an entry, a key, a signature,
  or a checkpoint.
- It does not stage, commit or push any file.
- It does not satisfy `PARAM-F.3` independent verification of a registration.
- It does not mark Gate R6.0-D met.
- It does not grant G7 or authorise registration, signing, checkpoint creation,
  R6.1, migrations, deployment, or production use.

**EVIDENCE — NOT EXECUTED.**
