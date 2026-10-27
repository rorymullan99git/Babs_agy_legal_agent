"""Tests for Tier 1 Item 2: AU jurisdiction (Queensland default), config defaults, and playbook."""

from __future__ import annotations

from legal_helper.config import SUPPORTED_JURISDICTIONS, load_settings
from legal_helper.connectors import ConnectorEntry, filter_for
from legal_helper.skills import load_playbook, load_playbook_section
from legal_helper.tool_exposure import GROUP_DESCRIPTIONS


def test_au_jurisdiction_and_config_defaults():
    settings = load_settings(refresh=True)
    assert "AU" in SUPPORTED_JURISDICTIONS
    assert settings.default_jurisdiction == "AU"
    assert settings.default_subjurisdiction == "QLD"
    assert settings.citation_style == "aglc4"
    assert settings.enable_cite_check is True
    assert "au_law" in GROUP_DESCRIPTIONS


def test_jurisdiction_filter_isolates_au():
    au_visible = {e.name for e in filter_for(["AU"], [])}
    # CN, US, EU, ET connectors should not leak into AU-only runs
    assert "flk_npc_search" not in au_visible
    assert "ecfr_search" not in au_visible
    assert "eurlex_search" not in au_visible
    assert "ethiopia_law_search" not in au_visible

    # Dummy AU connector entry filters in when AU is requested
    dummy = ConnectorEntry("qld_dummy", lambda: None, ("AU",))
    assert "AU" in dummy.jurisdiction


def test_australian_playbook_hierarchy_and_point_in_time_rule():
    playbook = load_playbook()
    assert "\u2014" not in playbook, "No em dashes allowed in playbook doc"
    assert "Research aid, not legal advice" in playbook

    sec0 = load_playbook_section("Jurisdiction & Source Hierarchy")
    # Verify exact hierarchy order in text
    positions = [
        sec0.index("1. **Constitution**"),
        sec0.index("2. **Commonwealth statutes**"),
        sec0.index("3. **Queensland statutes and subordinate legislation**"),
        sec0.index("4. **High Court of Australia (`HCA`)**"),
        sec0.index("5. **Queensland Court of Appeal (`QCA`)**"),
        sec0.index("6. **Other courts and tribunals**"),
        sec0.index("7. **Secondary sources**"),
    ]
    assert positions == sorted(positions), "Australian source hierarchy must appear in strict order"
    assert "as in force on the date of the" in sec0
    assert "weight-labelled by court" in sec0.lower() or "court weight label" in sec0.lower()
