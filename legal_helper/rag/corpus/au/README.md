# Australian Legal Corpus Subset

This directory contains the manifest and ingestion interface for the Queensland and Commonwealth subset of the Open Australian Legal Corpus (`umarbutler/open-australian-legal-corpus`).

## Hard Rules

1. **Leads only**: Hits from this corpus are research leads only.
2. **Mandatory live re-fetch**: Anything cited must be re-fetched and verified live via primary connectors or primary source documents.
3. **Status tag**: Any un-refetched citation from this corpus carries status `corpus only`.
4. **No bulk commits**: Corpus data files are fetched on demand via `scripts/fetch_au_corpus.py` and are git-ignored.
