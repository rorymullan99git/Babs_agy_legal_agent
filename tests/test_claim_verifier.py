"""Tests for the deterministic claim verifier."""

from __future__ import annotations

from legal_helper.citations import (
    AtomicClaim,
    EvidenceSource,
    verify_claim,
    verify_claims,
)


def test_claim_without_evidence_labelled_unverified() -> None:
    # Acceptance Test: A claim without evidence is removed or labelled UNVERIFIED.
    claim = AtomicClaim(
        claim_id="c1",
        text="The defendant owed a duty of care in negligence.",
        evidence_ids=[],
    )
    res = verify_claim(claim, {})
    assert res.status == "UNVERIFIED"
    assert not res.verified
    assert "no evidence provided" in res.reasons[0]


def test_real_section_with_wrong_quotation_fails() -> None:
    # Acceptance Test: A real section with a wrong quotation is flagged as not found.
    evidence = {
        "ev1": EvidenceSource(
            id="ev1",
            text="A person is not criminally responsible for an act or omission that occurs independently of the exercise of the person's will.",
            citation="Criminal Code 1899 (Qld) s 23(1)(a)",
            source_type="legislation",
            status="in_force",
            sections=["23", "23(1)(a)"],
        )
    }
    # Fabricated quotation
    claim = AtomicClaim(
        claim_id="c2",
        text="Section 23 provides that \"a person is strictly liable for any unexpected accident\".",
        evidence_ids=["ev1"],
        pinpoint="s 23(1)(a)",
    )
    res = verify_claim(claim, evidence)
    assert res.status == "UNVERIFIED"
    assert not res.verified
    assert any("does not round-trip" in r for r in res.reasons)


def test_provision_not_in_force_on_relevant_date_flagged() -> None:
    # Acceptance Test: A provision not in force on the relevant date is flagged.
    evidence = {
        "ev_repealed": EvidenceSource(
            id="ev_repealed",
            text="Historical provision text concerning defamation law.",
            citation="Defamation Act 1889 (Qld) s 5",
            source_type="legislation",
            status="repealed",
            in_force_start="1889-10-14",
            in_force_end="2005-12-31",
            sections=["5"],
        )
    }
    # Incident date occurred in 2024
    claim = AtomicClaim(
        claim_id="c3",
        text="The action is governed by section 5 of the Defamation Act 1889.",
        evidence_ids=["ev_repealed"],
        pinpoint="s 5",
        relevant_date="2024-03-01",
    )
    res = verify_claim(claim, evidence)
    assert res.status == "UNVERIFIED"
    assert not res.verified
    assert any("repealed" in r for r in res.reasons)


def test_pinpoint_to_nonexistent_page_or_clause_in_upload_fails() -> None:
    # Acceptance Test: A pinpoint to a page or clause that does not exist in the upload fails.
    evidence = {
        "doc1": EvidenceSource(
            id="doc1",
            text="1. Term.\n2. Services.\n3. Consideration.\n3.1 The fee is $1000 payable monthly.",
            citation="[Doc]",
            source_type="document",
            pages=[1, 2, 3],
            clauses=["1", "2", "3", "3.1"],
        )
    }

    # Pinpoint page 99 does not exist
    claim_bad_page = AtomicClaim(
        claim_id="c4a",
        text="The agreement specifies fees on page 99.",
        evidence_ids=["doc1"],
        pinpoint="p. 99",
    )
    res_page = verify_claim(claim_bad_page, evidence)
    assert res_page.status == "UNVERIFIED"
    assert any("page 99 does not exist" in r for r in res_page.reasons)

    # Pinpoint clause 9.4 does not exist
    claim_bad_clause = AtomicClaim(
        claim_id="c4b",
        text="The agreement specifies indemnity in clause 9.4.",
        evidence_ids=["doc1"],
        pinpoint="cl 9.4",
    )
    res_clause = verify_claim(claim_bad_clause, evidence)
    assert res_clause.status == "UNVERIFIED"
    assert any("clause 9.4 does not exist" in r for r in res_clause.reasons)


def test_fallback_or_ocr_page_marked_lower_trust() -> None:
    # Acceptance Test: A fallback-parsed or OCR page is marked lower trust.
    evidence_ocr = {
        "doc_ocr": EvidenceSource(
            id="doc_ocr",
            text="The buyer shall inspect the goods within seven days.",
            citation="[Doc p. 2]",
            source_type="document",
            pages=[1, 2],
            clauses=["4"],
            lower_trust=True,
            trust_level="low_ocr",
            trust_reason="scanned PDF processed via RapidOCR",
        )
    }
    claim = AtomicClaim(
        claim_id="c5",
        text="The buyer is required to \"inspect the goods within seven days\".",
        evidence_ids=["doc_ocr"],
        pinpoint="p. 2",
    )
    res = verify_claim(claim, evidence_ocr)
    assert res.status == "VERIFIED"
    assert res.verified
    assert res.lower_trust
    assert res.trust_level == "low_ocr"


def test_source_quote_with_em_dash_matches_hyphen_variant() -> None:
    # Acceptance Test: A source quote containing an em dash verifies against a hyphen variant of the same quote.
    # Source text contains em dash:
    source_with_em_dash = "The general rule\u2014subject to statutory exceptions\u2014is that liability requires fault."
    evidence = {
        "ev_dash": EvidenceSource(
            id="ev_dash",
            text=source_with_em_dash,
            citation="High Court Judgment [2020] HCA 10",
            source_type="case",
        )
    }

    # Claim quotes text with standard hyphens:
    claim = AtomicClaim(
        claim_id="c6",
        text="The High Court affirmed that \"The general rule-subject to statutory exceptions-is that liability requires fault.\"",
        evidence_ids=["ev_dash"],
    )
    res = verify_claim(claim, evidence)
    assert res.status == "VERIFIED"
    assert res.verified
    assert len(res.quote_results) == 1
    assert res.quote_results[0].status == "exact"


def test_batch_verification_all_verified_and_summary() -> None:
    evidence = {
        "ev1": EvidenceSource(
            id="ev1",
            text="Section 23 of the Criminal Code 1899 provides excuse for accident.",
            citation="Criminal Code 1899 (Qld) s 23",
            source_type="legislation",
            status="in_force",
            sections=["23"],
        )
    }
    claims = [
        AtomicClaim(
            claim_id="1",
            text="Section 23 provides an excuse for accident.",
            evidence_ids=["ev1"],
            pinpoint="s 23",
        ),
        AtomicClaim(
            claim_id="2",
            text="Unsupported claim with no citation.",
            evidence_ids=[],
        ),
    ]
    batch = verify_claims(claims, evidence)
    assert batch.total_claims == 2
    assert batch.verified_claims == 1
    assert batch.unverified_claims == 1
    assert not batch.all_verified
