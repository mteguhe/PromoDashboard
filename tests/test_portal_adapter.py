import pytest
from unittest.mock import patch, MagicMock
from scraper.adapters.portal_adapter import PortalAdapter

MOCK_SOURCES = [
    {
        "name": "TestPortal",
        "url": "https://testportal.com/promo",
        "category": "fashion",
        "selector": ".promo-card",
    }
]

@patch("scraper.adapters.portal_adapter.requests.get")
def test_fetch_returns_standard_shape(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b"""
        <html><body>
        <div class="promo-card"><a href="/promo/1">Diskon 50% Fashion Week</a></div>
        </body></html>
    """
    mock_get.return_value = mock_resp

    adapter = PortalAdapter(MOCK_SOURCES)
    results = adapter.fetch()

    assert len(results) == 1
    item = results[0]
    assert item["category"] == "fashion"
    assert item["source_platform"] == "TestPortal"
    assert "title" in item
    assert "source_url" in item
    assert "promo_code" in item
    assert "discount_value" in item
    assert "expired_date" in item

@patch("scraper.adapters.portal_adapter.requests.get")
def test_fetch_resolves_relative_url(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b"""
        <html><body>
        <div class="promo-card"><a href="/deals/summer">Summer Sale</a></div>
        </body></html>
    """
    mock_get.return_value = mock_resp

    adapter = PortalAdapter(MOCK_SOURCES)
    results = adapter.fetch()

    assert results[0]["source_url"] == "https://testportal.com/deals/summer"

@patch("scraper.adapters.portal_adapter.requests.get")
def test_fetch_skips_on_http_error(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_get.return_value = mock_resp

    adapter = PortalAdapter(MOCK_SOURCES)
    results = adapter.fetch()
    assert results == []

@patch("scraper.adapters.portal_adapter.requests.get")
def test_fetch_skips_on_network_error(mock_get):
    mock_get.side_effect = Exception("Connection refused")
    adapter = PortalAdapter(MOCK_SOURCES)
    results = adapter.fetch()
    assert results == []

@patch("scraper.adapters.portal_adapter.requests.get")
def test_fetch_returns_empty_when_no_selector_match(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b"<html><body><p>No promo cards here</p></body></html>"
    mock_get.return_value = mock_resp

    adapter = PortalAdapter(MOCK_SOURCES)
    results = adapter.fetch()
    assert results == []
