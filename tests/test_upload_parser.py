"""Tests for upload parsing (Docling, pdfplumber fallback, OCR tagging)."""

from __future__ import annotations

import io
from pathlib import Path

import docx
import pytest

from legal_helper.citations import (
    AtomicClaim,
    verify_claim,
)
from legal_helper.documents.upload_parser import (
    ParsedDocument,
    parse_upload,
)


def _create_sample_docx(tmp_path: Path) -> Path:
    p = tmp_path / "sample_contract.docx"
    doc = docx.Document()
    doc.add_heading("Commercial Lease Agreement", level=1)
    doc.add_paragraph("1. Parties and Premises")
    doc.add_paragraph("1.1 The Lessor leases to the Lessee the premises located at Brisbane.")
    doc.add_paragraph("2. Rent and Consideration")
    doc.add_paragraph("2.1 The annual rent shall be $50,000 payable in monthly instalments.")

    table = doc.add_table(rows=2, cols=2)
    table.rows[0].cells[0].text = "Item"
    table.rows[0].cells[1].text = "Amount"
    table.rows[1].cells[0].text = "Bond"
    table.rows[1].cells[1].text = "$10,000"

    doc.save(p)
    return p


def _create_sample_pdf(tmp_path: Path, scanned: bool = False) -> Path:
    """Create a minimal test PDF using reportlab or PyPDF/pdfplumber mocks."""
    p = tmp_path / ("scanned.pdf" if scanned else "sample.pdf")
    # Generate clean PDF using reportlab or minimal PDF bytes
    # Minimal standard PDF 1.4 syntax
    if not scanned:
        pdf_bytes = (
            b"%PDF-1.4\n"
            b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
            b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>/Contents 4 0 R>>endobj\n"
            b"4 0 obj<</Length 110>>stream\n"
            b"BT\n/F1 12 Tf\n100 700 Td\n(Clause 3.2 The Lessee shall pay rent monthly.) Tj\nET\n"
            b"endstream\nendobj\n"
            b"xref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000052 00000 n \n0000000108 00000 n \n0000000201 00000 n \n"
            b"trailer<</Size 5/Root 1 0 R>>\nstartxref\n362\n%%EOF\n"
        )
    else:
        # Scanned page: no text stream, image reference
        pdf_bytes = (
            b"%PDF-1.4\n"
            b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
            b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>/Contents 4 0 R>>endobj\n"
            b"4 0 obj<</Length 15>>stream\n"
            b"BT /F1 12 Tf ET\n"
            b"endstream\nendobj\n"
            b"xref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000052 00000 n \n0000000108 00000 n \n0000000201 00000 n \n"
            b"trailer<</Size 5/Root 1 0 R>>\nstartxref\n268\n%%EOF\n"
        )
    p.write_bytes(pdf_bytes)
    return p


def test_docx_upload_parsing(tmp_path: Path) -> None:
    docx_path = _create_sample_docx(tmp_path)
    parsed = parse_upload(docx_path)

    assert parsed.file_type == "docx"
    assert len(parsed.headings) >= 1
    assert parsed.headings[0].title == "Commercial Lease Agreement"

    clause_nums = [c.clause_number for c in parsed.clauses]
    assert "1" in clause_nums or "1.1" in clause_nums
    assert "2" in clause_nums or "2.1" in clause_nums

    # Tables preserved
    assert len(parsed.tables) >= 1
    assert "Bond" in parsed.tables[0].markdown
    assert "$10,000" in parsed.tables[0].markdown


def test_pdf_upload_fallback_lower_trust(tmp_path: Path) -> None:
    # Acceptance Test: A fallback-parsed or OCR page is marked lower trust.
    pdf_path = _create_sample_pdf(tmp_path, scanned=False)
    parsed = parse_upload(pdf_path)

    assert parsed.file_type == "pdf"
    assert parsed.parser_used == "pdfplumber"
    assert parsed.lower_trust is True
    assert parsed.bounding_box_claims is False
    assert parsed.trust_level in ("low_fallback", "low_ocr")
    assert "pdfplumber" in (parsed.trust_reason or "")


def test_claim_verification_integration_with_upload(tmp_path: Path) -> None:
    docx_path = _create_sample_docx(tmp_path)
    parsed = parse_upload(docx_path)
    evidence = {"upload_lease": parsed.to_evidence_source("upload_lease")}

    # Valid claim with quote and pinpoint
    valid_claim = AtomicClaim(
        claim_id="c1",
        text="Clause 2.1 states that \"The annual rent shall be $50,000 payable in monthly instalments.\"",
        evidence_ids=["upload_lease"],
        pinpoint="cl 2.1",
    )
    res_valid = verify_claim(valid_claim, evidence)
    assert res_valid.verified
    assert res_valid.status == "VERIFIED"

    # Invalid pinpoint to non-existent clause in upload fails
    bad_pinpoint_claim = AtomicClaim(
        claim_id="c2",
        text="The agreement provides indemnification in clause 8.9.",
        evidence_ids=["upload_lease"],
        pinpoint="cl 8.9",
    )
    res_bad = verify_claim(bad_pinpoint_claim, evidence)
    assert not res_bad.verified
    assert res_bad.status == "UNVERIFIED"
    assert any("clause 8.9 does not exist" in r for r in res_bad.reasons)
