# Operational Notes: Babs_agy_legal_agent

Operator-level notes for running, testing, and maintaining Babs_agy_legal_agent: a grounded Queensland legal research agent built for law students and practitioners.

## Environment

- Python 3.12+ virtual environment or conda environment with project dependencies.
- Windows, macOS, or Linux. On Windows, native certificate validation is handled automatically via `truststore`.
- Running commands via virtual environment:
  - `.\.venv\Scripts\python.exe -m pytest -q tests/`
  - `.\.venv\Scripts\python.exe -m legal_helper analyze --file <path>`
  - `.\.venv\Scripts\python.exe -m legal_helper serve --port 8010`

## Core CLI Commands

1. Document Upload Analysis:
   ```bash
   python -m legal_helper analyze --file path/to/document.pdf [--matter-type {standard,fact_heavy}] [--date YYYY-MM-DD]
   ```
   Parses uploaded contracts, cases, or notes; extracts pages, clauses, and tables; formulates atomic claims; runs the adversarial critic loop; verifies every statement against source text; and produces a grounded IRAC breakdown.

2. Interactive Legal Chat:
   ```bash
   python -m legal_helper chat --jurisdiction AU
   ```

3. One-Shot Research Task:
   ```bash
   python -m legal_helper run --jurisdiction AU --task "Analyze s 23 of the Queensland Criminal Code"
   ```

4. Web Service:
   ```bash
   python -m legal_helper serve --host 0.0.0.0 --port 8010
   ```

## In-Tree MCP Server

The Australian legal research suite is exposed as an in-tree stdio Model Context Protocol (MCP) server:
```bash
python -m legal_helper.mcp.servers.babs_au_legal
```
Registered tools:
- `qld_legislation_search`: Search Queensland legislation via legislation.qld.gov.au
- `qld_legislation_fetch`: Fetch Queensland statute text by title/slug, section, and point-in-time date
- `qld_caselaw_fetch`: Fetch Queensland judgments (QCA, QSC, QDC, QCAT) by citation or URL
- `cth_legislation_fetch`: Fetch Commonwealth legislation via Federal Register of Legislation
- `hca_judgment_fetch`: Fetch High Court of Australia judgments
- `verify_claims`: Deterministic verification of claims against evidence with quote roundtripping
- `analyze_document`: End-to-end document upload parsing and grounded IRAC analysis

Configuration lives in `.mcp.json` under `jurisdictions: ["AU"]`.

## RAG Corpus and Leads

Stream and filter primary law from the Open Australian Legal Corpus:
```bash
python scripts/fetch_au_corpus.py --max-records 100 --output data/corpus/au_sample.jsonl
```
Corpus records are strictly treated as research leads (`status: corpus only`). Any provision or precedent cited in final analysis must be fetched and verified live.

## Testing Standards

- Default test run is completely offline and uses recorded fixtures:
  ```bash
  python -m pytest -q tests/
  ```
- Acceptance tests verify:
  - Fabricated case names and citations are flagged UNVERIFIED.
  - Provisions not in force on the relevant date are flagged.
  - Upload anchors to non-existent pages or clauses fail verification.
  - Fallback-parsed and OCR pages propagate lower-trust warnings.
  - AGLC4 citation rules format statutes, cases, and document anchors.
  - Quotes with em dashes or curly quotes round-trip accurately without mutating source text.
- Live network smoke tests (skipped by default) can be enabled with `LEGAL_HELPER_LIVE=1`:
  ```bash
  LEGAL_HELPER_LIVE=1 python -m pytest -q tests/test_qld_legislation_connector.py tests/test_au_connectors.py
  ```

## Hard Operational Rules

1. Deterministic verification: All claims, quotes, and pinpoints are checked by code in `claim_verifier.py`.
2. Zero invention: Never hallucinate an authority, citation, quote, or date.
3. Closed evidence: Final analysis relies solely on text retrieved or uploaded during the session.
4. Scraping etiquette: Never scrape Jade. No bulk scraping of AustLII. Use official government and court endpoints.
5. Mandatory banner: Every analysis output must begin with `> Research aid, not legal advice.`
6. No em dashes: Em dashes are strictly prohibited in code, comments, documentation, and commit messages (exempt only in verbatim source quotes).
