"""Tests for Queensland Courts, Commonwealth Legislation, and High Court judgments connectors."""

from __future__ import annotations

import os
from unittest.mock import MagicMock

import httpx
import pytest

from legal_helper.connectors import filter_for
from legal_helper.connectors.cth_legislation import (
    cth_legislation_fetch,
    cth_legislation_search,
)
from legal_helper.connectors.hca_judgments import (
    hca_judgment_fetch,
    hca_judgment_search,
)
from legal_helper.connectors.qld_caselaw import (
    qld_caselaw_fetch,
    qld_caselaw_search,
)


_FIXTURE_QCA_HTML = """<!doctype html>
<html>
<head><title>R v Baden-Clay [2015] QCA 265</title></head>
<body>
<article class="judgment">
  <h1>R v Baden-Clay</h1>
  <div class="citation">[2015] QCA 265</div>
  <p>[45] The jury was entitled to infer intent to kill or do grievous bodily harm from the respondent's post-offence conduct.</p>
  <p>[46] The appeal is allowed and conviction for manslaughter substituted.</p>
</article>
</body>
</html>
"""

_FIXTURE_HCA_HTML = """<!doctype html>
<html>
<head><title>R v Baden-Clay [2016] HCA 35</title></head>
<body>
<article id="judgment">
  <h1>R v Baden-Clay</h1>
  <div class="citation">[2016] HCA 35</div>
  <p>[45] There was no evidence at trial to support a hypothesis of accidental death.</p>
  <p>[46] The jury's verdict of murder was reasonable and open on the evidence.</p>
</article>
</body>
</html>
"""

_FIXTURE_CTH_LEG_HTML = """<!doctype html>
<html>
<head><title>Corporations Act 2001 - Federal Register of Legislation</title></head>
<body>
<main id="content">
  <h1>Corporations Act 2001</h1>
  <p>Section 180 Care and diligence - civil obligation only</p>
  <p>(1) A director or other officer of a corporation must exercise their powers and discharge their duties with the degree of care and diligence that a reasonable person would exercise.</p>
</main>
</body>
</html>
"""


def test_au_connectors_registered() -> None:
    entries = filter_for("AU")
    names = {e.name for e in entries}
    assert "qld_legislation_fetch" in names
    assert "qld_caselaw_fetch" in names
    assert "cth_legislation_fetch" in names
    assert "hca_judgment_fetch" in names


def test_qld_caselaw_fixture_and_pinpoint() -> None:
    mock_resp = httpx.Response(status_code=200, html=_FIXTURE_QCA_HTML, request=httpx.Request("GET", "http://test"))
    mock_client = MagicMock()
    mock_client.get.return_value = mock_resp

    res = qld_caselaw_fetch("[2015] QCA 265", paragraph="45", client=mock_client)
    assert res["status"] == "verified online"
    assert not res["pinpoint_unavailable"]
    assert "[45]" in res["text"]
    assert "post-offence conduct" in res["text"]


def test_hca_judgment_fixture_and_pinpoint() -> None:
    mock_resp = httpx.Response(status_code=200, html=_FIXTURE_HCA_HTML, request=httpx.Request("GET", "http://test"))
    mock_client = MagicMock()
    mock_client.get.return_value = mock_resp

    res = hca_judgment_fetch(2016, 35, paragraph="45", client=mock_client)
    assert res["status"] == "verified online"
    assert res["court_weight"] == "binding"
    assert "no evidence at trial" in res["text"]


def test_cth_legislation_fixture_and_pinpoint() -> None:
    mock_resp = httpx.Response(status_code=200, html=_FIXTURE_CTH_LEG_HTML, request=httpx.Request("GET", "http://test"))
    mock_client = MagicMock()
    mock_client.get.return_value = mock_resp

    res = cth_legislation_fetch("Corporations Act 2001", section="180", client=mock_client)
    assert res["status"] == "in_force"
    assert "Care and diligence" in res["text"]


@pytest.mark.live
def test_live_qld_caselaw() -> None:
    if os.environ.get("LEGAL_HELPER_LIVE") != "1":
        pytest.skip("Skipping live test by default")
    res = qld_caselaw_search("murder", limit=2)
    assert res["status"] in ("ok", "error")


@pytest.mark.live
def test_live_cth_legislation() -> None:
    if os.environ.get("LEGAL_HELPER_LIVE") != "1":
        pytest.skip("Skipping live test by default")
    res = cth_legislation_search("corporations", limit=2)
    assert res["count"] >= 1
