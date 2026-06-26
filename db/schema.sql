CREATE TABLE IF NOT EXISTS flight_promos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    airline VARCHAR(100),
    origin_city VARCHAR(100),
    destination_city VARCHAR(100),
    promo_code VARCHAR(50),
    discount_value VARCHAR(100),
    terms_and_conditions TEXT,
    source_platform VARCHAR(50),
    source_url TEXT UNIQUE,
    expired_date DATE,
    created_at TIMESTAMP DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    scraped_at TIMESTAMP DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS food_promos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    brand_name VARCHAR(100),
    category VARCHAR(100),
    min_transaction VARCHAR(100),
    promo_code VARCHAR(50),
    discount_value VARCHAR(100),
    terms_and_conditions TEXT,
    locations VARCHAR(255),
    source_platform VARCHAR(50),
    source_url TEXT UNIQUE,
    expired_date DATE,
    created_at TIMESTAMP DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    scraped_at TIMESTAMP DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_flight_promos_created_at ON flight_promos(created_at);
CREATE INDEX IF NOT EXISTS idx_food_promos_created_at ON food_promos(created_at);

