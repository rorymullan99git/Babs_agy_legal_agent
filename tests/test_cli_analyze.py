"""Test CLI analyze subcommand and AU jurisdiction flag."""

from __future__ import annotations

from unittest.mock import patch

from legal_helper.cli import main
from legal_helper.documents.upload_parser import ParsedClause, ParsedDocument, ParsedPage


def test_cli_analyze_subcommand(tmp_path, capsys):
    test_file = tmp_path / "notes.txt"
    test_file.write_text("Clause 2.1 The lessee shall maintain the premises.", encoding="utf-8")

    dummy_parsed = ParsedDocument(
        file_path=str(test_file),
        file_type="txt",
        parser_used="docling",
        lower_trust=False,
        trust_level="high",
        bounding_box_claims=True,
        trust_reason=None,
        pages=[ParsedPage(page_number=1, text="Clause 2.1 The lessee shall maintain the premises.")],
        headings=[],
        clauses=[
            ParsedClause(
                clause_number="2.1",
                heading=None,
                text="The lessee shall maintain the premises.",
                page_number=1,
                anchor="[Doc p. 1, cl 2.1]",
            )
        ],
        tables=[],
        text="Clause 2.1 The lessee shall maintain the premises.",
    )

    with patch("legal_helper.documents.upload_parser.parse_upload", return_value=dummy_parsed):
        ret = main(["analyze", "--file", str(test_file), "--jurisdiction", "AU"])
        assert ret == 0
        captured = capsys.readouterr()
        assert "Research aid, not legal advice" in captured.out
        assert "## Sources" in captured.out
