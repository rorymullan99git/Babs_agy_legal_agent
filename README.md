# Babs_agy_legal_agent

**A grounded Queensland legal research agent for final-year law students and practitioners.**

Every legal statement carries a reference verified by deterministic code against source text. Honesty about what was not verified strictly supersedes ungrounded polish.

---

> Research aid, not legal advice. This harness assists with legal research and document analysis workflows. Every output must be reviewed by qualified legal counsel before reliance.

---

## Key Capabilities

- **Deterministic Verification in Code**: Language models propose; deterministic Python code verifies. Quotations, pinpoint sections, commencement dates, and document clauses are strictly round-tripped against source text.
- **Australian & Queensland Legal Hierarchy**: Custom playbook implementing the canonical Australian hierarchy: Commonwealth Constitution, Commonwealth statutes/regulations, Queensland statutes/subordinate legislation, High Court of Australia, Queensland Court of Appeal, interstate appellate courts, and trial courts.
- **AGLC4 Citation Formatting**: Formats statutes with pinpoints (`s`, `pt`, `div`, `sch`, `cl`, `para`), schedule short titles (`Criminal Code Act 1899 (Qld) sch 1 ('Criminal Code') s 23`), medium neutral citations (`[2024] HCA 1`), authorised law reports (`(2023) 275 CLR 1`), and document anchors (`[Doc p. 4, cl 3.2]`).
- **Document Upload Analysis**: Parses PDF and DOCX documents (contracts, pleadings, judgments, notes) via Docling with robust `pdfplumber` fallback.
- **Trust Propagation**: Automatically flags OCR-scanned and fallback-extracted pages as lower-trust.
- **Official Connectors Only**: Direct interfaces to Queensland Legislation (`legislation.qld.gov.au`), Queensland Judgments (`queenslandjudgments.com.au`), Federal Register of Legislation (`legislation.gov.au`), and the High Court of Australia (`hcourt.gov.au`). Scraping of Jade and bulk scraping of AustLII are strictly prohibited.
- **Streaming Corpus Leads**: Streams and filters the Open Australian Legal Corpus (`umarbutler/open-australian-legal-corpus`) for Queensland and Commonwealth law without storing massive binaries. Corpus hits serve strictly as leads requiring live verification.
- **In-Tree MCP Server**: Exposes official Australian legal retrieval tools and verification engines over the Model Context Protocol (MCP) for Antigravity, Claude Desktop, and IDE agents.

---

## Quickstart & Setup

### 1. Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- Git

### 2. Installation
Clone the repository and set up a virtual environment:
```bash
git clone https://github.com/rorymullan99git/Babs_agy_legal_agent.git
cd Babs_agy_legal_agent

python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configuration
Copy the sample environment file:
```bash
cp .env.example .env
```
Default settings in `config.yaml` configure Australia (`AU`) as the primary jurisdiction, Queensland (`QLD`) as default subjurisdiction, `aglc4` as citation style, and `enable_cite_check: true`.

---

## Document Upload Analysis

Analyze contracts, briefs, or lecture notes using the dedicated CLI subcommand:

```bash
python -m legal_helper analyze --file path/to/matter_brief.pdf --matter-type standard
```

Options:
- `--file <path>`: Required. Path to PDF, DOCX, or text file.
- `--matter-type {standard,fact_heavy}`: Chooses IRAC (Issue, Rule, Application, Conclusion) or FIRAC (Facts, Issue, Rule, Application, Conclusion).
- `--date YYYY-MM-DD`: Optional point-in-time date for historical matters.
- `--jurisdiction AU`: Confirms Australian legal context.

### Output Contract
Every analysis report strictly adheres to the output contract:
1. Research aid banner at the very top.
2. Every sentence carries a reference marker: `[1]`, `[Doc p. 2, cl 1.1]`, or `[UNVERIFIED]`.
3. Numbered `## Sources` section classifying each authority:
   - `verified online`
   - `verified in uploaded document`
   - `corpus only` (lead only, unverified)
   - `unverified`
   - `pinpoint unavailable`
4. Dedicated `## What I could not verify` section detailing any missing pinpoints, failed quote roundtrips, or unconfirmed historical provisions.

---

## Model Context Protocol (MCP) Server

Babs_agy_legal_agent includes an in-tree stdio MCP server for direct integration into agentic workflows:

```bash
python -m legal_helper.mcp.servers.babs_au_legal
```

### Exposed MCP Tools
- `qld_legislation_search`: Search Queensland Acts and Regulations.
- `qld_legislation_fetch`: Fetch Queensland section text with point-in-time validation.
- `qld_caselaw_fetch`: Fetch Queensland Court of Appeal and Supreme Court judgments.
- `cth_legislation_fetch`: Fetch Commonwealth Acts and pinpoints.
- `hca_judgment_fetch`: Fetch High Court of Australia decisions.
- `verify_claims`: Batch verification of claims against evidence with quote roundtripping.
- `analyze_document`: End-to-end document upload parsing and verified IRAC breakdown.

The MCP server is registered in `.mcp.json` under jurisdiction `AU`.

---

## Australian Legal Corpus Ingestion

To populate initial research leads from the Open Australian Legal Corpus without downloading the entire 1.2 billion token dataset:

```bash
python scripts/fetch_au_corpus.py --max-records 100 --output data/corpus/au_sample.jsonl
```

- Filters exclusively for Commonwealth and Queensland primary law.
- Records are flagged with `status: corpus only` and `corpus_lead=True`.
- In keeping with Hard Rule 3, no corpus lead may be cited as authoritative without being fetched and checked live against primary sources.

---

## Verification & Testing

Run the offline test suite:
```bash
python -m pytest -q tests/
```

### Key Acceptance Tests Verified:
- Fabricated case names and citations fail verification and are flagged `UNVERIFIED`.
- Accurate statutory provisions with wrong quotations are detected as quote mismatches.
- Provisions not in force on the specified matter date are flagged.
- Document pinpoints referencing non-existent pages or clauses fail verification.
- Fallback-parsed documents (`pdfplumber`) and OCR pages propagate lower-trust warnings.
- AGLC4 citation rules accurately format statutes, schedules, law reports, and document anchors.
- Quotes containing em dashes or curly quotes successfully round-trip against normalised text without altering displayed quotations.

### Live Network Smoke Tests
Live connectivity to official endpoints can be validated by setting `LEGAL_HELPER_LIVE=1`:
```bash
LEGAL_HELPER_LIVE=1 python -m pytest -q tests/test_qld_legislation_connector.py tests/test_au_connectors.py
```

---

## Known Limits & Scope

1. **Official Endpoints Only**: Does not scrape Jade or bulk-scrape AustLII. If an official government or court repository experiences temporary downtime, the agent surfaces "pinpoint unavailable" rather than guessing.
2. **Fallback Document Parsing**: When Docling is not installed or runs in a CPU-limited mode, `pdfplumber` extracts text accurately but does not provide precise bounding box coordinates. Such extractions are explicitly marked `trust_level="low_fallback"`.
3. **Point-in-Time Statute Scope**: Point-in-time validation is supported for post-1991 Queensland whole-statute endpoints; pre-1900 historical repealed acts require explicit historical matter dates.
4. **Corpus Leads Are Leads Only**: Open Australian Legal Corpus extracts are indexing references. Every authoritative statement in final output must be confirmed against live official primary sources.

---

## Attribution & Licences

- **Base Architecture**: Based on [Lawgent](https://github.com/WenzhuoXu/lawgent) (MIT Licence, Copyright (c) 2025 Wenzhuo Xu).
- **Queensland Legislation**: Crown in right of the State of Queensland, licensed under Creative Commons Attribution 4.0 International (CC BY 4.0).
- **Commonwealth Legislation**: Commonwealth of Australia, licensed under Creative Commons Attribution 4.0 International (CC BY 4.0).
- **Queensland Judgments**: Incorporated Council of Law Reporting for the State of Queensland (ICLRQ).
- **High Court of Australia Decisions**: High Court of Australia.
- **Open Australian Legal Corpus**: Umar Butler, licensed under the Open Australian Legal Corpus Licence. Full terms documented in `ATTRIBUTION.md`.
