import pytest
from unittest.mock import patch, MagicMock
from scraper.rss_scraper import fetch_rss_entries, extract_article_text

def test_fetch_rss_entries():
    mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <item>
                <title>Promo Tiket AirAsia 2026</title>
                <link>https://travel.detik.com/promo-airasia</link>
                <description>Diskon heboh tengah tahun</description>
            </item>
        </channel>
    </rss>"""
    
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = mock_xml.encode('utf-8')
        
        entries = fetch_rss_entries("https://mock-rss-url.xml")
        assert len(entries) == 1
        assert entries[0]["title"] == "Promo Tiket AirAsia 2026"
        assert entries[0]["link"] == "https://travel.detik.com/promo-airasia"

def test_extract_article_text():
    html_content = """
    <html>
        <body>
            <div class="nav">Menu Navigasi</div>
            <article class="detail">
                <h1 class="title">Judul Promo</h1>
                <div class="detail__body-text">
                    <p>Dapatkan potongan Rp 50.000 di Starbucks!</p>
                    <script>alert('ads')</script>
                </div>
            </article>
            <div class="footer">Footer Info</div>
        </body>
    </html>
    """
    text = extract_article_text(html_content, "article.detail, .detail__body-text")
    assert "Dapatkan potongan" in text
    assert "Menu Navigasi" not in text
    assert "alert" not in text

def test_extract_article_text_with_invalid_css_selector():
    html_content = """
    <html>
        <body>
            <div class="nav">Menu Navigasi</div>
            <article class="detail">
                <h1 class="title">Judul Promo</h1>
                <div class="detail__body-text">
                    <p>Dapatkan potongan Rp 50.000 di Starbucks!</p>
                </div>
            </article>
            <div class="footer">Footer Info</div>
        </body>
    </html>
    """
    # Test with None
    text_none = extract_article_text(html_content, None)
    assert "Dapatkan potongan" in text_none
    assert "Menu Navigasi" in text_none
    
    # Test with empty string
    text_empty = extract_article_text(html_content, "")
    assert "Dapatkan potongan" in text_empty
    assert "Menu Navigasi" in text_empty
    
    # Test with whitespace only
    text_whitespace = extract_article_text(html_content, "   ")
    assert "Dapatkan potongan" in text_whitespace
    assert "Menu Navigasi" in text_whitespace
