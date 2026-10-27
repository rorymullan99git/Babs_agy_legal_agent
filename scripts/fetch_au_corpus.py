"""Stream and filter the Open Australian Legal Corpus (Queensland and Commonwealth subset).

Rules:
- Never download the whole 1.2B token dataset; stream and filter.
- Retain only Queensland and Commonwealth primary law.
- Corpus hits are leads only; anything cited must be re-fetched and verified live.
- Tag every hit with corpus_lead=True and status='corpus only'.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any, Generator, Iterable, Optional

# Canonical target jurisdictions
TARGET_JURISDICTIONS = frozenset({"queensland", "qld", "commonwealth", "cth"})
TARGET_CIT_PATTERNS = re.compile(
    r"(?:\((?:Qld|Cth)\)|\b(?:HCA|QCA|QSC|QDC|QCAT|FCAFC|FCA|CLR|Qd\s*R)\b)",
    re.IGNORECASE,
)


def is_target_record(record: dict[str, Any]) -> bool:
    """Determine whether a corpus record belongs to Queensland or Commonwealth law."""
    jurisdiction = str(record.get("jurisdiction", "")).strip().lower()
    if jurisdiction in TARGET_JURISDICTIONS:
        return True

    citation = str(record.get("citation", ""))
    title = str(record.get("title", ""))
    text = str(record.get("text", "")[:300])

    if TARGET_CIT_PATTERNS.search(citation):
        return True
    if TARGET_CIT_PATTERNS.search(title):
        return True
    if TARGET_CIT_PATTERNS.search(text):
        return True

    return False


def stream_au_corpus(
    dataset_name: str = "umarbutler/open-australian-legal-corpus",
    split: str = "train",
    limit: Optional[int] = None,
) -> Generator[dict[str, Any], None, None]:
    """Stream records from Hugging Face dataset without downloading the whole corpus."""
    try:
        from datasets import load_dataset

        ds = load_dataset(dataset_name, split=split, streaming=True)
    except Exception as exc:
        raise RuntimeError(f"Failed to connect to Hugging Face dataset {dataset_name}: {exc}") from exc

    count = 0
    for record in ds:
        if is_target_record(record):
            # Enforce lead metadata
            item = dict(record)
            item["corpus_lead"] = True
            item["status"] = "corpus only"
            item["verification_required"] = "Must be re-fetched and verified live before citation"
            yield item
            count += 1
            if limit is not None and count >= limit:
                break


def save_corpus_sample(
    records: Iterable[dict[str, Any]],
    output_dir: Path,
    manifest_path: Optional[Path] = None,
) -> list[str]:
    """Save streamed sample records and update manifest."""
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_files: list[str] = []

    for idx, rec in enumerate(records, start=1):
        slug = re.sub(r"[^\w\-]", "_", str(rec.get("citation") or rec.get("title") or f"doc_{idx}"))[:60].strip("_")
        fname = f"{slug}.json"
        target_path = output_dir / fname
        target_path.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
        saved_files.append(fname)

    return saved_files


def main() -> None:
    parser = argparse.ArgumentParser(description="Stream and filter Open Australian Legal Corpus")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of records to stream")
    parser.add_argument("--output-dir", type=str, default="legal_helper/rag/corpus/au/data", help="Output directory")
    parser.add_argument("--dry-run", action="store_true", help="Filter and count without saving files")
    args = parser.parse_args()

    out_p = Path(args.output_dir)
    print(f"Streaming up to {args.limit} Queensland/Commonwealth records...")
    stream = stream_au_corpus(limit=args.limit)

    if args.dry_run:
        matched = sum(1 for _ in stream)
        print(f"Dry run matched {matched} target records.")
    else:
        saved = save_corpus_sample(stream, out_p)
        print(f"Saved {len(saved)} records to {out_p}")


if __name__ == "__main__":
    main()
