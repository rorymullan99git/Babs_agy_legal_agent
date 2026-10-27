"""Tests for the Australian legal corpus streaming loader."""

from __future__ import annotations

from pathlib import Path

from scripts.fetch_au_corpus import (
    is_target_record,
    save_corpus_sample,
)


def test_is_target_record_filters_correctly() -> None:
    # 1. Queensland records must be retained
    assert is_target_record({"jurisdiction": "queensland", "title": "Criminal Code"})
    assert is_target_record({"jurisdiction": "qld", "title": "Civil Liability Act"})
    assert is_target_record({"citation": "R v Baden-Clay [2016] HCA 35"})
    assert is_target_record({"citation": "Smith v Jones [2021] QCA 120"})
    assert is_target_record({"title": "Uniform Civil Procedure Rules 1999 (Qld)"})

    # 2. Commonwealth records must be retained
    assert is_target_record({"jurisdiction": "commonwealth", "title": "Corporations Act"})
    assert is_target_record({"jurisdiction": "cth", "title": "Evidence Act"})
    assert is_target_record({"citation": "Mabo v Queensland (No 2) (1992) 175 CLR 1"})
    assert is_target_record({"title": "Competition and Consumer Act 2010 (Cth)"})

    # 3. Non-target records (other states or foreign) must be rejected
    assert not is_target_record({"jurisdiction": "victoria", "title": "Crimes Act 1958"})
    assert not is_target_record({"jurisdiction": "nsw", "title": "Civil Procedure Act 2005"})
    assert not is_target_record({"citation": "Jones v Smith [2020] NSWSC 45"})
    assert not is_target_record({"citation": "US v Nixon 418 US 683 (1974)"})


def test_corpus_leads_carry_lead_metadata_and_save(tmp_path: Path) -> None:
    records = [
        {
            "jurisdiction": "queensland",
            "title": "Criminal Code Act 1899",
            "citation": "Criminal Code Act 1899 (Qld)",
            "text": "Schedule 1 contains the Criminal Code.",
            "corpus_lead": True,
            "status": "corpus only",
        },
        {
            "jurisdiction": "commonwealth",
            "title": "Constitution of Australia",
            "citation": "Commonwealth of Australia Constitution Act (Cth)",
            "text": "Chapter I The Parliament.",
            "corpus_lead": True,
            "status": "corpus only",
        },
    ]

    saved = save_corpus_sample(records, tmp_path)
    assert len(saved) == 2
    for s in saved:
        f = tmp_path / s
        assert f.is_file()
        content = f.read_text(encoding="utf-8")
        assert "corpus only" in content
        assert "corpus_lead" in content
