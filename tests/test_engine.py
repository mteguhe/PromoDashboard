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
    
    cursor.execute("SELECT COUNT(*) FROM flight_promos")
    flights_count = cursor.fetchone()[0]
    assert flights_count > 0
    
    cursor.execute("SELECT COUNT(*) FROM food_promos")
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
    cursor.execute("SELECT brand_name, promo_code, discount_value, source_url FROM food_promos")
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == "KFC"
    assert row[1] == "KFCFEAST"
    assert row[2] == "50%"
    assert row[3] == "https://food.detik.com/kfc-promo"
    conn.close()
