import sqlite3
import sys

def migrate(db_path: str = "promo.db") -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS promos (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            category        TEXT NOT NULL,
            title           TEXT NOT NULL,
            description     TEXT,
            brand_name      TEXT,
            promo_code      TEXT,
            discount_value  TEXT,
            min_transaction TEXT,
            expired_date    DATE,
            source_platform TEXT,
            source_url      TEXT UNIQUE,
            scraped_at      TIMESTAMP DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
            created_at      TIMESTAMP DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
        );
        CREATE INDEX IF NOT EXISTS idx_promos_category ON promos(category);
        CREATE INDEX IF NOT EXISTS idx_promos_created_at ON promos(created_at);
    """)

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='flight_promos'")
    if cur.fetchone():
        cur.execute("""
            INSERT OR IGNORE INTO promos
                (category, title, description, brand_name, promo_code, discount_value,
                 expired_date, source_platform, source_url, scraped_at, created_at)
            SELECT 'flight', title, description, airline, promo_code, discount_value,
                   expired_date, source_platform, source_url, scraped_at, created_at
            FROM flight_promos
        """)
        cur.execute("ALTER TABLE flight_promos RENAME TO flight_promos_backup")
        print("Migrated flight_promos → promos (backup: flight_promos_backup)")

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='food_promos'")
    if cur.fetchone():
        cur.execute("""
            INSERT OR IGNORE INTO promos
                (category, title, description, brand_name, promo_code, discount_value,
                 min_transaction, expired_date, source_platform, source_url, scraped_at, created_at)
            SELECT COALESCE(category, 'food'), title, description, brand_name, promo_code,
                   discount_value, min_transaction, expired_date, source_platform, source_url,
                   scraped_at, created_at
            FROM food_promos
        """)
        cur.execute("ALTER TABLE food_promos RENAME TO food_promos_backup")
        print("Migrated food_promos → promos (backup: food_promos_backup)")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "promo.db"
    migrate(db_path)
