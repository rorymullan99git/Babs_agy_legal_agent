"""Per-style citation formatting (gb_t_7714 | bluebook | oscola | aglc4)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal, Optional, Sequence

from .au import (
    AU_JURISDICTION_MAP,
    KNOWN_MNC_COURTS,
    KNOWN_REPORT_SERIES,
    AuCitation,
    extract_au,
)
from .extract import Citation


Style = Literal["gb_t_7714", "bluebook", "oscola", "aglc4"]


class AGLC4FormattedStr(str):
    """String subclass representing an AGLC4 formatted citation.

    Provides metadata attributes:
    - format_unverified (bool): True if the citation could not be formatted with confidence.
    - kind (str): Citation kind (legislation, case_mnc, case_reported, doc_anchor, or unverified).
    - reason (Optional[str]): Explanation when format_unverified is True.
    - raw_text (str): Input text before formatting.
    - citation_text (str): Clean formatted citation text without any trailing tag.
    """

    format_unverified: bool
    kind: str
    reason: Optional[str]
    raw_text: str
    citation_text: str

    def __new__(
        cls,
        rendered_text: str,
        *,
        format_unverified: bool = False,
        kind: str = "unverified",
        reason: Optional[str] = None,
        raw_text: str = "",
        citation_text: str = "",
    ) -> AGLC4FormattedStr:
        obj = super().__new__(cls, rendered_text)
        obj.format_unverified = format_unverified
        obj.kind = kind
        obj.reason = reason
        obj.raw_text = raw_text or rendered_text
        obj.citation_text = citation_text or rendered_text
        return obj

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": str(self),
            "citation_text": self.citation_text,
            "format_unverified": self.format_unverified,
            "kind": self.kind,
            "reason": self.reason,
            "raw_text": self.raw_text,
        }


@dataclass(frozen=True)
class FormattedCitation:
    text: str
    citation_text: str
    format_unverified: bool
    kind: str
    reason: Optional[str] = None
    raw_text: str = ""

    def to_formatted_str(self) -> AGLC4FormattedStr:
        return AGLC4FormattedStr(
            self.text,
            format_unverified=self.format_unverified,
            kind=self.kind,
            reason=self.reason,
            raw_text=self.raw_text,
            citation_text=self.citation_text,
        )


_PINPOINT_NORMALISATIONS: dict[str, tuple[str, str]] = {
    "s": ("s", "ss"),
    "ss": ("s", "ss"),
    "sec": ("s", "ss"),
    "section": ("s", "ss"),
    "sections": ("s", "ss"),
    "sub-s": ("sub-s", "sub-ss"),
    "sub-ss": ("sub-s", "sub-ss"),
    "subs": ("sub-s", "sub-ss"),
    "sub_s": ("sub-s", "sub-ss"),
    "pt": ("pt", "pts"),
    "pts": ("pt", "pts"),
    "part": ("pt", "pts"),
    "parts": ("pt", "pts"),
    "div": ("div", "divs"),
    "divs": ("div", "divs"),
    "division": ("div", "divs"),
    "divisions": ("div", "divs"),
    "sub-div": ("sub-div", "sub-divs"),
    "sub-divs": ("sub-div", "sub-divs"),
    "sub_div": ("sub-div", "sub-divs"),
    "subdivision": ("sub-div", "sub-divs"),
    "subdivisions": ("sub-div", "sub-divs"),
    "sch": ("sch", "schs"),
    "schs": ("sch", "schs"),
    "schedule": ("sch", "schs"),
    "schedules": ("sch", "schs"),
    "cl": ("cl", "cls"),
    "cls": ("cl", "cls"),
    "clause": ("cl", "cls"),
    "clauses": ("cl", "cls"),
    "sub-cl": ("sub-cl", "sub-cls"),
    "sub-cls": ("sub-cl", "sub-cls"),
    "sub_cl": ("sub-cl", "sub-cls"),
    "subclause": ("sub-cl", "sub-cls"),
    "subclauses": ("sub-cl", "sub-cls"),
    "para": ("para", "paras"),
    "paras": ("para", "paras"),
    "paragraph": ("para", "paras"),
    "paragraphs": ("para", "paras"),
    "sub-para": ("sub-para", "sub-paras"),
    "sub-paras": ("sub-para", "sub-paras"),
    "sub_para": ("sub-para", "sub-paras"),
    "subparagraph": ("sub-para", "sub-paras"),
    "subparagraphs": ("sub-para", "sub-paras"),
    "reg": ("reg", "regs"),
    "regs": ("reg", "regs"),
    "regulation": ("reg", "regs"),
    "regulations": ("reg", "regs"),
    "r": ("r", "rr"),
    "rr": ("r", "rr"),
    "rule": ("r", "rr"),
    "rules": ("r", "rr"),
    "art": ("art", "arts"),
    "arts": ("art", "arts"),
    "article": ("art", "arts"),
    "articles": ("art", "arts"),
}


def _is_range_or_multiple(val: str) -> bool:
    clean = val.strip()
    return any(sep in clean for sep in ("-", "–", "\u2014", ",", " to ", " and ", "&"))


def format_aglc4_legislation(
    title: str,
    year: int | str,
    jurisdiction: str,
    pinpoints: Sequence[tuple[str, str]] | str | None = None,
    schedule_short_title: Optional[str] = None,
    **kwargs: Any,
) -> AGLC4FormattedStr:
    """Format an Australian statute or subordinate instrument under AGLC4 Rule 3.

    Example:
        format_aglc4_legislation(
            "Criminal Code Act", 1899, "Qld",
            pinpoints=[("sch", "1"), ("s", "23")],
            schedule_short_title="Criminal Code"
        )
        -> "Criminal Code Act 1899 (Qld) sch 1 ('Criminal Code') s 23"
    """
    raw_repr = f"{title} {year} ({jurisdiction})"
    unverified_reasons: list[str] = []

    clean_title = " ".join(str(title or "").strip().split())
    clean_title = re.sub(r",?\s*(?:1[789]\d{2}|20\d{2})\b.*$", "", clean_title).strip()
    if not clean_title:
        unverified_reasons.append("missing legislation title")

    try:
        clean_year = int(str(year).strip())
        if not (1788 <= clean_year <= 2030):
            unverified_reasons.append(f"implausible year {clean_year}")
    except Exception:
        clean_year = 0
        unverified_reasons.append(f"invalid year {year!r}")

    norm_juris = AU_JURISDICTION_MAP.get(str(jurisdiction or "").strip().lower())
    if not norm_juris:
        norm_juris = str(jurisdiction or "").strip()
        unverified_reasons.append(f"unrecognised jurisdiction {jurisdiction!r}")

    pin_tokens: list[str] = []

    # Process kwargs such as sch="1", s="23", pt="2", div="1", cl="4", r="12"
    pin_items: list[tuple[str, str]] = []
    if isinstance(pinpoints, str) and pinpoints.strip():
        raw_pin = pinpoints.strip()
        if schedule_short_title and not re.search(r"\(['\"][^'\"]+['\"]\)", raw_pin):
            raw_pin = re.sub(
                r"\b(schs?|schedules?)\s+(\d+)\b",
                rf"\1 \2 ('{schedule_short_title.strip()}')",
                raw_pin,
                flags=re.IGNORECASE,
            )
        pin_items.append(("raw", raw_pin))
    elif isinstance(pinpoints, (list, tuple)):
        for item in pinpoints:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                pin_items.append((str(item[0]), str(item[1])))
            elif isinstance(item, str):
                pin_items.append(("raw", item))

    # Also check kwargs for standard designators
    kwarg_order = [
        "pt", "part", "div", "division", "sub_div", "subdivision",
        "sch", "schedule", "cl", "clause", "sub_cl", "subclause",
        "s", "sec", "section", "sub_s", "subsection",
        "para", "paragraph", "reg", "regulation", "r", "rule", "art", "article",
    ]
    for k in kwarg_order:
        if k in kwargs and kwargs[k] is not None:
            pin_items.append((k, str(kwargs[k])))

    for k, v in pin_items:
        v_str = str(v).strip()
        if not v_str:
            continue
        if k == "raw":
            pin_tokens.append(v_str)
            continue
        key_norm = k.lower().replace("_", "-")
        pair = _PINPOINT_NORMALISATIONS.get(key_norm)
        if not pair:
            unverified_reasons.append(f"unrecognised pinpoint designator {k!r}")
            pin_tokens.append(f"{k} {v_str}")
            continue
        sg, pl = pair
        designator = pl if _is_range_or_multiple(v_str) else sg
        pin_token = f"{designator} {v_str}"
        if sg == "sch" and schedule_short_title:
            pin_token = f"{pin_token} ('{schedule_short_title.strip()}')"
        pin_tokens.append(pin_token)

    pinpoint_str = (" " + " ".join(pin_tokens)) if pin_tokens else ""
    formatted = f"{clean_title} {clean_year} ({norm_juris}){pinpoint_str}"

    if unverified_reasons:
        reason_msg = "; ".join(unverified_reasons)
        return AGLC4FormattedStr(
            f"{formatted} [format_unverified]",
            format_unverified=True,
            kind="legislation",
            reason=reason_msg,
            raw_text=raw_repr,
            citation_text=formatted,
        )

    return AGLC4FormattedStr(
        formatted,
        format_unverified=False,
        kind="legislation",
        reason=None,
        raw_text=raw_repr,
        citation_text=formatted,
    )


def format_aglc4_case_mnc(
    party_names: str,
    year: int | str,
    court: str,
    judgment_number: int | str,
    pinpoint_paragraph: Optional[str | int] = None,
) -> AGLC4FormattedStr:
    """Format an Australian medium neutral case citation under AGLC4 Rule 2.3.1.

    Example:
        format_aglc4_case_mnc("R v Baden-Clay", 2016, "HCA", 35, 45)
        -> "R v Baden-Clay [2016] HCA 35, [45]"
    """
    raw_repr = f"{party_names} [{year}] {court} {judgment_number}"
    unverified_reasons: list[str] = []

    clean_parties = " ".join(str(party_names or "").strip().split())
    # Normalise party vs separator: replace " v. " with " v "
    clean_parties = re.sub(r"\s+v\.\s+", " v ", clean_parties)
    if not clean_parties:
        unverified_reasons.append("missing party names")

    try:
        clean_year = int(str(year).strip())
        if not (1990 <= clean_year <= 2030):
            unverified_reasons.append(f"implausible medium neutral year {clean_year}")
    except Exception:
        clean_year = 0
        unverified_reasons.append(f"invalid year {year!r}")

    clean_court = str(court or "").strip().upper()
    if clean_court not in KNOWN_MNC_COURTS:
        unverified_reasons.append(f"unknown or unverified court {court!r}")

    clean_num = str(judgment_number or "").strip()
    if not clean_num.isdigit() or int(clean_num) <= 0:
        unverified_reasons.append(f"invalid judgment number {judgment_number!r}")

    pin_part = ""
    if pinpoint_paragraph is not None:
        p_str = str(pinpoint_paragraph).strip()
        if p_str:
            if not p_str.startswith("["):
                p_str = f"[{p_str}]"
            pin_part = f", {p_str}"

    formatted = f"{clean_parties} [{clean_year}] {clean_court} {clean_num}{pin_part}"

    if unverified_reasons:
        return AGLC4FormattedStr(
            f"{formatted} [format_unverified]",
            format_unverified=True,
            kind="case_mnc",
            reason="; ".join(unverified_reasons),
            raw_text=raw_repr,
            citation_text=formatted,
        )

    return AGLC4FormattedStr(
        formatted,
        format_unverified=False,
        kind="case_mnc",
        reason=None,
        raw_text=raw_repr,
        citation_text=formatted,
    )


def format_aglc4_case_reported(
    party_names: str,
    year: int | str,
    series: str,
    starting_page: int | str,
    volume: Optional[int | str] = None,
    pinpoint: Optional[str | int] = None,
) -> AGLC4FormattedStr:
    """Format an Australian authorised or generalist law report citation under AGLC4 Rule 2.2.

    Example:
        format_aglc4_case_reported(
            "Farah Constructions Pty Ltd v Say-Dee Pty Ltd", 2007,
            "CLR", 89, volume=230, pinpoint="151 [134]"
        )
        -> "Farah Constructions Pty Ltd v Say-Dee Pty Ltd (2007) 230 CLR 89, 151 [134]"
    """
    raw_repr = f"{party_names} ({year}) {series} {starting_page}"
    unverified_reasons: list[str] = []

    clean_parties = " ".join(str(party_names or "").strip().split())
    clean_parties = re.sub(r"\s+v\.\s+", " v ", clean_parties)
    if not clean_parties:
        unverified_reasons.append("missing party names")

    try:
        clean_year = int(str(year).strip())
        if not (1788 <= clean_year <= 2030):
            unverified_reasons.append(f"implausible year {clean_year}")
    except Exception:
        clean_year = 0
        unverified_reasons.append(f"invalid year {year!r}")

    clean_series = str(series or "").strip()
    rule_info = KNOWN_REPORT_SERIES.get(clean_series)
    if not rule_info:
        unverified_reasons.append(f"unknown law report series {series!r}")
        bracket_type = "round"
    else:
        bracket_type = rule_info[0]

    yr_str = f"[{clean_year}]" if bracket_type == "square" else f"({clean_year})"
    vol_str = f"{volume} " if volume else ""
    page_str = str(starting_page or "").strip()
    if not page_str.isdigit() or int(page_str) <= 0:
        unverified_reasons.append(f"invalid starting page {starting_page!r}")

    pin_part = ""
    if pinpoint is not None:
        p_str = str(pinpoint).strip()
        if p_str:
            pin_part = f", {p_str}"

    formatted = f"{clean_parties} {yr_str} {vol_str}{clean_series} {page_str}{pin_part}"

    if unverified_reasons:
        return AGLC4FormattedStr(
            f"{formatted} [format_unverified]",
            format_unverified=True,
            kind="case_reported",
            reason="; ".join(unverified_reasons),
            raw_text=raw_repr,
            citation_text=formatted,
        )

    return AGLC4FormattedStr(
        formatted,
        format_unverified=False,
        kind="case_reported",
        reason=None,
        raw_text=raw_repr,
        citation_text=formatted,
    )


def format_aglc4_doc_anchor(
    page: Optional[int | str] = None,
    clause: Optional[str] = None,
    section: Optional[str] = None,
    paragraph: Optional[str] = None,
    raw_anchor: Optional[str] = None,
) -> AGLC4FormattedStr:
    """Format an uploaded-document anchor (e.g. [Doc p. 4, cl 3.2])."""
    parts: list[str] = []
    unverified_reasons: list[str] = []

    if raw_anchor:
        clean = raw_anchor.strip()
        if clean.startswith("[Doc") and clean.endswith("]"):
            clean = clean[4:-1].strip()
        elif clean.startswith("[") and clean.endswith("]"):
            clean = clean[1:-1].strip()
        # Normalise inside
        formatted = f"[Doc {clean}]"
        if not re.search(r"\b(?:pp?\.?|cl|cls|s|ss|para|paras|sch|pt|div|tbl|sec|page|clause)\b", clean, re.I):
            unverified_reasons.append("lacks recognized page or clause indicator")
            return AGLC4FormattedStr(
                f"{formatted} [format_unverified]",
                format_unverified=True,
                kind="doc_anchor",
                reason="; ".join(unverified_reasons),
                raw_text=raw_anchor,
                citation_text=formatted,
            )
        return AGLC4FormattedStr(
            formatted,
            format_unverified=False,
            kind="doc_anchor",
            reason=None,
            raw_text=raw_anchor,
            citation_text=formatted,
        )

    if page is not None:
        p_str = str(page).strip()
        prefix = "pp." if _is_range_or_multiple(p_str) else "p."
        parts.append(f"{prefix} {p_str}")

    if clause is not None:
        c_str = str(clause).strip()
        prefix = "cls" if _is_range_or_multiple(c_str) else "cl"
        parts.append(f"{prefix} {c_str}")

    if section is not None:
        s_str = str(section).strip()
        prefix = "ss" if _is_range_or_multiple(s_str) else "s"
        parts.append(f"{prefix} {s_str}")

    if paragraph is not None:
        para_str = str(paragraph).strip()
        prefix = "paras" if _is_range_or_multiple(para_str) else "para"
        parts.append(f"{prefix} {para_str}")

    if not parts:
        unverified_reasons.append("no anchor parameters provided")
        formatted = "[Doc pinpoint unavailable]"
        return AGLC4FormattedStr(
            f"{formatted} [format_unverified]",
            format_unverified=True,
            kind="doc_anchor",
            reason="; ".join(unverified_reasons),
            raw_text="",
            citation_text=formatted,
        )

    formatted = f"[Doc {', '.join(parts)}]"
    return AGLC4FormattedStr(
        formatted,
        format_unverified=False,
        kind="doc_anchor",
        reason=None,
        raw_text=formatted,
        citation_text=formatted,
    )


def format_aglc4(citation_or_text: Citation | AuCitation | str) -> AGLC4FormattedStr:
    """Format a citation or raw citation string under AGLC4 rules.

    Emits [format_unverified] if the citation is not covered with confidence.
    """
    if isinstance(citation_or_text, AuCitation):
        au = citation_or_text
    elif isinstance(citation_or_text, Citation):
        if isinstance(citation_or_text.raw, AuCitation):
            au = citation_or_text.raw
        else:
            # Fallback for foreign or eyecite citations
            extracted = extract_au(citation_or_text.text)
            if extracted:
                au = extracted[0]
            else:
                return AGLC4FormattedStr(
                    f"{citation_or_text.text} [format_unverified]",
                    format_unverified=True,
                    kind="unverified",
                    reason=f"non-Australian or unrecognised citation ({citation_or_text.jurisdiction})",
                    raw_text=citation_or_text.text,
                    citation_text=citation_or_text.text,
                )
    else:
        text = str(citation_or_text).strip()
        extracted = extract_au(text)
        if not extracted:
            return AGLC4FormattedStr(
                f"{text} [format_unverified]",
                format_unverified=True,
                kind="unverified",
                reason="unable to parse as AGLC4 citation",
                raw_text=text,
                citation_text=text,
            )
        au = extracted[0]

    if au.kind == "au_legislation":
        return format_aglc4_legislation(
            title=au.title_or_party,
            year=au.year,
            jurisdiction=au.jurisdiction_or_court,
            pinpoints=au.pinpoint,
        )

    if au.kind == "au_case_mnc":
        return format_aglc4_case_mnc(
            party_names=au.title_or_party,
            year=au.year,
            court=au.jurisdiction_or_court,
            judgment_number=au.number_or_page,
            pinpoint_paragraph=au.pinpoint,
        )

    if au.kind == "au_case_reported":
        return format_aglc4_case_reported(
            party_names=au.title_or_party,
            year=au.year,
            series=au.series or au.jurisdiction_or_court,
            starting_page=au.number_or_page,
            volume=au.volume,
            pinpoint=au.pinpoint,
        )

    if au.kind == "au_doc_anchor":
        return format_aglc4_doc_anchor(raw_anchor=au.text)

    return AGLC4FormattedStr(
        f"{au.text} [format_unverified]",
        format_unverified=True,
        kind="unverified",
        reason="unhandled citation kind",
        raw_text=au.text,
        citation_text=au.text,
    )


def _format_gb_t_7714(c: Citation) -> str:
    return c.text


def _format_bluebook(c: Citation) -> str:
    if c.raw is not None and hasattr(c.raw, "corrected_citation"):
        try:
            return c.raw.corrected_citation()
        except Exception:
            pass
    return c.text


def _format_oscola(c: Citation) -> str:
    return c.text


def format_citation(citation: Citation | AuCitation | str, style: Style = "aglc4") -> str:
    """Format a citation according to the specified style (default aglc4)."""
    if style == "aglc4":
        return format_aglc4(citation)
    if isinstance(citation, (AuCitation, str)):
        raw_str = citation.text if isinstance(citation, AuCitation) else str(citation)
        return raw_str
    if style == "gb_t_7714":
        return _format_gb_t_7714(citation)
    if style == "bluebook":
        return _format_bluebook(citation)
    return _format_oscola(citation)
