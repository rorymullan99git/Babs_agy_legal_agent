# CLAUDE.md: Project Guidance for Babs_agy_legal_agent

Project-level guidelines for developing and running Babs_agy_legal_agent: a grounded Queensland legal research agent.

## Identity & Scope

`Babs_agy_legal_agent` provides verifiable, source-grounded legal research for final-year law students and legal professionals. The primary jurisdiction is **Australia (`AU`)** with **Queensland (`QLD`)** as the default subjurisdiction.

A law student uploads a document (contract, case judgment, statute, or notes) and receives an IRAC-structured breakdown where every legal statement carries a reference marker verified by deterministic code against source text. Honesty about unverified points strictly supersedes breadth or speculative conclusions.

## Core Rules

1. Enforcement in Code: Verification is never delegated to language model self-assessment. Deterministic Python logic (`legal_helper/citations/claim_verifier.py`) checks all quotes, pinpoints, dates, and in-force statuses.
2. Zero Invention: Never hallucinate an authority, citation, quote, or date. Where a pinpoint or authority cannot be verified, emit "pinpoint unavailable" or mark the claim `UNVERIFIED`.
3. Closed Evidence World: Assertions must cite only text retrieved or uploaded during the active session.
4. Point-in-Time Statute Law: Legislation must be verified as in force as at the date of the relevant facts.
5. Trust Propagation: Documents parsed via fallback extractors (`pdfplumber`) or containing OCR/scanned text must propagate `low_fallback` or `low_ocr` lower-trust indicators.
6. Scraping Etiquette: Never scrape Jade. No bulk scraping of AustLII. Use official endpoints (`legislation.qld.gov.au`, `queenslandjudgments.com.au`, `legislation.gov.au`, `hcourt.gov.au`) with respectful rate limits and descriptive user agents.
7. Output Contract: Every rendered answer must include:
   - Top banner: `> Research aid, not legal advice.`
   - Reference marker on every statement (`[1]`, `[Doc p. 4, cl 3.2]`, or `[UNVERIFIED]`).
   - Numbered `## Sources` section with approved status labels (`verified online`, `verified in uploaded document`, `corpus only`, `unverified`, `pinpoint unavailable`).
   - Dedicated `## What I could not verify` section.
8. No Em Dashes: Em dashes (Unicode U+2014) are strictly forbidden in code comments, documentation, and commit messages. Verbatim source quotes are exempt.
9. No Secrets: API tokens must never be hardcoded or printed. Use `.env` or environment variables.

## Architecture & Code Structure

- `legal_helper/playbook/general_playbook.md`: Australian legal source hierarchy, precedent weight rules, and point-in-time guidance.
- `legal_helper/citations/au.py`: Australian citation parsing and validation (statutes, MNCs, law reports, document anchors).
- `legal_helper/citations/format.py`: AGLC4 citation formatter.
- `legal_helper/citations/claim_verifier.py`: Deterministic claim verification engine (quote roundtrip with dash/curly quote normalisation, in-force verification, structural pinpoint matching, trust levels).
- `legal_helper/documents/upload_parser.py`: PDF and DOCX document extraction (Docling with `pdfplumber` fallback, page/clause/table indexing, OCR detection).
- `legal_helper/connectors/`: Official legal data connectors:
  - `qld_legislation.py`: Queensland legislation via `legislation.qld.gov.au`
  - `qld_caselaw.py`: Queensland court judgments via `queenslandjudgments.com.au`
  - `cth_legislation.py`: Commonwealth legislation via `legislation.gov.au`
  - `hca_judgments.py`: High Court of Australia judgments
- `legal_helper/au_analysis.py`: IRAC/FIRAC structured analysis, adversarial critic loop (max 3 rounds), and grounded output rendering.
- `legal_helper/mcp/servers/babs_au_legal/`: In-tree stdio MCP server exposing connectors and analysis tools.
- `scripts/fetch_au_corpus.py`: Streaming loader for Open Australian Legal Corpus leads.

## Running Commands

- Run unit tests:
  ```bash
  python -m pytest -q tests/
  ```
- Run document analysis via CLI:
  ```bash
  python -m legal_helper analyze --file path/to/contract.pdf [--matter-type {standard,fact_heavy}] [--date YYYY-MM-DD]
  ```
- Run MCP server:
  ```bash
  python -m legal_helper.mcp.servers.babs_au_legal
  ```
- Start web UI / API:
  ```bash
  python -m legal_helper serve --port 8010
  ```
- Run live connector tests:
  ```bash
  LEGAL_HELPER_LIVE=1 python -m pytest -q tests/test_qld_legislation_connector.py tests/test_au_connectors.py
  ```
