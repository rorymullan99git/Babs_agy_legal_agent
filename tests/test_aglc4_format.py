"""Tests for AGLC4 citation extraction, validation, and formatting."""

from __future__ import annotations

from legal_helper.citations import (
    AuCitation,
    court_weight_for,
    extract_au,
    extract_citations,
    format_aglc4,
    format_aglc4_case_mnc,
    format_aglc4_case_reported,
    format_aglc4_doc_anchor,
    format_aglc4_legislation,
    format_citation,
    validate_au,
    validate_citations,
)


def test_mandatory_starting_test_criminal_code_s23() -> None:
    # Starting test specified in brief: Criminal Code Act 1899 (Qld) sch 1 ('Criminal Code') s 23
    text = "Criminal Code Act 1899 (Qld) sch 1 ('Criminal Code') s 23"
    cites = extract_citations(text)
    assert len(cites) == 1
    c = cites[0]
    assert c.jurisdiction == "AU"
    assert c.kind == "au_legislation"

    formatted = format_citation(c, style="aglc4")
    assert formatted == "Criminal Code Act 1899 (Qld) sch 1 ('Criminal Code') s 23"
    assert hasattr(formatted, "format_unverified")
    assert not formatted.format_unverified


def test_format_aglc4_legislation_structured() -> None:
    res = format_aglc4_legislation(
        title="Criminal Code Act",
        year=1899,
        jurisdiction="Qld",
        pinpoints=[("sch", "1"), ("s", "23")],
        schedule_short_title="Criminal Code",
    )
    assert res == "Criminal Code Act 1899 (Qld) sch 1 ('Criminal Code') s 23"
    assert not res.format_unverified
    assert res.kind == "legislation"


def test_legislation_pinpoints_all_forms() -> None:
    # Test s, ss, pt, pts, div, divs, sub-div, sch, schs, cl, cls, para, paras, reg, regs, r, rr
    cases = [
        (
            format_aglc4_legislation("Civil Liability Act", 2003, "Qld", s="9"),
            "Civil Liability Act 2003 (Qld) s 9",
        ),
        (
            format_aglc4_legislation("Civil Liability Act", 2003, "Qld", s="9-11"),
            "Civil Liability Act 2003 (Qld) ss 9-11",
        ),
        (
            format_aglc4_legislation("Acts Interpretation Act", 1954, "Qld", pt="3", div="2", s="14A"),
            "Acts Interpretation Act 1954 (Qld) pt 3 div 2 s 14A",
        ),
        (
            format_aglc4_legislation("Acts Interpretation Act", 1954, "Qld", pt="3-4", div="2-3"),
            "Acts Interpretation Act 1954 (Qld) pts 3-4 divs 2-3",
        ),
        (
            format_aglc4_legislation("Corporations Act", 2001, "Cth", sub_div="2A", cl="5"),
            "Corporations Act 2001 (Cth) sub-div 2A cl 5",
        ),
        (
            format_aglc4_legislation("Competition and Consumer Act", 2010, "Cth", sch="2", cl="18"),
            "Competition and Consumer Act 2010 (Cth) sch 2 cl 18",
        ),
        (
            format_aglc4_legislation("Competition and Consumer Act", 2010, "Cth", sch="2", cl="18-20"),
            "Competition and Consumer Act 2010 (Cth) sch 2 cls 18-20",
        ),
        (
            format_aglc4_legislation("Uniform Civil Procedure Rules", 1999, "Qld", r="149"),
            "Uniform Civil Procedure Rules 1999 (Qld) r 149",
        ),
        (
            format_aglc4_legislation("Uniform Civil Procedure Rules", 1999, "Qld", r="149-152"),
            "Uniform Civil Procedure Rules 1999 (Qld) rr 149-152",
        ),
        (
            format_aglc4_legislation("Criminal Practice Rules", 1999, "Qld", para="3"),
            "Criminal Practice Rules 1999 (Qld) para 3",
        ),
        (
            format_aglc4_legislation("Criminal Practice Rules", 1999, "Qld", para="3-5"),
            "Criminal Practice Rules 1999 (Qld) paras 3-5",
        ),
        (
            format_aglc4_legislation("Migration Regulations", 1994, "Cth", reg="1.03"),
            "Migration Regulations 1994 (Cth) reg 1.03",
        ),
        (
            format_aglc4_legislation("Migration Regulations", 1994, "Cth", reg="1.03-1.05"),
            "Migration Regulations 1994 (Cth) regs 1.03-1.05",
        ),
    ]
    for formatted, expected in cases:
        assert formatted == expected
        assert not formatted.format_unverified


def test_medium_neutral_citation_formatting() -> None:
    res = format_aglc4_case_mnc(
        party_names="R v Baden-Clay",
        year=2016,
        court="HCA",
        judgment_number=35,
        pinpoint_paragraph=45,
    )
    assert res == "R v Baden-Clay [2016] HCA 35, [45]"
    assert not res.format_unverified
    assert res.kind == "case_mnc"


def test_reported_case_citations_round_and_square() -> None:
    # 1. Round brackets series (e.g. CLR, FCR, ALR)
    mabo = format_aglc4_case_reported(
        party_names="Mabo v Queensland (No 2)",
        year=1992,
        series="CLR",
        starting_page=1,
        volume=175,
        pinpoint=15,
    )
    assert mabo == "Mabo v Queensland (No 2) (1992) 175 CLR 1, 15"
    assert not mabo.format_unverified

    # 2. Combined page and paragraph pinpoint (e.g. 151 [134])
    farah = format_aglc4_case_reported(
        party_names="Farah Constructions Pty Ltd v Say-Dee Pty Ltd",
        year=2007,
        series="CLR",
        starting_page=89,
        volume=230,
        pinpoint="151 [134]",
    )
    assert farah == "Farah Constructions Pty Ltd v Say-Dee Pty Ltd (2007) 230 CLR 89, 151 [134]"
    assert not farah.format_unverified

    # 3. Square brackets series (e.g. Qd R, AC)
    qdr = format_aglc4_case_reported(
        party_names="R v Smith",
        year=1999,
        series="Qd R",
        starting_page=100,
        volume=1,
        pinpoint=105,
    )
    assert qdr == "R v Smith [1999] 1 Qd R 100, 105"
    assert not qdr.format_unverified


def test_doc_anchor_formatting() -> None:
    a1 = format_aglc4_doc_anchor(page=4, clause="3.2")
    assert a1 == "[Doc p. 4, cl 3.2]"
    assert not a1.format_unverified

    a2 = format_aglc4_doc_anchor(page="4-5", clause="3.2(a)")
    assert a2 == "[Doc pp. 4-5, cl 3.2(a)]"
    assert not a2.format_unverified

    a3 = format_aglc4_doc_anchor(raw_anchor="[Doc p. 4, cl 3.2]")
    assert a3 == "[Doc p. 4, cl 3.2]"
    assert not a3.format_unverified


def test_format_unverified_flag_on_uncertain_forms() -> None:
    # 1. Unknown court
    bad_court = format_aglc4_case_mnc(
        party_names="Doe v Roe",
        year=2021,
        court="FAKECT",
        judgment_number=10,
    )
    assert bad_court.format_unverified
    assert " [format_unverified]" in str(bad_court)

    # 2. Unknown report series
    bad_series = format_aglc4_case_reported(
        party_names="Doe v Roe",
        year=2020,
        series="XYZREP",
        starting_page=12,
    )
    assert bad_series.format_unverified
    assert " [format_unverified]" in str(bad_series)

    # 3. Unknown jurisdiction
    bad_juris = format_aglc4_legislation(
        title="Unknown Act",
        year=2020,
        jurisdiction="Mars",
    )
    assert bad_juris.format_unverified
    assert " [format_unverified]" in str(bad_juris)

    # 4. Doc anchor lacking page or clause
    bad_doc = format_aglc4_doc_anchor(raw_anchor="[Doc some arbitrary note]")
    assert bad_doc.format_unverified
    assert " [format_unverified]" in str(bad_doc)


def test_court_weights_for_australian_hierarchy() -> None:
    # High Court is binding
    assert court_weight_for("HCA") == "binding"
    assert court_weight_for("CLR") == "binding"

    # Queensland Court of Appeal is binding
    assert court_weight_for("QCA") == "binding"

    # Intermediate appellate comity
    assert court_weight_for("NSWCA") == "comity_appellate"
    assert court_weight_for("FCAFC") == "comity_appellate"

    # Single judge persuasive
    assert court_weight_for("QSC") == "persuasive"
    assert court_weight_for("FCA") == "persuasive"

    # Lower courts & tribunals
    assert court_weight_for("QDC") == "lower_court_or_tribunal"
    assert court_weight_for("QCAT") == "lower_court_or_tribunal"

    # Comparative persuasive (UK / NZ)
    assert court_weight_for("UKSC") == "comparative_persuasive"
    assert court_weight_for("AC") == "comparative_persuasive"


def test_acceptance_fabricated_case_never_verified_offline() -> None:
    # Acceptance Test: A fabricated case name and citation is flagged, never shown as verified.
    text = "See Fake v Phony [2022] FAKECT 999 and Ghost v Shadow [2021] HCA 9999."
    cites = extract_citations(text)
    results = validate_citations(cites)
    assert len(results) >= 1

    # Fake court must be flagged
    fake_results = [r for r in results if "FAKECT" in r.citation.text]
    assert len(fake_results) == 1
    assert fake_results[0].status == "flagged"
    assert not fake_results[0].ok

    # Even a citation with a real court identifier (HCA) cannot be verified offline
    # without source text retrieval (Hard Rule 2).
    hca_results = [r for r in results if "HCA" in r.citation.text]
    assert len(hca_results) == 1
    assert hca_results[0].status == "could_not_check"
    assert not hca_results[0].ok
