# R6-REG-PROTOCOL-03B-R1 — U1–U3 Reproducibility Verification Report

**Status:** VERIFICATION REPORT — **REGISTRAR-SIDE SELF-CHECK**. This is **not**
the `PARAM-F.3` independent verification. It approves nothing, incorporates
nothing, and executes nothing.

**Date:** 2026-11-06 (UTC)

**Verifier:** Claude Code (registrar role, `PARAM-F.2`).

**Subject:** the §4 test vectors of
`docs/r6-registration-protocol-03b-r1-u1-u3-proposal.md`.

**Repository baseline:** `feat/sabiroute-routing-foundation` @
`08201da8013a58b486d5fa2d6c46b36588a27781`. Confirmed at verification time:
`git rev-parse HEAD` returned that commit, `git branch --show-current` returned
that branch, `git status --porcelain | grep -v '^??'` returned **no** entries
(no tracked modifications), and `git diff --cached --stat` returned **no**
entries (nothing staged). Untracked files are present in the working tree but
none is tracked and none affects the digests below.

---

## 0. What this report is, and what it is not

**It is** an independent *reimplementation* of the normative procedures in
proposal §1.1 (U1), §2.1 (U2) and §3.2 (U3), written from the specification text
alone, and a field-by-field comparison of its output against the §4 tables.

**It is not** the independent verification the proposal requires. The proposal
header and §1.3 require **Claude Desktop** (`PARAM-F.3`) to reproduce the vectors
independently. This report was produced by the **same agent that authored the
proposal**. A misreading of the specification shared between author and
re-implementer would therefore **not** be caught by this report. What it does
establish is that the §4 numbers are not an arithmetic or transcription error:
they are what the written procedure actually produces.

**It does not:** create a REG or VER record; create, modify or sign a manifest;
generate a key or signature; create the VER ledger or establish a checkpoint;
modify T16; change any decision's approval status; mark any gate COMPLETE; or
authorise BL-22, R6.1, or any implementation. Operational registration authority
remains **DEFERRED**.

---

## 1. Method

- **Runtime:** Python 3.11.16, standard library only (`hashlib`, `re`, `json`).
  No third-party packages, no network access.
- **Script:** reproduced in full at Appendix A. Its own SHA-256 is
  `d2d9a541a5f5fcf7e15b3b147f92deb76a045c6670a7268308fe5c1a1f004c00`.
- **U1 / U2 pipeline, as implemented:** read raw bytes → reject if the file
  begins with `EF BB BF` → decode UTF-8 strict → replace `CRLF` with `LF`, then
  remaining `CR` with `LF` → split on `LF`.
- **U1 card location:** fence mask (a line whose first non-space characters are
  ` ``` ` or `~~~` opens a fence; the matching token closes it); ATX headings
  `^(#{1,6})\s+(.*)$` outside fences; card heading
  `^(#{1,6})\s+(<ID>)\s+[—–-]\s+` outside fences, required to be unique; span
  ends at the first subsequent heading outside a fence whose level is `≤` the
  card heading's level, else at end of file.
- **U1 trailing-separator stripping:** remove trailing blank lines, then remove a
  trailing horizontal rule matching `^ {0,3}(-{3,}|\*{3,}|_{3,})\s*$`, repeating
  to a fixpoint.
- **U1 canonical card text:** remaining lines joined with a single `LF`, encoded
  UTF-8 with no BOM, hashed SHA-256, rendered lowercase hex.
- **U2:** canonical text encoded UTF-8 with no BOM, hashed SHA-256, lowercase hex.
- **U3:** `SHA-256(UTF-8("R6-VER-LEDGER-GENESIS:v1"))`, lowercase hex.

No NFC/NFD normalisation, no whitespace trimming, and no trailing-newline
retention were applied — matching the proposal's explicit exclusions.

---

## 2. Results summary

| Group | Vectors | Reproduced exactly | Mismatch |
|---|---|---|---|
| U1 — extracted-card digests (§4.1) | 23 | **23** | 0 |
| U2 — whole-file digests (§4.2) | 3 | **3** | 0 |
| U3 — genesis constant (§4.3) | 1 | **1** | 0 |
| §4.4 behavioural tests | 5 rows / 6 assertions | **6** | 0 |

**Overall: 33 assertions reproduced, 0 mismatch.** (§4.4 defines five test rows;
the "non-existent ID" row names two IDs, `Z9` and `A5`, and was run as two
separate assertions.)

---

## 3. U1 — extracted-card digests

`start` is the 1-based line number of the card heading; `end` is the exclusive
end line. Both are in the newline-canonicalised form, and both agree with the
"Lines (canonical)" column of proposal §4.1.

| ID | start | end | Bytes | SHA-256 (reproduced) | vs §4.1 |
|---|---|---|---|---|---|
| A1 | 123 | 135 | 767 | `70cb1ddeed5b84f17520e90ba69e4182e519a5998ec10747d9eb5f22c7353bc4` | MATCH |
| A2 | 136 | 148 | 1022 | `afbb96c4ea74efd862d775ce49b32d637b22d0e1f746a352acd28d5209208e34` | MATCH |
| A3 | 149 | 167 | 1763 | `9dadd0f232df4daa7485ead444ac562283065527bc2f3c147dfab9060ff90e3b` | MATCH |
| A4 | 168 | 182 | 683 | `ce9c8e2926efbb0a189d68ae050e1e9d052f013360467bd76ef56044ea6965d3` | MATCH |
| B1 | 187 | 212 | 2410 | `b19da622ef05d57be53f0932714b51643ebb8a79cee81a43a92df07e034fa2f4` | MATCH |
| B2 | 213 | 225 | 723 | `e041985cee5b4bcd1408c412a3d88b11ede018ce29d60231565c01a918fe3466` | MATCH |
| B3 | 226 | 238 | 721 | `db9606a1d44ec430ba38937585802f85255b6bbd77960661695c72a03fc8c4b1` | MATCH |
| B4 | 239 | 251 | 620 | `a7836a4847f15714e894d4c0e54eef054f0789aa537e6424959783b7bfb80d2d` | MATCH |
| B5 | 252 | 270 | 1891 | `f39ef13072107af456090507b7d6538493460dc6616f6aac266fc9aceae6045e` | MATCH |
| B6 | 271 | 295 | 2076 | `9c22e56afab5a367db13d451c04fdbb022b74a93d367b0bbc6963e0bf8907374` | MATCH |
| B7 | 296 | 308 | 924 | `b1e497bf590185cbaaf370bfd59133c47fb4a9c7b6db38489e635917efc92fff` | MATCH |
| B8 | 309 | 321 | 689 | `50afcf458560cb68994906bf2b9fcc195c33174c8ddba9a3c4466e07e6771dae` | MATCH |
| B9 | 322 | 336 | 630 | `851a80438990ea0c6221c654821029a84b3411265d01679b8eb7c77a1ea6b88a` | MATCH |
| C1 | 343 | 355 | 1354 | `071f1cb93a3b4f8489cad63c6d9f0e6cbd5606cb64a77364083bfdcf036312c5` | MATCH |
| C2 | 356 | 368 | 800 | `10e53984d2a684283886872e7085ec0d63f7776235ccd92f9ec95e57f333442a` | MATCH |
| C3 | 369 | 381 | 843 | `6bfeebbed8775506db300068733fcce8bdfeffa568febd1bbca06113946a4a3b` | MATCH |
| C4 | 382 | 394 | 1071 | `51e4e7491f2333eee0c274dd2091ba5b9b4e8a4f35d7d73944d333ec27b19bab` | MATCH |
| D1 | 399 | 412 | 858 | `62905f789fa0efa97fbf3abaaa34aa93fcd710347a3ea76e30172c9428cc014f` | MATCH |
| D2 | 413 | 425 | 1038 | `77cb466bffba3f3d14195c009362b8bb20e5f130241fc47d778f5371aa54cdb2` | MATCH |
| D3 | 426 | 446 | 1933 | `bf1c0075f445f3bbfbd7b1b7b302e5112dc7762f3037b44a00ebe3f9aac108ef` | MATCH |
| D4 | 447 | 459 | 922 | `55a557ceb62ab25df55d73e3a456cf405a4e5f398ca3524ca4bd28b9a22e5c99` | MATCH |
| D5 | 460 | 472 | 841 | `9fcda8d4f9a2b1a842f0afec2f370be71e398d5de5a694a141047fee6e4f5485` | MATCH |
| D6 | 473 | 487 | 807 | `21c67a9aa474b442d98389e17ee49cc1dfa3f6db3087ad47f5caa27b5eec3109` | MATCH |

All 23 cards were located unambiguously; no `MISSING CARD` or `AMBIGUOUS CARD`
condition arose on the unmodified source.

---

## 4. U2 — whole-file digests

| File | Canonical bytes | SHA-256 (reproduced) | vs §4.2 |
|---|---|---|---|
| `docs/r6-t16-r6-decision-option-register.md` | 52782 | `43c7331c8045026fb57695b74230897d0efcf1952e1fc1c337149e2a202c558c` | MATCH |
| `docs/r6-registration-protocol-03b-r1.md` | 12619 | `3a00363278de1427945a8ab7f77870f3a10f07b1acd09031c6f174e9c3cd512b` | MATCH |
| `docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md` | 26782 | `2ff885e32ffbcc90c7dc7d49631b28b7eafa49b46958de6d01c17f3789fee14f` | MATCH |

All three files are LF-only with no BOM at this baseline, so for them the
canonical byte form equals the raw byte form — as proposal §2.2 anticipates.

---

## 5. U3 — genesis constant

| Item | Value (reproduced) | vs §4.3 |
|---|---|---|
| `SHA-256(UTF-8("R6-VER-LEDGER-GENESIS:v1"))` | `e893bd2cea4dfaa0db92c7343038d85c1cc50995d08bb5f1bdfbf38cba66d307` | MATCH |

The genesis constant is confirmed to be the domain-separated hash of the literal
`R6-VER-LEDGER-GENESIS:v1`, and is not 64 zeros.

**Not verified:** the example genesis line in proposal §3.2 carries placeholder
values (`YYYY-MM-DD`, `<LEDGER_ID>`, `SHA256:<base64>`), so its `entry_sha256` is
not computable and was not computed. What *was* checked by inspection is that the
example's key order is ascending by Unicode code point
(`addendum_sha256`, `created`, `entry_type`, `ledger_id`,
`owner_key_fingerprint`, `prev`, `protocol_sha256`, `seq`, `t16_sha256`), that
separators are bare `,` and `:`, and that `seq` is a bare integer `0` — all
consistent with the §3.1 canonical-JSON rules.

---

## 6. Behavioural tests (§4.4)

| Test | Expected | Observed | Result |
|---|---|---|---|
| Extract `A3` twice | identical digest | identical digest | PASS |
| Extract `A3` from a CRLF-converted copy | identical digest | identical digest | PASS |
| Whole-file digest of a CRLF-converted copy | identical to LF original | identical | PASS |
| Extract a non-existent ID `Z9` | fail closed (`MISSING CARD`) | `MISSING CARD` | PASS |
| Extract a non-existent ID `A5` | fail closed (`MISSING CARD`) | `MISSING CARD` | PASS |
| Extract from a file with a duplicated card heading | fail closed (`AMBIGUOUS CARD`) | `AMBIGUOUS CARD` | PASS |

The CRLF tests were performed by converting the canonical text to CRLF in memory
and re-running the full pipeline, not by writing a converted file to disk.

---

## 7. Limitations of this report

1. **Not independent of the author.** Same agent wrote the proposal and this
   re-implementation. A shared misreading of §1.1/§2.1/§3.2 survives this check.
   Only Claude Desktop (`PARAM-F.3`) can close that gap.
2. **One implementation, one language.** Python 3.11.16 only. The proposal's
   cross-language reproducibility claim (notably the §3.1 canonical-JSON rules)
   is not exercised by this report, because no ledger entry with real values
   exists to hash.
3. **The U3 chain, checkpoint and signature layers are unexercised.** No key
   exists, no ledger exists, no checkpoint message was signed. §3.4–§3.9 remain
   specified but untested.
4. **Fence and heading detection were tested only against the real T16 file** and
   the synthetic duplicate-heading case. Adversarial inputs (nested fences,
   indented fences, setext headings, headings inside HTML blocks) were not
   exercised.
5. **The script lives outside the repository** and is preserved only by being
   reproduced in Appendix A. Its digest above refers to the `/tmp` copy as run.

---

## 8. What this report does not do

- It does not approve, incorporate, or execute the proposal.
- It does not satisfy the `PARAM-F.3` independent-verification requirement.
- It does not create a REG or VER record, a ledger, a key, a signature, or a
  checkpoint.
- It does not modify T16 or change any approval status.
- It does not mark any gate COMPLETE.
- It does not authorise BL-22, R6.1, or any implementation.
- It does not supply operational registration authority, which remains
  **DEFERRED**.

**VERIFICATION REPORT — REGISTRAR-SIDE SELF-CHECK. NOT AN APPROVAL.**

---

## Appendix A — verification script

Run as `python3 verify_u1u3.py`. Standard library only. Read-only: it reads the
three source documents and writes nothing.

```python
#!/usr/bin/env python3
"""Independent verification of R6-REG-PROTOCOL-03B-R1 U1/U2/U3 test vectors.

Implements the normative procedures from
docs/r6-registration-protocol-03b-r1-u1-u3-proposal.md sections 1.1, 2.1, 3.2.
Read-only: reads three markdown docs, writes nothing, prints JSON to stdout.
"""
import hashlib
import json
import re

REPO = "/Users/airm2/My ML Hub/SabiRoute"

T16 = REPO + "/docs/r6-t16-r6-decision-option-register.md"
PROTO = REPO + "/docs/r6-registration-protocol-03b-r1.md"
ADDENDUM = REPO + "/docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md"

BOM = b"\xef\xbb\xbf"


def canonical_text(path):
    """U2 steps 1-5: raw bytes -> canonical UTF-8 text (newlines canonicalised)."""
    raw = open(path, "rb").read()
    if raw.startswith(BOM):
        raise SystemExit("BOM present in %s" % path)
    text = raw.decode("utf-8", "strict")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def u2_digest(path):
    b = canonical_text(path).encode("utf-8")
    return hashlib.sha256(b).hexdigest(), len(b)


FENCE_RE = re.compile(r"^\s*(```|~~~)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
HR_RE = re.compile(r"^ {0,3}(-{3,}|\*{3,}|_{3,})\s*$")


def fence_mask(lines):
    """True for lines inside (or delimiting) a fenced region."""
    mask = [False] * len(lines)
    open_tok = None
    for i, line in enumerate(lines):
        m = FENCE_RE.match(line)
        if open_tok is None:
            if m:
                open_tok = m.group(1)
                mask[i] = True
        else:
            mask[i] = True
            if m and m.group(1) == open_tok:
                open_tok = None
    return mask


def headings(lines, mask):
    out = []
    for i, line in enumerate(lines):
        if mask[i]:
            continue
        m = HEADING_RE.match(line)
        if m:
            out.append((i, len(m.group(1)), m.group(2)))
    return out


def extract_card(lines, mask, heads, card_id):
    pat = re.compile(r"^(#{1,6})\s+(" + re.escape(card_id) + r")\s+[—–-]\s+")
    matches = []
    for i, line in enumerate(lines):
        if mask[i]:
            continue
        m = pat.match(line)
        if m:
            matches.append((i, len(m.group(1))))
    if not matches:
        raise LookupError("MISSING CARD")
    if len(matches) > 1:
        raise LookupError("AMBIGUOUS CARD")
    start, level = matches[0]
    end = len(lines)
    for (i, lvl, _t) in heads:
        if i > start and lvl <= level:
            end = i
            break
    span = lines[start:end]
    while True:
        while span and span[-1].strip() == "":
            span.pop()
        if span and HR_RE.match(span[-1]):
            span.pop()
            continue
        break
    return "\n".join(span), start + 1, end


def main():
    results = {}

    u2 = {}
    for label, path in (("t16", T16), ("protocol", PROTO), ("addendum", ADDENDUM)):
        d, n = u2_digest(path)
        u2[label] = {"sha256": d, "bytes": n}
    results["u2"] = u2

    results["genesis"] = hashlib.sha256(b"R6-VER-LEDGER-GENESIS:v1").hexdigest()

    text = canonical_text(T16)
    lines = text.split("\n")
    mask = fence_mask(lines)
    heads = headings(lines, mask)

    ids = (["A1", "A2", "A3", "A4"]
           + ["B%d" % i for i in range(1, 10)]
           + ["C%d" % i for i in range(1, 5)]
           + ["D%d" % i for i in range(1, 7)])
    cards = {}
    for cid in ids:
        try:
            card, start, end = extract_card(lines, mask, heads, cid)
        except LookupError as e:
            cards[cid] = {"error": str(e)}
            continue
        b = card.encode("utf-8")
        cards[cid] = {"start": start, "end": end, "bytes": len(b),
                      "sha256": hashlib.sha256(b).hexdigest()}
    results["u1"] = cards

    beh = {}
    a3a = extract_card(lines, mask, heads, "A3")[0]
    a3b = extract_card(lines, mask, heads, "A3")[0]
    beh["determinism_A3"] = (hashlib.sha256(a3a.encode()).hexdigest()
                             == hashlib.sha256(a3b.encode()).hexdigest())

    crlf_canon = text.replace("\n", "\r\n").replace("\r\n", "\n").replace("\r", "\n")
    beh["u2_crlf_invariance"] = (hashlib.sha256(crlf_canon.encode()).hexdigest()
                                 == u2["t16"]["sha256"])

    clines = crlf_canon.split("\n")
    cmask = fence_mask(clines)
    cheads = headings(clines, cmask)
    a3c = extract_card(clines, cmask, cheads, "A3")[0]
    beh["u1_crlf_invariance"] = (hashlib.sha256(a3c.encode()).hexdigest()
                                 == hashlib.sha256(a3a.encode()).hexdigest())

    for bad in ("Z9", "A5"):
        try:
            extract_card(lines, mask, heads, bad)
            beh["missing_%s" % bad] = "NO ERROR (unexpected)"
        except LookupError as e:
            beh["missing_%s" % bad] = str(e)

    dup = list(lines)
    a3_idx = extract_card(lines, mask, heads, "A3")[1] - 1
    dup.insert(a3_idx + 1, lines[a3_idx])
    dmask = fence_mask(dup)
    dheads = headings(dup, dmask)
    try:
        extract_card(dup, dmask, dheads, "A3")
        beh["ambiguous_A3"] = "NO ERROR (unexpected)"
    except LookupError as e:
        beh["ambiguous_A3"] = str(e)
    results["behavioural"] = beh

    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
```
