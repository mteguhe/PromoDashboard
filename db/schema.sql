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
