"""Australian citation extraction and structural validation (AGLC4).

Covers:
1. Australian legislation with pinpoints (s, ss, pt, pts, div, divs, sub-div,
   sch, schs, cl, cls, para, paras, reg, regs, r, rr) and schedule short titles
   such as ``Criminal Code Act 1899 (Qld) sch 1 ('Criminal Code') s 23``.
2. Australian medium neutral case citations (e.g. ``R v Baden-Clay [2016] HCA 35, [45]``).
3. Australian authorised and generalist law report citations (e.g.
   ``Mabo v Queensland (No 2) (1992) 175 CLR 1, 15``,
   ``Farah Constructions Pty Ltd v Say-Dee Pty Ltd (2007) 230 CLR 89, 151 [134]``,
   ``[1999] 1 Qd R 100, 105``).
4. Uploaded-document anchors (e.g. ``[Doc p. 4, cl 3.2]``).

Per Hard Rule 2 and Acceptance Test 1, structural validation NEVER returns
``verified`` for a case or statute citation without source text verification:
plausible citations return ``could_not_check`` and malformed or unknown
court/reporter citations return ``flagged``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Optional

AuCitationKind = Literal[
    "au_legislation",
    "au_case_mnc",
    "au_case_reported",
    "au_doc_anchor",
]

#: Official AGLC4 Australian & related jurisdiction abbreviations (Rule 3.1.3).
AU_JURISDICTION_MAP: dict[str, str] = {
    "cth": "Cth",
    "commonwealth": "Cth",
    "qld": "Qld",
    "queensland": "Qld",
    "nsw": "NSW",
    "new south wales": "NSW",
    "vic": "Vic",
    "victoria": "Vic",
    "sa": "SA",
    "south australia": "SA",
    "wa": "WA",
    "western australia": "WA",
    "tas": "Tas",
    "tasmania": "Tas",
    "act": "ACT",
    "australian capital territory": "ACT",
    "nt": "NT",
    "northern territory": "NT",
    "imp": "Imp",
    "uk": "UK",
    "nz": "NZ",
}

CANONICAL_AU_JURISDICTIONS: frozenset[str] = frozenset(AU_JURISDICTION_MAP.values())

#: Recognised AGLC4 Medium Neutral Court Identifiers (Rule 2.3.1 & Appendix B).
KNOWN_MNC_COURTS: dict[str, str] = {
    "HCA": "binding",
    "FCAFC": "comity_appellate",
    "FCA": "persuasive",
    "FamCAFC": "comity_appellate",
    "FamCA": "persuasive",
    "FedCFamC1A": "comity_appellate",
    "FedCFamC1F": "persuasive",
    "FedCFamC2F": "lower_court_or_tribunal",
    "FCCA": "lower_court_or_tribunal",
    "FMCA": "lower_court_or_tribunal",
    "AAT": "lower_court_or_tribunal",
    "ART": "lower_court_or_tribunal",
    "QCA": "binding",
    "QSC": "persuasive",
    "QSCPR": "persuasive",
    "QDC": "lower_court_or_tribunal",
    "QMC": "lower_court_or_tribunal",
    "QCAT": "lower_court_or_tribunal",
    "QCATA": "lower_court_or_tribunal",
    "QPEC": "lower_court_or_tribunal",
    "QLC": "lower_court_or_tribunal",
    "QLAC": "comity_appellate",
    "QIRC": "lower_court_or_tribunal",
    "ICQ": "lower_court_or_tribunal",
    "NSWCA": "comity_appellate",
    "NSWCCA": "comity_appellate",
    "NSWSC": "persuasive",
    "NSWDC": "lower_court_or_tribunal",
    "NSWLEC": "persuasive",
    "NSWCATAD": "lower_court_or_tribunal",
    "NSWCATAP": "lower_court_or_tribunal",
    "VSCA": "comity_appellate",
    "VSC": "persuasive",
    "VCC": "lower_court_or_tribunal",
    "VCAT": "lower_court_or_tribunal",
    "WASCA": "comity_appellate",
    "WASC": "persuasive",
    "WADC": "lower_court_or_tribunal",
    "WASAT": "lower_court_or_tribunal",
    "SASCA": "comity_appellate",
    "SASCFC": "comity_appellate",
    "SASC": "persuasive",
    "SADC": "lower_court_or_tribunal",
    "SACAT": "lower_court_or_tribunal",
    "TASFC": "comity_appellate",
    "TASCCA": "comity_appellate",
    "TASSC": "persuasive",
    "ACTCA": "comity_appellate",
    "ACTSC": "persuasive",
    "ACAT": "lower_court_or_tribunal",
    "NTCA": "comity_appellate",
    "NTSC": "persuasive",
    "NTCAT": "lower_court_or_tribunal",
    "UKSC": "comparative_persuasive",
    "UKHL": "comparative_persuasive",
    "UKPC": "comparative_persuasive",
    "EWCA": "comparative_persuasive",
    "EWHC": "comparative_persuasive",
    "NZSC": "comparative_persuasive",
    "NZCA": "comparative_persuasive",
    "NZHC": "comparative_persuasive",
}

#: Recognised AGLC4 Authorised & Generalist Law Report Series (Rule 2.2 & Appendix A).
#: Maps canonical series abbreviation -> ("round" | "square" | "either", court_weight_default).
KNOWN_REPORT_SERIES: dict[str, tuple[str, str]] = {
    "CLR": ("round", "binding"),
    "ALJR": ("round", "binding"),
    "ALR": ("round", "persuasive"),
    "FCR": ("round", "persuasive"),
    "FLR": ("round", "persuasive"),
    "Qd R": ("square", "persuasive"),
    "QR": ("either", "persuasive"),
    "QSR": ("square", "persuasive"),
    "QWN": ("square", "persuasive"),
    "QCAR": ("round", "binding"),
    "NSWLR": ("round", "persuasive"),
    "VR": ("round", "persuasive"),
    "SASR": ("round", "persuasive"),
    "WAR": ("round", "persuasive"),
    "Tas R": ("round", "persuasive"),
    "ACTSR": ("round", "persuasive"),
    "NTLR": ("round", "persuasive"),
    "AC": ("square", "comparative_persuasive"),
    "QB": ("square", "comparative_persuasive"),
    "KB": ("square", "comparative_persuasive"),
    "Ch": ("square", "comparative_persuasive"),
    "WLR": ("square", "comparative_persuasive"),
    "All ER": ("square", "comparative_persuasive"),
    "NZLR": ("square", "comparative_persuasive"),
}


@dataclass(frozen=True)
class AuCitation:
    text: str
    kind: AuCitationKind
    span: tuple[int, int]
    title_or_party: str = ""
    year: int = 0
    jurisdiction_or_court: str = ""
    volume: Optional[str] = None
    series: Optional[str] = None
    number_or_page: str = ""
    pinpoint: str = ""
    court_weight: Optional[str] = None


_LEADING_SIGNAL_RE = re.compile(
    r"^(?:(?:see\s+also|see\s+generally|see|cf\.?|per|in|under\s+the|under|"
    r"pursuant\s+to\s+the|pursuant\s+to|by\s+the|by|according\s+to\s+the|"
    r"according\s+to|following|applied\s+in|distinguished\s+in|considered\s+in|"
    r"e\.?g\.?,?|for\s+example,?|the)\s+)+",
    re.IGNORECASE,
)


def _strip_leading_signals(raw: str) -> tuple[str, int]:
    """Strip leading prose signals (e.g. 'See ', 'Under the ') and return (cleaned, offset_delta)."""
    m = _LEADING_SIGNAL_RE.match(raw)
    if not m:
        return raw, 0
    cleaned = raw[m.end():]
    if cleaned:
        return cleaned, m.end()
    return raw, 0


# 1. Uploaded document anchor: [Doc p. 4, cl 3.2], [Doc p. 4], [Doc cl 3.2]
_DOC_ANCHOR_RE = re.compile(r"\[Doc\s+([^\[\]\n]{1,80})\]")

# 2. Australian Legislation:
# e.g. Criminal Code Act 1899 (Qld) sch 1 ('Criminal Code') s 23
# e.g. Civil Liability Act 2003 (Qld) s 9(1)(a)
# e.g. Uniform Civil Procedure Rules 1999 (Qld) r 149
_PINPOINT_TOKEN = (
    r"(?:pts?|divs?|sub-divs?|schs?|ss?|sub-ss?|cls?|sub-cls?|paras?|sub-paras?|regs?|rr?|arts?)"
    r"\s+[0-9A-Za-z().\-–]+(?:\s*(?:to|and)\s*[0-9A-Za-z().\-–]+)?(?:\s*\(['\"][^'\"]+['\"]\))?"
)
_TITLE_WORD = r"[A-Z][A-Za-z0-9'\-]*"
_TITLE_CONNECTOR = r"(?:of|and|for|in|to|the|on|at|by|with|&)"
_AU_LEGISLATION_RE = re.compile(
    r"\b(?P<title>" + _TITLE_WORD + r"(?:\s+(?:" + _TITLE_WORD + r"|" + _TITLE_CONNECTOR + r"|,\s*)){0,12}\s+"
    r"(?:Act|Regulation|Regulations|Rules|Code|Order|Proclamation|Notice|Instrument))\s+"
    r"(?P<year>1[789]\d{2}|20\d{2})\s*"
    r"\((?P<juris>Cth|Qld|QLD|NSW|Vic|VIC|SA|WA|Tas|TAS|ACT|NT|Imp|UK|NZ)\)"
    r"(?P<pinpoint>(?:\s+" + _PINPOINT_TOKEN + r")*)"
)

# 3. Medium Neutral Citation:
# e.g. R v Baden-Clay [2016] HCA 35, [45]
_PARTY_SIDE = (
    r"[A-Z][A-Za-z0-9'&.\-()]*(?:\s+(?:[A-Z][A-Za-z0-9'&.\-()]*|of|and|the|in|for|on|\(No\s+\d+\))){0,8}"
)
_PARTY_NAME_PAT = (
    r"(?:" + _PARTY_SIDE + r"\s+v\s+" + _PARTY_SIDE + r"|Re\s+" + _PARTY_SIDE + r")"
)
_MNC_RE = re.compile(
    r"(?:(?P<party>" + _PARTY_NAME_PAT + r")\s+)?"
    r"\[(?P<year>19\d{2}|20\d{2})\]\s+"
    r"(?P<court>[A-Z][A-Za-z0-9]{1,11})\s+"
    r"(?P<num>\d+)"
    r"(?:,\s*(?P<pinpoint>\[?\d+\]?(?:\s*[-–]\s*\[?\d+\]?)?(?:\s*,\s*\[?\d+\]?)*))?"
)

# 4. Reported Case Citation:
# e.g. Mabo v Queensland (No 2) (1992) 175 CLR 1, 15
# e.g. Farah Constructions Pty Ltd v Say-Dee Pty Ltd (2007) 230 CLR 89, 151 [134]
# e.g. [1999] 1 Qd R 100, 105
_SERIES_ALTERNATION = "|".join(
    sorted((re.escape(k) for k in KNOWN_REPORT_SERIES), key=len, reverse=True)
    + [r"[A-Z]{2,6}R"]
)
_REPORTED_RE = re.compile(
    r"(?:(?P<party>" + _PARTY_NAME_PAT + r")\s+)?"
    r"(?P<yr_bracket>\((?P<year_r>1[89]\d{2}|20\d{2})\)|\[(?P<year_s>1[89]\d{2}|20\d{2})\])\s+"
    r"(?:(?P<vol>\d+)\s+)?"
    r"(?P<series>" + _SERIES_ALTERNATION + r")\s+"
    r"(?P<page>\d+)"
    r"(?:,\s*(?P<pinpoint>\d+(?:\s*[-–]\s*\d+)?(?:\s*\[\d+(?:\s*[-–]\s*\d+)?\])?|\[\d+(?:\s*[-–]\s*\d+)?\]))?"
)


def court_weight_for(court_or_series: str) -> str:
    """Return the playbook court weight label for an Australian court or report series."""
    token = (court_or_series or "").strip()
    if token in KNOWN_MNC_COURTS:
        return KNOWN_MNC_COURTS[token]
    if token in KNOWN_REPORT_SERIES:
        return KNOWN_REPORT_SERIES[token][1]
    return "unverified_court"


def extract_au(text: str) -> list[AuCitation]:
    """Extract Australian legislation, cases, and uploaded-document anchors from ``text``."""
    out: list[AuCitation] = []

    for m in _DOC_ANCHOR_RE.finditer(text):
        out.append(
            AuCitation(
                text=m.group(0),
                kind="au_doc_anchor",
                span=m.span(),
                pinpoint=m.group(1).strip(),
            )
        )

    for m in _AU_LEGISLATION_RE.finditer(text):
        raw_full = m.group(0)
        raw_title = m.group("title")
        clean_title, delta = _strip_leading_signals(raw_title)
        title = " ".join(clean_title.split())
        year = int(m.group("year"))
        juris_raw = m.group("juris")
        juris = AU_JURISDICTION_MAP.get(juris_raw.lower(), juris_raw)
        pin = (m.group("pinpoint") or "").strip()
        span = (m.start() + delta, m.end())
        cite_text = raw_full[delta:].strip()
        out.append(
            AuCitation(
                text=cite_text,
                kind="au_legislation",
                span=span,
                title_or_party=title,
                year=year,
                jurisdiction_or_court=juris,
                pinpoint=pin,
            )
        )

    for m in _MNC_RE.finditer(text):
        raw_full = m.group(0)
        court = m.group("court")
        raw_party = m.group("party") or ""
        clean_party, delta = _strip_leading_signals(raw_party) if raw_party else ("", 0)
        party = " ".join(clean_party.split())
        year = int(m.group("year"))
        num = m.group("num")
        pin = (m.group("pinpoint") or "").strip()
        span = (m.start() + delta, m.end())
        cite_text = raw_full[delta:].strip()
        out.append(
            AuCitation(
                text=cite_text,
                kind="au_case_mnc",
                span=span,
                title_or_party=party,
                year=year,
                jurisdiction_or_court=court,
                number_or_page=num,
                pinpoint=pin,
                court_weight=court_weight_for(court),
            )
        )

    for m in _REPORTED_RE.finditer(text):
        raw_full = m.group(0)
        raw_party = m.group("party") or ""
        clean_party, delta = _strip_leading_signals(raw_party) if raw_party else ("", 0)
        party = " ".join(clean_party.split())
        yr_str = m.group("year_r") or m.group("year_s")
        year = int(yr_str)
        vol = m.group("vol")
        series = m.group("series")
        page = m.group("page")
        pin = (m.group("pinpoint") or "").strip()
        span = (m.start() + delta, m.end())
        cite_text = raw_full[delta:].strip()
        out.append(
            AuCitation(
                text=cite_text,
                kind="au_case_reported",
                span=span,
                title_or_party=party,
                year=year,
                jurisdiction_or_court=series,
                volume=vol,
                series=series,
                number_or_page=page,
                pinpoint=pin,
                court_weight=court_weight_for(series),
            )
        )

    out.sort(key=lambda c: c.span[0])
    return out


def validate_au(c: AuCitation) -> tuple[Literal["verified", "flagged", "could_not_check"], str | None]:
    """Validate an Australian citation structurally.

    Offline structural checks NEVER return ``verified`` for primary law (cases or
    legislation) because existence and pinpoint accuracy require checking
    retrieved source text. Unknown courts, unknown report series, or invalid
    years/numbers return ``flagged``.
    """
    if c.kind == "au_doc_anchor":
        if not re.search(r"\b(?:pp?\.?|cl|cls|s|ss|para|paras|sch|pt|div|tbl|sec|page|clause)\b", c.pinpoint, re.I):
            return ("flagged", f"document anchor {c.text!r} lacks a recognized page or clause designator")
        return (
            "could_not_check",
            "uploaded document anchor requires verification against parsed upload pages/clauses",
        )

    if c.kind == "au_legislation":
        if c.jurisdiction_or_court not in CANONICAL_AU_JURISDICTIONS:
            return ("flagged", f"unrecognised AGLC4 jurisdiction: {c.jurisdiction_or_court!r}")
        if not (1788 <= c.year <= 2030):
            return ("flagged", f"implausible Australian legislation year: {c.year}")
        return (
            "could_not_check",
            "Australian legislation citation requires round-trip against retrieved point-in-time source text",
        )

    if c.kind == "au_case_mnc":
        if c.jurisdiction_or_court not in KNOWN_MNC_COURTS:
            return ("flagged", f"unknown or unverified medium neutral court identifier: {c.jurisdiction_or_court!r}")
        if not (1990 <= c.year <= 2030):
            return ("flagged", f"implausible medium neutral citation year: {c.year}")
        if not c.number_or_page.isdigit() or int(c.number_or_page) <= 0:
            return ("flagged", f"invalid judgment number in medium neutral citation: {c.number_or_page!r}")
        return (
            "could_not_check",
            "medium neutral case citation requires verification against retrieved judgment text",
        )

    if c.kind == "au_case_reported":
        series = c.series or c.jurisdiction_or_court
        if series not in KNOWN_REPORT_SERIES:
            return ("flagged", f"unknown law report series: {series!r}")
        bracket_rule, _ = KNOWN_REPORT_SERIES[series]
        has_round = f"({c.year})" in c.text
        has_square = f"[{c.year}]" in c.text
        if bracket_rule == "round" and not has_round:
            return ("flagged", f"report series {series!r} uses round brackets ({c.year}) under AGLC4 Rule 2.2.1")
        if bracket_rule == "square" and not has_square:
            return ("flagged", f"report series {series!r} uses square brackets [{c.year}] under AGLC4 Rule 2.2.1")
        return (
            "could_not_check",
            "reported case citation requires verification against retrieved judgment text",
        )

    return ("could_not_check", "unrecognised Australian citation type")
