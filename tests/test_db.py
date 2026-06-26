import os
import sqlite3
import pytest
from db.init_db import init_database

DB_FILE = "test_promo.db"

def setup_function():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

def teardown_function():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

def test_database_initialization():
    init_database(DB_FILE)
    assert os.path.exists(DB_FILE)
    
    conn = sqlite3.connect(DB_FILE)
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
    
    conn.close()
