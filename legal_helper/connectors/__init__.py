"""In-process connector layer.

Each connector is a ``@beta_tool``-decorated function with a JSON-Schema
description that both the Anthropic and OpenAI providers can register as a
plain function tool. ``REGISTRY`` collects them with their jurisdiction +
domain-pack metadata so ``tools/connectors_tools.py`` can filter them per
invocation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .aviation import faa_title14_search
from .caac_local import caac_local_fetch, caac_local_search
from .cth_legislation import cth_legislation_fetch, cth_legislation_search
from .easa_safety import easa_ad_fetch, easa_ad_search, easa_ear_index
from .ethiopia import ecaa_fetch, ecaa_index, ethiopia_law_fetch, ethiopia_law_search
from .eu import eurlex_fetch, eurlex_search
from .faa_drs import drs_search
from .hca_judgments import hca_judgment_fetch, hca_judgment_search
from .prc import flk_npc_fetch, flk_npc_search
from .qld_caselaw import qld_caselaw_fetch, qld_caselaw_search
from .qld_legislation import qld_legislation_fetch, qld_legislation_search
from .us_courts import courtlistener_fetch, courtlistener_search
from .us_federal import (
    ecfr_fetch,
    ecfr_search,
    federal_register_fetch,
    federal_register_search,
    govinfo_fetch,
    govinfo_search,
)


@dataclass(frozen=True)
class ConnectorEntry:
    name: str
    fn: Any
    jurisdiction: tuple[str, ...]
    domain_packs: tuple[str, ...] = ()


REGISTRY: tuple[ConnectorEntry, ...] = (
    ConnectorEntry("qld_legislation_search", qld_legislation_search, ("AU",)),
    ConnectorEntry("qld_legislation_fetch", qld_legislation_fetch, ("AU",)),
    ConnectorEntry("qld_caselaw_search", qld_caselaw_search, ("AU",)),
    ConnectorEntry("qld_caselaw_fetch", qld_caselaw_fetch, ("AU",)),
    ConnectorEntry("cth_legislation_search", cth_legislation_search, ("AU",)),
    ConnectorEntry("cth_legislation_fetch", cth_legislation_fetch, ("AU",)),
    ConnectorEntry("hca_judgment_search", hca_judgment_search, ("AU",)),
    ConnectorEntry("hca_judgment_fetch", hca_judgment_fetch, ("AU",)),
    ConnectorEntry("ecfr_search", ecfr_search, ("US",)),
    ConnectorEntry("ecfr_fetch", ecfr_fetch, ("US",)),
    ConnectorEntry("federal_register_search", federal_register_search, ("US",)),
    ConnectorEntry("federal_register_fetch", federal_register_fetch, ("US",)),
    ConnectorEntry("govinfo_search", govinfo_search, ("US",)),
    ConnectorEntry("govinfo_fetch", govinfo_fetch, ("US",)),
    ConnectorEntry("courtlistener_search", courtlistener_search, ("US",)),
    ConnectorEntry("courtlistener_fetch", courtlistener_fetch, ("US",)),
    ConnectorEntry("eurlex_search", eurlex_search, ("EU",)),
    ConnectorEntry("eurlex_fetch", eurlex_fetch, ("EU",)),
    ConnectorEntry("flk_npc_search", flk_npc_search, ("CN",)),
    ConnectorEntry("flk_npc_fetch", flk_npc_fetch, ("CN",)),
    ConnectorEntry("caac_local_search", caac_local_search, ("CN",), ("aviation",)),
    ConnectorEntry("caac_local_fetch", caac_local_fetch, ("CN",), ("aviation",)),
    ConnectorEntry("easa_ad_search", easa_ad_search, ("EU",), ("aviation",)),
    ConnectorEntry("easa_ad_fetch", easa_ad_fetch, ("EU",), ("aviation",)),
    ConnectorEntry("easa_ear_index", easa_ear_index, ("EU",), ("aviation",)),
    ConnectorEntry("faa_title14_search", faa_title14_search, ("US",), ("aviation",)),
    ConnectorEntry("drs_search", drs_search, ("US",), ("aviation",)),
    ConnectorEntry("ecaa_index", ecaa_index, ("ET",), ("aviation",)),
    ConnectorEntry("ecaa_fetch", ecaa_fetch, ("ET",), ("aviation",)),
    ConnectorEntry("ethiopia_law_search", ethiopia_law_search, ("ET",)),
    ConnectorEntry("ethiopia_law_fetch", ethiopia_law_fetch, ("ET",)),
)


def filter_for(
    jurisdiction: str,
    domain_packs: Iterable[str] = (),
) -> list[ConnectorEntry]:
    """Return the connectors that apply to ``jurisdiction`` and the active ``domain_packs``."""
    packs = frozenset(domain_packs)
    visible: list[ConnectorEntry] = []
    for entry in REGISTRY:
        if jurisdiction not in entry.jurisdiction:
            continue
        if entry.domain_packs and not (packs & set(entry.domain_packs)):
            continue
        visible.append(entry)
    return visible


__all__ = [
    "ConnectorEntry",
    "REGISTRY",
    "filter_for",
    "caac_local_fetch",
    "caac_local_search",
    "courtlistener_fetch",
    "courtlistener_search",
    "cth_legislation_fetch",
    "cth_legislation_search",
    "drs_search",
    "easa_ad_fetch",
    "easa_ad_search",
    "easa_ear_index",
    "ecaa_fetch",
    "ecaa_index",
    "ecfr_fetch",
    "ecfr_search",
    "ethiopia_law_fetch",
    "ethiopia_law_search",
    "eurlex_fetch",
    "eurlex_search",
    "faa_title14_search",
    "federal_register_fetch",
    "federal_register_search",
    "flk_npc_fetch",
    "flk_npc_search",
    "govinfo_fetch",
    "govinfo_search",
    "hca_judgment_fetch",
    "hca_judgment_search",
    "qld_caselaw_fetch",
    "qld_caselaw_search",
    "qld_legislation_fetch",
    "qld_legislation_search",
]
