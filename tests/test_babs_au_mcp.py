"""Tests for babs_au_legal in-tree MCP server and tool dispatch."""

from __future__ import annotations

import json
from unittest.mock import patch

from legal_helper.documents.upload_parser import ParsedClause, ParsedDocument, ParsedPage
from legal_helper.mcp.servers.babs_au_legal.__main__ import dispatch


def test_babs_au_mcp_unknown_tool():
    res = json.loads(dispatch("nonexistent_tool", {}))
    assert "error" in res
    assert "unknown tool" in res["error"]


def test_babs_au_mcp_dispatch_qld_legislation():
    with patch(
        "legal_helper.connectors.qld_legislation.qld_legislation_fetch",
        return_value={"text": "s 23 Criminal Code text", "status": "in_force"},
    ) as mock_fetch:
        res = json.loads(
            dispatch(
                "qld_legislation_fetch",
                {"title_or_slug": "Criminal Code", "pinpoint": "s 23"},
            )
        )
        assert res["status"] == "in_force"
        assert "s 23" in res["text"]
        mock_fetch.assert_called_once()


def test_babs_au_mcp_dispatch_verify_claims():
    claims = [
        {
            "claim_id": "c1",
            "text": 'The rule states: "no person shall be put twice in jeopardy".',
            "evidence_ids": ["e1"],
        }
    ]
    evidence_sources = [
        {
            "source_id": "e1",
            "citation": "Criminal Code Act 1899 (Qld)",
            "source_type": "statute",
            "text": "no person shall be put twice in jeopardy.",
            "status": "in_force",
        }
    ]

    res = json.loads(
        dispatch(
            "verify_claims",
            {"claims": claims, "evidence_sources": evidence_sources},
        )
    )
    assert res["total_claims"] == 1
    assert res["verified_claims"] == 1
    results = res["results"]
    assert len(results) == 1
    assert results[0]["claim_id"] == "c1"
    assert results[0]["status"] == "VERIFIED"
    assert len(results[0]["quote_results"]) == 1
    assert results[0]["quote_results"][0]["status"] == "exact"


def test_babs_au_mcp_dispatch_analyze_document(tmp_path):
    doc_path = tmp_path / "test_contract.txt"
    doc_path.write_text("Clause 1.1 The supplier shall deliver the goods by Friday.", encoding="utf-8")

    dummy_parsed = ParsedDocument(
        file_path=str(doc_path),
        file_type="txt",
        parser_used="docling",
        lower_trust=False,
        trust_level="high",
        bounding_box_claims=True,
        trust_reason=None,
        pages=[
            ParsedPage(
                page_number=1,
                text="Clause 1.1 The supplier shall deliver the goods by Friday.",
            )
        ],
        headings=[],
        clauses=[
            ParsedClause(
                clause_number="1.1",
                heading=None,
                text="The supplier shall deliver the goods by Friday.",
                page_number=1,
                anchor="[Doc p. 1, cl 1.1]",
            )
        ],
        tables=[],
        text="Clause 1.1 The supplier shall deliver the goods by Friday.",
    )

    with patch("legal_helper.mcp.servers.babs_au_legal.__main__.parse_upload", return_value=dummy_parsed):
        res = json.loads(
            dispatch(
                "analyze_document",
                {"file_path": str(doc_path), "matter_type": "standard"},
            )
        )
        assert "rendered_analysis" in res
        assert "Research aid, not legal advice" in res["rendered_analysis"]
        assert res["pages"] == 1
        assert res["trust_level"] == "high"
