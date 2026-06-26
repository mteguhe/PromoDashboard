import sqlite3
import pytest
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

def test_run_scraping_job_real_source_not_implemented(tmp_path):
    db_file = tmp_path / DB_FILE
    init_database(str(db_file))
    
    # Jalankan engine dengan use_mock_source=False
    run_scraping_job(str(db_file), use_mock_source=False)
    
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM flight_promos")
    flights_count = cursor.fetchone()[0]
    assert flights_count == 0
    
    cursor.execute("SELECT COUNT(*) FROM food_promos")
    foods_count = cursor.fetchone()[0]
    assert foods_count == 0
    
    conn.close()

