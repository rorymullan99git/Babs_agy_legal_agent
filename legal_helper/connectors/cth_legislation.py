"""Commonwealth Legislation connector (Federal Register of Legislation - legislation.gov.au).

Provides point-in-time lookup and section text extraction for Commonwealth legislation.
Material is licensed under CC BY 4.0.
"""

from __future__ import annotations

import datetime
import re
from typing import Any, Optional

import httpx
from bs4 import BeautifulSoup

from .base import TTLCache, cache_key, request_with_retry


CTH_LEGISLATION_BASE = "https://www.legislation.gov.au"
USER_AGENT = "BabsAgyLegalAgent/1.0 (+academic legal research; contact: student@example.edu.au)"

_CACHE = TTLCache(maxsize=128)
_CACHE_TTL = 3600

KNOWN_CTH_ACTS: dict[str, str] = {
    "corporations act 2001": "C2004A00818",
    "corporations act": "C2004A00818",
    "competition and consumer act 2010": "C2004A00109",
    "competition and consumer act": "C2004A00109",
    "australian consumer law": "C2004A00109",
    "constitution": "C1900A00001",
    "commonwealth of australia constitution act": "C1900A00001",
    "acts interpretation act 1901": "C1901A00002",
    "acts interpretation act": "C1901A00002",
    "evidence act 1995": "C2004A04856",
    "evidence act": "C2004A04856",
    "judiciary act 1903": "C1903A00006",
    "native title act 1993": "C2004A04665",
    "fair work act 2009": "C2009A00028",
    "migration act 1958": "C2004A03868",
}


def cth_legislation_search(
    query: str,
    limit: int = 5,
    client: Optional[httpx.Client] = None,
) -> dict[str, Any]:
    """Search Commonwealth legislation."""
    clean_q = query.strip().lower()
    matches = []
    for title, act_id in KNOWN_CTH_ACTS.items():
        if clean_q in title or any(w in title for w in clean_q.split()):
            matches.append({
                "title": title.title(),
                "act_id": act_id,
                "url": f"{CTH_LEGISLATION_BASE}/Details/{act_id}",
                "jurisdiction": "Cth",
            })
        if len(matches) >= limit:
            break

    return {
        "query": query,
        "results": matches,
        "count": len(matches),
    }


def cth_legislation_fetch(
    act: str,
    section: Optional[str] = None,
    as_at: str = "current",
    client: Optional[httpx.Client] = None,
) -> dict[str, Any]:
    """Fetch Commonwealth legislation from legislation.gov.au."""
    clean_target = act.strip().lower()
    act_id = KNOWN_CTH_ACTS.get(clean_target, act.strip())
    cache_k = cache_key("cth_leg", act_id, str(section or ""))
    cached = _CACHE.get(cache_k)
    if cached is not _CACHE._MISS and client is None:
        return cached

    url = f"{CTH_LEGISLATION_BASE}/Details/{act_id}" if not act_id.startswith("http") else act_id
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html"}

    try:
        if client:
            resp = client.get(url, headers=headers)
        else:
            resp = request_with_retry("GET", url, headers=headers)

        if resp.status_code != 200:
            return {
                "act": act,
                "url": url,
                "status": "not_found",
                "text": "",
                "pinpoint_unavailable": True,
                "error": f"HTTP {resp.status_code}",
                "retrieved_at": now_iso,
            }

        soup = BeautifulSoup(resp.text, "html.parser")
        title_el = soup.find("title") or soup.find("h1")
        title = title_el.get_text(strip=True) if title_el else act

        body_el = soup.find("main") or soup.find("div", id=re.compile(r"content|body", re.I)) or soup.find("body")
        full_text = body_el.get_text("\n", strip=True) if body_el else soup.get_text("\n", strip=True)

        target_text = full_text
        if section:
            clean_s = re.sub(r"[^\w]", "", section)
            m_sec = re.search(rf"\b(?:section|s\.?)\s+{clean_s}\b[^\n]+(?:\n[^\n]+){{0,15}}", full_text, re.I)
            if m_sec:
                target_text = m_sec.group(0)
            else:
                return {
                    "act": act,
                    "title": title,
                    "url": url,
                    "status": "pinpoint_unavailable",
                    "text": "",
                    "pinpoint": section,
                    "pinpoint_unavailable": True,
                    "retrieved_at": now_iso,
                }

        result = {
            "act": act,
            "title": title,
            "url": url,
            "status": "in_force",
            "text": target_text,
            "pinpoint": section,
            "pinpoint_unavailable": False,
            "source_type": "legislation",
            "jurisdiction": "Cth",
            "retrieved_at": now_iso,
        }
        if client is None:
            _CACHE.set(cache_k, result, _CACHE_TTL)
        return result
    except Exception as exc:
        return {
            "act": act,
            "url": url,
            "status": "unverified",
            "text": "",
            "pinpoint_unavailable": True,
            "error": str(exc),
            "retrieved_at": now_iso,
        }
