import sqlite3
from datetime import datetime, timezone

class DatabaseManager:
    def __init__(self, db_path: str = "promo.db"):
        self.conn = sqlite3.connect(db_path, timeout=30.0)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.row_factory = sqlite3.Row

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def url_exists(self, source_url: str) -> bool:
        cur = self.conn.cursor()
        cur.execute("SELECT 1 FROM promos WHERE source_url=?", (source_url,))
        return cur.fetchone() is not None

    def insert_promo(self, data: dict) -> None:
        if not isinstance(data, dict):
            return
        now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        self.conn.execute("""
            INSERT OR IGNORE INTO promos (
                category, title, description, brand_name, promo_code,
                discount_value, min_transaction, expired_date,
                source_platform, source_url, scraped_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("category"),
            data.get("title"),
            data.get("description"),
            data.get("brand_name"),
            data.get("promo_code"),
            data.get("discount_value"),
            data.get("min_transaction"),
            data.get("expired_date"),
            data.get("source_platform"),
            data.get("source_url"),
            now,
        ))
        self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
