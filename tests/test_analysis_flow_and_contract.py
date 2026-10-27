"""Tests for the Australian analysis flow, critic loop, and output contract."""

from __future__ import annotations

import pytest

from legal_helper.answer_contract import (
    RESEARCH_AID_BANNER,
    validate_grounded_output,
)
from legal_helper.answer_lint import AnswerLinter, lint_answer
from legal_helper.au_analysis import (
    GroundedSourceItem,
    StructuredClaim,
    render_grounded_answer,
    run_critic_loop,
    run_critic_round,
)
from legal_helper.citations.claim_verifier import EvidenceSource


def test_validate_grounded_output_passes_on_conforming_answer() -> None:
    answer = f"""{RESEARCH_AID_BANNER}

## Issue
Whether the defendant is criminally responsible under Queensland law [1].

## Rule
Section 23 provides that a person is not criminally responsible for an act occurring independently of the will [1].

## Application
The client suffered an involuntary muscle spasm causing the fall [Doc p. 4, cl 3.2].

## Conclusion
The defence of unwilled act is available [1].

## Sources
1. Criminal Code Act 1899 (Qld) sch 1 ('Criminal Code') s 23 - verified online
2. [Doc p. 4, cl 3.2] - verified in uploaded document

## What I could not verify
All statements and cited authorities were successfully verified against primary source evidence.
"""
    ok, errors = validate_grounded_output(answer)
    assert ok, f"Expected conforming output to pass, got: {errors}"
    assert len(errors) == 0


def test_validate_grounded_output_fails_on_missing_banner() -> None:
    bad_answer = """## Issue
Whether the defendant is liable [1].

## Sources
1. Civil Liability Act 2003 (Qld) s 9 - verified online

## What I could not verify
None.
"""
    ok, errors = validate_grounded_output(bad_answer)
    assert not ok
    assert any("research aid, not legal advice" in e for e in errors)


def test_validate_grounded_output_fails_on_missing_sources_or_unverified_section() -> None:
    missing_sources = f"""{RESEARCH_AID_BANNER}

## Issue
Whether the contract is valid [1].
"""
    ok, errors = validate_grounded_output(missing_sources)
    assert not ok
    assert any("Sources" in e for e in errors)
    assert any("What I could not verify" in e for e in errors)


def test_validate_grounded_output_fails_on_unmarked_body_sentences() -> None:
    unmarked_body = f"""{RESEARCH_AID_BANNER}

## Issue
This sentence has no reference marker at all.

## Sources
1. Some Act 2020 (Qld) s 5 - verified online

## What I could not verify
None.
"""
    ok, errors = validate_grounded_output(unmarked_body)
    assert not ok
    assert any("reference marker" in e for e in errors)


def test_critic_loop_flags_unsupported_and_overstated_claims() -> None:
    evidence = {
        "ev1": EvidenceSource(
            id="ev1",
            text="Subject to the express provisions of this Code, a person is not criminally responsible for an unwilled act.",
            citation="Criminal Code 1899 (Qld) s 23",
            source_type="legislation",
            status="in_force",
            sections=["23"],
        )
    }

    claims = [
        StructuredClaim(
            claim_id="c1",
            section="rule",
            text="Section 23 of the Criminal Code provides an absolute defence for unwilled acts.",
            evidence_ids=["ev1"],
            pinpoint="s 23",
        ),
        StructuredClaim(
            claim_id="c2",
            section="application",
            text="The defendant is strictly liable regardless of fault.",
            evidence_ids=["ev1"],
        ),
        StructuredClaim(
            claim_id="c3",
            section="conclusion",
            text="Unsupported assertion with zero evidence.",
            evidence_ids=[],
        ),
    ]

    final_claims, rounds_log = run_critic_loop(claims, evidence, max_rounds=3)
    assert len(rounds_log) >= 1

    # c1 had 'absolute' when evidence said 'Subject to express provisions' -> flagged
    # c2 had 'strictly liable' -> flagged
    # c3 had no evidence -> flagged
    assert any(c.status == "UNVERIFIED" for c in final_claims)
    assert final_claims[2].status == "UNVERIFIED"
    assert final_claims[2].reference_marker == "[UNVERIFIED]"


def test_render_grounded_answer_firac_and_irac() -> None:
    evidence = {
        "ev1": EvidenceSource(
            id="ev1",
            text="A person is not criminally responsible for an act occurring independently of the will.",
            citation="Criminal Code 1899 (Qld) s 23(1)(a)",
            source_type="legislation",
            status="in_force",
            sections=["23"],
        )
    }

    claims = [
        StructuredClaim(
            claim_id="f1",
            section="facts",
            text="The client was involved in a collision while experiencing a medical seizure",
            evidence_ids=["ev1"],
            reference_marker="[Doc p. 2]",
            status="VERIFIED",
        ),
        StructuredClaim(
            claim_id="r1",
            section="rule",
            text="Section 23 excuses an act that occurs independently of will",
            evidence_ids=["ev1"],
            pinpoint="s 23",
            reference_marker="[1]",
            status="VERIFIED",
        ),
        StructuredClaim(
            claim_id="c1",
            section="conclusion",
            text="Criminal responsibility is excluded by the unwilled act defence",
            evidence_ids=["ev1"],
            reference_marker="[1]",
            status="VERIFIED",
        ),
    ]

    sources = [
        GroundedSourceItem(
            index=1,
            citation_text="Criminal Code Act 1899 (Qld) sch 1 ('Criminal Code') s 23",
            status="verified online",
        ),
        GroundedSourceItem(
            index=2,
            citation_text="[Doc p. 2]",
            status="verified in uploaded document",
        ),
    ]

    # FIRAC for fact-heavy matter
    rendered_firac = render_grounded_answer("fact_heavy", claims, sources)
    assert "## Facts" in rendered_firac
    assert "## Rule" in rendered_firac
    assert "## Conclusion" in rendered_firac
    assert "## Sources" in rendered_firac
    assert "## What I could not verify" in rendered_firac
    assert RESEARCH_AID_BANNER in rendered_firac

    # Lint check passes
    ok, errors = validate_grounded_output(rendered_firac)
    assert ok, f"Rendered FIRAC failed lint: {errors}"
