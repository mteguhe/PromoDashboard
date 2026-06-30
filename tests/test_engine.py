import sqlite3
import pytest
from unittest.mock import patch, MagicMock
from db.init_db import init_database
from scraper.engine import run_scraping_job

@pytest.fixture
def fresh_db(tmp_path):
    db_path = str(tmp_path / "test_engine.db")
    init_database(db_path)
    return db_path

def test_run_mock_job_inserts_promos(fresh_db):
    run_scraping_job(fresh_db, use_mock_source=True)
    conn = sqlite3.connect(fresh_db)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM promos")
    count = cur.fetchone()[0]
    conn.close()
    assert count > 0

@patch("scraper.engine.RssAdapter")
@patch("scraper.engine.SocialAdapter")
@patch("scraper.engine.PortalAdapter")
def test_real_job_calls_all_adapters(mock_portal, mock_social, mock_rss, fresh_db):
    mock_portal.return_value.fetch.return_value = []
    mock_social.return_value.fetch.return_value = []
    mock_rss.return_value.fetch.return_value = []

    run_scraping_job(fresh_db, use_mock_source=False)

    mock_portal.return_value.fetch.assert_called_once()
    mock_social.return_value.fetch.assert_called_once()
    mock_rss.return_value.fetch.assert_called_once()

@patch("scraper.engine.parse_promo_text")
@patch("scraper.engine.RssAdapter")
@patch("scraper.engine.SocialAdapter")
@patch("scraper.engine.PortalAdapter")
def test_real_job_inserts_valid_promo(mock_portal, mock_social, mock_rss, mock_parse, fresh_db):
    mock_portal.return_value.fetch.return_value = [{
        "title": "KFC Diskon 50%",
        "description": "KFC diskon 50% kode promo KFCFEAST s.d 2026-08-30",
        "category": "food",
        "brand_name": "KFC",
        "source_platform": "GoFood Promo",
        "source_url": "https://gofood.co.id/promo/kfc-1",
        "promo_code": None,
        "discount_value": None,
        "min_transaction": None,
        "expired_date": None,
    }]
    mock_social.return_value.fetch.return_value = []
    mock_rss.return_value.fetch.return_value = []
    mock_parse.return_value = {
        "promo_code": "KFCFEAST",
        "discount_value": "50%",
        "expired_date": "2026-08-30",
        "brand_name": "KFC",
        "category": "food",
    }

    run_scraping_job(fresh_db, use_mock_source=False)

    conn = sqlite3.connect(fresh_db)
    cur = conn.cursor()
    cur.execute("SELECT promo_code, discount_value FROM promos WHERE source_url=?",
                ("https://gofood.co.id/promo/kfc-1",))
    row = cur.fetchone()
    conn.close()
    assert row is not None
    assert row[0] == "KFCFEAST"
    assert row[1] == "50%"

@patch("scraper.engine.RssAdapter")
@patch("scraper.engine.SocialAdapter")
@patch("scraper.engine.PortalAdapter")
def test_real_job_skips_duplicate_url(mock_portal, mock_social, mock_rss, fresh_db):
    item = {
        "title": "Promo Zalora",
        "description": "Sale 70% off",
        "category": "fashion",
        "brand_name": "Zalora",
        "source_platform": "Zalora Sale",
        "source_url": "https://zalora.co.id/sale/1",
        "promo_code": "SALE70",
        "discount_value": "70%",
        "min_transaction": None,
        "expired_date": "2026-09-01",
    }
    mock_portal.return_value.fetch.return_value = [item, item]
    mock_social.return_value.fetch.return_value = []
    mock_rss.return_value.fetch.return_value = []

    run_scraping_job(fresh_db, use_mock_source=False)

    conn = sqlite3.connect(fresh_db)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM promos WHERE source_url=?", (item["source_url"],))
    assert cur.fetchone()[0] == 1
    conn.close()

@patch("scraper.engine.validate_promo", return_value=False)
@patch("scraper.engine.RssAdapter")
@patch("scraper.engine.SocialAdapter")
@patch("scraper.engine.PortalAdapter")
def test_real_job_skips_invalid_promo(mock_portal, mock_social, mock_rss, mock_validate, fresh_db):
    mock_portal.return_value.fetch.return_value = [{
        "title": "Berita Umum",
        "description": "Artikel tanpa promo",
        "category": "food",
        "brand_name": None,
        "source_platform": "RSS",
        "source_url": "https://news.com/artikel-1",
        "promo_code": None,
        "discount_value": None,
        "min_transaction": None,
        "expired_date": None,
    }]
    mock_social.return_value.fetch.return_value = []
    mock_rss.return_value.fetch.return_value = []

    run_scraping_job(fresh_db, use_mock_source=False)

    conn = sqlite3.connect(fresh_db)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM promos")
    assert cur.fetchone()[0] == 0
    conn.close()
