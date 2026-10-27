"""Citation subsystem.

Preserves the legacy ``audit_citations`` import surface used by
``workflow.py`` and adds:

* ``extract_citations`` / ``validate_citations`` - eyecite (US) + PRC
  regex + EU Celex/OJ/Reg/Dir regex + AU (AGLC4) with a three-valued
  ``status`` (``verified`` | ``flagged`` | ``could_not_check``).
* ``groundedness`` - Mode-2 round-trip primitives (does the source
  actually say what's claimed).
* ``claim_verifier`` - deterministic verification of atomic claims
  against retrieved and uploaded evidence.
* ``provenance`` - provenance-tag taxonomy
  (``[PKULaw]`` / ``[CourtListener]`` / ``[model knowledge - verify]`` / ...).
* ``report`` - severity-tiered ``verification-report.md`` renderer with
  coverage line + do-not-file escalation.
* ``log`` - append-only ``verification-log.md`` so repeat-verified cites
  don't get re-checked.
"""

from .audit import audit_citations
from .au import (
    AU_JURISDICTION_MAP,
    CANONICAL_AU_JURISDICTIONS,
    KNOWN_MNC_COURTS,
    KNOWN_REPORT_SERIES,
    AuCitation,
    court_weight_for,
    extract_au,
    validate_au,
)
from .claim_verifier import (
    AtomicClaim,
    ClaimVerificationResult,
    EvidenceSource,
    VerificationBatchSummary,
    verify_claim,
    verify_claims,
)
from .extract import Citation, extract_citations
from .format import (
    AGLC4FormattedStr,
    FormattedCitation,
    format_aglc4,
    format_aglc4_case_mnc,
    format_aglc4_case_reported,
    format_aglc4_doc_anchor,
    format_aglc4_legislation,
    format_citation,
)
from .groundedness import (
    Assertion,
    QuotedPhrase,
    RoundtripResult,
    extract_assertions,
    extract_quoted_phrases,
    nearest_citation_after,
    roundtrip_quote,
)
from .grounding import QuoteVerdict, ground_answer, prc_aware_fetch
from .provenance import (
    RETRIEVAL_TAGS,
    VERIFY_TAGS,
    TagInspection,
    find_untagged_citations,
    inspect_tag,
    is_provenance_tag,
)
from .report import (
    CoverageStats,
    ReportItem,
    Severity,
    TrustTag,
    Verdict,
    VerificationReport,
    annotate_sources_with_trust,
    assign_trust_tiers,
)
from .validate import Status, ValidationResult, validate_citations

__all__ = [
    "AGLC4FormattedStr",
    "AU_JURISDICTION_MAP",
    "Assertion",
    "AtomicClaim",
    "AuCitation",
    "CANONICAL_AU_JURISDICTIONS",
    "Citation",
    "ClaimVerificationResult",
    "CoverageStats",
    "EvidenceSource",
    "FormattedCitation",
    "KNOWN_MNC_COURTS",
    "KNOWN_REPORT_SERIES",
    "QuotedPhrase",
    "RETRIEVAL_TAGS",
    "ReportItem",
    "RoundtripResult",
    "QuoteVerdict",
    "Severity",
    "Status",
    "TagInspection",
    "TrustTag",
    "VERIFY_TAGS",
    "Verdict",
    "ValidationResult",
    "VerificationBatchSummary",
    "VerificationReport",
    "annotate_sources_with_trust",
    "assign_trust_tiers",
    "audit_citations",
    "court_weight_for",
    "extract_assertions",
    "extract_au",
    "extract_citations",
    "extract_quoted_phrases",
    "find_untagged_citations",
    "format_aglc4",
    "format_aglc4_case_mnc",
    "format_aglc4_case_reported",
    "format_aglc4_doc_anchor",
    "format_aglc4_legislation",
    "format_citation",
    "ground_answer",
    "inspect_tag",
    "is_provenance_tag",
    "nearest_citation_after",
    "prc_aware_fetch",
    "roundtrip_quote",
    "validate_au",
    "validate_citations",
    "verify_claim",
    "verify_claims",
]
