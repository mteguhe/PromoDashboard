# filepath: tests/test_config.py
from scraper.config import FEED_SOURCES

def test_feed_sources_config():
    assert len(FEED_SOURCES) >= 2
    
    # Pastikan terdapat feed penerbangan dan makanan
    categories = [feed["category"] for feed in FEED_SOURCES]
    assert "flight" in categories
    assert "food" in categories
    
    for feed in FEED_SOURCES:
        assert "url" in feed
        assert "selector" in feed
        assert feed["url"].startswith("http")
