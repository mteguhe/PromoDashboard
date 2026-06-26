import os
import sqlite3
import pytest
from db.init_db import init_database

def test_database_initialization(tmp_path):
    db_file = tmp_path / "test_promo.db"
    db_path = str(db_file)
    
    init_database(db_path)
    assert os.path.exists(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verifikasi tabel flight_promos
    cursor.execute("PRAGMA table_info(flight_promos)")
    columns = [row[1] for row in cursor.fetchall()]
    assert "id" in columns
    assert "title" in columns
    assert "terms_and_conditions" in columns
    
    # Verifikasi tabel food_promos
    cursor.execute("PRAGMA table_info(food_promos)")
    columns_food = [row[1] for row in cursor.fetchall()]
    assert "id" in columns_food
    assert "brand_name" in columns_food
    assert "terms_and_conditions" in columns_food
    
    # Verifikasi keberadaan index yang baru ditambahkan
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = [row[0] for row in cursor.fetchall()]
    assert "idx_flight_promos_created_at" in indexes
    assert "idx_food_promos_created_at" in indexes
    
    conn.close()
