# Project Status: Babs_agy_legal_agent

## DONE

- **1. Repo setup**: Cloned `https://github.com/WenzhuoXu/lawgent`, renamed remote to `upstream`, added `https://github.com/rorymullan99git/Babs_agy_legal_agent.git` as `origin`, preserved `LICENSE` and `NOTICE`, pushed unmodified upstream `main` to `origin/main` (`git push -u origin main` -> `* [new branch] main -> main`), created branch `feat/au-jurisdiction`, and added `ATTRIBUTION.md`.
- **2. AU jurisdiction**: Added `AU` (with `default_subjurisdiction: QLD`) to `config.yaml`, `legal_helper/config.py`, `legal_helper/tool_exposure.py`, and `legal_helper/server.py`. Set `default_jurisdiction: AU`, `citation_style: aglc4`, and `enable_cite_check: true`. Replaced `legal_helper/playbook/general_playbook.md` with the Australian source hierarchy (1. Constitution, 2. Commonwealth statutes, 3. Queensland statutes and subordinate legislation, 4. High Court, 5. Queensland Court of Appeal, 6. Other courts and tribunals, 7. Secondary sources), mandatory court weight labels, and point-in-time legislation rules. Proven by `.\.venv\Scripts\python.exe -m pytest -q tests/test_au_jurisdiction.py tests/test_legal_method_content.py tests/test_skills_loaded.py tests/test_answer_contract.py` (`55 passed in 4.28s`).
- **3. AGLC4 formatter**: Implemented Australian citation extraction (`legal_helper/citations/au.py`), structural validation (`validate_au`), and formatting (`legal_helper/citations/format.py`) under AGLC4 rules. Supports legislation with pinpoints (s, ss, pt, pts, div, divs, sub-div, sch, schs, cl, cls, para, paras, reg, regs, r, rr) and schedule short titles (starting test: `Criminal Code Act 1899 (Qld) sch 1 ('Criminal Code') s 23`), medium neutral case citations (`R v Baden-Clay [2016] HCA 35, [45]`), authorised and generalist law reports (`CLR`, `ALJR`, `Qd R`, etc.), uploaded-document anchors (`[Doc p. 4, cl 3.2]`), and `format_unverified` fallback flag when a form is not covered with confidence. Proven by `.\.venv\Scripts\python.exe -m pytest -q tests/test_aglc4_format.py tests/test_citations.py tests/test_au_jurisdiction.py` (`35 passed in 6.16s`).

## STUBBED

- None.

## NOT STARTED

- **4. Deterministic claim verifier**: Offline verifier for atomic claims with `claim_id`, `text`, `evidence_ids`, and optional `pinpoint`, reusing `grounding.py` and `groundedness.py` with dash/quote normalisation.
- **5. Upload parsing**: Docling (with `pdfplumber` lower-trust fallback and OCR lower-trust tagging) for PDF and DOCX preserving pages, headings, clauses, and tables.
- **6. Queensland legislation connector**: `legislation.qld.gov.au` connector with fixture tests and opt-in `live` test for Criminal Code s 23.
- **7. Analysis flow and output contract**: IRAC/FIRAC claim drafting, deterministic verifier pass, isolated LLM critic loop (max 3 rounds), and updated `answer_contract.py` / `answer_lint.py` with research-aid banner.
- **8. Corpus loader (Tier 2)**: Streaming Open Australian Legal Corpus loader for Queensland and Commonwealth subsets.
- **9. Additional AU connectors (Tier 2)**: Connectors for Queensland courts/judgments, Commonwealth legislation, and High Court judgments.
- **10. Antigravity wiring & docs (Tier 2)**: CLI and MCP exposure, rewritten `AGENTS.md`, `CLAUDE.md`, `README.md`, and `docs/adr/ADR-001-architecture.md`.

## ASSUMPTIONS

- **Git SSL backend on Windows**: Configured `git config http.sslBackend schannel` locally because OpenSSL lacked the local Windows certificate store issuer; `schannel` uses the native Windows trust store cleanly.
- **Main branch vs feature branch**: Pushed unmodified `lawgent` to `origin/main` first and committed `ATTRIBUTION.md` and `STATUS.md` onto `feat/au-jurisdiction` so `main` stays an exact unmodified mirror of upstream until merged.
- **AU sub-jurisdiction field**: Added `default_subjurisdiction: QLD` to `Settings` and `config.yaml` alongside `default_jurisdiction: AU` so Queensland is the explicit default sub-jurisdiction while preserving two-letter ISO-style top-level jurisdiction codes in `filter_for`.
- **AGLC4 schedule short titles**: Supported schedule short titles in parenthetical single quotes after the schedule number per AGLC4 Rule 3.1.7, allowing both explicit arguments and inline extraction to format `Criminal Code Act 1899 (Qld) sch 1 ('Criminal Code') s 23`.
