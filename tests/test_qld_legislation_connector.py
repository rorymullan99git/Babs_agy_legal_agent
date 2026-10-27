"""Tests for Queensland Legislation connector (fixture tests + opt-in live test)."""

from __future__ import annotations

import os
from unittest.mock import MagicMock

import httpx
import pytest

from legal_helper.citations.groundedness import roundtrip_quote
from legal_helper.connectors import filter_for
from legal_helper.connectors.qld_legislation import (
    KNOWN_QLD_ACTS,
    qld_legislation_fetch,
    qld_legislation_search,
)


_RECORDED_CRIMINAL_CODE_HTML = """<!doctype html>
<html>
<head><title>Criminal Code Act 1899 - Queensland Legislation</title></head>
<body>
<h1>Criminal Code Act 1899</h1>
<p>An Act to establish a Code of Criminal Law</p>
<div id="sch.1">
  <h2>Schedule 1 - The Criminal Code</h2>
  <div id="sec.23-container">
    <a name="sch.1-sec.23"></a>
    <p><b>23 Intention-motive</b></p>
    <p>(1) Subject to the express provisions of this Code relating to negligent acts and omissions, a person is not criminally responsible for-</p>
    <p>(a) an act or omission that occurs independently of the exercise of the person's will; or</p>
    <p>(b) an event that the person does not intend or foresee as a possible consequence.</p>
  </div>
  <div id="sec.24-container">
    <a name="sch.1-sec.24"></a>
    <p><b>24 Mistake of fact</b></p>
    <p>(1) A person who does or omits to do an act under an honest and reasonable, but mistaken, belief in the existence of any state of things is not criminally responsible.</p>
  </div>
</div>
</body>
</html>
"""


def test_qld_connector_registered_under_au() -> None:
    entries = filter_for("AU")
    names = [e.name for e in entries]
    assert "qld_legislation_fetch" in names
    assert "qld_legislation_search" in names


def test_qld_legislation_search() -> None:
    res = qld_legislation_search("criminal code")
    assert res["count"] >= 1
    assert any("Criminal Code" in r["title"] for r in res["results"])
    assert res["results"][0]["act_slug"] == "act-1899-009"


def test_qld_legislation_fetch_with_fixture() -> None:
    mock_resp = httpx.Response(
        status_code=200,
        html=_RECORDED_CRIMINAL_CODE_HTML,
        request=httpx.Request("GET", "https://www.legislation.qld.gov.au/view/whole/html/inforce/current/act-1899-009"),
    )
    mock_client = MagicMock()
    mock_client.get.return_value = mock_resp

    res = qld_legislation_fetch("act-1899-009", as_at="current", section="23", client=mock_client)
    assert res["status"] == "in_force"
    assert res["pinpoint_unavailable"] is False
    assert "23 Intention-motive" in res["text"]
    assert "independently of the exercise of the person's will" in res["text"]

    # Round-trip quote test on fixture
    quote = "an act or omission that occurs independently of the exercise of the person's will"
    rt = roundtrip_quote(quote, res["text"])
    assert rt.status == "exact"


def test_qld_legislation_fetch_missing_section() -> None:
    mock_resp = httpx.Response(
        status_code=200,
        html=_RECORDED_CRIMINAL_CODE_HTML,
        request=httpx.Request("GET", "https://www.legislation.qld.gov.au/view/whole/html/inforce/current/act-1899-009"),
    )
    mock_client = MagicMock()
    mock_client.get.return_value = mock_resp

    res = qld_legislation_fetch("act-1899-009", as_at="current", section="999", client=mock_client)
    assert res["pinpoint_unavailable"] is True
    assert res["text"] == ""


def test_qld_legislation_offline_error_handling() -> None:
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.ConnectError("Network unreachable")

    res = qld_legislation_fetch("act-1899-009", as_at="current", section="23", client=mock_client)
    assert res["status"] == "unverified"
    assert res["pinpoint_unavailable"] is True
    assert "connector error" in res["reason"]


@pytest.mark.live
def test_live_qld_legislation_criminal_code_s23() -> None:
    # Opt-in live test: run when LEGAL_HELPER_LIVE=1
    if os.environ.get("LEGAL_HELPER_LIVE") != "1":
        pytest.skip("Skipping live test by default. Set LEGAL_HELPER_LIVE=1 to run.")

    res = qld_legislation_fetch("act-1899-009", as_at="current", section="23")
    assert res["status"] == "in_force"
    assert not res["pinpoint_unavailable"]
    assert res["text"]

    # Round-trip quote from Criminal Code s 23(1)(a)
    quote = "an act or omission that occurs independently of the exercise of the person's will"
    rt = roundtrip_quote(quote, res["text"])
    assert rt.status in ("exact", "near"), f"Quote failed to roundtrip: {rt}"
