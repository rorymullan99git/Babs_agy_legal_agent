"""High Court of Australia judgments connector (hcourt.gov.au decisions).

Fetches High Court of Australia judgments directly from official publications without third-party scrapers.
"""

from __future__ import annotations

import datetime
import re
from typing import Any, Optional

import httpx
from bs4 import BeautifulSoup

from .base import TTLCache, cache_key, request_with_retry


HCA_BASE = "https://www.hcourt.gov.au"
USER_AGENT = "BabsAgyLegalAgent/1.0 (+academic legal research; contact: student@example.edu.au)"

_CACHE = TTLCache(maxsize=128)
_CACHE_TTL = 3600


def hca_judgment_search(
    query: str,
    year: Optional[int] = None,
    limit: int = 5,
    client: Optional[httpx.Client] = None,
) -> dict[str, Any]:
    """Search High Court of Australia judgments."""
    clean_q = query.strip()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    url = f"{HCA_BASE}/cases/search"
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html"}
    params = {"q": clean_q}
    if year:
        params["year"] = str(year)

    try:
        if client:
            resp = client.get(url, params=params, headers=headers)
        else:
            resp = request_with_retry("GET", url, params=params, headers=headers)

        if resp.status_code != 200:
            return {
                "query": clean_q,
                "results": [],
                "count": 0,
                "status": "error",
                "error": f"HTTP {resp.status_code}",
                "retrieved_at": now_iso,
            }

        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for item in soup.find_all(["div", "li", "tr"], class_=re.compile(r"case|judgment|result", re.I)):
            link = item.find("a")
            if link and link.get("href"):
                href = link.get("href", "")
                results.append({
                    "title": link.get_text(strip=True),
                    "url": f"{HCA_BASE}{href}" if href.startswith("/") else href,
                    "jurisdiction": "Cth",
                    "court": "HCA",
                })
            if len(results) >= limit:
                break

        return {
            "query": clean_q,
            "results": results,
            "count": len(results),
            "retrieved_at": now_iso,
            "status": "ok",
        }
    except Exception as exc:
        return {
            "query": clean_q,
            "results": [],
            "count": 0,
            "status": "error",
            "error": str(exc),
            "retrieved_at": now_iso,
        }


def hca_judgment_fetch(
    year: int | str,
    number: int | str,
    paragraph: Optional[str | int] = None,
    client: Optional[httpx.Client] = None,
) -> dict[str, Any]:
    """Fetch High Court judgment text (e.g. [2016] HCA 35)."""
    yr = str(year).strip().strip("[]")
    num = str(number).strip()
    cache_k = cache_key("hca_case", yr, num, str(paragraph or ""))
    cached = _CACHE.get(cache_k)
    if cached is not _CACHE._MISS and client is None:
        return cached

    url = f"{HCA_BASE}/cases/cases3/{yr}/{num}"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html"}

    try:
        if client:
            resp = client.get(url, headers=headers)
        else:
            resp = request_with_retry("GET", url, headers=headers)

        if resp.status_code != 200:
            return {
                "citation": f"[{yr}] HCA {num}",
                "url": url,
                "status": "not_found",
                "text": "",
                "pinpoint_unavailable": True,
                "error": f"HTTP {resp.status_code}",
                "retrieved_at": now_iso,
            }

        soup = BeautifulSoup(resp.text, "html.parser")
        body_el = soup.find("article") or soup.find("div", id=re.compile(r"judgment|content", re.I)) or soup.find("body")
        full_text = body_el.get_text("\n", strip=True) if body_el else soup.get_text("\n", strip=True)

        target_text = full_text
        if paragraph is not None:
            p_clean = str(paragraph).strip().strip("[]")
            m_p = re.search(rf"\[{p_clean}\]\s+([^\n]+(?:\n[^\n]+){{0,6}})", full_text)
            if m_p:
                target_text = m_p.group(0)
            else:
                return {
                    "citation": f"[{yr}] HCA {num}",
                    "url": url,
                    "status": "pinpoint_unavailable",
                    "text": "",
                    "pinpoint": f"[{p_clean}]",
                    "pinpoint_unavailable": True,
                    "retrieved_at": now_iso,
                }

        result = {
            "citation": f"[{yr}] HCA {num}",
            "url": url,
            "status": "verified online",
            "text": target_text,
            "pinpoint": f"[{paragraph}]" if paragraph else None,
            "pinpoint_unavailable": False,
            "source_type": "case",
            "jurisdiction": "Cth",
            "court": "HCA",
            "court_weight": "binding",
            "retrieved_at": now_iso,
        }
        if client is None:
            _CACHE.set(cache_k, result, _CACHE_TTL)
        return result
    except Exception as exc:
        return {
            "citation": f"[{yr}] HCA {num}",
            "url": url,
            "status": "unverified",
            "text": "",
            "pinpoint_unavailable": True,
            "error": str(exc),
            "retrieved_at": now_iso,
        }
