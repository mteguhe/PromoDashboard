import pytest
from unittest.mock import patch, MagicMock
from scraper.adapters.rss_adapter import RssAdapter

MOCK_SOURCES = [{
    "name": "Test RSS",
    "url": "https://testrss.com/feed",
    "category": "food",
    "selector": ".content",
}]

@patch("scraper.adapters.rss_adapter.extract_article_text")
@patch("scraper.adapters.rss_adapter.download_page_html")
@patch("scraper.adapters.rss_adapter.fetch_rss_entries")
def test_fetch_returns_standard_shape(mock_fetch, mock_download, mock_extract):
    mock_fetch.return_value = [{
        "title": "Promo KFC Besar",
        "link": "https://testrss.com/article/1",
        "description": "Diskon 50% semua menu",
    }]
    mock_download.return_value = "<html><body>Konten artikel</body></html>"
    mock_extract.return_value = "KFC diskon 50% kode promo KFCFEAST s.d 2026-08-30"

    adapter = RssAdapter(MOCK_SOURCES)
    results = adapter.fetch()

    assert len(results) == 1
    item = results[0]
    assert item["title"] == "Promo KFC Besar"
    assert item["category"] == "food"
    assert item["source_platform"] == "RSS"
    assert item["source_url"] == "https://testrss.com/article/1"
    assert "description" in item
    assert "promo_code" in item
    assert "discount_value" in item

@patch("scraper.adapters.rss_adapter.extract_article_text")
@patch("scraper.adapters.rss_adapter.download_page_html")
@patch("scraper.adapters.rss_adapter.fetch_rss_entries")
def test_fetch_falls_back_to_rss_summary(mock_fetch, mock_download, mock_extract):
    mock_fetch.return_value = [{
        "title": "Promo Makanan",
        "link": "https://testrss.com/article/2",
        "description": "Ringkasan dari RSS",
    }]
    mock_download.return_value = None
    mock_extract.return_value = None

    adapter = RssAdapter(MOCK_SOURCES)
    results = adapter.fetch()

    assert len(results) == 1
    assert results[0]["description"] == "Ringkasan dari RSS"

@patch("scraper.adapters.rss_adapter.fetch_rss_entries")
def test_fetch_skips_entry_without_link(mock_fetch):
    mock_fetch.return_value = [{"title": "No Link Entry", "link": "", "description": ""}]
    adapter = RssAdapter(MOCK_SOURCES)
    results = adapter.fetch()
    assert results == []

@patch("scraper.adapters.rss_adapter.fetch_rss_entries")
def test_fetch_skips_on_source_error(mock_fetch):
    mock_fetch.side_effect = Exception("Connection error")
    adapter = RssAdapter(MOCK_SOURCES)
    results = adapter.fetch()
    assert results == []
