from unittest.mock import MagicMock, patch
from scraper.adapters.ota_adapter import OtaAdapter

SOURCE = {
    "name": "Traveloka Promo Hotel",
    "url": "https://www.traveloka.com/id-id/hotel/promotion",
    "category": "hotel",
    "platform": "Traveloka",
    "selector": "article",
    "wait_ms": 0,
}


def _make_playwright_mock(inner_texts: list, has_link: bool = False):
    """Build nested mocks for sync_playwright context manager (browser → ctx → page)."""
    mock_cm = MagicMock()
    mock_pw = MagicMock()
    mock_browser = MagicMock()
    mock_ctx = MagicMock()
    mock_page = MagicMock()

    mock_cm.__enter__ = MagicMock(return_value=mock_pw)
    mock_cm.__exit__ = MagicMock(return_value=False)
    mock_pw.chromium.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_ctx
    mock_ctx.new_page.return_value = mock_page
    mock_page.wait_for_timeout = MagicMock()

    elements = []
    for text in inner_texts:
        el = MagicMock()
        el.inner_text.return_value = text
        el.get_attribute.return_value = None  # no href on element itself
        if has_link:
            link = MagicMock()
            link.get_attribute.return_value = f"/hotel/promo/{text[:10].replace(' ', '-').lower()}"
            el.query_selector.return_value = link
        else:
            el.query_selector.return_value = None
        elements.append(el)

    mock_page.query_selector_all.return_value = elements
    return mock_cm


def test_fetch_returns_standard_shape():
    mock_cm = _make_playwright_mock(["Hotel Bintang 5 Diskon 50% kode: HOTEL50 berlaku 2026-12-31"])
    with patch("scraper.adapters.ota_adapter.sync_playwright", return_value=mock_cm):
        adapter = OtaAdapter([SOURCE])
        results = adapter.fetch()

    assert len(results) == 1
    item = results[0]
    required_keys = {
        "title", "description", "category", "brand_name",
        "promo_code", "discount_value", "min_transaction",
        "expired_date", "source_platform", "source_url",
    }
    assert required_keys == set(item.keys())
    assert item["category"] == "hotel"
    assert item["source_platform"] == "Traveloka"


def test_fetch_uses_card_link_as_source_url():
    mock_cm = _make_playwright_mock(["Promo Hotel Diskon 30%"], has_link=True)
    with patch("scraper.adapters.ota_adapter.sync_playwright", return_value=mock_cm):
        adapter = OtaAdapter([SOURCE])
        results = adapter.fetch()

    assert len(results) == 1
    assert "traveloka.com" in results[0]["source_url"]


def test_fetch_skips_on_selector_timeout():
    from playwright.sync_api import TimeoutError as PlaywrightTimeout
    mock_cm = MagicMock()
    mock_pw = MagicMock()
    mock_browser = MagicMock()
    mock_ctx = MagicMock()
    mock_page = MagicMock()

    mock_cm.__enter__ = MagicMock(return_value=mock_pw)
    mock_cm.__exit__ = MagicMock(return_value=False)
    mock_pw.chromium.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_ctx
    mock_ctx.new_page.return_value = mock_page
    mock_page.wait_for_timeout = MagicMock()
    mock_page.wait_for_selector.side_effect = PlaywrightTimeout("timeout")

    with patch("scraper.adapters.ota_adapter.sync_playwright", return_value=mock_cm):
        adapter = OtaAdapter([SOURCE])
        results = adapter.fetch()

    assert results == []


def test_fetch_skips_empty_text_elements():
    mock_cm = _make_playwright_mock(["", "   ", "x"])  # all too short
    with patch("scraper.adapters.ota_adapter.sync_playwright", return_value=mock_cm):
        adapter = OtaAdapter([SOURCE])
        results = adapter.fetch()

    assert results == []


def test_fetch_handles_browser_launch_error():
    mock_cm = MagicMock()
    mock_cm.__enter__ = MagicMock(side_effect=Exception("browser not found"))
    mock_cm.__exit__ = MagicMock(return_value=False)

    with patch("scraper.adapters.ota_adapter.sync_playwright", return_value=mock_cm):
        adapter = OtaAdapter([SOURCE])
        results = adapter.fetch()

    assert results == []
