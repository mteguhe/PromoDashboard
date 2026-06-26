import os
import sqlite3
import pytest
from db.init_db import init_database
from scraper.db_manager import DatabaseManager

DB_FILE = "test_promo_mgr.db"

@pytest.fixture
def db_manager(tmp_path):
    db_file = tmp_path / DB_FILE
    init_database(str(db_file))
    mgr = DatabaseManager(str(db_file))
    yield mgr
    mgr.close()

def test_insert_flight_promo(db_manager, tmp_path):
    promo_data = {
        "title": "Diskon 20% Garuda Indonesia",
        "description": "Terbang keliling Indonesia",
        "airline": "Garuda Indonesia",
        "origin_city": "Jakarta",
        "destination_city": "Bali",
        "promo_code": "GARUDA20",
        "discount_value": "20%",
        "terms_and_conditions": "Min pembelian 2 tiket",
        "source_platform": "News",
        "source_url": "https://news.com/garuda-promo",
        "expired_date": "2026-07-31"
    }
    
    # Test insert baru
    db_manager.insert_flight_promo(promo_data)
    
    # Verifikasi data tersimpan
    db_file = tmp_path / DB_FILE
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    cursor.execute("SELECT title, promo_code, terms_and_conditions FROM flight_promos WHERE source_url=?", (promo_data["source_url"],))
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == promo_data["title"]
    assert row[1] == promo_data["promo_code"]
    assert row[2] == promo_data["terms_and_conditions"]
    conn.close()

    # Test ignore duplicate
    db_manager.insert_flight_promo(promo_data)
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM flight_promos")
    count = cursor.fetchone()[0]
    assert count == 1
    conn.close()

def test_insert_food_promo(db_manager, tmp_path):
    promo_data = {
        "title": "Diskon 50K Kopi Kenangan",
        "description": "Promo Kopi Kenangan Mantan",
        "brand_name": "Kopi Kenangan",
        "category": "Minuman",
        "min_transaction": "100000",
        "promo_code": "KENANGAN50",
        "discount_value": "50000",
        "terms_and_conditions": "Melalui aplikasi Kopi Kenangan",
        "locations": "Jakarta, Bandung",
        "source_platform": "Instagram",
        "source_url": "https://instagram.com/p/kopi-promo",
        "expired_date": "2026-08-15"
    }
    
    # Test insert baru
    db_manager.insert_food_promo(promo_data)
    
    # Verifikasi data tersimpan
    db_file = tmp_path / DB_FILE
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    cursor.execute("SELECT title, brand_name, category FROM food_promos WHERE source_url=?", (promo_data["source_url"],))
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == promo_data["title"]
    assert row[1] == promo_data["brand_name"]
    assert row[2] == promo_data["category"]
    conn.close()

    # Test ignore duplicate
    db_manager.insert_food_promo(promo_data)
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM food_promos")
    count = cursor.fetchone()[0]
    assert count == 1
    conn.close()
