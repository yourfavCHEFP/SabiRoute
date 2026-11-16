# R6-CLOSE-FINAL-04 — R6.0-D Evidence Manifest and Privacy Review

**Status:** EVIDENCE — **NOT EXECUTED**. This document tracks nothing, stages
nothing, commits nothing, pushes nothing, and creates no REG or VER record,
ledger, key, signature or checkpoint.

**Date:** 2026-11-07 (UTC)

**Repository baseline:** `feat/sabiroute-routing-foundation` @
`08201da8013a58b486d5fa2d6c46b36588a27781`.

**Subject:** the exact evidence manifest and privacy review required by Gate
R6.0-D, as selected by the owner in
`docs/r6-final-o3-o4-o5-owner-decision-pack-2026-11-07.md` §0.

---

## 1. The R6.0-D decision

Gate R6.0-D (FAST-04 §2.4) records that the U2 digests bind **untracked** files.
A `git clean`, a fresh clone, or a branch switch that discards untracked files
destroys the evidence the digests refer to. The digests are *recoverable, not
durable*.

The owner has selected: **the R6 governance corpus must be made durable (tracked
in Git) before the registration act.** This document supplies the evidence for
that act. It does not perform it.

**Verified at authorship:** `git ls-files docs` returns **16** tracked files, none
of them in the R6 governance corpus. The corpus below is **entirely untracked**.

---

## 2. Evidence manifest

**Scope:** every `docs/r6-*.md` file in the R6 governance corpus, **39 files**.
Digests are SHA-256 of the raw file bytes (no normalisation), lowercase hex.
`U2` marks the three files the genesis entry binds.

**Self-exclusion (explicit).** This document inventories the R6 governance
corpus but **excludes its own file from its own digest table**, because a file
cannot contain its own digest. This document is therefore the **40th** corpus
file and does not appear in the table below. Its digest is recorded at the
tracking act (commit message or a separate checksum file), not here. Nothing in
this table verifies this document's own digest, and this document makes no claim
to do so.

| # | Path | SHA-256 | Bytes | Lines | U2 |
|---:|---|---|---:|---:|:--:|
| 1 | `docs/r6-architecture-decision-pack.md` | `ed144c3cab2a20a6360db61019e3bd37438562621846fafc4c2dd6888c931206` | 35947 | 626 |  |
| 2 | `docs/r6-c01-settlement-integrity-and-remediation-dependency-report.md` | `f3761f88511da6f61702bd898646cb51144e706497cc439901af63c738f27fae` | 21211 | 329 |  |
| 3 | `docs/r6-close-final-01-addendum-a-verification.md` | `9b75007fcb6267695f553f6f492002b946c254cb45fa89527727a5f17283bff5` | 10694 | 174 |  |
| 4 | `docs/r6-close-final-01-r6.0-closure-package.md` | `33dcbff439fd93655eae85fcede7e4b44a550969ea44b36f7232af5edb616347` | 42316 | 656 |  |
| 5 | `docs/r6-close-final-02-r6.0-closure-reverification-2026-11-05.md` | `e4427d6a675f9e96756e5208bc4cb6c7a9cc03a6014e194430aef7ecf9e81052` | 17069 | 220 |  |
| 6 | `docs/r6-close-final-03-r6.0-registration-go-no-go-and-u4-decision-pack.md` | `971dc147d0126fd78aa150e662f93a35ac8022d85e02c3908b8876d433afd50e` | 24543 | 463 |  |
| 7 | `docs/r6-close-final-05-independent-verification-2026-11-07.md` | `44b8e5870f7da445ef959ac45c686b4ba416b320d2e83bf84c1ca9c75f88be2d` | 6897 | 141 |  |
| 8 | `docs/r6-command-centre-01-master-ledger-and-workstream-assignments-2026-11-05.md` | `aea269aebe8de9214bf130c13855b351e18820775bb635294eb44db201a72326` | 28543 | 424 |  |
| 9 | `docs/r6-decision-resolution-and-approval-campaign.md` | `3eff41e41afc7ff36f4ec233e0ed06afe0adc49671f61110a5c0ca74d124e33e` | 50154 | 401 |  |
| 10 | `docs/r6-fast-02-governance-reconciliation.md` | `f1882bd3d95037c4ceae16f9f44668bf8b8c46560c333492bd7e2dc09528ae16` | 22780 | 483 |  |
| 11 | `docs/r6-fast-03-settlement-integrity-audit.md` | `11447f3ac570e00c7405f4e0d9b62f09dba476b64906355e9b9e2c15609181c2` | 27696 | 423 |  |
| 12 | `docs/r6-fast-04-r6.0-closure-architecture.md` | `cc31554cdd17d5da3c616202831dc3913103e5d1ee560dc7069e5f37514d3f96` | 37069 | 548 |  |
| 13 | `docs/r6-fast-05-independent-red-team-challenge.md` | `1b53a1b335ee3b8bb955d7d61c99283ddbb7660d05b46f36e75aa0a77d98e234` | 22335 | 341 |  |
| 14 | `docs/r6-final-o3-o4-o5-canonical-corrections-proposal-2026-11-07.md` | `5bb7c0d22aeed31a7d9e58356b284724e4affb15a743d3fb3b3d9f834485e591` | 13037 | 314 |  |
| 15 | `docs/r6-final-o3-o4-o5-owner-decision-pack-2026-11-07.md` | `7dcfa2c6d5b686acaeb439093fb19c525377d88f4f590062d2579548d9dfa133` | 39580 | 708 |  |
| 16 | `docs/r6-g07-independent-closure-readiness-review.md` | `a7bb8ccd18e59b916a2a58adc00cd80f3ef7c8e14edd713dc4c0898c491349e6` | 42684 | 369 |  |
| 17 | `docs/r6-impl-prep-02-r62-r65-pipeline-preparation.md` | `470620cccd24e5502c175b48e3e5285b4192e6c8c2876163bd6329c8ea6afe3d` | 34156 | 369 |  |
| 18 | `docs/r6-impl-prep-03-r6.6-r6.7-validation-and-rollout-preparation.md` | `e0ae2f8a58ef1abc877e4a3d532bd42e2340962a4727dd6c01dee057c3fee120` | 38234 | 689 |  |
| 19 | `docs/r6-independent-review-r6-settlement-integrity-tests.md` | `2f05683242da3767db5a71e5ee751dd48f76b76e315fb2c23a6e17692ab450a1` | 27085 | 511 |  |
| 20 | `docs/r6-owner-decision-supplement-2026-11-04.md` | `8cf072df2b7a2f34ab3b15a905c3b3055752fa205c23355150cd984265543560` | 35795 | 471 |  |
| 21 | `docs/r6-owner-decision-worksheet-2026-11-04.md` | `42756357797db05931e5ff62a40fa54d31479f8370d0ea2bf0fe7fe86595604b` | 41782 | 562 |  |
| 22 | `docs/r6-r64-bm25-vendored-scorer-selection-record-2026-11-05.md` | `ecde5e0efa6d2065231069244d0463fea9cc038889fc895d6336fe73d2bb49c5` | 23080 | 240 |  |
| 23 | `docs/r6-register-amendment-proposal-2026-11-05.md` | `79230674a93beb644c460d56bad12c77271250baea424f60ca5ac5399c0eabf4` | 18715 | 260 |  |
| 24 | `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md` | `2ff885e32ffbcc90c7dc7d49631b28b7eafa49b46958de6d01c17f3789fee14f` | 26782 | 498 | **U2** |
| 25 | `docs/r6-registration-protocol-03b-r1-u1-u3-correction-proposal-2026-11-07.md` | `0a6c0f762b3836cbb0a4a0bb2d39d31461fc0948de9e18e8e76a94e60d5e8e6f` | 48596 | 885 |  |
| 26 | `docs/r6-registration-protocol-03b-r1-u1-u3-independent-review.md` | `a85454e8890e5b7f2104b5c24c7a7f87718c8ef866245e18991e8180cf36dbf7` | 16871 | 322 |  |
| 27 | `docs/r6-registration-protocol-03b-r1-u1-u3-independent-verification-2026-11-07.md` | `eae80e88047bf1c969fabfee22eff88eebb5a9c55eb0b590935855e07a1f0a11` | 21263 | 433 |  |
| 28 | `docs/r6-registration-protocol-03b-r1-u1-u3-proposal.md` | `14bca39df3caa0fd0ad8d6f1237d69d80776f6f5f124dd8d9c19a9755ae3fb9c` | 24975 | 552 |  |
| 29 | `docs/r6-registration-protocol-03b-r1-u1-u3-verification-report.md` | `e99318769160c17be4f75fbff92b9c26dc20ee88712c638613214e363c85f048` | 16539 | 388 |  |
| 30 | `docs/r6-registration-protocol-03b-r1.md` | `3a00363278de1427945a8ab7f77870f3a10f07b1acd09031c6f174e9c3cd512b` | 12619 | 348 | **U2** |
| 31 | `docs/r6-t10-decision-consolidation-and-freeze-preparation.md` | `394552b41eef2b83add17df7b67c43d6eda64dc90c1afcece30357fb8d98615f` | 54604 | 489 |  |
| 32 | `docs/r6-t11-r6-readiness-and-implementation-preparation.md` | `a3801d895bc9525200fd9de1b46748b801f0bcf9800cf720e0b49b9922d6b0af` | 69543 | 557 |  |
| 33 | `docs/r6-t12-accounting-integrity-and-gate-closure.md` | `6d1cb04338204d2c334150865fb44925e7c8381dcba65340a3f327766409cbfd` | 88581 | 1016 |  |
| 34 | `docs/r6-t13-documentation-correction-and-owner-decision-preparation.md` | `0651ec1d272d789e63c2851d7ee669d5aeccbd08b5d4bc9326d1ead3579755fb` | 80713 | 984 |  |
| 35 | `docs/r6-t14-independent-t13-audit-and-decision-readiness.md` | `a0188055242ebb13469f27815cf186b9fc20905a1c93b2b4c0e8c6e6e0c01879` | 33636 | 400 |  |
| 36 | `docs/r6-t15-r6-owner-decision-brief.md` | `d981e56e394221aaf427605a850d3caf9ddd5d01e1cd0ca8ffd6f260fa30663d` | 25668 | 240 |  |
| 37 | `docs/r6-t16-r6-decision-option-register.md` | `43c7331c8045026fb57695b74230897d0efcf1952e1fc1c337149e2a202c558c` | 52782 | 633 | **U2** |
| 38 | `docs/r6-t17-foundation-contract-extraction-and-track-a-engagement-packet.md` | `8309947222183884ab0dfa4938de2d5d2a79695940f61c90eacad7a0070a2cab` | 45184 | 434 |  |
| 39 | `docs/r6-t9-capability-recovery-review.md` | `4b756b7e6069af2d6d07e670510c21235557ee1f195771fc72c3b5cbc2f3b9fb` | 96839 | 576 |  |

**Revision note (2026-11-07).** This table was recomputed after the F1–F4
corrections to the decision pack, the canonical corrections proposal and the
U1/U3 proposal, and after the independent verification report
(`docs/r6-close-final-05-independent-verification-2026-11-07.md`) was created.
The report is row 7. The three U2-bound digests are unchanged, because no
canonical document was modified.

**No BOM** in any of the 39 files. All decode as strict UTF-8.

---

## 3. U2-bound digests (current, pre-amendment)

These are the three digests the genesis entry binds. They are recorded here as
the **pre-amendment** values. Applying the canonical corrections C-1…C-7 changes
`protocol_sha256` and `addendum_sha256` (R1); genesis must be built from the
**post-amendment** values, re-derived at the genesis act.

| File | Current SHA-256 |
|---|---|
| `docs/r6-t16-r6-decision-option-register.md` | `43c7331c8045026fb57695b74230897d0efcf1952e1fc1c337149e2a202c558c` |
| `docs/r6-registration-protocol-03b-r1.md` | `3a00363278de1427945a8ab7f77870f3a10f07b1acd09031c6f174e9c3cd512b` |
| `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md` | `2ff885e32ffbcc90c7dc7d49631b28b7eafa49b46958de6d01c17f3789fee14f` |

---

## 4. Privacy review

**Method.** Every file in the manifest was scanned for secret- and PII-shaped
strings: AWS access keys, private-key blocks, GitHub and Slack tokens, JWTs,
bearer tokens, generic `key/secret/token/password = <value>` assignments, email
addresses, absolute home paths, and IPv4 addresses. Matches are reported by
count and a redacted 6-character prefix only; no matched value is reproduced.

**Scope of this review.** Three scopes must not be conflated:

- the **manifest** (§2) — **39** files, each with SHA-256, byte size and line
  count;
- **this privacy scan** — those same **39** files. It does **not** cover this
  document itself, which is excluded from its own table (§2, self-exclusion);
- the **corpus** — **42** `docs/r6-*.md` files on disk at this correction
  (2026-11-08).

The independent verification report
(`docs/r6-close-final-05-independent-verification-2026-11-07.md` §5) scanned the
**40** corpus files then on disk — the 39 plus this document — and found no
additional hits. The corpus now contains **42**: `r6-close-final-06` and
`r6-close-final-07` were written afterwards and are outside both the manifest and
the scan. The conclusion below is therefore **measured for 40 files and
unmeasured for FINAL-06 and FINAL-07**; it does not presently hold for "the
corpus as a whole" (C-3).

**Result: 1 finding, low severity. No credentials.**

| File | Line | Class | Finding | Severity |
|---|---:|---|---|---|
| `docs/r6-registration-protocol-03b-r1-u1-u3-verification-report.md` | 229 | absolute home path | `REPO = "<HOME>/My ML Hub/SabiRoute"` inside a code snippet (original contains the OS username) | **Low** |

**Assessment.** The finding is a local absolute path in an illustrative Python
snippet. It discloses the OS username and the project path. It is **not
a credential**, not a token, and not a secret. No AWS key, private key, GitHub or
Slack token, JWT, bearer token, generic secret assignment, email address, or IPv4
address was found in any of the 39 files.

**Recommendation (non-blocking).** Before tracking, replace the literal path with
`<REPO>` or a relative path, or accept the disclosure as low-risk (username only).
This is a cosmetic edit to a non-U2-bound file; it does not affect any digest the
genesis entry binds.

**Limitation.** The scan is heuristic. It detects the listed patterns; it does not
prove the absence of every possible secret. A human review of the corpus remains
advisable before the corpus is published beyond the repository.

---

## 5. Conformance evidence

Run at the baseline above, against the **unmodified** canonical documents (the
corrections are proposed, not applied).

### 5.1 Existing conformance suite

```
python3 -m pytest tests/test_r6_registration_digest_conformance.py -q
67 passed, 2 skipped in 0.27s
```

The two skips are the executable form of the open decisions:

- `T10` — BLOCKED on O3: `PARAM-B.1` undefined for multi-line owner responses.
- `T11` — BLOCKED on O4/O5: genesis entry hash not derivable.

### 5.2 Proposed-correction vectors (O3 / O4)

Every vector claimed in the corrections proposal and the decision pack was
recomputed from the real source bytes, applying 03B-R1 §8 exactly. **All
reproduce.**

| Vector | Bytes | SHA-256 | Result |
|---|---:|---|---|
| O3 Alt-1 (value only, `A3: ` retained, LF preserved) | 163 | `97dc52a6b4880c53a9da4e84219c37b3cfda3070d52ff3cc287e87e64fbff149` | PASS |
| O3 Alt-1b (`A3: ` stripped) | 159 | `e067ed95785ab190ca658cf1b05e9576d74c98e1b340da421a2fce046e769098` | PASS |
| O3 Alt-2 (label + space + value) | 183 | `35de850fa80b00ecbe2c03b7846b489f3247c251351f53a9456f19176d926ccb` | PASS |
| O3 hazard (hard-break spaces stripped — **negative vector**) | 161 | `fc16e6d2ffd7d6fc19ad683816fb22aae7f89c336d14caf6c043761729a233d6` | PASS (must not equal Alt-1) |
| O4 genesis `prev` constant | — | `e893bd2cea4dfaa0db92c7343038d85c1cc50995d08bb5f1bdfbf38cba66d307` | PASS |
| O4 canonical genesis line (no LF) | 508 | `ad1484b0758f0accfd9986ed6f2d5f8fac1ded3a83d95974ed58af7fc74caf28` | PASS |
| O4 canonical genesis line + LF (O4-C, must differ) | 509 | `452a05bb8c241e46b3e86851821dd3daa604e478baad6ed41354e0dda592bbbe` | PASS |
| O4 key order sorted; `/` unescaped | — | — | PASS |

**Interpretation.** The proposed corrections are mechanically executable and
reproduce their published vectors. This does **not** mean the corrections are
applied, and it does **not** un-skip T10/T11: those tests read the canonical
documents, which are unchanged. It means the vectors the corrections would
introduce are sound.

---

## 6. Proposed tracking set and ordering

**Tracking set.** The 39 files in §2, plus this document (40 total). The three
U2-bound files are the minimum for R6.0-D; the full corpus is recommended so the
evidence chain is self-contained.

**Ordering (binding).** Each step is a separate act under its own authority:

1. Apply canonical corrections C-1…C-7 (changes `protocol_sha256`,
   `addendum_sha256` — R1).
2. Track the corpus (R6.0-D; repository act).
3. Re-derive U2 against the **post-amendment** files.
4. Build genesis from those post-amendment digests.
5. Perform the registration act under separate operational authority.

Building genesis from the §3 pre-amendment digests and amending afterwards yields
a genesis entry that does not match the files it claims to bind.

---

## 7. What this document does not do

- It does not track, stage, commit or push any file.
- It does not apply any canonical correction.
- It does not create a REG or VER record, a ledger, an entry, a key, a signature,
  or a checkpoint.
- It does not satisfy `PARAM-F.3` independent verification.
- It does not mark Gate R6.0-D met; it supplies the evidence for the act that
  would.
- It does not authorise registration, signing, checkpoint creation, R6.1,
  migrations, deployment, or production use.

**EVIDENCE — NOT EXECUTED.**
