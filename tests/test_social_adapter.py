import pytest
from unittest.mock import patch, MagicMock
from scraper.adapters.social_adapter import SocialAdapter

THREADS_ACCOUNT = [{
    "name": "PromoHunter",
    "url": "https://www.threads.com/@thepromohunter2",
    "category": "flight",
    "platform": "threads",
    "selector": "",
}]

TIKTOK_ACCOUNT = [{
    "name": "BrandTikTok",
    "url": "https://www.tiktok.com/@brand/video/123456",
    "category": "food",
    "platform": "tiktok",
    "selector": "",
}]

INSTAGRAM_ACCOUNT = [{
    "name": "BrandIG",
    "url": "https://www.instagram.com/brandpromo/",
    "category": "fashion",
    "platform": "instagram",
    "selector": ".post-text",
}]


def _make_playwright_mock(posts: list[dict]):
    """Mock sync_playwright for Threads scraping."""
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
    mock_page.keyboard = MagicMock()
    mock_page.evaluate.return_value = posts

    return mock_cm


def test_fetch_threads_standard_shape():
    posts = [
        {"text": "Indo Bangkok 990ribu November 2026 LCC", "href": "https://www.threads.com/@thepromohunter2/post/abc123"},
    ]
    mock_cm = _make_playwright_mock(posts)
    with patch("scraper.adapters.social_adapter.sync_playwright", return_value=mock_cm):
        adapter = SocialAdapter(THREADS_ACCOUNT)
        results = adapter.fetch()

    assert len(results) == 1
    item = results[0]
    required_keys = {
        "title", "description", "category", "brand_name",
        "promo_code", "discount_value", "min_transaction",
        "expired_date", "source_platform", "source_url",
    }
    assert required_keys == set(item.keys())
    assert item["source_platform"] == "Threads"
    assert item["category"] == "flight"
    assert "thepromohunter2/post/abc123" in item["source_url"]


def test_fetch_threads_uses_post_permalink():
    posts = [
        {"text": "Jakarta Seoul 1,6juta direct flight promo", "href": "https://www.threads.com/@thepromohunter2/post/xyz999"},
    ]
    mock_cm = _make_playwright_mock(posts)
    with patch("scraper.adapters.social_adapter.sync_playwright", return_value=mock_cm):
        adapter = SocialAdapter(THREADS_ACCOUNT)
        results = adapter.fetch()

    assert results[0]["source_url"] == "https://www.threads.com/@thepromohunter2/post/xyz999"


def test_fetch_threads_skips_short_posts():
    posts = [{"text": "ok", "href": ""}, {"text": "x", "href": ""}]
    mock_cm = _make_playwright_mock(posts)
    with patch("scraper.adapters.social_adapter.sync_playwright", return_value=mock_cm):
        adapter = SocialAdapter(THREADS_ACCOUNT)
        results = adapter.fetch()

    assert results == []


def test_fetch_threads_playwright_error_returns_empty():
    mock_cm = MagicMock()
    mock_cm.__enter__ = MagicMock(side_effect=Exception("browser crashed"))
    mock_cm.__exit__ = MagicMock(return_value=False)
    with patch("scraper.adapters.social_adapter.sync_playwright", return_value=mock_cm):
        adapter = SocialAdapter(THREADS_ACCOUNT)
        results = adapter.fetch()

    assert results == []


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
    assert results[0]["source_platform"] == "TikTok"
