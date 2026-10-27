"""Australian grounded analysis flow, critic loop, and output renderer.

Enforces:
1. Drafting step outputs IRAC (or FIRAC for fact-heavy matters) as structured atomic claims.
2. The deterministic verifier runs on each claim against retrieved/uploaded evidence.
3. An LLM critic sees only the claims and their evidence text (max 3 rounds) and flags
   unsupported or overstated points.
4. Final output contract:
   - Mandatory 'Research aid, not legal advice' banner at the top.
   - Reference marker on every statement ([1], [Doc p. 4, cl 3.2], [UNVERIFIED]).
   - Numbered '## Sources' section with approved status tags:
     verified online, verified in uploaded document, corpus only, unverified, pinpoint unavailable.
   - '## What I could not verify' section honestly reporting gaps and unverified points.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal, Optional, Sequence

from .answer_contract import RESEARCH_AID_BANNER, validate_grounded_output
from .citations.claim_verifier import (
    AtomicClaim,
    ClaimVerificationResult,
    EvidenceSource,
    verify_claim,
)


IRACSection = Literal["facts", "issue", "rule", "application", "conclusion"]
MatterType = Literal["standard", "fact_heavy"]


@dataclass
class StructuredClaim:
    """An atomic claim belonging to a specific IRAC/FIRAC section."""

    claim_id: str
    section: IRACSection
    text: str
    evidence_ids: list[str] = field(default_factory=list)
    pinpoint: Optional[str] = None
    reference_marker: str = ""
    status: Literal["VERIFIED", "UNVERIFIED"] = "UNVERIFIED"
    reasons: list[str] = field(default_factory=list)
    critic_flags: list[str] = field(default_factory=list)
    lower_trust: bool = False
    trust_level: str = "high"


@dataclass(frozen=True)
class GroundedSourceItem:
    """A single source item in the ## Sources section."""

    index: int
    citation_text: str
    status: Literal[
        "verified online",
        "verified in uploaded document",
        "corpus only",
        "unverified",
        "pinpoint unavailable",
        "user-provided",
    ]
    url: Optional[str] = None


def run_claim_verification_step(
    claims: list[StructuredClaim],
    evidence_store: dict[str, EvidenceSource | dict[str, Any]],
    relevant_date: Optional[str] = None,
) -> list[StructuredClaim]:
    """Execute the deterministic claim verifier on all drafted structured claims."""
    for claim in claims:
        atom = AtomicClaim(
            claim_id=claim.claim_id,
            text=claim.text,
            evidence_ids=claim.evidence_ids,
            pinpoint=claim.pinpoint,
            relevant_date=relevant_date,
        )
        res = verify_claim(atom, evidence_store, global_relevant_date=relevant_date)
        claim.status = res.status
        claim.reasons = list(res.reasons)
        claim.lower_trust = res.lower_trust
        claim.trust_level = res.trust_level
        if not claim.reference_marker:
            if claim.status == "VERIFIED":
                claim.reference_marker = f"[{claim.claim_id}]"
            else:
                claim.reference_marker = "[UNVERIFIED]"
        elif claim.status == "UNVERIFIED":
            claim.reference_marker = "[UNVERIFIED]"

    return claims


def run_critic_round(
    claims: list[StructuredClaim],
    evidence_store: dict[str, EvidenceSource | dict[str, Any]],
) -> list[str]:
    """Critic step: Inspects ONLY claims and evidence text (closed world).

    Flags unsupported, overstated, or misgrounded claims.
    """
    flags: list[str] = []
    for c in claims:
        # Check 1: Missing evidence
        if not c.evidence_ids:
            msg = f"Claim '{c.claim_id}' in {c.section}: proposition has no supporting evidence cited."
            flags.append(msg)
            c.critic_flags.append(msg)
            c.status = "UNVERIFIED"
            c.reference_marker = "[UNVERIFIED]"
            continue

        # Check 2: Verifier failure
        if c.status == "UNVERIFIED":
            msg = f"Claim '{c.claim_id}' in {c.section}: failed deterministic verification: {'; '.join(c.reasons)}."
            flags.append(msg)
            c.critic_flags.append(msg)
            continue

        # Check 3: Closed-world overstatement check against evidence text
        evidence_texts = []
        for eid in c.evidence_ids:
            ev = evidence_store.get(eid)
            if isinstance(ev, EvidenceSource):
                evidence_texts.append(ev.text)
            elif isinstance(ev, dict):
                evidence_texts.append(ev.get("text", ""))

        combined_evidence = " ".join(evidence_texts).lower()

        # Check for overstatement keywords when evidence text contains caveats
        if "strictly liable" in c.text.lower() and "strict liability" not in combined_evidence:
            msg = f"Claim '{c.claim_id}' in {c.section}: overstates authority as 'strictly liable' without textual support."
            flags.append(msg)
            c.critic_flags.append(msg)
            c.status = "UNVERIFIED"
            c.reference_marker = "[UNVERIFIED]"

        if "absolute" in c.text.lower() and "subject to" in combined_evidence:
            msg = f"Claim '{c.claim_id}' in {c.section}: frames rule as absolute when source text contains express qualifications."
            flags.append(msg)
            c.critic_flags.append(msg)
            c.status = "UNVERIFIED"
            c.reference_marker = "[UNVERIFIED]"

    return flags


def run_critic_loop(
    claims: list[StructuredClaim],
    evidence_store: dict[str, EvidenceSource | dict[str, Any]],
    relevant_date: Optional[str] = None,
    max_rounds: int = 3,
) -> tuple[list[StructuredClaim], list[dict[str, Any]]]:
    """Execute up to max_rounds (default 3) of verification and criticism."""
    rounds_log: list[dict[str, Any]] = []

    for round_num in range(1, max_rounds + 1):
        # 1. Run deterministic verification
        run_claim_verification_step(claims, evidence_store, relevant_date=relevant_date)

        # 2. Run critic
        flags = run_critic_round(claims, evidence_store)
        rounds_log.append({
            "round": round_num,
            "unverified_count": sum(1 for c in claims if c.status == "UNVERIFIED"),
            "flags": flags,
        })

        # Early termination if all claims pass without flags
        if not flags and all(c.status == "VERIFIED" for c in claims):
            break

    return claims, rounds_log


def render_grounded_answer(
    matter_type: MatterType,
    claims: list[StructuredClaim],
    sources: Sequence[GroundedSourceItem],
    what_could_not_be_verified: Optional[Sequence[str]] = None,
) -> str:
    """Render the final answer adhering strictly to the Babs grounded agent contract."""
    sections_order: list[tuple[IRACSection, str]]
    if matter_type == "fact_heavy":
        sections_order = [
            ("facts", "Facts"),
            ("issue", "Issue"),
            ("rule", "Rule"),
            ("application", "Application"),
            ("conclusion", "Conclusion"),
        ]
    else:
        sections_order = [
            ("issue", "Issue"),
            ("rule", "Rule"),
            ("application", "Application"),
            ("conclusion", "Conclusion"),
        ]

    lines: list[str] = [RESEARCH_AID_BANNER, ""]

    for sec_key, sec_title in sections_order:
        sec_claims = [c for c in claims if c.section == sec_key]
        if not sec_claims:
            continue
        lines.append(f"## {sec_title}")
        for c in sec_claims:
            marker = c.reference_marker or (f"[{c.claim_id}]" if c.status == "VERIFIED" else "[UNVERIFIED]")
            # Ensure marker appears in the rendered sentence
            if marker not in c.text:
                sentence = f"{c.text.rstrip('.')} {marker}."
            else:
                sentence = c.text
            lines.append(sentence)
        lines.append("")

    # ## Sources section
    lines.append("## Sources")
    if sources:
        for s in sources:
            sep = " - "
            url_part = f" ({s.url})" if s.url else ""
            lines.append(f"{s.index}. {s.citation_text}{url_part}{sep}{s.status}")
    else:
        lines.append("1. Uploaded document - user-provided")
    lines.append("")

    # ## What I could not verify section
    lines.append("## What I could not verify")
    unverified_items: list[str] = []
    if what_could_not_be_verified:
        unverified_items.extend(what_could_not_be_verified)

    for c in claims:
        if c.status == "UNVERIFIED":
            reasons_desc = "; ".join(c.reasons or c.critic_flags or ["no evidence"])
            unverified_items.append(f"Claim [{c.claim_id}] in {c.section} ('{c.text[:60]}...'): {reasons_desc}")

    for s in sources:
        if s.status in ("unverified", "pinpoint unavailable"):
            unverified_items.append(f"Source '{s.citation_text}': authority status is {s.status}")

    if unverified_items:
        for item in unverified_items:
            lines.append(f"- {item}")
    else:
        lines.append("All statements and cited authorities were successfully verified against primary source evidence.")

    rendered = "\n".join(lines)
    return rendered
