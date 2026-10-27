"""Queensland Court and Tribunal judgments connector (Queensland Judgments).

Covers Queensland Court of Appeal (QCA), Supreme Court (QSC), District Court (QDC),
and Queensland Civil and Administrative Tribunal (QCAT).
Respects rate limits and uses descriptive user-agent.
Corpus and search hits are leads only; anything cited must be verified against source text.
"""

from __future__ import annotations

import datetime
import re
from typing import Any, Optional

import httpx
from bs4 import BeautifulSoup

from .base import TTLCache, cache_key, request_with_retry


QLD_JUDGMENTS_BASE = "https://www.queenslandjudgments.com.au"
USER_AGENT = "BabsAgyLegalAgent/1.0 (+academic legal research; contact: student@example.edu.au)"

_CACHE = TTLCache(maxsize=128)
_CACHE_TTL = 3600


def qld_caselaw_search(
    query: str,
    court: Optional[str] = None,
    year: Optional[int] = None,
    limit: int = 5,
    client: Optional[httpx.Client] = None,
) -> dict[str, Any]:
    """Search Queensland Court judgments."""
    clean_q = query.strip()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    url = f"{QLD_JUDGMENTS_BASE}/caselaw"
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/json"}
    params = {"q": clean_q}
    if court:
        params["court"] = court.upper()
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
                "court": court,
                "results": [],
                "count": 0,
                "status": "error",
                "error": f"HTTP {resp.status_code}",
            }

        # Parse results
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for item in soup.find_all(["div", "article", "li"], class_=re.compile(r"case|result|decision", re.I)):
            title_el = item.find(["a", "h3", "h4"])
            if title_el:
                href = title_el.get("href", "")
                results.append({
                    "title": title_el.get_text(strip=True),
                    "url": f"{QLD_JUDGMENTS_BASE}{href}" if href.startswith("/") else href,
                    "jurisdiction": "QLD",
                    "court": court or "QCA",
                })
            if len(results) >= limit:
                break

        return {
            "query": clean_q,
            "court": court,
            "results": results,
            "count": len(results),
            "retrieved_at": now_iso,
            "status": "ok",
        }
    except Exception as exc:
        return {
            "query": clean_q,
            "court": court,
            "results": [],
            "count": 0,
            "status": "error",
            "error": str(exc),
            "retrieved_at": now_iso,
        }


def qld_caselaw_fetch(
    citation_or_url: str,
    paragraph: Optional[str | int] = None,
    client: Optional[httpx.Client] = None,
) -> dict[str, Any]:
    """Fetch judgment text from Queensland Courts."""
    clean_target = citation_or_url.strip()
    cache_k = cache_key("qld_case", clean_target, str(paragraph or ""))
    cached = _CACHE.get(cache_k)
    if cached is not _CACHE._MISS and client is None:
        return cached

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if clean_target.startswith("http"):
        url = clean_target
    else:
        # Resolve medium neutral citation, e.g. [2021] QCA 1 -> /caselaw/QCA/2021/1
        m = re.search(r"\[(\d{4})\]\s+([A-Z]{3,6})\s+(\d+)", clean_target)
        if m:
            yr, ct, num = m.groups()
            url = f"{QLD_JUDGMENTS_BASE}/caselaw/{ct}/{yr}/{num}"
        else:
            url = f"{QLD_JUDGMENTS_BASE}/caselaw"

    headers = {"User-Agent": USER_AGENT, "Accept": "text/html"}

    try:
        if client:
            resp = client.get(url, headers=headers)
        else:
            resp = request_with_retry("GET", url, headers=headers)

        if resp.status_code != 200:
            return {
                "citation": clean_target,
                "url": url,
                "status": "not_found",
                "text": "",
                "pinpoint_unavailable": True,
                "error": f"HTTP {resp.status_code}",
                "retrieved_at": now_iso,
            }

        soup = BeautifulSoup(resp.text, "html.parser")
        body_el = soup.find("article") or soup.find("div", class_=re.compile(r"judgment|content|decision", re.I)) or soup.find("body")
        full_text = body_el.get_text("\n", strip=True) if body_el else soup.get_text("\n", strip=True)

        target_text = full_text
        if paragraph is not None:
            p_str = str(paragraph).strip().strip("[]")
            m_p = re.search(rf"\[{p_str}\]\s+([^\n]+(?:\n[^\n]+){{0,6}})", full_text)
            if m_p:
                target_text = m_p.group(0)
            else:
                return {
                    "citation": clean_target,
                    "url": url,
                    "status": "pinpoint_unavailable",
                    "text": "",
                    "pinpoint": f"[{p_str}]",
                    "pinpoint_unavailable": True,
                    "retrieved_at": now_iso,
                }

        result = {
            "citation": clean_target,
            "url": url,
            "status": "verified online",
            "text": target_text,
            "pinpoint": f"[{paragraph}]" if paragraph else None,
            "pinpoint_unavailable": False,
            "source_type": "case",
            "jurisdiction": "QLD",
            "retrieved_at": now_iso,
        }
        if client is None:
            _CACHE.set(cache_k, result, _CACHE_TTL)
        return result
    except Exception as exc:
        return {
            "citation": clean_target,
            "url": url,
            "status": "unverified",
            "text": "",
            "pinpoint_unavailable": True,
            "error": str(exc),
            "retrieved_at": now_iso,
        }
