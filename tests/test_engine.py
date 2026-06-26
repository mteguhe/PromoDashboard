import os
import sqlite3
import pytest
from db.init_db import init_database
from scraper.engine import run_scraping_job

DB_FILE = "test_engine.db"

def setup_function():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    init_database(DB_FILE)

def teardown_function():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

def test_run_scraping_job():
    # Jalankan parser mock di engine
    run_scraping_job(DB_FILE, use_mock_source=True)
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM flight_promos")
    flights_count = cursor.fetchone()[0]
    assert flights_count > 0
    
    cursor.execute("SELECT COUNT(*) FROM food_promos")
    foods_count = cursor.fetchone()[0]
    assert foods_count > 0
    
    conn.close()
