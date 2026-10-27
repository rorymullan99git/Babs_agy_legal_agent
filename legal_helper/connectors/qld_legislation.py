"""Queensland Legislation connector (legislation.qld.gov.au).

Retrieves point-in-time Queensland statutes, subordinate legislation, and section text.
Enforces:
- Descriptive user-agent: BabsAgyLegalAgent/1.0
- Respects robots.txt and reasonable access rate.
- Returns uniform metadata: text, url, retrieved_at, as_at date, and status.
- Resilient fallback returning pinpoint_unavailable=True when offline without fabricating.
"""

from __future__ import annotations

import datetime
import re
from typing import Any, Optional
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from .base import USER_AGENT, TTLCache, cache_key, request_with_retry


QLD_LEGISLATION_BASE = "https://www.legislation.qld.gov.au"
QLD_USER_AGENT = "BabsAgyLegalAgent/1.0 (+academic legal research; contact: student@example.edu.au)"

# Enable Windows certificate resolution if truststore is available
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

_CACHE = TTLCache(maxsize=128)
_CACHE_TTL = 3600  # 1 hour cache for fetched legislation

# Known Queensland Acts and subordinate legislation slug mappings
KNOWN_QLD_ACTS: dict[str, str] = {
    "criminal code act 1899": "act-1899-009",
    "criminal code": "act-1899-009",
    "criminal code 1899": "act-1899-009",
    "acts interpretation act 1954": "act-1954-003",
    "civil liability act 2003": "act-2003-016",
    "uniform civil procedure rules 1999": "sl-1999-0111",
    "legal profession act 2007": "act-2007-024",
    "human rights act 2019": "act-2019-005",
    "evidence act 1977": "act-1977-047",
    "penalties and sentences act 1992": "act-1992-048",
    "bail act 1980": "act-1980-035",
    "police powers and responsibilities act 2000": "act-2000-005",
    "property law act 1974": "act-1974-076",
    "property law act 2023": "act-2023-025",
    "work health and safety act 2011": "act-2011-018",
    "justices act 1886": "act-1886-017",
    "defamation act 2005": "act-2005-055",
}


def _resolve_act_slug(slug_or_title: str) -> str:
    """Resolve an Act title or shorthand to a legislation.qld.gov.au act slug."""
    clean = " ".join(slug_or_title.strip().lower().split())
    if clean.startswith("act-") or clean.startswith("sl-"):
        return clean
    if clean in KNOWN_QLD_ACTS:
        return KNOWN_QLD_ACTS[clean]
    # Check without year or prefix
    clean_no_act = re.sub(r"\bact\b", "", clean).strip()
    for k, v in KNOWN_QLD_ACTS.items():
        if clean in k or k in clean or clean_no_act in k:
            return v
    # Pattern matching: e.g. "Criminal Code Act 1899" -> act-1899-009 if known
    m = re.search(r"(\d{4})", clean)
    year = m.group(1) if m else "current"
    return f"act-{year}-001"


def _extract_section_text(soup: BeautifulSoup, section_num: str) -> Optional[str]:
    """Extract the text of a specific section from the full Queensland Act HTML."""
    clean_sec = section_num.strip().lower()
    # Normalize e.g. "s 23" -> "23", "sch 1 s 23" -> "23"
    sec_digits = re.search(r"(\d+[A-Za-z]*)", clean_sec)
    sec_id = sec_digits.group(1) if sec_digits else clean_sec

    # Anchors in QLD legislation: <a name="sch.1-sec.23"> or <a name="sec.23">
    patterns = [
        f"sch.1-sec.{sec_id}",
        f"sec.{sec_id}",
        f"s.{sec_id}",
        f"s{sec_id}",
        f"sec-{sec_id}",
    ]
    anchor = None
    for pat in patterns:
        anchor = soup.find("a", attrs={"name": re.compile(rf"^(?:sch\.\d+-)?sec\.{sec_id}$", re.I)})
        if anchor:
            break
        anchor = soup.find(id=re.compile(rf"^(?:sch\.\d+-)?sec\.{sec_id}$", re.I))
        if anchor:
            break

    if not anchor:
        # Fallback text search for Section header e.g. "23 Intention"
        for tag in soup.find_all(["p", "div", "h2", "h3", "h4", "h5", "blockquote"]):
            txt = tag.get_text(strip=True)
            if re.match(rf"^{sec_id}\s+[A-Z]", txt):
                anchor = tag
                break

    if not anchor:
        return None

    # Collect consecutive paragraphs belonging to this section until the next section
    collected_paras: list[str] = []
    curr = anchor.parent if anchor.name == "a" else anchor

    # Look through following elements
    for el in curr.find_all_next(["p", "blockquote", "div"]):
        t = el.get_text(" ", strip=True)
        if not t:
            continue
        # Check if next section began (e.g. "24 Mistake of fact")
        if re.match(r"^\d+[A-Za-z]*\s+[A-Z]", t) and not re.match(rf"^{sec_id}\s+", t):
            break
        # Stop at division or part headers
        if re.match(r"^(?:Part|Division|Chapter|Schedule)\s+\d+", t, re.I):
            break
        if t not in collected_paras:
            collected_paras.append(t)
        if len(collected_paras) > 30:  # safety bound
            break

    if not collected_paras:
        return None

    return "\n\n".join(collected_paras)


def qld_legislation_fetch(
    act: str,
    as_at: str = "current",
    section: Optional[str] = None,
    client: Optional[httpx.Client] = None,
    bypass_cache: bool = False,
) -> dict[str, Any]:
    """Fetch legislation text from legislation.qld.gov.au.

    Parameters:
        act: Act slug (e.g. 'act-1899-009') or Act title ('Criminal Code Act 1899').
        as_at: Point-in-time date YYYY-MM-DD or 'current'.
        section: Optional pinpoint section number (e.g. '23', 's 23').
        client: Optional injected httpx.Client for testing.
        bypass_cache: If True, do not read from cache.
    """
    act_slug = _resolve_act_slug(act)
    as_at_clean = as_at.strip()
    cache_k = cache_key("qld_leg", act_slug, as_at_clean, section or "")

    if not bypass_cache and client is None:
        cached = _CACHE.get(cache_k)
        if cached is not _CACHE._MISS:
            return cached

    url = f"{QLD_LEGISLATION_BASE}/view/whole/html/inforce/{as_at_clean}/{act_slug}"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    headers = {
        "User-Agent": QLD_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
    }

    try:
        if client:
            resp = client.get(url, headers=headers)
        else:
            resp = request_with_retry(
                "GET",
                url,
                headers=headers,
                timeout=httpx.Timeout(25.0, connect=10.0),
            )

        if resp.status_code != 200:
            result = {
                "act_slug": act_slug,
                "url": str(resp.url),
                "as_at": as_at_clean,
                "retrieved_at": now_iso,
                "status": "not_found",
                "error": f"HTTP {resp.status_code}",
                "text": "",
                "pinpoint_unavailable": True,
            }
            return result

        html_text = resp.text
        soup = BeautifulSoup(html_text, "html.parser")

        # Extract title
        title_el = soup.find("title") or soup.find("h1")
        title = title_el.get_text(strip=True) if title_el else act

        # Determine in-force status from legislative metadata
        status = "in_force"
        if "/repealed/" in str(resp.url) or "this act was repealed" in html_text.lower():
            status = "repealed"

        target_text = ""
        if section:
            extracted_sec = _extract_section_text(soup, section)
            if extracted_sec:
                target_text = extracted_sec
            else:
                # Section pinpoint not located in whole act
                result = {
                    "act_slug": act_slug,
                    "title": title,
                    "url": str(resp.url),
                    "as_at": as_at_clean,
                    "retrieved_at": now_iso,
                    "status": status,
                    "text": "",
                    "pinpoint": section,
                    "pinpoint_unavailable": True,
                    "reason": f"section {section} not found in {act_slug}",
                }
                return result
        else:
            # Whole text cleaned
            body_el = soup.find("body")
            target_text = body_el.get_text("\n", strip=True) if body_el else soup.get_text("\n", strip=True)

        result = {
            "act_slug": act_slug,
            "title": title,
            "url": str(resp.url),
            "as_at": as_at_clean,
            "retrieved_at": now_iso,
            "status": status,
            "text": target_text,
            "pinpoint": section,
            "pinpoint_unavailable": False,
            "source_type": "legislation",
            "jurisdiction": "QLD",
        }
        if client is None:
            _CACHE.set(cache_k, result, _CACHE_TTL)
        return result

    except Exception as exc:
        return {
            "act_slug": act_slug,
            "url": url,
            "as_at": as_at_clean,
            "retrieved_at": now_iso,
            "status": "unverified",
            "error": str(exc),
            "text": "",
            "pinpoint_unavailable": True,
            "reason": f"connector error: {exc}",
        }


def qld_legislation_search(
    query: str,
    as_at: str = "current",
    limit: int = 5,
) -> dict[str, Any]:
    """Search known Queensland legislation by title or topic."""
    clean_q = query.strip().lower()
    matches = []
    for title, slug in KNOWN_QLD_ACTS.items():
        if clean_q in title or any(token in title for token in clean_q.split()):
            matches.append({
                "title": title.title(),
                "act_slug": slug,
                "url": f"{QLD_LEGISLATION_BASE}/view/whole/html/inforce/{as_at}/{slug}",
                "jurisdiction": "QLD",
            })
        if len(matches) >= limit:
            break

    return {
        "query": query,
        "as_at": as_at,
        "results": matches,
        "count": len(matches),
    }
