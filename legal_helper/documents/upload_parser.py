"""Upload parsing with Docling and pdfplumber fallback.

Preserves page numbers, headings, clause numbers, and tables.
Enforces Hard Rules:
- If Docling is unavailable, pdfplumber (never pypdf) is used as a fallback.
- Every anchor from the fallback is marked lower trust with bounding_box_claims=False.
- Any page processed via OCR is marked lower trust (trust_level="low_ocr").
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Optional, Sequence

from ..citations.claim_verifier import EvidenceSource


ParserType = Literal["docling", "pdfplumber", "docx_reader"]
TrustLevel = Literal["high", "low_ocr", "low_fallback", "unverified"]


@dataclass(frozen=True)
class ParsedTable:
    """Extracted table representation."""

    page_number: int
    rows: list[list[str]]
    markdown: str


@dataclass(frozen=True)
class ParsedHeading:
    """Extracted heading."""

    level: int
    title: str
    page_number: int


@dataclass(frozen=True)
class ParsedClause:
    """Extracted clause structure."""

    clause_number: str
    heading: Optional[str]
    page_number: int
    text: str
    anchor: str  # e.g. [Doc p. 4, cl 3.2] or [Doc cl 3.2]


@dataclass(frozen=True)
class ParsedPage:
    """Individual parsed page with text and metadata."""

    page_number: int
    text: str
    is_ocr: bool = False
    lower_trust: bool = False
    trust_level: TrustLevel = "high"
    trust_reason: Optional[str] = None
    tables: list[ParsedTable] = field(default_factory=list)


@dataclass(frozen=True)
class ParsedDocument:
    """Full structured document representation."""

    file_path: str
    file_type: str
    parser_used: ParserType
    lower_trust: bool
    trust_level: TrustLevel
    bounding_box_claims: bool
    trust_reason: Optional[str]
    pages: list[ParsedPage]
    headings: list[ParsedHeading]
    clauses: list[ParsedClause]
    tables: list[ParsedTable]
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_evidence_source(self, evidence_id: str = "doc_upload") -> EvidenceSource:
        """Convert parsed document into an EvidenceSource for claim verification."""
        page_nums = [p.page_number for p in self.pages]
        clause_nums = [c.clause_number for c in self.clauses]
        return EvidenceSource(
            id=evidence_id,
            text=self.text,
            title=Path(self.file_path).name,
            citation=f"[Doc: {Path(self.file_path).name}]",
            source_type="document",
            pages=page_nums if page_nums else None,
            clauses=clause_nums if clause_nums else None,
            lower_trust=self.lower_trust,
            trust_level=self.trust_level,
            trust_reason=self.trust_reason,
        )


_CLAUSE_PATTERN = re.compile(
    r"^(?:(?:clause|cl\.?|section|sec\.?|art\.?|article)\s+)?([0-9]+(?:\.[0-9]+)*(?:\([a-z0-9]+\))*|[A-Z]\.|\([a-z0-9]+\))\s+([A-Z].*)",
    re.IGNORECASE,
)


def _table_to_markdown(rows: Sequence[Sequence[Any]]) -> str:
    """Format raw tabular rows into clean markdown."""
    if not rows:
        return ""
    clean_rows: list[list[str]] = []
    col_counts = [len(r) for r in rows if r]
    if not col_counts:
        return ""
    max_cols = max(col_counts)
    for r in rows:
        cells = [str(cell or "").replace("\n", " ").strip() for cell in r]
        while len(cells) < max_cols:
            cells.append("")
        clean_rows.append(cells)

    header = clean_rows[0]
    separator = ["---"] * max_cols
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(separator) + " |"]
    for row in clean_rows[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _extract_clauses_from_text(page_num: int, text: str) -> tuple[list[ParsedClause], list[ParsedHeading]]:
    """Identify clauses and headings from page lines."""
    clauses: list[ParsedClause] = []
    headings: list[ParsedHeading] = []

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        m = _CLAUSE_PATTERN.match(line)
        if m:
            num = m.group(1).rstrip(".")
            title = m.group(2).strip()
            anchor = f"[Doc p. {page_num}, cl {num}]"
            clauses.append(
                ParsedClause(
                    clause_number=num,
                    heading=title,
                    page_number=page_num,
                    text=line,
                    anchor=anchor,
                )
            )
        elif len(line) < 80 and not line.endswith(".") and (line.isupper() or line.istitle()):
            headings.append(ParsedHeading(level=1, title=line, page_number=page_num))

    return clauses, headings


def _parse_pdf_pdfplumber(path: Path) -> ParsedDocument:
    """Parse PDF with pdfplumber fallback.

    Marks every anchor lower trust with bounding_box_claims=False.
    """
    import pdfplumber

    pages_out: list[ParsedPage] = []
    all_clauses: list[ParsedClause] = []
    all_headings: list[ParsedHeading] = []
    all_tables: list[ParsedTable] = []
    combined_texts: list[str] = []

    has_ocr = False

    with pdfplumber.open(path) as pdf:
        for idx, page in enumerate(pdf.pages, start=1):
            raw_text = page.extract_text() or ""
            # OCR / Scanned page detection
            is_scanned = len(raw_text.strip()) < 100 and len(page.images or []) > 0
            if is_scanned:
                has_ocr = True
                p_trust_level: TrustLevel = "low_ocr"
                p_reason = "scanned page with sparse text; marked lower trust"
            else:
                p_trust_level = "low_fallback"
                p_reason = "parsed via pdfplumber fallback; no bounding box claims"

            # Table extraction
            page_tables: list[ParsedTable] = []
            try:
                extracted = page.extract_tables() or []
                for tbl in extracted:
                    md = _table_to_markdown(tbl)
                    page_tables.append(ParsedTable(page_number=idx, rows=tbl, markdown=md))
            except Exception:
                pass
            all_tables.extend(page_tables)

            page_full_text = raw_text
            if page_tables:
                page_full_text += "\n\n" + "\n\n".join(t.markdown for t in page_tables)

            p_clauses, p_headings = _extract_clauses_from_text(idx, page_full_text)
            all_clauses.extend(p_clauses)
            all_headings.extend(p_headings)

            pages_out.append(
                ParsedPage(
                    page_number=idx,
                    text=page_full_text,
                    is_ocr=is_scanned,
                    lower_trust=True,
                    trust_level=p_trust_level,
                    trust_reason=p_reason,
                    tables=page_tables,
                )
            )
            combined_texts.append(f"--- Page {idx} ---\n{page_full_text}")

    doc_trust: TrustLevel = "low_ocr" if has_ocr else "low_fallback"
    doc_reason = (
        "scanned pages detected; marked lower trust"
        if has_ocr
        else "parsed via pdfplumber fallback parser; no bounding box claims"
    )

    return ParsedDocument(
        file_path=str(path),
        file_type="pdf",
        parser_used="pdfplumber",
        lower_trust=True,
        trust_level=doc_trust,
        bounding_box_claims=False,
        trust_reason=doc_reason,
        pages=pages_out,
        headings=all_headings,
        clauses=all_clauses,
        tables=all_tables,
        text="\n\n".join(combined_texts),
        metadata={"page_count": len(pages_out)},
    )


def _parse_docx(path: Path) -> ParsedDocument:
    """Parse DOCX preserving headings, clause numbering, and tables."""
    import docx

    doc = docx.Document(path)
    paragraphs_text: list[str] = []
    clauses: list[ParsedClause] = []
    headings: list[ParsedHeading] = []
    tables: list[ParsedTable] = []

    # Process paragraphs
    for p in doc.paragraphs:
        txt = p.text.strip()
        if not txt:
            continue
        paragraphs_text.append(txt)
        style_name = getattr(p.style, "name", "")
        if "Heading" in style_name:
            try:
                lvl = int("".join(c for c in style_name if c.isdigit()) or "1")
            except ValueError:
                lvl = 1
            headings.append(ParsedHeading(level=lvl, title=txt, page_number=1))
        m = _CLAUSE_PATTERN.match(txt)
        if m:
            num = m.group(1).rstrip(".")
            title = m.group(2).strip()
            clauses.append(
                ParsedClause(
                    clause_number=num,
                    heading=title,
                    page_number=1,
                    text=txt,
                    anchor=f"[Doc cl {num}]",
                )
            )

    # Process tables
    for tbl in doc.tables:
        raw_rows: list[list[str]] = []
        for row in tbl.rows:
            raw_rows.append([cell.text.strip() for cell in row.cells])
        md = _table_to_markdown(raw_rows)
        tables.append(ParsedTable(page_number=1, rows=raw_rows, markdown=md))

    table_mds = [t.markdown for t in tables]
    full_text = "\n\n".join(paragraphs_text + table_mds)
    page = ParsedPage(
        page_number=1,
        text=full_text,
        is_ocr=False,
        lower_trust=False,
        trust_level="high",
        tables=tables,
    )

    return ParsedDocument(
        file_path=str(path),
        file_type="docx",
        parser_used="docx_reader",
        lower_trust=False,
        trust_level="high",
        bounding_box_claims=False,
        trust_reason=None,
        pages=[page],
        headings=headings,
        clauses=clauses,
        tables=tables,
        text=full_text,
        metadata={"paragraph_count": len(paragraphs_text), "table_count": len(tables)},
    )


def parse_upload(file_path: str | Path) -> ParsedDocument:
    """Parse an uploaded PDF or DOCX document with Docling or compliant fallbacks."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()

    # 1. Attempt Docling if available
    try:
        import docling  # noqa: F401
        from docling.document_converter import DocumentConverter

        converter = DocumentConverter()
        conv_res = converter.convert(str(path))
        exported_text = conv_res.document.export_to_markdown()

        # Docling successful high-trust parse
        pages_out = [
            ParsedPage(
                page_number=1,
                text=exported_text,
                is_ocr=False,
                lower_trust=False,
                trust_level="high",
            )
        ]
        clauses, headings = _extract_clauses_from_text(1, exported_text)
        return ParsedDocument(
            file_path=str(path),
            file_type=suffix.lstrip("."),
            parser_used="docling",
            lower_trust=False,
            trust_level="high",
            bounding_box_claims=True,
            trust_reason=None,
            pages=pages_out,
            headings=headings,
            clauses=clauses,
            tables=[],
            text=exported_text,
            metadata={"docling_success": True},
        )
    except Exception:
        # Fall through to pdfplumber or python-docx
        pass

    # 2. Resilient fallback execution
    if suffix == ".pdf":
        return _parse_pdf_pdfplumber(path)
    elif suffix in (".docx", ".doc"):
        return _parse_docx(path)
    else:
        # Fallback text read
        content = path.read_text(encoding="utf-8", errors="replace")
        clauses, headings = _extract_clauses_from_text(1, content)
        page = ParsedPage(page_number=1, text=content, lower_trust=True, trust_level="low_fallback")
        return ParsedDocument(
            file_path=str(path),
            file_type=suffix.lstrip("."),
            parser_used="pdfplumber",
            lower_trust=True,
            trust_level="low_fallback",
            bounding_box_claims=False,
            trust_reason="plain text fallback parser; no bounding box claims",
            pages=[page],
            headings=headings,
            clauses=clauses,
            tables=[],
            text=content,
        )
