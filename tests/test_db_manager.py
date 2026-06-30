import sqlite3
import pytest
from db.init_db import init_database
from scraper.db_manager import DatabaseManager

@pytest.fixture
def db_manager(tmp_path):
    db_file = tmp_path / "test_promo_mgr.db"
    init_database(str(db_file))
    mgr = DatabaseManager(str(db_file))
    yield mgr
    mgr.close()

def test_insert_promo_flight(db_manager, tmp_path):
    data = {
        "category": "flight",
        "title": "Diskon 20% Garuda Indonesia",
        "description": "Terbang keliling Indonesia",
        "brand_name": "Garuda Indonesia",
        "promo_code": "GARUDA20",
        "discount_value": "20%",
        "min_transaction": None,
        "source_platform": "News",
        "source_url": "https://news.com/garuda-promo",
        "expired_date": "2026-07-31",
    }
    db_manager.insert_promo(data)

    cur = db_manager.conn.cursor()
    cur.execute("SELECT title, category, promo_code FROM promos WHERE source_url=?", (data["source_url"],))
    row = cur.fetchone()
    assert row is not None
    assert row["title"] == "Diskon 20% Garuda Indonesia"
    assert row["category"] == "flight"
    assert row["promo_code"] == "GARUDA20"

def test_insert_promo_food(db_manager):
    data = {
        "category": "food",
        "title": "Diskon 50K Kopi Kenangan",
        "brand_name": "Kopi Kenangan",
        "promo_code": "KENANGAN50",
        "discount_value": "50000",
        "min_transaction": "100000",
        "source_platform": "Instagram",
        "source_url": "https://instagram.com/p/kopi-promo",
        "expired_date": "2026-08-15",
    }
    db_manager.insert_promo(data)

    cur = db_manager.conn.cursor()
    cur.execute("SELECT brand_name, category FROM promos WHERE source_url=?", (data["source_url"],))
    row = cur.fetchone()
    assert row["brand_name"] == "Kopi Kenangan"
    assert row["category"] == "food"

def test_insert_promo_deduplication(db_manager):
    data = {"category": "fashion", "title": "Zalora Sale", "source_url": "https://zalora.co.id/sale/1"}
    db_manager.insert_promo(data)
    db_manager.insert_promo(data)

    cur = db_manager.conn.cursor()
    cur.execute("SELECT COUNT(*) FROM promos WHERE source_url=?", (data["source_url"],))
    assert cur.fetchone()[0] == 1

def test_url_exists_true(db_manager):
    data = {"category": "event", "title": "Event Test", "source_url": "https://loket.com/event/1"}
    db_manager.insert_promo(data)
    assert db_manager.url_exists("https://loket.com/event/1") is True

def test_url_exists_false(db_manager):
    assert db_manager.url_exists("https://notexist.com/promo") is False

def test_insert_promo_defensive(db_manager):
    db_manager.insert_promo(None)
    db_manager.insert_promo({})
    db_manager.insert_promo([1, 2, 3])

def test_scraped_at_format(db_manager):
    data = {"category": "food", "title": "TZ Test", "source_url": "https://promo.com/tz"}
    db_manager.insert_promo(data)
    cur = db_manager.conn.cursor()
    cur.execute("SELECT scraped_at FROM promos WHERE source_url=?", (data["source_url"],))
    scraped_at = cur.fetchone()["scraped_at"]
    assert scraped_at.endswith("Z")
    assert "T" in scraped_at
    assert len(scraped_at) == 20

def test_context_manager(tmp_path):
    db_file = str(tmp_path / "ctx.db")
    init_database(db_file)
    with DatabaseManager(db_file) as mgr:
        assert mgr.conn is not None
        mgr.insert_promo({"category": "food", "title": "ctx test", "source_url": "https://ctx.com/1"})
    assert mgr.conn is None
