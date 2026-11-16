"""R6 registration conformance tests — pre-implementation conformance test (PICT).

These tests encode the *specification* of R6-REG-PROTOCOL-03B-R1 U1/U2/U3/U4 as
executable assertions. They do not exercise SabiRoute application code; they
assert that the registration protocol is mechanically executable and that its
published vectors reproduce.

Authority: this module is evidence only. It approves nothing, registers nothing,
and confers no execution authority. See
``docs/r6-close-final-03-r6.0-registration-go-no-go-and-u4-decision-pack.md``.

Provenance of the vectors asserted here
---------------------------------------
* U1 (23 cards) / U2 (3 files) / U3 (constant): independently re-derived for the
  closure assessment by a fourth implementation written from the normative prose
  of proposal §1.1, §2.1, §3.2 — not copied from any prior report. All 33 values
  reproduce.
* U4 (REG-marker digest): vectors computed against a *synthetic* marker fixture,
  because no REG marker exists yet. These are the first U4 vectors in the corpus.
* A4/B9/D6 use the corrected canonical spans ``[168,180)``, ``[322,334)``,
  ``[473,485)`` from correction proposal §5 (D4), not the original labels.

A test is skipped only where a *first-execution artefact* it needs does not
exist and may not be fabricated. A skipped test here is a finding, not a pass.
Since Amendment 1 to the addendum (2026-11-07), the U1–U4 and O3/O4/O5
*definitions* are all incorporated normatively; what remains missing for U11 is
the ledger artefact itself, not a definition.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
T16 = REPO / "docs/r6-t16-r6-decision-option-register.md"
PROTOCOL = REPO / "docs/r6-registration-protocol-03b-r1.md"
ADDENDUM = REPO / "docs/r6-registration-protocol-03b-r1-owner-parameter-addendum.md"

# --------------------------------------------------------------------------- #
# Normative machinery — U1 extraction (proposal §1.1 as corrected by D1)
# --------------------------------------------------------------------------- #

FENCE_RE = re.compile(r"^\s*(```|~~~)")
ATX_RE = re.compile(r"^(#{1,6})\s+(.*)$")
HR_RE = re.compile(r"^ {0,3}(-{3,}|\*{3,}|_{3,})\s*$")


class SpecError(Exception):
    """Raised for a fail-closed specification outcome."""


def _read_canonical(path: Path) -> str:
    """Steps 1-4 of §1.1: raw bytes, reject BOM, strict UTF-8, canonical newlines."""
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise SpecError("BOM")
    text = raw.decode("utf-8", "strict")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _fence_mask(lines: list[str]) -> list[bool]:
    """§1.1 step 6: lines inside a fenced region are excluded from heading detection."""
    mask = [False] * len(lines)
    in_fence = False
    token = None
    for i, line in enumerate(lines):
        m = FENCE_RE.match(line)
        if not in_fence:
            if m:
                in_fence, token, mask[i] = True, m.group(1), True
        else:
            mask[i] = True
            if m and m.group(1) == token:
                in_fence, token = False, None
    return mask


def extract_card(text: str, decision_id: str) -> tuple[int, int, int, str]:
    """Return ``(start, end, line_count, canonical_text)`` for one card.

    Ordinals are 1-based and describe the canonical span, half-open ``[start, end)``
    (correction proposal §3.1(C), step 11a). ``end - start == line_count`` must hold.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    mask = _fence_mask(lines)
    pattern = re.compile(r"^(#{1,6})\s+(" + re.escape(decision_id) + r")\s+[—–-]\s+")

    hits = [
        (i, len(m.group(1)))
        for i, line in enumerate(lines)
        if not mask[i] and (m := pattern.match(line))
    ]
    if not hits:
        raise SpecError("MISSING CARD")
    if len(hits) > 1:
        raise SpecError("AMBIGUOUS CARD")

    start_idx, level = hits[0]
    end_idx = len(lines)
    for j in range(start_idx + 1, len(lines)):
        if mask[j]:
            continue
        m = ATX_RE.match(lines[j])
        if m and len(m.group(1)) <= level:
            end_idx = j
            break

    # §1.1 step 11: strip trailing separators to a fixpoint.
    span = lines[start_idx:end_idx]
    while True:
        while span and span[-1].strip() == "":
            span.pop()
        if span and HR_RE.match(span[-1]):
            span.pop()
            continue
        break

    canonical = "\n".join(span)
    start = start_idx + 1
    return start, start + len(span), len(span), canonical


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def whole_file_digest(path: Path) -> tuple[int, str]:
    text = _read_canonical(path)
    raw = text.encode("utf-8")
    return len(raw), sha256_text(text)


# --------------------------------------------------------------------------- #
# U1 vectors — proposal §4.1, line column corrected per D4
#   (id, start, end, line_count, bytes, sha256)
# --------------------------------------------------------------------------- #

U1_VECTORS = [
    ("A1", 123, 135, 12, 767, "70cb1ddeed5b84f17520e90ba69e4182e519a5998ec10747d9eb5f22c7353bc4"),
    ("A2", 136, 148, 12, 1022, "afbb96c4ea74efd862d775ce49b32d637b22d0e1f746a352acd28d5209208e34"),
    ("A3", 149, 167, 18, 1763, "9dadd0f232df4daa7485ead444ac562283065527bc2f3c147dfab9060ff90e3b"),
    ("A4", 168, 180, 12, 683, "ce9c8e2926efbb0a189d68ae050e1e9d052f013360467bd76ef56044ea6965d3"),
    ("B1", 187, 212, 25, 2410, "b19da622ef05d57be53f0932714b51643ebb8a79cee81a43a92df07e034fa2f4"),
    ("B2", 213, 225, 12, 723, "e041985cee5b4bcd1408c412a3d88b11ede018ce29d60231565c01a918fe3466"),
    ("B3", 226, 238, 12, 721, "db9606a1d44ec430ba38937585802f85255b6bbd77960661695c72a03fc8c4b1"),
    ("B4", 239, 251, 12, 620, "a7836a4847f15714e894d4c0e54eef054f0789aa537e6424959783b7bfb80d2d"),
    ("B5", 252, 270, 18, 1891, "f39ef13072107af456090507b7d6538493460dc6616f6aac266fc9aceae6045e"),
    ("B6", 271, 295, 24, 2076, "9c22e56afab5a367db13d451c04fdbb022b74a93d367b0bbc6963e0bf8907374"),
    ("B7", 296, 308, 12, 924, "b1e497bf590185cbaaf370bfd59133c47fb4a9c7b6db38489e635917efc92fff"),
    ("B8", 309, 321, 12, 689, "50afcf458560cb68994906bf2b9fcc195c33174c8ddba9a3c4466e07e6771dae"),
    ("B9", 322, 334, 12, 630, "851a80438990ea0c6221c654821029a84b3411265d01679b8eb7c77a1ea6b88a"),
    ("C1", 343, 355, 12, 1354, "071f1cb93a3b4f8489cad63c6d9f0e6cbd5606cb64a77364083bfdcf036312c5"),
    ("C2", 356, 368, 12, 800, "10e53984d2a684283886872e7085ec0d63f7776235ccd92f9ec95e57f333442a"),
    ("C3", 369, 381, 12, 843, "6bfeebbed8775506db300068733fcce8bdfeffa568febd1bbca06113946a4a3b"),
    ("C4", 382, 394, 12, 1071, "51e4e7491f2333eee0c274dd2091ba5b9b4e8a4f35d7d73944d333ec27b19bab"),
    ("D1", 399, 412, 13, 858, "62905f789fa0efa97fbf3abaaa34aa93fcd710347a3ea76e30172c9428cc014f"),
    ("D2", 413, 425, 12, 1038, "77cb466bffba3f3d14195c009362b8bb20e5f130241fc47d778f5371aa54cdb2"),
    ("D3", 426, 446, 20, 1933, "bf1c0075f445f3bbfbd7b1b7b302e5112dc7762f3037b44a00ebe3f9aac108ef"),
    ("D4", 447, 459, 12, 922, "55a557ceb62ab25df55d73e3a456cf405a4e5f398ca3524ca4bd28b9a22e5c99"),
    ("D5", 460, 472, 12, 841, "9fcda8d4f9a2b1a842f0afec2f370be71e398d5de5a694a141047fee6e4f5485"),
    ("D6", 473, 485, 12, 807, "21c67a9aa474b442d98389e17ee49cc1dfa3f6db3087ad47f5caa27b5eec3109"),
]

U2_VECTORS = {
    T16: (52782, "43c7331c8045026fb57695b74230897d0efcf1952e1fc1c337149e2a202c558c"),
    PROTOCOL: (15898, "59643d242effe3bca2a50ae4e52e86d28d9b5105465c446cab87e38fc69a6590"),
    ADDENDUM: (42917, "601a27a36e1fc4ed25de0ef45ced6afec67ea61f45a12f12ecf352eaa51c49f5"),
}

U3_GENESIS_CONSTANT = hashlib.sha256(b"R6-VER-LEDGER-GENESIS:v1").hexdigest()

# Synthetic REG marker fixture (03B-R1 §5 grammar). No real marker exists yet.
SYNTHETIC_MARKER = (
    "<!-- REG:v1 decision=A3 state=SELECTED option=A owner_sha256="
    "9dadd0f232df4daa7485ead444ac562283065527bc2f3c147dfab9060ff90e3b\n"
    "     confirmed=2026-11-06 recorded=2026-11-06 registrar=Claude Code "
    "revision=UNRESOLVED prev_state=PENDING -->"
)
U4_MARKER_DIGEST = "c69ea393c1f2760c6c338327dedcca4586cec1c80b8669fd0ff40198f743d8d7"
U4_MARKER_BYTES = 236


def u4_marker_digest(text: str) -> tuple[int, str]:
    """U4 (correction proposal §3.2(C)): digest of the delimited marker text."""
    if text.encode("utf-8").startswith(b"\xef\xbb\xbf"):
        raise SpecError("BOM")
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    start = t.find("<!-- REG:v1 ")
    if start < 0:
        raise SpecError("MISSING MARKER")
    end = t.find("-->", start)
    if end < 0:
        raise SpecError("MISSING MARKER")
    if t.find("<!-- REG:v1 ", end) >= 0:
        raise SpecError("AMBIGUOUS MARKER")
    marker = t[start : end + len("-->")]
    return len(marker.encode("utf-8")), sha256_text(marker)


# --------------------------------------------------------------------------- #
# T10 — PARAM-B.1 owner-response digest, as closed by owner decision O3
# --------------------------------------------------------------------------- #

OWNER_FIELD_PREFIX = "**Owner response:** "
NEXT_FIELD_RE = re.compile(r"^\*\*[^*]+\*\*")

# Approved A3 vector (addendum PARAM-B.1; independently reproduced 2026-11-08).
A3_OWNER_BYTES = 163
A3_OWNER_SHA256 = "97dc52a6b4880c53a9da4e84219c37b3cfda3070d52ff3cc287e87e64fbff149"
# Documented negative vector: the same value with the hard-break spaces stripped.
A3_HAZARD_BYTES = 161
A3_HAZARD_SHA256 = "fc16e6d2ffd7d6fc19ad683816fb22aae7f89c336d14caf6c043761729a233d6"


def _card_bounds(text: str, decision_id: str) -> tuple[int, int]:
    """Half-open ``lines`` index bounds of one card, reusing ``extract_card``."""
    start, end, _nlines, _canonical = extract_card(text, decision_id)
    return start - 1, end - 1


def extract_owner_response(text: str, decision_id: str) -> str:
    """Return the exact ``PARAM-B.1`` owner-response value for one card.

    The value is the text following the ``**Owner response:** `` label through
    the end of that field — i.e. up to, but excluding, the next line that opens a
    new ``**…**`` field. Terminating at the next field rather than at the next
    heading means a card with no response field fails closed instead of
    silently absorbing the remainder of the card.

    Line breaks inside the value are preserved verbatim. The two markdown
    hard-break spaces that end a visually wrapped line are *internal* whitespace
    under 03B-R1 §8 step 5 and are therefore retained: stripping them produces
    the documented 161-byte negative vector, never the approved A3 value.
    """
    lines = text.split("\n")
    card_start, card_end = _card_bounds(text, decision_id)
    label_at = None
    for i in range(card_start, card_end):
        if lines[i].startswith(OWNER_FIELD_PREFIX):
            if label_at is not None:
                raise SpecError("AMBIGUOUS OWNER RESPONSE")
            label_at = i
    if label_at is None:
        raise SpecError("MISSING OWNER RESPONSE")

    value = [lines[label_at][len(OWNER_FIELD_PREFIX) :]]
    for j in range(label_at + 1, card_end):
        if NEXT_FIELD_RE.match(lines[j]):
            break
        value.append(lines[j])
    return "\n".join(value)


def owner_response_digest(value: str) -> tuple[int, str]:
    """03B-R1 §8 steps 1-8 over exactly the extracted value (``PARAM-B.1``)."""
    v = value.replace("\r\n", "\n").replace("\r", "\n")
    v = unicodedata.normalize("NFC", v)
    v = v.strip()
    raw = v.encode("utf-8")
    return len(raw), hashlib.sha256(raw).hexdigest()


# --------------------------------------------------------------------------- #
# PARAM-B.5 — canonical JSON for the U3 ledger (definition-only; no ledger)
# --------------------------------------------------------------------------- #


def canonical_json(obj) -> str:
    """PARAM-B.5: sorted keys, no inter-token whitespace, ``,``/``:`` separators.

    Non-ASCII is emitted as literal UTF-8 and ``/`` is not escaped, which is
    Python's behaviour for ``ensure_ascii=False``.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _rejecting_pairs_hook(pairs):
    seen = {}
    for key, val in pairs:
        if key in seen:
            raise SpecError("MALFORMED LEDGER ENTRY")
        seen[key] = val
    return seen


def parse_canonical_json(text: str):
    """PARAM-B.5 parser contract: duplicate keys are malformed, never last-wins."""
    return json.loads(text, object_pairs_hook=_rejecting_pairs_hook)


# --------------------------------------------------------------------------- #
# Availability guard — the protocol documents are untracked (finding F9)
# --------------------------------------------------------------------------- #

pytestmark = pytest.mark.skipif(
    not (T16.exists() and PROTOCOL.exists() and ADDENDUM.exists()),
    reason="R6 protocol corpus absent (untracked files; see finding F9 durability)",
)


# --------------------------------------------------------------------------- #
# T5 / T1–T4 — U1: all 23 vectors, identity, determinism, newline invariance
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("cid,start,end,nlines,nbytes,digest", U1_VECTORS)
def test_u1_reproduces_published_vector(cid, start, end, nlines, nbytes, digest):
    text = _read_canonical(T16)
    got_start, got_end, got_nlines, canonical = extract_card(text, cid)
    assert (got_start, got_end, got_nlines) == (start, end, nlines), f"{cid} span"
    assert len(canonical.encode("utf-8")) == nbytes, f"{cid} byte length"
    assert sha256_text(canonical) == digest, f"{cid} digest"


@pytest.mark.parametrize("cid,start,end,nlines,nbytes,digest", U1_VECTORS)
def test_u1_span_identity_holds(cid, start, end, nlines, nbytes, digest):
    """D1's validation identity: end - start == canonical line count."""
    assert end - start == nlines, f"{cid}: {end} - {start} != {nlines}"


def test_u1_determinism():
    text = _read_canonical(T16)
    a = extract_card(text, "A3")[3]
    b = extract_card(text, "A3")[3]
    assert sha256_text(a) == sha256_text(b)


def test_u1_crlf_invariance():
    text = _read_canonical(T16)
    lf = sha256_text(extract_card(text, "A3")[3])
    crlf = sha256_text(extract_card(text.replace("\n", "\r\n"), "A3")[3])
    assert lf == crlf


@pytest.mark.parametrize("cid", ["Z9", "A5"])
def test_u1_missing_card_fails_closed(cid):
    with pytest.raises(SpecError, match="MISSING CARD"):
        extract_card(_read_canonical(T16), cid)


def test_u1_ambiguous_card_fails_closed():
    lines = _read_canonical(T16).split("\n")
    idx = next(
        i for i, ln in enumerate(lines) if re.match(r"^#{1,6}\s+A3\s+[—–-]\s+", ln)
    )
    decoy = lines[: idx + 1] + ["### A3 — Duplicate decoy", ""] + lines[idx + 1 :]
    with pytest.raises(SpecError, match="AMBIGUOUS CARD"):
        extract_card("\n".join(decoy), "A3")


def test_bom_rejected(tmp_path):
    target = tmp_path / "bom.md"
    target.write_bytes(b"\xef\xbb\xbf" + T16.read_bytes())
    with pytest.raises(SpecError, match="BOM"):
        _read_canonical(target)


def test_invalid_utf8_rejected(tmp_path):
    target = tmp_path / "bad.md"
    target.write_bytes(b"### A3 \xff\xfe\x00 broken\n")
    with pytest.raises(UnicodeDecodeError):
        _read_canonical(target)


# --------------------------------------------------------------------------- #
# T4 — U2: whole-file digests and newline invariance
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("path", list(U2_VECTORS))
def test_u2_reproduces_published_digest(path):
    expected_bytes, expected_digest = U2_VECTORS[path]
    nbytes, digest = whole_file_digest(path)
    assert nbytes == expected_bytes
    assert digest == expected_digest


@pytest.mark.parametrize("path", list(U2_VECTORS))
def test_u2_crlf_invariance(path):
    lf = whole_file_digest(path)[1]
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        pytest.skip("BOM")
    crlf_text = raw.decode("utf-8", "strict").replace("\n", "\r\n")
    canonical = crlf_text.replace("\r\n", "\n").replace("\r", "\n")
    assert sha256_text(canonical) == lf


# --------------------------------------------------------------------------- #
# T8 — U3: genesis constant
# --------------------------------------------------------------------------- #


def test_u3_genesis_constant():
    assert U3_GENESIS_CONSTANT == (
        "e893bd2cea4dfaa0db92c7343038d85c1cc50995d08bb5f1bdfbf38cba66d307"
    )
    assert U3_GENESIS_CONSTANT != "0" * 64, "genesis prev must be domain-separated"


# --------------------------------------------------------------------------- #
# T9 — U4: REG-marker digest on a synthetic fixture
# --------------------------------------------------------------------------- #


def test_u4_synthetic_marker_vector():
    nbytes, digest = u4_marker_digest(SYNTHETIC_MARKER)
    assert nbytes == U4_MARKER_BYTES
    assert digest == U4_MARKER_DIGEST


def test_u4_newline_invariance():
    assert (
        u4_marker_digest(SYNTHETIC_MARKER)[1]
        == u4_marker_digest(SYNTHETIC_MARKER.replace("\n", "\r\n"))[1]
    )


def test_u4_sensitive_to_indentation_and_content():
    base = u4_marker_digest(SYNTHETIC_MARKER)[1]
    reindented = SYNTHETIC_MARKER.replace("\n     confirmed", "\n    confirmed")
    assert u4_marker_digest(reindented)[1] != base
    assert u4_marker_digest(SYNTHETIC_MARKER.replace("option=A ", "option=B "))[1] != base
    assert u4_marker_digest(SYNTHETIC_MARKER.replace(" -->", "  -->"))[1] != base


def test_u4_missing_marker_fails_closed():
    with pytest.raises(SpecError, match="MISSING MARKER"):
        u4_marker_digest("no marker here")


def test_u4_ambiguous_marker_fails_closed():
    with pytest.raises(SpecError, match="AMBIGUOUS MARKER"):
        u4_marker_digest(SYNTHETIC_MARKER + "\n\n" + SYNTHETIC_MARKER)


def test_u4_delimiter_mutation_fails_closed_at_locator():
    """F11: a '<!--' -> '<!---' mutation is caught by the locator, not the digest."""
    with pytest.raises(SpecError, match="MISSING MARKER"):
        u4_marker_digest(SYNTHETIC_MARKER.replace("<!-- REG", "<!--- REG", 1))


# --------------------------------------------------------------------------- #
# T10 — PARAM-B.1 owner-response digest (owner decision O3, incorporated)
# --------------------------------------------------------------------------- #


def test_u10_owner_response_digest_is_single_valued():
    """PARAM-B.1 reproduces the approved 163-byte A3 vector.

    O3 is owner-selected and incorporated in the addendum (PARAM-B.1, "Multi-line
    response rule"), so this is no longer a blocked specification gap: the
    approved reading is retained ``A3: `` prefix, internal ``LF`` preserved,
    03B-R1 §8 applied, and markdown hard-break spaces *not* stripped.
    """
    value = extract_owner_response(_read_canonical(T16), "A3")
    nbytes, digest = owner_response_digest(value)
    assert nbytes == A3_OWNER_BYTES, f"A3 owner-response byte length: {nbytes}"
    assert digest == A3_OWNER_SHA256, f"A3 owner_sha256: {digest}"


def test_u10_is_deterministic():
    text = _read_canonical(T16)
    first = owner_response_digest(extract_owner_response(text, "A3"))
    second = owner_response_digest(extract_owner_response(text, "A3"))
    assert first == second


def test_u10_crlf_invariance():
    text = _read_canonical(T16)
    lf = owner_response_digest(extract_owner_response(text, "A3"))[1]
    crlf = owner_response_digest(
        extract_owner_response(text.replace("\n", "\r\n"), "A3")
    )[1]
    assert lf == crlf


def test_u10_hard_break_spaces_are_internal_not_trailing():
    """The 161-byte form is the documented negative vector, never the A3 value."""
    value = extract_owner_response(_read_canonical(T16), "A3")
    assert value.count("\n") == 1, "A3 is the two-line owner response"
    hazard = value.replace(".  \n", ".\n")
    assert hazard != value, "the A3 value must carry the hard-break spaces"
    nbytes, digest = owner_response_digest(hazard)
    assert (nbytes, digest) == (A3_HAZARD_BYTES, A3_HAZARD_SHA256)
    assert digest != A3_OWNER_SHA256


def test_u10_field_terminates_at_the_next_field():
    """The extracted value must not absorb the card's following fields."""
    value = extract_owner_response(_read_canonical(T16), "A3")
    assert "**Source provenance:**" not in value
    assert "**Approval record:**" not in value
    assert value.startswith("A3: ")
    assert value.endswith("this selection authorises no implementation.")


def test_u10_missing_field_fails_closed():
    text = (
        "### A9 — Synthetic probe\n\n"
        "**Decision question:** probe?\n\n"
        "**Approval record:** `NOT APPROVED`\n"
    )
    with pytest.raises(SpecError, match="MISSING OWNER RESPONSE"):
        extract_owner_response(text, "A9")


def test_u10_ambiguous_field_fails_closed():
    text = (
        "### A9 — Synthetic probe\n\n"
        "**Owner response:** one\n\n"
        "**Owner response:** two\n\n"
        "**Approval record:** `NOT APPROVED`\n"
    )
    with pytest.raises(SpecError, match="AMBIGUOUS OWNER RESPONSE"):
        extract_owner_response(text, "A9")


def test_owner_and_marker_digests_are_distinct_classes():
    """PARAM-B.6: marker_sha256 digests the marker object, never owner_sha256.

    ``marker_sha256`` covers the bytes *including* ``<!--`` and ``-->``; the
    ``owner_sha256`` the marker carries is hashed over the response value alone.
    The two must never be equal, substituted, or derived from one another. The
    fixture is synthetic, so the digest it embeds is a stand-in — read it out
    rather than assuming which vector it uses.
    """
    _nb, marker_digest = u4_marker_digest(SYNTHETIC_MARKER)
    match = re.search(r"owner_sha256=([0-9a-f]{64})", SYNTHETIC_MARKER)
    assert match, "the synthetic fixture must carry an owner_sha256 field"
    embedded_owner = match.group(1)

    _nb2, a3_owner = owner_response_digest(
        extract_owner_response(_read_canonical(T16), "A3")
    )
    assert marker_digest != embedded_owner
    assert marker_digest != a3_owner
    assert embedded_owner != a3_owner, (
        "the fixture's stand-in digest is not the A3 owner-response digest"
    )


# --------------------------------------------------------------------------- #
# T11 — BLOCKED: genesis entry hash awaits the ledger artefact itself
# --------------------------------------------------------------------------- #


def test_u11_genesis_entry_hash_is_computable():
    """BLOCKED — awaiting authorised ledger instantiation.

    O4 (VER/ledger field set) and O5 (``ledger_id``) are owner-selected and are
    incorporated normatively at addendum ``PARAM-A.7`` / ``PARAM-B.5``, so the
    genesis *form* is no longer undefined. What does not exist is the *artefact*:
    no ledger, no ``ledger_id``, no genesis entry and no checkpoint may be
    created without the separate first-execution authority (addendum §10).

    The synthetic nine-field worked example in decision pack §3.5/§3.6 is
    normative for the *computation* (508-byte canonical line, ``ad1484b0…af28``)
    but is explicitly not the real chain head, so it cannot stand in for one
    here. Fabricating a ledger to make this pass would be the failure this test
    exists to prevent.
    """
    pytest.skip("awaiting authorised ledger instantiation")


# --------------------------------------------------------------------------- #
# PARAM-B.5 — canonical JSON rules for the U3 ledger entry payload
# --------------------------------------------------------------------------- #


def test_b5_canonical_json_has_sorted_keys_and_no_whitespace():
    text = canonical_json({"b": 1, "a": 2, "A": 3})
    assert text == '{"A":3,"a":2,"b":1}'
    assert " " not in text


def test_b5_non_ascii_is_literal_utf8_and_slash_unescaped():
    text = canonical_json({"path": "a/b", "name": "café"})
    assert "/" in text and "\\/" not in text
    assert "café" in text
    assert "\\u" not in text, "non-ASCII must be emitted as literal UTF-8"
    # The literal form and the escaped form are different byte strings; only the
    # literal one is canonical.
    assert text.encode("utf-8") != text.encode("ascii", "backslashreplace")


def test_b5_integers_have_no_leading_zero_or_exponent():
    assert canonical_json({"n": 0}) == '{"n":0}'
    assert canonical_json({"n": 42}) == '{"n":42}'
    assert canonical_json({"n": -7}) == '{"n":-7}'


def test_b5_duplicate_key_is_malformed_not_last_wins():
    with pytest.raises(SpecError, match="MALFORMED LEDGER ENTRY"):
        parse_canonical_json('{"a":1,"a":2}')


def test_b5_omitted_field_and_explicit_null_are_distinct():
    omitted = canonical_json({"a": 1})
    explicit = canonical_json({"a": 1, "b": None})
    assert omitted != explicit
    assert omitted == '{"a":1}'
    assert explicit == '{"a":1,"b":null}'


def test_b5_entry_hash_excludes_the_terminating_lf():
    """PARAM-B.5: entry_sha256 covers the line bytes, not the trailing LF."""
    payload = canonical_json({"seq": 0, "prev": "x"})
    on_disk = payload + "\n"
    assert sha256_text(payload) == hashlib.sha256(payload.encode("utf-8")).hexdigest()
    assert sha256_text(payload) != sha256_text(on_disk)
    assert len(on_disk.encode("utf-8")) == len(payload.encode("utf-8")) + 1


# --------------------------------------------------------------------------- #
# Provenance: record the measured source digests so the evidence is self-checking
# --------------------------------------------------------------------------- #


def test_source_digests_are_stable_against_the_record():
    recorded = {p.name: d for p, (_, d) in U2_VECTORS.items()}
    measured = {p.name: whole_file_digest(p)[1] for p in U2_VECTORS}
    assert measured == recorded
    # The genesis binds these three; serialise for auditability on failure.
    assert json.dumps(measured, sort_keys=True)


# --------------------------------------------------------------------------- #
# WP2-D9 — five negative-first conformance groups (appended 2026-11-16)
#
# Each group establishes that malformed input FAILS CLOSED before it establishes
# that well-formed input passes. A group that only demonstrates the happy path
# does not satisfy WP2-D9. Authored after the D8 pass so the vectors are stable.
# --------------------------------------------------------------------------- #

VER_PAYLOAD_KEYS = (
    "decision",
    "verifier",
    "verified",
    "result",
    "marker_sha256",
    "items_checked",
    "card_sha256",
    "file_sha256",
)
# entry_sha256 is computed, never serialised: 11 keys are hashed, 12 are stored.
VER_HASHED_KEYS = tuple(sorted(("seq", "prev", "entry_type") + VER_PAYLOAD_KEYS))
VER_LEDGER_KEYS = tuple(sorted(VER_HASHED_KEYS + ("entry_sha256",)))


def _ver_entry(**overrides):
    """A conforming 12-key VER ledger entry, as a dict."""
    entry = {
        "seq": 1,
        "prev": U3_GENESIS_CONSTANT,
        "entry_type": "VER",
        "decision": "A3",
        "verifier": "Claude Desktop Chat 05",
        "verified": "2026-11-16",
        "result": "PASS",
        "marker_sha256": U4_MARKER_DIGEST,
        "items_checked": 10,
        "card_sha256": A3_OWNER_SHA256,
        "file_sha256": U2_VECTORS[T16][1],
    }
    entry.update(overrides)
    return entry


def _ver_line(entry) -> str:
    """Serialise an entry, appending its computed ``entry_sha256``."""
    hashed = {k: entry[k] for k in VER_HASHED_KEYS}
    digest = sha256_text(canonical_json(hashed))
    return canonical_json({**hashed, "entry_sha256": digest})


def _validate_ver_line(text: str) -> dict:
    """03B-R1 §6 schema contract. Raises ``SpecError`` on any violation."""
    if "REG:v1" in text:
        raise SpecError("REG MARKER CO-LOCATED WITH VER ENTRY")
    if "\\/" in text:
        raise SpecError("ESCAPED SOLIDUS — not canonical")
    if ": " in text:
        raise SpecError("WHITESPACE AFTER COLON — not canonical")
    try:
        entry = parse_canonical_json(text)  # duplicate keys raise here
    except ValueError as exc:  # JSONDecodeError is a ValueError
        raise SpecError("MALFORMED LEDGER ENTRY") from exc
    if not isinstance(entry, dict):
        raise SpecError("ENTRY IS NOT AN OBJECT")
    if tuple(sorted(entry)) != VER_LEDGER_KEYS:
        raise SpecError("KEY SET MISMATCH")
    if text != canonical_json(entry):
        raise SpecError("NON-CANONICAL SERIALISATION")
    if entry["entry_type"] not in ("GENESIS", "VER"):
        raise SpecError("ENTRY_TYPE OUT OF DOMAIN")
    if not isinstance(entry["seq"], int) or isinstance(entry["seq"], bool):
        raise SpecError("SEQ IS NOT AN INTEGER")
    if entry["result"] not in ("PASS", "FAIL"):
        raise SpecError("RESULT OUT OF DOMAIN")
    if not isinstance(entry["items_checked"], int) or isinstance(
        entry["items_checked"], bool
    ):
        raise SpecError("ITEMS_CHECKED IS NOT AN INTEGER")
    return entry


# --- Group 1 — VER schema --------------------------------------------------- #


def test_d9_g1_conforming_ver_entry_passes():
    parsed = _validate_ver_line(_ver_line(_ver_entry()))
    assert tuple(sorted(parsed)) == VER_LEDGER_KEYS
    assert len(VER_HASHED_KEYS) == 11
    assert len(VER_LEDGER_KEYS) == 12


def test_d9_g1_duplicate_key_fails_closed():
    line = _ver_line(_ver_entry())
    bad = line[:-1] + ',"seq":1}'
    with pytest.raises(SpecError, match="MALFORMED LEDGER ENTRY"):
        _validate_ver_line(bad)


def test_d9_g1_escaped_solidus_fails_closed():
    line = _ver_line(_ver_entry(verifier="Claude Desktop / Chat 05"))
    assert "/" in line
    bad = line.replace("/", "\\/")
    with pytest.raises(SpecError, match="ESCAPED SOLIDUS"):
        _validate_ver_line(bad)


def test_d9_g1_reordered_keys_fail_closed():
    line = _ver_line(_ver_entry())
    parsed = parse_canonical_json(line)
    reversed_order = {k: parsed[k] for k in reversed(list(parsed))}
    reordered = json.dumps(
        reversed_order, sort_keys=False, separators=(",", ":"), ensure_ascii=False
    )
    assert reordered != line
    with pytest.raises(SpecError, match="NON-CANONICAL SERIALISATION"):
        _validate_ver_line(reordered)


def test_d9_g1_space_after_colon_fails_closed():
    line = _ver_line(_ver_entry())
    bad = line.replace(":", ": ", 1)
    with pytest.raises(SpecError, match="WHITESPACE AFTER COLON"):
        _validate_ver_line(bad)


def test_d9_g1_seq_as_float_fails_closed():
    line = _ver_line(_ver_entry(seq=0.0))
    with pytest.raises(SpecError, match="SEQ IS NOT AN INTEGER"):
        _validate_ver_line(line)


def test_d9_g1_seq_as_string_fails_closed():
    line = _ver_line(_ver_entry(seq="0"))
    with pytest.raises(SpecError, match="SEQ IS NOT AN INTEGER"):
        _validate_ver_line(line)


# --- Group 2 — F7 bound (WP2-D11) ------------------------------------------- #


def _validate_items_bound(entry) -> None:
    """``1 <= items_checked <= 10``; a ``PASS`` result requires exactly 10."""
    n = entry["items_checked"]
    if not 1 <= n <= 10:
        raise SpecError("ITEMS_CHECKED OUT OF BOUND")
    if entry["result"] == "PASS" and n != 10:
        raise SpecError("PASS REQUIRES EXACTLY 10")


def test_d9_g2_items_checked_zero_fails_closed():
    with pytest.raises(SpecError, match="OUT OF BOUND"):
        _validate_items_bound(_ver_entry(items_checked=0))


def test_d9_g2_items_checked_eleven_fails_closed():
    with pytest.raises(SpecError, match="OUT OF BOUND"):
        _validate_items_bound(_ver_entry(items_checked=11))


def test_d9_g2_items_checked_negative_fails_closed():
    with pytest.raises(SpecError, match="OUT OF BOUND"):
        _validate_items_bound(_ver_entry(items_checked=-1))


def test_d9_g2_pass_with_nine_fails_closed():
    with pytest.raises(SpecError, match="PASS REQUIRES EXACTLY 10"):
        _validate_items_bound(_ver_entry(result="PASS", items_checked=9))


def test_d9_g2_fail_with_partial_count_is_permitted():
    _validate_items_bound(_ver_entry(result="FAIL", items_checked=1))
    _validate_items_bound(_ver_entry(result="FAIL", items_checked=10))


def test_d9_g2_pass_with_ten_is_permitted():
    _validate_items_bound(_ver_entry(result="PASS", items_checked=10))


# --- Group 3 — REG/VER separation ------------------------------------------- #


def test_d9_g3_entry_type_has_no_reg_member():
    with pytest.raises(SpecError, match="ENTRY_TYPE OUT OF DOMAIN"):
        _validate_ver_line(_ver_line(_ver_entry(entry_type="REG")))


def test_d9_g3_ver_co_located_with_reg_fails_closed():
    reg = "<!-- REG:v1 decision=A3 state=SELECTED option=O1 -->"
    combined = reg + "\n" + _ver_line(_ver_entry())
    with pytest.raises(SpecError, match="REG MARKER CO-LOCATED"):
        _validate_ver_line(combined)


# --- Group 4 — COMPLETE derivation (PARAM-A.4) ------------------------------ #


def _complete_is_valid(entries, canonical_marker_sha256) -> bool:
    """COMPLETE is valid only with a matching ``PASS`` entry and read-back."""
    if not entries:
        return False
    for raw in entries:
        try:
            entry = _validate_ver_line(raw)
        except SpecError:
            return False
        if entry["result"] != "PASS":
            return False
        if entry["marker_sha256"] != canonical_marker_sha256:
            return False
        if entry["items_checked"] != 10:
            return False
    return True


def test_d9_g4_missing_ver_makes_complete_invalid():
    assert _complete_is_valid([], U4_MARKER_DIGEST) is False


def test_d9_g4_malformed_ver_makes_complete_invalid():
    assert _complete_is_valid(["{not json"], U4_MARKER_DIGEST) is False


def test_d9_g4_mismatched_marker_makes_complete_invalid():
    line = _ver_line(_ver_entry(marker_sha256="0" * 64))
    assert _complete_is_valid([line], U4_MARKER_DIGEST) is False


def test_d9_g4_fail_result_makes_complete_invalid():
    line = _ver_line(_ver_entry(result="FAIL", items_checked=10))
    assert _complete_is_valid([line], U4_MARKER_DIGEST) is False


def test_d9_g4_matching_pass_entry_makes_complete_valid():
    assert _complete_is_valid([_ver_line(_ver_entry())], U4_MARKER_DIGEST) is True


# --- Group 5 — genesis conformance ------------------------------------------ #


def _genesis_line() -> str:
    """The synthetic nine-field genesis preimage from decision pack §3.6."""
    import base64

    def h(s: str) -> str:
        return hashlib.sha256(s.encode("utf-8")).hexdigest()
    obj = {
        "addendum_sha256": h("sabiroute-r6-addendum-synthetic"),
        "created": "2026-11-07",
        "entry_type": "GENESIS",
        "ledger_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "owner_key_fingerprint": "SHA256:"
        + base64.b64encode(
            hashlib.sha256(b"sabiroute-r6-owner-ed25519-synthetic").digest()
        ).decode(),
        "prev": h("R6-VER-LEDGER-GENESIS:v1"),
        "protocol_sha256": h("sabiroute-r6-protocol-03b-r1-synthetic"),
        "seq": 0,
        "t16_sha256": h("sabiroute-r6-t16-synthetic"),
    }
    return canonical_json(obj)


def test_d9_g5_genesis_preimage_reproduces_published_digest():
    line = _genesis_line()
    assert len(line.encode("utf-8")) == 508
    assert (
        sha256_text(line)
        == "ad1484b0758f0accfd9986ed6f2d5f8fac1ded3a83d95974ed58af7fc74caf28"
    )


def test_d9_g5_terminating_lf_changes_the_digest():
    line = _genesis_line()
    with_lf = line + "\n"
    assert len(with_lf.encode("utf-8")) == 509
    assert (
        sha256_text(with_lf)
        == "452a05bb8c241e46b3e86851821dd3daa604e478baad6ed41354e0dda592bbbe"
    )
    assert sha256_text(with_lf) != sha256_text(line)


def test_d9_g5_genesis_has_nine_hashed_keys_and_no_entry_sha256():
    obj = parse_canonical_json(_genesis_line())
    assert len(obj) == 9
    assert "entry_sha256" not in obj
    assert obj["prev"] == U3_GENESIS_CONSTANT

# --- PH-3 — synthetic-fixture proof for the genesis entry-hash function ---- #
#
# PH-3 / F-02. This test proves the genesis *arithmetic* — determinism,
# totality, and sensitivity to every field — and **instantiates nothing**. No
# ledger file, no REG record, no VER record, no chain head and no real entry is
# created. The fixture is decision pack §3.6's synthetic nine-field preimage,
# which is explicitly not the real chain head.
#
# F-02 therefore becomes PARTIALLY PROVEN, never closed. The live test
# ``test_u11_genesis_entry_hash_is_computable`` STAYS SKIPPED, because the
# *artefact* it asserts on still may not be created without first-execution
# authority (addendum §10).

_HEX_DIGITS = set("0123456789abcdef")

def test_ph3_genesis_entry_hash_is_deterministic_total_and_field_sensitive() -> None:
    # --- determinism ------------------------------------------------------- #
    # Same fixture, same digest, every call; and the canonical form is a fixed
    # point, so hashing is independent of which representation we start from.
    base = _genesis_line()
    assert sha256_text(base) == sha256_text(_genesis_line())
    assert sha256_text(base) == sha256_text(canonical_json(parse_canonical_json(base)))
    assert (
        sha256_text(base)
        == "ad1484b0758f0accfd9986ed6f2d5f8fac1ded3a83d95974ed58af7fc74caf28"
    )

    # --- totality ---------------------------------------------------------- #
    # The function is defined over the whole fixture: nine fields, no more and
    # no fewer, and the digest is always 64 lowercase hex characters.
    obj = parse_canonical_json(base)
    assert set(obj) == {
        "addendum_sha256",
        "created",
        "entry_type",
        "ledger_id",
        "owner_key_fingerprint",
        "prev",
        "protocol_sha256",
        "seq",
        "t16_sha256",
    }
    assert len(sha256_text(base)) == 64
    assert set(sha256_text(base)) <= _HEX_DIGITS

    # --- sensitivity to each field ----------------------------------------- #
    # Perturb exactly one field at a time. Every mutation must produce a
    # well-formed digest, and no two mutations may collide with each other or
    # with the base — so no field is silently dropped by canonicalisation.
    mutated_digests = {}
    for field in sorted(obj):
        mutated = dict(obj)
        value = mutated[field]
        if isinstance(value, int):
            mutated[field] = value + 1
        elif field == "entry_type":
            mutated[field] = "VER"
        else:
            mutated[field] = value + "x"
        assert mutated != obj, f"{field} mutation must actually change the value"

        digest = sha256_text(canonical_json(mutated))
        assert len(digest) == 64, f"{field} produced a malformed digest"
        assert set(digest) <= _HEX_DIGITS, f"{field} digest is not lowercase hex"
        mutated_digests[field] = digest

    assert len(mutated_digests) == 9
    assert len(set(mutated_digests.values())) == 9, (
        "each field must move the digest independently"
    )
    assert sha256_text(base) not in set(mutated_digests.values()), (
        "no mutation may collide with the unmutated fixture"
    )
