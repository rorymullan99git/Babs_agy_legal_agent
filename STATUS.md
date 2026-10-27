# Project Status: Babs_agy_legal_agent

## DONE

- **1. Repo setup**: Cloned `https://github.com/WenzhuoXu/lawgent`, renamed remote to `upstream`, added `https://github.com/rorymullan99git/Babs_agy_legal_agent.git` as `origin`, preserved `LICENSE` and `NOTICE`, pushed unmodified upstream `main` to `origin/main` (`git push -u origin main` -> `* [new branch] main -> main`), created branch `feat/au-jurisdiction`, and added `ATTRIBUTION.md`.

## STUBBED

- None.

## NOT STARTED

- **2. AU jurisdiction**: Add `AU` (Queensland default) to jurisdiction filter and settings, set `default_jurisdiction: AU`, `citation_style: aglc4`, `enable_cite_check: true`, and replace PRC-default playbook with Australian source hierarchy.
- **3. AGLC4 formatter**: Implement `aglc4` in `legal_helper/citations/format.py` for legislation with pinpoints, cases, uploaded-document anchors, and `format_unverified` fallback flags.
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
