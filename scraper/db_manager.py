import sqlite3
from datetime import datetime, timezone

class DatabaseManager:
    def __init__(self, db_path="promo.db"):
        self.conn = sqlite3.connect(db_path, timeout=30.0)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.row_factory = sqlite3.Row

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def insert_flight_promo(self, data):
        if not isinstance(data, dict):
            data = {}
        cursor = self.conn.cursor()
        query = """
        INSERT OR IGNORE INTO flight_promos (
            title, description, airline, origin_city, destination_city,
            promo_code, discount_value, terms_and_conditions,
            source_platform, source_url, expired_date, scraped_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        cursor.execute(query, (
            data.get("title"),
            data.get("description"),
            data.get("airline"),
            data.get("origin_city"),
            data.get("destination_city"),
            data.get("promo_code"),
            data.get("discount_value"),
            data.get("terms_and_conditions"),
            data.get("source_platform"),
            data.get("source_url"),
            data.get("expired_date"),
            now
        ))
        self.conn.commit()

    def insert_food_promo(self, data):
        if not isinstance(data, dict):
            data = {}
        cursor = self.conn.cursor()
        query = """
        INSERT OR IGNORE INTO food_promos (
            title, description, brand_name, category, min_transaction,
            promo_code, discount_value, terms_and_conditions, locations,
            source_platform, source_url, expired_date, scraped_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        cursor.execute(query, (
            data.get("title"),
            data.get("description"),
            data.get("brand_name"),
            data.get("category"),
            data.get("min_transaction"),
            data.get("promo_code"),
            data.get("discount_value"),
            data.get("terms_and_conditions"),
            data.get("locations"),
            data.get("source_platform"),
            data.get("source_url"),
            data.get("expired_date"),
            now
        ))
        self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None


