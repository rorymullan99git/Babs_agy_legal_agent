# ADR 001: Architecture of Babs Grounded Legal Research Agent

## Status

Accepted

## Context

Final-year Queensland law students require a grounded research assistant to analyze uploaded documents (contracts, cases, statutes, and notes) and return structured legal breakdowns. General-purpose language models frequently fabricate authorities, invent pinpoint citations, quote inaccuracies, and extrapolate dates. In legal practice and study, honesty regarding what cannot be verified is strictly superior to unverified breadth or superficial polish.

This project builds "Babs_agy_legal_agent" on top of the `lawgent` foundation (package `legal_helper`), adapting it specifically for Queensland and Australian legal research with uncompromising verification guarantees.

## Decision Drivers

1. Deterministic Verification: All verification checks must execute in deterministic code rather than relying on language model self-evaluation.
2. Zero Invention: No authority, pinpoint citation, quotation, or date may be invented. If a source cannot be checked, it must be labelled UNVERIFIED or designated "pinpoint unavailable".
3. Closed Evidence World: Statements can only cite text retrieved live or uploaded during the specific run.
4. Point-in-Time Accuracy: Legislation must be verified as in force as at the relevant date of the matter.
5. Trust Propagation: Low-trust extraction (OCR, fallback parsers) must propagate to claims.
6. Ethical Sourcing: Jade scraping and bulk AustLII scraping are strictly forbidden.

## Key Architectural Decisions

### 1. Australian Source Hierarchy and Playbook

We configured Australia (`AU`) as the primary jurisdiction with Queensland (`QLD`) as default subjurisdiction. The playbook enforces the canonical Australian source hierarchy:
- Commonwealth Constitution
- Commonwealth Statutes and Regulations
- Queensland Statutes and Subordinate Legislation
- High Court of Australia (binding nationally)
- Queensland Court of Appeal (binding on Queensland courts)
- Interstate Appellate Courts (persuasive under intermediate appellate comity)
- Queensland Supreme, District, and Magistrates Courts, and QCAT
- Secondary sources (scholarly treatises, Law Reform Commission reports)

Precedent weighting is mandatory: every case cited must carry a weight label (`binding`, `comity_appellate`, `persuasive`, or `distinguishable`).

### 2. AGLC4 Citation Engine

We implemented an AGLC4 (Australian Guide to Legal Citation, 4th ed) formatter supporting:
- Statutes and subordinate legislation with pinpoints (`s`, `pt`, `div`, `sch`, `cl`, `para`)
- Schedule short titles, e.g.: `Criminal Code Act 1899 (Qld) sch 1 ('Criminal Code') s 23`
- Case citations using medium neutral citations (`[2024] HCA 1`) and authorised law reports (`(2023) 275 CLR 1`)
- Uploaded document anchors, e.g.: `[Doc p. 4, cl 3.2]`
- Uncovered forms emit a `format_unverified` flag rather than risking non-compliant output.

### 3. Deterministic Claim Verifier

Claim verification (`legal_helper/citations/claim_verifier.py`) operates offline and deterministically on atomic claims:
- Quotation Roundtrip: Extracts quoted phrases and tests exact or near substring presence in source text. Normalises hyphens, en dashes, em dashes, and curly quotes while preserving the verbatim displayed quote.
- Point-in-Time Status: Confirms statute commencement and repeal dates against the matter date.
- Pinpoint Structural Verification: Verifies that cited page numbers, clause IDs, and sections exist within the document structure.
- Trust Level: Inherits `low_ocr` or `low_fallback` trust markers from parsed sources. Claims failing verification are marked `UNVERIFIED`.

### 4. Upload Document Parsing Pipeline

Document parsing (`legal_helper/documents/upload_parser.py`) processes PDF and DOCX uploads:
- Primary parser: Docling for rich layout and clause structure.
- Fallback parser: `pdfplumber` (never `pypdf`), explicitly marking extracted text with `lower_trust=True`, `trust_level="low_fallback"`, and `bounding_box_claims=False`.
- OCR detection: Scanned pages with minimal text density are flagged as `low_ocr`.

### 5. Official Connectors and Scraping Guardrails

To protect against licensing breaches and automated IP blocks, we built dedicated connectors using official public APIs and endpoints:
- Queensland Legislation: `legislation.qld.gov.au` whole-act point-in-time HTML endpoints.
- Queensland Judgments: `queenslandjudgments.com.au` official judgment repository.
- Commonwealth Legislation: `legislation.gov.au` Federal Register of Legislation.
- High Court of Australia: `hcourt.gov.au` decisions.
- Third-party scrapers for Jade and bulk AustLII are deliberately excluded.

### 6. Streaming Open Australian Legal Corpus Leads

The Open Australian Legal Corpus (`umarbutler/open-australian-legal-corpus`) is loaded via streaming filters for Queensland and Commonwealth subsets (`scripts/fetch_au_corpus.py`). Corpus hits are treated strictly as research leads (`status: corpus only`); any provision or case cited in a final analysis must be retrieved and verified against primary sources.

### 7. Structured IRAC Analysis and Output Contract

The analysis pipeline (`legal_helper/au_analysis.py`) formats outputs as IRAC (or FIRAC for fact-heavy scenarios):
- Every statement carries a bracketed reference marker.
- An adversarial critic loop (up to 3 rounds) reviews claims against evidence text to catch unsupported or overstated propositions.
- Mandatory Research Aid Banner: `> Research aid, not legal advice.`
- Numbered Sources section with verified status tags.
- Mandatory `## What I could not verify` section honestly documenting omissions and unverified assertions.

### 8. CLI and MCP Server Integration

The agent is exposed through:
- Command-line interface: `python -m legal_helper analyze --file <path> [--matter-type {standard,fact_heavy}] [--date YYYY-MM-DD]`
- In-tree stdio MCP server: `python -m legal_helper.mcp.servers.babs_au_legal` exposing research connectors, verification tools, and upload analysis to external agent environments.

## Consequences

- Full traceability: Every output assertion is tied to a specific verified line or clause of evidence.
- Safe failure: Gaps in retrieved text or unavailable pinpoints are surfaced immediately to the user rather than smoothed over with plausible text.
- Offline resilience: Fixture-based testing ensures core verification and analysis functions execute reliably without internet access.
