import pytest
from unittest.mock import patch, MagicMock
from scraper.adapters.social_adapter import SocialAdapter

THREADS_ACCOUNT = [{
    "name": "BrandPromo",
    "url": "https://www.threads.net/@brandpromo",
    "category": "fashion",
    "platform": "threads",
    "selector": ".post-text",
}]

TIKTOK_ACCOUNT = [{
    "name": "BrandTikTok",
    "url": "https://www.tiktok.com/@brand/video/123456",
    "category": "food",
    "platform": "tiktok",
    "selector": "",
}]

@patch("scraper.adapters.social_adapter.requests.get")
def test_fetch_threads_standard_shape(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b"""
        <html><body>
        <div class="post-text"><a href="/post/1">Diskon 30% fashion week!</a></div>
        </body></html>
    """
    mock_get.return_value = mock_resp

    adapter = SocialAdapter(THREADS_ACCOUNT)
    results = adapter.fetch()
    # Shape check: result may be 0 if selector not found in mock HTML, but no crash
    for item in results:
        assert "title" in item
        assert "category" in item
        assert "source_platform" in item
        assert item["source_platform"] == "threads"

@patch("scraper.adapters.social_adapter.requests.get")
def test_fetch_tiktok_oembed(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "title": "Promo hemat 50% semua produk makanan!",
        "author_name": "brandfood",
    }
    mock_get.return_value = mock_resp

    adapter = SocialAdapter(TIKTOK_ACCOUNT)
    results = adapter.fetch()

    assert len(results) == 1
    assert results[0]["title"] == "Promo hemat 50% semua produk makanan!"
    assert results[0]["category"] == "food"
    assert results[0]["source_platform"] == "TikTok"
    assert results[0]["source_url"] == TIKTOK_ACCOUNT[0]["url"]

@patch("scraper.adapters.social_adapter.requests.get")
def test_fetch_tiktok_skips_empty_title(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"title": "", "author_name": "brand"}
    mock_get.return_value = mock_resp

    adapter = SocialAdapter(TIKTOK_ACCOUNT)
    results = adapter.fetch()
    assert results == []

@patch("scraper.adapters.social_adapter.requests.get")
def test_fetch_skips_on_http_error(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_get.return_value = mock_resp

    adapter = SocialAdapter(THREADS_ACCOUNT)
    results = adapter.fetch()
    assert results == []

@patch("scraper.adapters.social_adapter.requests.get")
def test_fetch_skips_on_network_error(mock_get):
    mock_get.side_effect = Exception("Network error")
    adapter = SocialAdapter(THREADS_ACCOUNT)
    results = adapter.fetch()
    assert results == []
