# Attribution and Source Licences

This file records the software, legal corpora, primary law repositories, and citation standards used or referenced by `Babs_agy_legal_agent`, together with their licences and access rules.

## 1. Base Software and Upstream Attributions

- **Lawgent (`WenzhuoXu/lawgent`)**
  - URL: https://github.com/WenzhuoXu/lawgent
  - Licence: MIT License (kept intact in `LICENSE`; upstream notice kept in `NOTICE`).
  - Upstream attributions carried forward via `NOTICE`:
    - `anthropics/claude-for-legal` (Apache-2.0): provenance-tag taxonomy, groundedness framing, verification-log format.
    - `CSlawyer1985/claude-for-legal-ZH` (Apache-2.0): structured skill framing.
    - `sboghossian/master-claude-for-legal`: citation-verifier procedure and verification-report format.
    - `anthropics/skills`: Agent Skills `SKILL.md` format.
    - `anthropics/claude-cookbooks` (MIT): prompting patterns.
    - `vercel/ai-elements` and `shadcn/ui`: web UI component layer.

## 2. Australian Primary Law Sources and Corpora

- **Queensland Legislation (`legislation.qld.gov.au`)**
  - Publisher: Office of the Queensland Parliamentary Counsel (State of Queensland).
  - URL: https://www.legislation.qld.gov.au
  - Licence: Creative Commons Attribution 4.0 International (CC BY 4.0) per the Queensland Legislation copyright notice (`© State of Queensland`).
  - Access policy: Fetched on demand with a descriptive `User-Agent` and bounded rate limits (no bulk scraping). Point-in-time (`inforce/<yyyy-mm-dd>`) and legislative history (`/lh`) URLs are queried only for specific instruments requested during a run.

- **Federal Register of Legislation (`legislation.gov.au`)**
  - Publisher: Office of Parliamentary Counsel (Commonwealth of Australia).
  - URL: https://www.legislation.gov.au
  - Licence: Creative Commons Attribution 4.0 International (CC BY 4.0) (`© Commonwealth of Australia`).
  - Access policy: Fetched on demand with a descriptive `User-Agent` and bounded request rate.

- **Open Australian Legal Corpus (`umarbutler/open-australian-legal-corpus`)**
  - Creator / Maintainer: Umar Butler (Isaacus).
  - URL: https://huggingface.co/datasets/umarbutler/open-australian-legal-corpus
  - Licence: Creative Commons Attribution 4.0 International (CC BY 4.0) for the compiled corpus (`LICENCE.md`), with underlying Commonwealth, Queensland, NSW, WA, SA, and Tasmanian legislative and judicial texts governed by CC BY 4.0 or compatible open Crown copyright terms. Creator scripts (`open-australian-legal-corpus-creator`) are MIT licensed.
  - Access policy: Streamed and filtered on demand (`streaming=True` or HTTP range/shard streaming) for Queensland and Commonwealth subsets only; never downloaded in bulk or committed as binary files to git. Corpus matches are treated strictly as research leads and must be re-fetched and verified against primary sources before citation.

- **Queensland Courts and Supreme Court Library Queensland (`queenslandjudgments.com.au` / `sclqld.org.au`)**
  - Publisher: Supreme Court Library Queensland / Queensland Courts.
  - URL: https://www.queenslandjudgments.com.au
  - Licence & Terms: Crown / Court copyright; published for public legal information, educational and non-commercial legal research use.
  - Access policy: Low-rate, single-decision retrieval with a descriptive `User-Agent`; never bulk scraped.

- **High Court of Australia (`hcourt.gov.au`)**
  - Publisher: High Court of Australia.
  - URL: https://www.hcourt.gov.au
  - Licence & Terms: Public legal information / Crown copyright (reproduction permitted for legal research and study with attribution).
  - Access policy: Low-rate, single-decision retrieval with a descriptive `User-Agent`; never bulk scraped.

## 3. Excluded Sources (Do Not Scrape)

- **BarNet Jade (`jade.io`)**: Excluded per project rules and commercial terms of service. No connector or scraper is implemented.
- **AustLII (`austlii.edu.au`)**: Excluded from automated scraping per project rules and `robots.txt` / bulk-access restrictions. No connector or scraper is implemented.

## 4. Citation Standard Reference

- **Australian Guide to Legal Citation, 4th Edition (AGLC4)**
  - Publishers: Melbourne University Law Review Association Inc and Melbourne Journal of International Law Inc (2018).
  - Usage: Bibliographic and pinpoint formatting conventions are implemented algorithmically in `legal_helper/citations/format.py`. No copyright prose from the guide is redistributed.
