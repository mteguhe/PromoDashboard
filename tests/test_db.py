import os
import sqlite3
import pytest
from db.init_db import init_database

def test_promos_table_exists(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_database(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(promos)")
    columns = [row[1] for row in cur.fetchall()]
    conn.close()
    assert "id" in columns
    assert "category" in columns
    assert "title" in columns
    assert "brand_name" in columns
    assert "source_url" in columns
    assert "scraped_at" in columns

def test_promos_indexes_exist(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_database(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = [row[0] for row in cur.fetchall()]
    conn.close()
    assert "idx_promos_category" in indexes
    assert "idx_promos_created_at" in indexes

def test_migrate_from_old_tables(tmp_path):
    db_path = str(tmp_path / "old.db")
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE flight_promos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            airline TEXT,
            promo_code TEXT,
            discount_value TEXT,
            source_url TEXT UNIQUE,
            expired_date DATE,
            source_platform TEXT,
            scraped_at TIMESTAMP,
            created_at TIMESTAMP
        );
        INSERT INTO flight_promos (title, airline, promo_code, source_url)
        VALUES ('Promo Garuda', 'Garuda Indonesia', 'GARUDA10', 'https://test.com/1');

        CREATE TABLE food_promos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            brand_name TEXT,
            category TEXT,
            promo_code TEXT,
            discount_value TEXT,
            min_transaction TEXT,
            locations TEXT,
            source_url TEXT UNIQUE,
            expired_date DATE,
            source_platform TEXT,
            scraped_at TIMESTAMP,
            created_at TIMESTAMP
        );
        INSERT INTO food_promos (title, brand_name, promo_code, source_url, category)
        VALUES ('Promo KFC', 'KFC', 'KFCHEMAT', 'https://test.com/2', 'food');
    """)
    conn.commit()
    conn.close()

    from db.migrate_to_unified import migrate
    migrate(db_path)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT category, title FROM promos ORDER BY title")
    rows = cur.fetchall()
    # Verify old tables renamed to backup
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='flight_promos_backup'")
    assert cur.fetchone() is not None
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='food_promos_backup'")
    assert cur.fetchone() is not None
    conn.close()

    assert len(rows) == 2
    assert ('flight', 'Promo Garuda') in rows
    assert ('food', 'Promo KFC') in rows
