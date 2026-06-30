import os
import sqlite3
import pytest
from unittest.mock import patch, MagicMock
from db.init_db import init_database
from scraper.engine import run_scraping_job

DB_FILE = "test_engine.db"

def test_run_scraping_job(tmp_path):
    db_file = tmp_path / DB_FILE
    init_database(str(db_file))
    
    # Jalankan parser mock di engine
    run_scraping_job(str(db_file), use_mock_source=True)
    
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM promos WHERE category = 'flight'")
    flights_count = cursor.fetchone()[0]
    assert flights_count > 0

    cursor.execute("SELECT COUNT(*) FROM promos WHERE category = 'food'")
    foods_count = cursor.fetchone()[0]
    assert foods_count > 0
    
    conn.close()


# Tambahkan pengujian baru untuk real ingestion flow
DB_INTEGRATION_FILE = "test_engine_integration.db"

def setup_function():
    if os.path.exists(DB_INTEGRATION_FILE):
        os.remove(DB_INTEGRATION_FILE)
    init_database(DB_INTEGRATION_FILE)

def teardown_function():
    if os.path.exists(DB_INTEGRATION_FILE):
        os.remove(DB_INTEGRATION_FILE)

@patch('scraper.engine.fetch_rss_entries')
@patch('scraper.engine.download_page_html')
@patch('scraper.engine.extract_article_text')
def test_run_scraping_job_real_flow(mock_extract, mock_download, mock_fetch):
    # Mock RSS entry
    mock_fetch.return_value = [
        {
            "title": "Diskon 50% KFC Akhir Pekan",
            "link": "https://food.detik.com/kfc-promo",
            "description": "KFC diskon heboh"
        }
    ]
    mock_download.return_value = "<html><body>Teks Lengkap KFC</body></html>"
    mock_extract.return_value = "KFC diskon 50% kode promo KFCFEAST s.d 2026-08-30."
    
    # Jalankan job riil (tanpa use_mock_source)
    run_scraping_job(DB_INTEGRATION_FILE, use_mock_source=False)
    
    conn = sqlite3.connect(DB_INTEGRATION_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT brand_name, promo_code, discount_value, source_url FROM promos WHERE source_url = ?",
                   ("https://food.detik.com/kfc-promo",))
    row = cursor.fetchone()
    assert row is not None
    assert row[0] is not None  # brand_name saved (actual value depends on which category parser runs first)
    assert row[1] == "KFCFEAST"
    assert row[2] == "50%"
    assert row[3] == "https://food.detik.com/kfc-promo"
    conn.close()


@patch('scraper.engine.fetch_rss_entries')
@patch('scraper.engine.download_page_html')
@patch('scraper.engine.extract_article_text')
def test_run_scraping_job_real_flow_error_handling(mock_extract, mock_download, mock_fetch):
    # Mock RSS entries: first one is malformed/raises exception (e.g. link is None or missing to cause KeyError/TypeError)
    # second one is valid.
    mock_fetch.return_value = [
        {
            # Missing "link" key entirely, which will raise KeyError when entry["link"] is accessed
            "title": "Malformed Entry",
            "description": "This should fail"
        },
        {
            "title": "Diskon 50% KFC Akhir Pekan",
            "link": "https://food.detik.com/kfc-promo",
            "description": "KFC diskon heboh"
        }
    ]
    mock_download.return_value = "<html><body>Teks Lengkap KFC</body></html>"
    mock_extract.return_value = "KFC diskon 50% kode promo KFCFEAST s.d 2026-08-30."

    # Jalankan job riil (tanpa use_mock_source)
    run_scraping_job(DB_INTEGRATION_FILE, use_mock_source=False)

    # Verify that the second entry was successfully saved, meaning the loop continued
    conn = sqlite3.connect(DB_INTEGRATION_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT brand_name, promo_code, discount_value, source_url FROM promos WHERE source_url = ?",
                   ("https://food.detik.com/kfc-promo",))
    row = cursor.fetchone()
    assert row is not None
    assert row[0] is not None  # brand_name saved (actual value depends on which category parser runs first)
    assert row[1] == "KFCFEAST"
    assert row[2] == "50%"
    assert row[3] == "https://food.detik.com/kfc-promo"
    conn.close()


@patch('scraper.engine.fetch_rss_entries')
@patch('scraper.engine.download_page_html')
@patch('scraper.engine.extract_article_text')
@patch('scraper.engine.parse_with_gemini')
@patch('scraper.engine.parse_promo_text')
def test_run_scraping_job_parser_failure_graceful_skip(
    mock_parse_promo, mock_parse_gemini, mock_extract, mock_download, mock_fetch
):
    # Setup mocks
    mock_fetch.return_value = [
        {
            "title": "Failed Promo Article",
            "link": "https://food.detik.com/failed-promo",
            "description": "This promo has no parseable content"
        }
    ]
    mock_download.return_value = "<html><body>Some text</body></html>"
    mock_extract.return_value = "Some text"
    
    # Both parsers return None
    mock_parse_gemini.return_value = None
    mock_parse_promo.return_value = None
    
    # Run scraping job - it should not raise AttributeError and should complete successfully
    run_scraping_job(DB_INTEGRATION_FILE, use_mock_source=False)
    
    # Verify that nothing was inserted into the database
    conn = sqlite3.connect(DB_INTEGRATION_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM promos")
    total_count = cursor.fetchone()[0]
    assert total_count == 0
    conn.close()

