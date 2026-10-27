"""Deterministic claim verification against retrieved and uploaded source evidence.

Hard Rules enforced:
1. Enforcement lives in code, not model self-scoring.
2. Zero fabrication: never invent an authority, pinpoint, quote, or date.
3. Closed evidence: cite only text retrieved or uploaded during this run.
4. Confidence labels come strictly from verifier results.
5. Quotes round-trip against source text with dash and curly quote normalisation,
   never altering the displayed quote.
6. Provisions must be confirmed in force as at the relevant date.
7. Non-existent pages/clauses in upload documents cause verification to fail.
8. OCR and fallback-parsed pages are flagged as lower trust.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Literal, Optional, Sequence

from .groundedness import QuotedPhrase, RoundtripResult, extract_quoted_phrases, roundtrip_quote


VerificationStatus = Literal["VERIFIED", "UNVERIFIED"]
TrustLevel = Literal["high", "low_ocr", "low_fallback", "unverified"]


@dataclass(frozen=True)
class AtomicClaim:
    """An atomic legal assertion to be verified against evidence."""

    claim_id: str
    text: str
    evidence_ids: list[str] = field(default_factory=list)
    pinpoint: Optional[str] = None
    relevant_date: Optional[str] = None  # YYYY-MM-DD


@dataclass(frozen=True)
class EvidenceSource:
    """Source material retrieved online or parsed from an uploaded document."""

    id: str
    text: str
    title: str = ""
    citation: Optional[str] = None
    source_type: str = "document"  # legislation, case, document, corpus
    status: str = "in_force"  # in_force, repealed, not_yet_in_force, unverified
    in_force_start: Optional[str] = None  # YYYY-MM-DD
    in_force_end: Optional[str] = None  # YYYY-MM-DD
    pages: Optional[list[int]] = None
    clauses: Optional[list[str]] = None
    sections: Optional[list[str]] = None
    lower_trust: bool = False
    trust_level: TrustLevel = "high"
    trust_reason: Optional[str] = None


@dataclass(frozen=True)
class ClaimVerificationResult:
    """Verification outcome for an individual atomic claim."""

    claim_id: str
    status: VerificationStatus
    text: str
    reasons: list[str] = field(default_factory=list)
    lower_trust: bool = False
    trust_level: TrustLevel = "high"
    quote_results: list[RoundtripResult] = field(default_factory=list)
    pinpoint_verified: bool = False

    @property
    def verified(self) -> bool:
        return self.status == "VERIFIED"


@dataclass(frozen=True)
class VerificationBatchSummary:
    """Batch verification summary."""

    results: list[ClaimVerificationResult]
    total_claims: int
    verified_claims: int
    unverified_claims: int
    all_verified: bool


def _normalize_text_for_comparison(s: str) -> str:
    """Normalize text for comparison without altering displayed strings."""
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"\s+", " ", s).strip()
    table = str.maketrans({
        "\u201c": "\"",
        "\u201d": "\"",
        "\u2018": "'",
        "\u2019": "'",
        "\u2013": "-",
        "\u2014": "-",
    })
    return s.translate(table)


def _check_in_force(
    evidence: EvidenceSource, relevant_date: Optional[str]
) -> tuple[bool, Optional[str]]:
    """Verify whether legislation was in force as at relevant_date."""
    if evidence.source_type != "legislation":
        return True, None

    if evidence.status == "repealed":
        if not relevant_date:
            return False, "legislation is repealed and no historical relevant date was specified"
        if evidence.in_force_end and relevant_date > evidence.in_force_end:
            return (
                False,
                f"legislation was repealed on {evidence.in_force_end}; not in force on {relevant_date}",
            )

    if evidence.status == "not_yet_in_force":
        return False, "legislation is not yet in force"

    if relevant_date:
        if evidence.in_force_start and relevant_date < evidence.in_force_start:
            return (
                False,
                f"legislation not yet in force on {relevant_date} (commenced {evidence.in_force_start})",
            )
        if evidence.in_force_end and relevant_date > evidence.in_force_end:
            return (
                False,
                f"legislation no longer in force on {relevant_date} (repealed {evidence.in_force_end})",
            )

    return True, None


def _extract_pinpoint_targets(pinpoint: str) -> dict[str, list[str]]:
    """Extract target pages, clauses, sections, and paragraphs from a pinpoint string."""
    targets: dict[str, list[str]] = {
        "pages": [],
        "clauses": [],
        "sections": [],
        "paragraphs": [],
    }
    clean = pinpoint.strip()
    # Match pages: p. 4, pp. 4-5, page 4
    for m in re.finditer(r"\b(?:pp?\.?|pages?)\s*([0-9]+(?:\s*[-–]\s*[0-9]+)?)", clean, re.I):
        val = m.group(1)
        if "-" in val or "\u2013" in val:
            parts = re.split(r"[-–]", val)
            try:
                start, end = int(parts[0].strip()), int(parts[1].strip())
                targets["pages"].extend(str(p) for p in range(start, end + 1))
            except ValueError:
                targets["pages"].append(val)
        else:
            targets["pages"].append(val.strip())

    # Match clauses: cl 3.2, cls 3.2-3.4, clause 3.2(a)
    for m in re.finditer(r"\b(?:cls?\.?|clauses?)\s*([0-9A-Za-z().\-–]+)", clean, re.I):
        targets["clauses"].append(m.group(1).strip())

    # Match sections: s 23, ss 23-25, sec 9
    for m in re.finditer(r"\b(?:ss?\.?|sections?)\s*([0-9A-Za-z().\-–]+)", clean, re.I):
        targets["sections"].append(m.group(1).strip())

    # Match paragraphs: para 5, paras 5-6, [45]
    for m in re.finditer(r"\b(?:paras?\.?|paragraphs?)\s*([0-9A-Za-z().\-–]+)", clean, re.I):
        targets["paragraphs"].append(m.group(1).strip())
    for m in re.finditer(r"\[([0-9]+)\]", clean):
        targets["paragraphs"].append(m.group(1).strip())

    return targets


def _verify_pinpoint(evidence: EvidenceSource, pinpoint: str) -> tuple[bool, Optional[str]]:
    """Check that the cited pinpoint exists in the evidence source."""
    targets = _extract_pinpoint_targets(pinpoint)
    structural_checked = False

    # 1. Page verification for upload documents
    if targets["pages"] and evidence.pages is not None:
        structural_checked = True
        int_pages = set(evidence.pages)
        for p in targets["pages"]:
            try:
                if int(p) not in int_pages:
                    return False, f"pinpoint page {p} does not exist in uploaded document"
            except ValueError:
                pass

    # 2. Clause verification for upload documents
    if targets["clauses"] and evidence.clauses is not None:
        structural_checked = True
        known_cls = {c.lower() for c in evidence.clauses}
        for c in targets["clauses"]:
            base_c = c.split("(")[0].lower()
            if not any(base_c == kc or kc.startswith(base_c) for kc in known_cls):
                return False, f"pinpoint clause {c} does not exist in uploaded document"

    # 3. Section verification for legislation
    if targets["sections"] and evidence.sections is not None:
        structural_checked = True
        known_sec = {s.lower() for s in evidence.sections}
        for s in targets["sections"]:
            base_s = s.split("(")[0].lower()
            if not any(base_s == ks or ks.startswith(base_s) for ks in known_sec):
                return False, f"pinpoint section {s} absent from legislation source"

    if structural_checked:
        return True, None

    # 4. Fallback textual check across evidence text
    norm_source = _normalize_text_for_comparison(evidence.text)
    pin_clean = re.sub(r"[\[\](),.]", " ", pinpoint)
    tokens = [t for t in pin_clean.split() if t.isalnum() and not re.match(r"^(?:doc|p|pp|page|cl|cls|clause|s|ss|sec|section|para|paras)$", t, re.I)]
    for token in tokens:
        if token.lower() not in norm_source.lower():
            return False, f"pinpoint token {token!r} absent from source text"

    return True, None


def verify_claim(
    claim: AtomicClaim,
    evidence_store: dict[str, EvidenceSource | dict[str, Any]],
    global_relevant_date: Optional[str] = None,
) -> ClaimVerificationResult:
    """Deterministically verify a single atomic claim against the provided evidence store."""
    reasons: list[str] = []

    # 1. Evidence presence check
    if not claim.evidence_ids:
        return ClaimVerificationResult(
            claim_id=claim.claim_id,
            status="UNVERIFIED",
            text=claim.text,
            reasons=["no evidence provided for claim"],
            trust_level="unverified",
        )

    matched_evidence: list[EvidenceSource] = []
    for eid in claim.evidence_ids:
        if eid not in evidence_store:
            reasons.append(f"evidence ID {eid!r} not found in evidence store")
            continue
        item = evidence_store[eid]
        if isinstance(item, EvidenceSource):
            matched_evidence.append(item)
        elif isinstance(item, dict):
            matched_evidence.append(
                EvidenceSource(
                    id=item.get("id", eid),
                    text=item.get("text", ""),
                    title=item.get("title", ""),
                    citation=item.get("citation"),
                    source_type=item.get("source_type", "document"),
                    status=item.get("status", "in_force"),
                    in_force_start=item.get("in_force_start"),
                    in_force_end=item.get("in_force_end"),
                    pages=item.get("pages"),
                    clauses=item.get("clauses"),
                    sections=item.get("sections"),
                    lower_trust=item.get("lower_trust", False),
                    trust_level=item.get("trust_level", "high"),
                    trust_reason=item.get("trust_reason"),
                )
            )

    if not matched_evidence:
        return ClaimVerificationResult(
            claim_id=claim.claim_id,
            status="UNVERIFIED",
            text=claim.text,
            reasons=reasons or ["no valid evidence found"],
            trust_level="unverified",
        )

    # 2. Check in-force status for legislation
    relevant_date = claim.relevant_date or global_relevant_date
    for ev in matched_evidence:
        ok_in_force, in_force_msg = _check_in_force(ev, relevant_date)
        if not ok_in_force and in_force_msg:
            reasons.append(in_force_msg)

    # 3. Check pinpoint if supplied
    pinpoint_verified = False
    if claim.pinpoint:
        pin_ok = False
        pin_err: Optional[str] = None
        for ev in matched_evidence:
            ok, err = _verify_pinpoint(ev, claim.pinpoint)
            if ok:
                pin_ok = True
                break
            pin_err = err
        if not pin_ok:
            reasons.append(pin_err or f"pinpoint {claim.pinpoint} absent from evidence")
        else:
            pinpoint_verified = True

    # 4. Check all quotes roundtrip against evidence text
    quotes = extract_quoted_phrases(claim.text)
    quote_results: list[RoundtripResult] = []
    combined_source_text = "\n\n".join(ev.text for ev in matched_evidence)

    for q in quotes:
        res = roundtrip_quote(q.text, combined_source_text)
        quote_results.append(res)
        if res.status in ("not_found", "could_not_check"):
            reasons.append(
                f"quote \"{q.text}\" does not round-trip against source text ({res.status})"
            )

    # 5. Check lower trust propagation
    is_lower_trust = any(ev.lower_trust for ev in matched_evidence)
    resolved_trust: TrustLevel = "high"
    if is_lower_trust:
        if any(ev.trust_level == "low_ocr" for ev in matched_evidence):
            resolved_trust = "low_ocr"
        else:
            resolved_trust = "low_fallback"

    status: VerificationStatus = "VERIFIED" if not reasons else "UNVERIFIED"
    if status == "UNVERIFIED":
        resolved_trust = "unverified"

    return ClaimVerificationResult(
        claim_id=claim.claim_id,
        status=status,
        text=claim.text,
        reasons=reasons,
        lower_trust=is_lower_trust,
        trust_level=resolved_trust,
        quote_results=quote_results,
        pinpoint_verified=pinpoint_verified,
    )


def verify_claims(
    claims: Sequence[AtomicClaim | dict[str, Any]],
    evidence_store: dict[str, EvidenceSource | dict[str, Any]],
    global_relevant_date: Optional[str] = None,
) -> VerificationBatchSummary:
    """Batch verify multiple atomic claims deterministically."""
    results: list[ClaimVerificationResult] = []
    for item in claims:
        if isinstance(item, AtomicClaim):
            c = item
        elif isinstance(item, dict):
            c = AtomicClaim(
                claim_id=str(item.get("claim_id", "")),
                text=str(item.get("text", "")),
                evidence_ids=list(item.get("evidence_ids", [])),
                pinpoint=item.get("pinpoint"),
                relevant_date=item.get("relevant_date"),
            )
        else:
            continue
        res = verify_claim(c, evidence_store, global_relevant_date=global_relevant_date)
        results.append(res)

    verified_count = sum(1 for r in results if r.verified)
    unverified_count = len(results) - verified_count
    return VerificationBatchSummary(
        results=results,
        total_claims=len(results),
        verified_claims=verified_count,
        unverified_claims=unverified_count,
        all_verified=(unverified_count == 0 and len(results) > 0),
    )
