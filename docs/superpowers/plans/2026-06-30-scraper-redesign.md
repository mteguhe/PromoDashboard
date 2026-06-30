# Scraper Redesign — Multi-Source Adapter Pipeline: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the split-table scraper architecture with a unified `promos` table and a multi-adapter pipeline covering trusted portals, social media, and RSS.

**Architecture:** All scraped data lands in a single `promos` table (keyed by `category`). Three adapter modules (Portal, Social, RSS) each implement `BaseAdapter.fetch()` and return a standard dict shape. The engine iterates adapters, parses with Gemini→regex, validates with `validate_promo()`, then inserts.

**Tech Stack:** Python 3, SQLite, `requests`, `feedparser`, `beautifulsoup4`, `google-generativeai`, Next.js 14 (API Routes), `pytest`.

## Global Constraints

- SQLite journal mode must remain WAL.
- All timestamps stored as `YYYY-MM-DDTHH:MM:SSZ` (UTC, `strftime('%Y-%m-%dT%H:%M:%SZ', 'now')`).
- `source_url` is UNIQUE across the `promos` table — duplicates silently ignored (`INSERT OR IGNORE`).
- Valid `category` values: `flight`, `food`, `fashion`, `entertainment`, `event`.
- Gemini model: `gemini-1.5-flash`.
- Test runner: `pytest` from project root. Activate `.venv` first: `source .venv/bin/activate`.
- Existing `scraper/rss_scraper.py` is NOT deleted — `scraper/scrape_single.py` imports from it.

---

## File Map

**Created:**
- `db/migrate_to_unified.py` — copies old tables → `promos`, renames as backup
- `scraper/validator.py` — `validate_promo(parsed: dict) -> bool`
- `scraper/adapters/__init__.py` — empty package marker
- `scraper/adapters/base.py` — `BaseAdapter` ABC
- `scraper/adapters/portal_adapter.py` — HTTP GET scraper for trusted portal promo pages
- `scraper/adapters/social_adapter.py` — Threads/Instagram web scraper + TikTok oEmbed
- `scraper/adapters/rss_adapter.py` — thin wrapper over existing `rss_scraper.py` functions
- `tests/test_validator.py`
- `tests/test_portal_adapter.py`
- `tests/test_social_adapter.py`
- `tests/test_rss_adapter.py`

**Modified:**
- `db/schema.sql` — replace two category tables with unified `promos` table
- `scraper/db_manager.py` — replace `insert_flight_promo`/`insert_food_promo` with `insert_promo` + `url_exists`
- `scraper/config.py` — add `PORTAL_SOURCES` and `SOCIAL_ACCOUNTS` lists; extend `FEED_SOURCES`
- `scraper/ai_parser.py` — stricter `is_promo` gate, `confidence` field, category-aware prompt
- `scraper/engine.py` — orchestrate all three adapters; default `use_mock_source=False`
- `scraper/scrape_single.py` — use `db_mgr.insert_promo()` instead of category-branching insert
- `app/api/promos/route.js` — single `SELECT * FROM promos WHERE category=?` query
- `tests/test_db.py` — check `promos` table instead of old tables
- `tests/test_db_manager.py` — test `insert_promo` and `url_exists`
- `tests/test_engine.py` — mock new adapter interface
- `tests/test_ai_parser.py` — add `confidence` and `is_promo=false` cases

---

## Task 1: Unified DB Schema + Migration Script

**Files:**
- Modify: `db/schema.sql`
- Create: `db/migrate_to_unified.py`
- Modify: `tests/test_db.py`

**Interfaces:**
- Produces: `promos` table; `migrate(db_path: str) -> None` in `db/migrate_to_unified.py`

- [ ] **Step 1: Write the failing test**

Replace the entire content of `tests/test_db.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
source .venv/bin/activate && pytest tests/test_db.py -v
```

Expected: FAIL — `promos` table not found, `migrate` not found.

- [ ] **Step 3: Replace `db/schema.sql`**

```sql
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
```

- [ ] **Step 4: Create `db/migrate_to_unified.py`**

```python
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
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_db.py -v
```

Expected: All 3 tests PASS.

- [ ] **Step 6: Run migration on the live database**

```bash
python db/migrate_to_unified.py promo.db
```

Expected output contains: `Migrated flight_promos → promos` and `Migrated food_promos → promos`.

- [ ] **Step 7: Commit**

```bash
git add db/schema.sql db/migrate_to_unified.py tests/test_db.py
git commit -m "feat: replace split-table schema with unified promos table + migration script"
```

---

## Task 2: Update DatabaseManager

**Files:**
- Modify: `scraper/db_manager.py`
- Modify: `tests/test_db_manager.py`

**Interfaces:**
- Consumes: `promos` table (Task 1)
- Produces:
  - `DatabaseManager.insert_promo(data: dict) -> None`
  - `DatabaseManager.url_exists(source_url: str) -> bool`

- [ ] **Step 1: Write the failing tests**

Replace `tests/test_db_manager.py`:

```python
import sqlite3
import pytest
from db.init_db import init_database
from scraper.db_manager import DatabaseManager

@pytest.fixture
def db_manager(tmp_path):
    db_file = tmp_path / "test_promo_mgr.db"
    init_database(str(db_file))
    mgr = DatabaseManager(str(db_file))
    yield mgr
    mgr.close()

def test_insert_promo_flight(db_manager, tmp_path):
    data = {
        "category": "flight",
        "title": "Diskon 20% Garuda Indonesia",
        "description": "Terbang keliling Indonesia",
        "brand_name": "Garuda Indonesia",
        "promo_code": "GARUDA20",
        "discount_value": "20%",
        "min_transaction": None,
        "source_platform": "News",
        "source_url": "https://news.com/garuda-promo",
        "expired_date": "2026-07-31",
    }
    db_manager.insert_promo(data)

    cur = db_manager.conn.cursor()
    cur.execute("SELECT title, category, promo_code FROM promos WHERE source_url=?", (data["source_url"],))
    row = cur.fetchone()
    assert row is not None
    assert row["title"] == "Diskon 20% Garuda Indonesia"
    assert row["category"] == "flight"
    assert row["promo_code"] == "GARUDA20"

def test_insert_promo_food(db_manager):
    data = {
        "category": "food",
        "title": "Diskon 50K Kopi Kenangan",
        "brand_name": "Kopi Kenangan",
        "promo_code": "KENANGAN50",
        "discount_value": "50000",
        "min_transaction": "100000",
        "source_platform": "Instagram",
        "source_url": "https://instagram.com/p/kopi-promo",
        "expired_date": "2026-08-15",
    }
    db_manager.insert_promo(data)

    cur = db_manager.conn.cursor()
    cur.execute("SELECT brand_name, category FROM promos WHERE source_url=?", (data["source_url"],))
    row = cur.fetchone()
    assert row["brand_name"] == "Kopi Kenangan"
    assert row["category"] == "food"

def test_insert_promo_deduplication(db_manager):
    data = {"category": "fashion", "title": "Zalora Sale", "source_url": "https://zalora.co.id/sale/1"}
    db_manager.insert_promo(data)
    db_manager.insert_promo(data)

    cur = db_manager.conn.cursor()
    cur.execute("SELECT COUNT(*) FROM promos WHERE source_url=?", (data["source_url"],))
    assert cur.fetchone()[0] == 1

def test_url_exists_true(db_manager):
    data = {"category": "event", "title": "Event Test", "source_url": "https://loket.com/event/1"}
    db_manager.insert_promo(data)
    assert db_manager.url_exists("https://loket.com/event/1") is True

def test_url_exists_false(db_manager):
    assert db_manager.url_exists("https://notexist.com/promo") is False

def test_insert_promo_defensive(db_manager):
    db_manager.insert_promo(None)
    db_manager.insert_promo({})
    db_manager.insert_promo([1, 2, 3])

def test_scraped_at_format(db_manager):
    data = {"category": "food", "title": "TZ Test", "source_url": "https://promo.com/tz"}
    db_manager.insert_promo(data)
    cur = db_manager.conn.cursor()
    cur.execute("SELECT scraped_at FROM promos WHERE source_url=?", (data["source_url"],))
    scraped_at = cur.fetchone()["scraped_at"]
    assert scraped_at.endswith("Z")
    assert "T" in scraped_at
    assert len(scraped_at) == 20

def test_context_manager(tmp_path):
    db_file = str(tmp_path / "ctx.db")
    init_database(db_file)
    with DatabaseManager(db_file) as mgr:
        assert mgr.conn is not None
        mgr.insert_promo({"category": "food", "title": "ctx test", "source_url": "https://ctx.com/1"})
    assert mgr.conn is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_db_manager.py -v
```

Expected: FAIL — `insert_promo` and `url_exists` not found.

- [ ] **Step 3: Replace `scraper/db_manager.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_db_manager.py -v
```

Expected: All 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scraper/db_manager.py tests/test_db_manager.py
git commit -m "feat: replace insert_flight_promo/insert_food_promo with unified insert_promo + url_exists"
```

---

## Task 3: Update Frontend API and scrape_single.py

**Files:**
- Modify: `app/api/promos/route.js`
- Modify: `scraper/scrape_single.py`

**Interfaces:**
- Consumes: `promos` table (Task 1), `insert_promo` (Task 2)
- Produces: `GET /api/promos?category=<cat>&search=<q>` queries `promos` table

- [ ] **Step 1: Replace `app/api/promos/route.js`**

```javascript
import { NextResponse } from 'next/server';
import { getDbConnection } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const category = searchParams.get('category') || 'flight';
    const validCategories = ['flight', 'food', 'fashion', 'event', 'entertainment'];
    if (!validCategories.includes(category)) {
      return NextResponse.json(
        { success: false, error: `Invalid category. Must be one of: ${validCategories.join(', ')}` },
        { status: 400 }
      );
    }
    const search = searchParams.get('search') || '';
    const db = await getDbConnection();

    let query = 'SELECT * FROM promos WHERE category = ?';
    const params = [category];
    if (search) {
      query += ' AND (title LIKE ? OR description LIKE ? OR brand_name LIKE ?)';
      params.push(`%${search}%`, `%${search}%`, `%${search}%`);
    }
    query += ' ORDER BY created_at DESC';

    const promos = await db.all(query, params);
    return NextResponse.json({ success: true, data: promos });
  } catch (error) {
    console.error('API Promos Error:', error);
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
```

- [ ] **Step 2: Update `scraper/scrape_single.py` — replace category-branching DB insert**

Find this block (lines 52–56):
```python
        # Save to DB
        with DatabaseManager(db_path) as db_mgr:
            if category == "flight":
                db_mgr.insert_flight_promo(parsed)
            else:
                db_mgr.insert_food_promo(parsed)
```

Replace with:
```python
        # Save to DB
        parsed["category"] = category
        if not parsed.get("brand_name") and parsed.get("airline"):
            parsed["brand_name"] = parsed["airline"]
        with DatabaseManager(db_path) as db_mgr:
            db_mgr.insert_promo(parsed)
```

- [ ] **Step 3: Verify app still loads**

```bash
npm run dev &
sleep 3
curl -s "http://localhost:3000/api/promos?category=flight" | python3 -m json.tool | head -20
```

Expected: `{"success": true, "data": [...]}` (data may be empty or have migrated rows).

```bash
kill %1
```

- [ ] **Step 4: Commit**

```bash
git add app/api/promos/route.js scraper/scrape_single.py
git commit -m "feat: update API and scrape_single to query unified promos table"
```

---

## Task 4: Validation Gate

**Files:**
- Create: `scraper/validator.py`
- Create: `tests/test_validator.py`

**Interfaces:**
- Produces: `validate_promo(parsed: dict) -> bool`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_validator.py`:

```python
import pytest
from scraper.validator import validate_promo

def test_valid_with_promo_code():
    assert validate_promo({"title": "Promo X", "promo_code": "CODE10"}) is True

def test_valid_with_discount():
    assert validate_promo({"title": "Promo X", "discount_value": "20%"}) is True

def test_valid_with_expired_date():
    assert validate_promo({"title": "Promo X", "expired_date": "2026-12-31"}) is True

def test_valid_with_all_signals():
    assert validate_promo({
        "title": "Promo X",
        "promo_code": "ABC",
        "discount_value": "50%",
        "expired_date": "2026-09-01",
    }) is True

def test_invalid_no_title():
    assert validate_promo({"promo_code": "CODE10"}) is False

def test_invalid_empty_title():
    assert validate_promo({"title": "", "promo_code": "CODE10"}) is False

def test_invalid_no_signals():
    assert validate_promo({"title": "Artikel Berita Biasa"}) is False

def test_invalid_empty_dict():
    assert validate_promo({}) is False

def test_invalid_none():
    assert validate_promo(None) is False

def test_invalid_not_dict():
    assert validate_promo("string") is False
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_validator.py -v
```

Expected: FAIL — `scraper.validator` not found.

- [ ] **Step 3: Create `scraper/validator.py`**

```python
def validate_promo(parsed: dict) -> bool:
    if not isinstance(parsed, dict):
        return False
    if not parsed.get("title"):
        return False
    return any([
        parsed.get("promo_code"),
        parsed.get("discount_value"),
        parsed.get("expired_date"),
    ])
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_validator.py -v
```

Expected: All 10 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scraper/validator.py tests/test_validator.py
git commit -m "feat: add validate_promo gate — require title + at least one promo signal"
```

---

## Task 5: BaseAdapter + PortalAdapter

**Files:**
- Create: `scraper/adapters/__init__.py`
- Create: `scraper/adapters/base.py`
- Create: `scraper/adapters/portal_adapter.py`
- Modify: `scraper/config.py` — add `PORTAL_SOURCES`
- Create: `tests/test_portal_adapter.py`

**Interfaces:**
- Produces:
  - `BaseAdapter.fetch(self) -> list[dict]`
  - `PortalAdapter(sources: list[dict]).fetch() -> list[dict]`
  - Each dict has keys: `title`, `description`, `category`, `brand_name`, `promo_code`, `discount_value`, `min_transaction`, `expired_date`, `source_platform`, `source_url`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_portal_adapter.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from scraper.adapters.portal_adapter import PortalAdapter

MOCK_SOURCES = [
    {
        "name": "TestPortal",
        "url": "https://testportal.com/promo",
        "category": "fashion",
        "selector": ".promo-card",
    }
]

@patch("scraper.adapters.portal_adapter.requests.get")
def test_fetch_returns_standard_shape(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b"""
        <html><body>
        <div class="promo-card"><a href="/promo/1">Diskon 50% Fashion Week</a></div>
        </body></html>
    """
    mock_get.return_value = mock_resp

    adapter = PortalAdapter(MOCK_SOURCES)
    results = adapter.fetch()

    assert len(results) == 1
    item = results[0]
    assert item["category"] == "fashion"
    assert item["source_platform"] == "TestPortal"
    assert "title" in item
    assert "source_url" in item
    assert "promo_code" in item
    assert "discount_value" in item
    assert "expired_date" in item

@patch("scraper.adapters.portal_adapter.requests.get")
def test_fetch_resolves_relative_url(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b"""
        <html><body>
        <div class="promo-card"><a href="/deals/summer">Summer Sale</a></div>
        </body></html>
    """
    mock_get.return_value = mock_resp

    adapter = PortalAdapter(MOCK_SOURCES)
    results = adapter.fetch()

    assert results[0]["source_url"] == "https://testportal.com/deals/summer"

@patch("scraper.adapters.portal_adapter.requests.get")
def test_fetch_skips_on_http_error(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_get.return_value = mock_resp

    adapter = PortalAdapter(MOCK_SOURCES)
    results = adapter.fetch()
    assert results == []

@patch("scraper.adapters.portal_adapter.requests.get")
def test_fetch_skips_on_network_error(mock_get):
    mock_get.side_effect = Exception("Connection refused")
    adapter = PortalAdapter(MOCK_SOURCES)
    results = adapter.fetch()
    assert results == []

@patch("scraper.adapters.portal_adapter.requests.get")
def test_fetch_returns_empty_when_no_selector_match(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b"<html><body><p>No promo cards here</p></body></html>"
    mock_get.return_value = mock_resp

    adapter = PortalAdapter(MOCK_SOURCES)
    results = adapter.fetch()
    assert results == []
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_portal_adapter.py -v
```

Expected: FAIL — `scraper.adapters.portal_adapter` not found.

- [ ] **Step 3: Create `scraper/adapters/__init__.py`**

Empty file — just creates the package.

```python
```

- [ ] **Step 4: Create `scraper/adapters/base.py`**

```python
from abc import ABC, abstractmethod

class BaseAdapter(ABC):
    @abstractmethod
    def fetch(self) -> list[dict]:
        """Return list of promo dicts with standard shape."""
        raise NotImplementedError
```

- [ ] **Step 5: Create `scraper/adapters/portal_adapter.py`**

```python
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from scraper.adapters.base import BaseAdapter

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

class PortalAdapter(BaseAdapter):
    def __init__(self, sources: list[dict]):
        self.sources = sources

    def fetch(self) -> list[dict]:
        results = []
        for source in self.sources:
            try:
                results.extend(self._fetch_source(source))
            except Exception as e:
                print(f"[PortalAdapter] Skip {source.get('name', '?')}: {e}")
        return results

    def _fetch_source(self, source: dict) -> list[dict]:
        resp = requests.get(source["url"], headers=_HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"[PortalAdapter] {source['name']} → HTTP {resp.status_code}, skipping")
            return []
        soup = BeautifulSoup(resp.content, "html.parser")
        elements = soup.select(source["selector"])
        if not elements:
            print(f"[PortalAdapter] No elements for '{source['name']}' selector '{source['selector']}'")
            return []

        base = urlparse(source["url"])
        items = []
        for el in elements:
            title = el.get_text(strip=True)[:255]
            if not title:
                continue
            link = el.find("a")
            href = link["href"] if link and link.get("href") else source["url"]
            if href.startswith("/"):
                href = f"{base.scheme}://{base.netloc}{href}"
            items.append({
                "title": title,
                "description": title,
                "category": source["category"],
                "brand_name": source.get("name"),
                "promo_code": None,
                "discount_value": None,
                "min_transaction": None,
                "expired_date": None,
                "source_platform": source["name"],
                "source_url": href,
            })
        return items
```

- [ ] **Step 6: Add `PORTAL_SOURCES` to `scraper/config.py`**

Append to the end of the existing file:

```python
PORTAL_SOURCES = [
    {
        "name": "Traveloka Promo",
        "url": "https://www.traveloka.com/id-id/promotion",
        "category": "flight",
        "selector": "a[data-testid='promotion-card'], .promotion-card, article.promo",
    },
    {
        "name": "Tiket.com Deals",
        "url": "https://www.tiket.com/promo",
        "category": "flight",
        "selector": ".promo-card, .deal-card, article.promo-item",
    },
    {
        "name": "Zalora Sale",
        "url": "https://www.zalora.co.id/sale/",
        "category": "fashion",
        "selector": ".catalogue__list article, .product-card, .promo-item",
    },
    {
        "name": "Loket Event",
        "url": "https://www.loket.com/event",
        "category": "event",
        "selector": ".event-card, .event-item, article.event",
    },
    {
        "name": "GoFood Promo",
        "url": "https://gofood.co.id/jakarta/promo",
        "category": "food",
        "selector": ".promo-card, .promotion-card, article.promo",
    },
]
```

- [ ] **Step 7: Run tests to verify they pass**

```bash
pytest tests/test_portal_adapter.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 8: Commit**

```bash
git add scraper/adapters/__init__.py scraper/adapters/base.py scraper/adapters/portal_adapter.py scraper/config.py tests/test_portal_adapter.py
git commit -m "feat: add BaseAdapter and PortalAdapter with portal promo sources"
```

---

## Task 6: SocialAdapter

**Files:**
- Create: `scraper/adapters/social_adapter.py`
- Modify: `scraper/config.py` — add `SOCIAL_ACCOUNTS`
- Create: `tests/test_social_adapter.py`

**Interfaces:**
- Consumes: `BaseAdapter` (Task 5)
- Produces: `SocialAdapter(accounts: list[dict]).fetch() -> list[dict]`
  - Config shape: `{name, url, category, platform, selector}` where `platform` ∈ `{"threads", "instagram", "tiktok"}`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_social_adapter.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from scraper.adapters.social_adapter import SocialAdapter

THREADS_ACCOUNT = [{
    "name": "BrandPromo",
    "url": "https://www.threads.net/@brandpromo",
    "category": "fashion",
    "platform": "threads",
    "selector": ".post-text",
}]

TIKTOK_ACCOUNT = [{
    "name": "BrandTikTok",
    "url": "https://www.tiktok.com/@brand/video/123456",
    "category": "food",
    "platform": "tiktok",
    "selector": "",
}]

@patch("scraper.adapters.social_adapter.requests.get")
def test_fetch_threads_standard_shape(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b"""
        <html><body>
        <div class="post-text"><a href="/post/1">Diskon 30% fashion week!</a></div>
        </body></html>
    """
    mock_get.return_value = mock_resp

    adapter = SocialAdapter(THREADS_ACCOUNT)
    results = adapter.fetch()
    # Shape check: result may be 0 if selector not found in mock HTML, but no crash
    for item in results:
        assert "title" in item
        assert "category" in item
        assert "source_platform" in item
        assert item["source_platform"] == "threads"

@patch("scraper.adapters.social_adapter.requests.get")
def test_fetch_tiktok_oembed(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "title": "Promo hemat 50% semua produk makanan!",
        "author_name": "brandfood",
    }
    mock_get.return_value = mock_resp

    adapter = SocialAdapter(TIKTOK_ACCOUNT)
    results = adapter.fetch()

    assert len(results) == 1
    assert results[0]["title"] == "Promo hemat 50% semua produk makanan!"
    assert results[0]["category"] == "food"
    assert results[0]["source_platform"] == "TikTok"
    assert results[0]["source_url"] == TIKTOK_ACCOUNT[0]["url"]

@patch("scraper.adapters.social_adapter.requests.get")
def test_fetch_tiktok_skips_empty_title(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"title": "", "author_name": "brand"}
    mock_get.return_value = mock_resp

    adapter = SocialAdapter(TIKTOK_ACCOUNT)
    results = adapter.fetch()
    assert results == []

@patch("scraper.adapters.social_adapter.requests.get")
def test_fetch_skips_on_http_error(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_get.return_value = mock_resp

    adapter = SocialAdapter(THREADS_ACCOUNT)
    results = adapter.fetch()
    assert results == []

@patch("scraper.adapters.social_adapter.requests.get")
def test_fetch_skips_on_network_error(mock_get):
    mock_get.side_effect = Exception("Network error")
    adapter = SocialAdapter(THREADS_ACCOUNT)
    results = adapter.fetch()
    assert results == []
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_social_adapter.py -v
```

Expected: FAIL — `scraper.adapters.social_adapter` not found.

- [ ] **Step 3: Create `scraper/adapters/social_adapter.py`**

```python
import requests
from bs4 import BeautifulSoup
from scraper.adapters.base import BaseAdapter

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

class SocialAdapter(BaseAdapter):
    def __init__(self, accounts: list[dict]):
        self.accounts = accounts

    def fetch(self) -> list[dict]:
        results = []
        for account in self.accounts:
            try:
                if account["platform"] == "tiktok":
                    results.extend(self._fetch_tiktok(account))
                else:
                    results.extend(self._fetch_web(account))
            except Exception as e:
                print(f"[SocialAdapter] Skip {account.get('name', '?')}: {e}")
        return results

    def _fetch_web(self, account: dict) -> list[dict]:
        resp = requests.get(account["url"], headers=_HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"[SocialAdapter] {account['name']} → HTTP {resp.status_code}, skipping")
            return []
        soup = BeautifulSoup(resp.content, "html.parser")
        elements = soup.select(account["selector"]) if account.get("selector") else []
        items = []
        for el in elements:
            text = el.get_text(strip=True)[:500]
            if not text:
                continue
            link = el.find("a")
            source_url = link["href"] if link and link.get("href") else account["url"]
            items.append({
                "title": text[:100],
                "description": text,
                "category": account["category"],
                "brand_name": account["name"],
                "promo_code": None,
                "discount_value": None,
                "min_transaction": None,
                "expired_date": None,
                "source_platform": account["platform"],
                "source_url": source_url,
            })
        return items

    def _fetch_tiktok(self, account: dict) -> list[dict]:
        oembed_url = f"https://www.tiktok.com/oembed?url={account['url']}"
        resp = requests.get(oembed_url, headers=_HEADERS, timeout=15)
        if resp.status_code != 200:
            return []
        data = resp.json()
        title = data.get("title", "")
        if not title:
            return []
        return [{
            "title": title[:100],
            "description": title,
            "category": account["category"],
            "brand_name": account["name"],
            "promo_code": None,
            "discount_value": None,
            "min_transaction": None,
            "expired_date": None,
            "source_platform": "TikTok",
            "source_url": account["url"],
        }]
```

- [ ] **Step 4: Add `SOCIAL_ACCOUNTS` to `scraper/config.py`**

Append after `PORTAL_SOURCES`:

```python
SOCIAL_ACCOUNTS = [
    {
        "name": "Traveloka",
        "url": "https://www.threads.net/@traveloka",
        "category": "flight",
        "platform": "threads",
        "selector": "article, [data-pressable-container], .x9f619",
    },
    {
        "name": "Shopee Indonesia",
        "url": "https://www.threads.net/@shopee_id",
        "category": "food",
        "platform": "threads",
        "selector": "article, [data-pressable-container]",
    },
    {
        "name": "Zalora Indonesia",
        "url": "https://www.threads.net/@zaloraid",
        "category": "fashion",
        "platform": "threads",
        "selector": "article, [data-pressable-container]",
    },
    {
        "name": "Loket",
        "url": "https://www.threads.net/@loket.com",
        "category": "event",
        "platform": "threads",
        "selector": "article, [data-pressable-container]",
    },
]
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_social_adapter.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add scraper/adapters/social_adapter.py scraper/config.py tests/test_social_adapter.py
git commit -m "feat: add SocialAdapter for Threads and TikTok oEmbed sources"
```

---

## Task 7: RssAdapter + Extended Config

**Files:**
- Create: `scraper/adapters/rss_adapter.py`
- Modify: `scraper/config.py` — add fashion + entertainment RSS sources
- Create: `tests/test_rss_adapter.py`

**Interfaces:**
- Consumes: `BaseAdapter` (Task 5), functions from `scraper/rss_scraper.py`
- Produces: `RssAdapter(sources: list[dict]).fetch() -> list[dict]`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_rss_adapter.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from scraper.adapters.rss_adapter import RssAdapter

MOCK_SOURCES = [{
    "name": "Test RSS",
    "url": "https://testrss.com/feed",
    "category": "food",
    "selector": ".content",
}]

@patch("scraper.adapters.rss_adapter.extract_article_text")
@patch("scraper.adapters.rss_adapter.download_page_html")
@patch("scraper.adapters.rss_adapter.fetch_rss_entries")
def test_fetch_returns_standard_shape(mock_fetch, mock_download, mock_extract):
    mock_fetch.return_value = [{
        "title": "Promo KFC Besar",
        "link": "https://testrss.com/article/1",
        "description": "Diskon 50% semua menu",
    }]
    mock_download.return_value = "<html><body>Konten artikel</body></html>"
    mock_extract.return_value = "KFC diskon 50% kode promo KFCFEAST s.d 2026-08-30"

    adapter = RssAdapter(MOCK_SOURCES)
    results = adapter.fetch()

    assert len(results) == 1
    item = results[0]
    assert item["title"] == "Promo KFC Besar"
    assert item["category"] == "food"
    assert item["source_platform"] == "RSS"
    assert item["source_url"] == "https://testrss.com/article/1"
    assert "description" in item
    assert "promo_code" in item
    assert "discount_value" in item

@patch("scraper.adapters.rss_adapter.extract_article_text")
@patch("scraper.adapters.rss_adapter.download_page_html")
@patch("scraper.adapters.rss_adapter.fetch_rss_entries")
def test_fetch_falls_back_to_rss_summary(mock_fetch, mock_download, mock_extract):
    mock_fetch.return_value = [{
        "title": "Promo Makanan",
        "link": "https://testrss.com/article/2",
        "description": "Ringkasan dari RSS",
    }]
    mock_download.return_value = None
    mock_extract.return_value = None

    adapter = RssAdapter(MOCK_SOURCES)
    results = adapter.fetch()

    assert len(results) == 1
    assert results[0]["description"] == "Ringkasan dari RSS"

@patch("scraper.adapters.rss_adapter.fetch_rss_entries")
def test_fetch_skips_entry_without_link(mock_fetch):
    mock_fetch.return_value = [{"title": "No Link Entry", "link": "", "description": ""}]
    adapter = RssAdapter(MOCK_SOURCES)
    results = adapter.fetch()
    assert results == []

@patch("scraper.adapters.rss_adapter.fetch_rss_entries")
def test_fetch_skips_on_source_error(mock_fetch):
    mock_fetch.side_effect = Exception("Connection error")
    adapter = RssAdapter(MOCK_SOURCES)
    results = adapter.fetch()
    assert results == []
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_rss_adapter.py -v
```

Expected: FAIL — `scraper.adapters.rss_adapter` not found.

- [ ] **Step 3: Create `scraper/adapters/rss_adapter.py`**

```python
from scraper.adapters.base import BaseAdapter
from scraper.rss_scraper import fetch_rss_entries, download_page_html, extract_article_text

class RssAdapter(BaseAdapter):
    def __init__(self, sources: list[dict]):
        self.sources = sources

    def fetch(self) -> list[dict]:
        results = []
        for source in self.sources:
            try:
                results.extend(self._fetch_source(source))
            except Exception as e:
                print(f"[RssAdapter] Skip {source.get('name', '?')}: {e}")
        return results

    def _fetch_source(self, source: dict) -> list[dict]:
        entries = fetch_rss_entries(source["url"])
        items = []
        for entry in entries:
            url = entry.get("link", "")
            if not url:
                continue
            title = entry.get("title", "")
            summary = entry.get("description", "")

            html = download_page_html(url)
            article_text = None
            if html:
                article_text = extract_article_text(html, source.get("selector", ""))
            if not article_text:
                article_text = summary

            if not article_text:
                continue

            items.append({
                "title": title[:255],
                "description": article_text[:500],
                "category": source["category"],
                "brand_name": None,
                "promo_code": None,
                "discount_value": None,
                "min_transaction": None,
                "expired_date": None,
                "source_platform": "RSS",
                "source_url": url,
            })
        return items
```

- [ ] **Step 4: Add fashion + entertainment RSS sources to `scraper/config.py`**

Extend the existing `FEED_SOURCES` list — replace the entire list:

```python
FEED_SOURCES = [
    {
        "name": "Detik Travel",
        "url": "https://rss.detik.com/index.php/travel",
        "category": "flight",
        "selector": "article.detail, .detail__body-text"
    },
    {
        "name": "Katalog Promosi",
        "url": "https://katalogpromosi.com/feed/",
        "category": "food",
        "selector": ".entry-content, article.post, .post-content"
    },
    {
        "name": "Antara News Lifestyle",
        "url": "https://www.antaranews.com/rss/lifestyle.xml",
        "category": "food",
        "selector": "article.post, .post-content, .entry-content"
    },
    {
        "name": "Jadwal Event",
        "url": "https://jadwalevent.web.id/feed",
        "category": "event",
        "selector": ".entry-content, article.post, .post-content"
    },
    {
        "name": "Female Daily Fashion",
        "url": "https://femaledaily.com/feed",
        "category": "fashion",
        "selector": ".entry-content, .post-content, article"
    },
    {
        "name": "Detik Hot",
        "url": "https://rss.detik.com/index.php/hot",
        "category": "entertainment",
        "selector": "article.detail, .detail__body-text"
    },
]
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_rss_adapter.py -v
```

Expected: All 4 tests PASS.

- [ ] **Step 6: Verify existing rss_scraper tests still pass**

```bash
pytest tests/test_rss_scraper.py -v
```

Expected: All existing tests PASS (file unchanged).

- [ ] **Step 7: Commit**

```bash
git add scraper/adapters/rss_adapter.py scraper/config.py tests/test_rss_adapter.py
git commit -m "feat: add RssAdapter wrapping existing rss_scraper; extend FEED_SOURCES for fashion+entertainment"
```

---

## Task 8: Improve AI Parser

**Files:**
- Modify: `scraper/ai_parser.py`
- Modify: `tests/test_ai_parser.py`

**Interfaces:**
- Produces: `parse_with_gemini(text: str, category: str) -> dict | None`
  - Returns `None` if `is_promo == False` or `confidence < 0.7`
  - Returns dict with same shape as Task 5's standard shape plus `is_promo` and `confidence`

- [ ] **Step 1: Write the failing tests**

Replace `tests/test_ai_parser.py`:

```python
import os
import json
import pytest
from unittest.mock import patch, MagicMock
from scraper.ai_parser import parse_with_gemini

def _mock_response(payload: dict) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.text = json.dumps(payload)
    return mock_resp

VALID_PROMO_PAYLOAD = {
    "is_promo": True,
    "confidence": 0.9,
    "title": "Promo AirAsia Murah",
    "description": "Diskon 20% tiket pesawat",
    "category": "flight",
    "brand_name": "AirAsia",
    "promo_code": "AASCHOOL",
    "discount_value": "20%",
    "min_transaction": None,
    "expired_date": "2026-07-31",
    "terms_and_conditions": "Min 2 tiket",
}

def test_returns_none_without_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    result = parse_with_gemini("Teks artikel promo", category="flight")
    assert result is None

@patch("google.generativeai.GenerativeModel")
def test_returns_parsed_promo_on_success(mock_model_class, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "mock_key")
    mock_model = MagicMock()
    mock_model.generate_content.return_value = _mock_response(VALID_PROMO_PAYLOAD)
    mock_model_class.return_value = mock_model

    result = parse_with_gemini("Teks artikel", category="flight")

    assert result is not None
    assert result["promo_code"] == "AASCHOOL"
    assert result["discount_value"] == "20%"
    assert result["brand_name"] == "AirAsia"

@patch("google.generativeai.GenerativeModel")
def test_returns_none_when_not_promo(mock_model_class, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "mock_key")
    mock_model = MagicMock()
    mock_model.generate_content.return_value = _mock_response({
        **VALID_PROMO_PAYLOAD,
        "is_promo": False,
        "confidence": 0.2,
        "promo_code": None,
        "discount_value": None,
        "expired_date": None,
    })
    mock_model_class.return_value = mock_model

    result = parse_with_gemini("Tips hemat belanja", category="food")
    assert result is None

@patch("google.generativeai.GenerativeModel")
def test_returns_none_when_confidence_below_threshold(mock_model_class, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "mock_key")
    mock_model = MagicMock()
    mock_model.generate_content.return_value = _mock_response({
        **VALID_PROMO_PAYLOAD,
        "is_promo": True,
        "confidence": 0.5,
    })
    mock_model_class.return_value = mock_model

    result = parse_with_gemini("Teks ambigu", category="food")
    assert result is None

@patch("google.generativeai.GenerativeModel")
def test_returns_none_on_api_exception(mock_model_class, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "mock_key")
    mock_model = MagicMock()
    mock_model.generate_content.side_effect = Exception("API quota exceeded")
    mock_model_class.return_value = mock_model

    result = parse_with_gemini("Teks artikel", category="event")
    assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_ai_parser.py -v
```

Expected: `test_returns_none_when_not_promo` and `test_returns_none_when_confidence_below_threshold` FAIL (old parser doesn't implement these gates).

- [ ] **Step 3: Replace `scraper/ai_parser.py`**

```python
import os
import json
import google.generativeai as genai

_CATEGORY_HINTS = {
    "flight": "Fokus ekstrak: maskapai (brand_name), kota asal, kota tujuan, kode promo, diskon, tanggal kedaluwarsa.",
    "food": "Fokus ekstrak: nama brand/restoran (brand_name), minimal transaksi, lokasi berlaku, kode promo, besaran diskon.",
    "fashion": "Fokus ekstrak: nama brand pakaian/sepatu/tas (brand_name), persentase diskon, periode sale, minimal pembelian.",
    "entertainment": "Fokus ekstrak: nama venue/bioskop (brand_name), harga tiket, tanggal acara, kode promo.",
    "event": "Fokus ekstrak: nama event/pameran (brand_name), tanggal pelaksanaan, lokasi, harga tiket masuk.",
}

_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "is_promo": {"type": "boolean"},
        "confidence": {"type": "number", "description": "Confidence 0.0–1.0 that this is an active promo"},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "category": {"type": "string", "enum": ["flight", "food", "fashion", "event", "entertainment"]},
        "brand_name": {"type": "string", "nullable": True},
        "promo_code": {"type": "string", "nullable": True},
        "discount_value": {"type": "string", "nullable": True},
        "min_transaction": {"type": "string", "nullable": True},
        "expired_date": {"type": "string", "description": "Format YYYY-MM-DD", "nullable": True},
        "terms_and_conditions": {"type": "string", "nullable": True},
    },
    "required": [
        "is_promo", "confidence", "title", "description", "category",
        "brand_name", "promo_code", "discount_value", "min_transaction",
        "expired_date", "terms_and_conditions",
    ],
}

def parse_with_gemini(text: str, category: str = "flight") -> dict | None:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": _JSON_SCHEMA,
            },
        )
        hint = _CATEGORY_HINTS.get(category, "")
        prompt = f"""Analisis teks berikut dan tentukan apakah ini adalah artikel promo/diskon aktif.

ATURAN PENTING:
- Jika artikel hanya berisi berita umum, resep, tips, atau opini TANPA penawaran diskon/promo aktif yang spesifik, set is_promo=false dan confidence di bawah 0.5.
- Jika artikel berisi promo aktif dengan diskon nyata atau kode promo, set is_promo=true.
- {hint}
- Terjemahkan tanggal kedaluwarsa ke format YYYY-MM-DD.

Teks:
---
{text}
---"""
        response = model.generate_content(prompt)
        data = json.loads(response.text)

        if not data.get("is_promo"):
            return None
        if data.get("confidence", 0) < 0.7:
            return None

        return data
    except Exception as e:
        print(f"[ai_parser] Gemini error: {e}")
        return None
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_ai_parser.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scraper/ai_parser.py tests/test_ai_parser.py
git commit -m "feat: tighten ai_parser — add confidence gate, is_promo guard, category-aware prompts"
```

---

## Task 9: Update Engine Orchestration

**Files:**
- Modify: `scraper/engine.py`
- Modify: `tests/test_engine.py`

**Interfaces:**
- Consumes: `PortalAdapter` (Task 5), `SocialAdapter` (Task 6), `RssAdapter` (Task 7), `validate_promo` (Task 4), `insert_promo` + `url_exists` (Task 2), `PORTAL_SOURCES`, `SOCIAL_ACCOUNTS`, `FEED_SOURCES` (Task 5–7)
- Produces: `run_scraping_job(db_path: str, use_mock_source: bool = False) -> None`

- [ ] **Step 1: Write the failing tests**

Replace `tests/test_engine.py`:

```python
import sqlite3
import pytest
from unittest.mock import patch, MagicMock
from db.init_db import init_database
from scraper.engine import run_scraping_job

@pytest.fixture
def fresh_db(tmp_path):
    db_path = str(tmp_path / "test_engine.db")
    init_database(db_path)
    return db_path

def test_run_mock_job_inserts_promos(fresh_db):
    run_scraping_job(fresh_db, use_mock_source=True)
    conn = sqlite3.connect(fresh_db)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM promos")
    count = cur.fetchone()[0]
    conn.close()
    assert count > 0

@patch("scraper.engine.RssAdapter")
@patch("scraper.engine.SocialAdapter")
@patch("scraper.engine.PortalAdapter")
def test_real_job_calls_all_adapters(mock_portal, mock_social, mock_rss, fresh_db):
    mock_portal.return_value.fetch.return_value = []
    mock_social.return_value.fetch.return_value = []
    mock_rss.return_value.fetch.return_value = []

    run_scraping_job(fresh_db, use_mock_source=False)

    mock_portal.return_value.fetch.assert_called_once()
    mock_social.return_value.fetch.assert_called_once()
    mock_rss.return_value.fetch.assert_called_once()

@patch("scraper.engine.parse_promo_text")
@patch("scraper.engine.RssAdapter")
@patch("scraper.engine.SocialAdapter")
@patch("scraper.engine.PortalAdapter")
def test_real_job_inserts_valid_promo(mock_portal, mock_social, mock_rss, mock_parse, fresh_db):
    mock_portal.return_value.fetch.return_value = [{
        "title": "KFC Diskon 50%",
        "description": "KFC diskon 50% kode promo KFCFEAST s.d 2026-08-30",
        "category": "food",
        "brand_name": "KFC",
        "source_platform": "GoFood Promo",
        "source_url": "https://gofood.co.id/promo/kfc-1",
        "promo_code": None,
        "discount_value": None,
        "min_transaction": None,
        "expired_date": None,
    }]
    mock_social.return_value.fetch.return_value = []
    mock_rss.return_value.fetch.return_value = []
    mock_parse.return_value = {
        "promo_code": "KFCFEAST",
        "discount_value": "50%",
        "expired_date": "2026-08-30",
        "brand_name": "KFC",
        "category": "food",
    }

    run_scraping_job(fresh_db, use_mock_source=False)

    conn = sqlite3.connect(fresh_db)
    cur = conn.cursor()
    cur.execute("SELECT promo_code, discount_value FROM promos WHERE source_url=?",
                ("https://gofood.co.id/promo/kfc-1",))
    row = cur.fetchone()
    conn.close()
    assert row is not None
    assert row[0] == "KFCFEAST"
    assert row[1] == "50%"

@patch("scraper.engine.RssAdapter")
@patch("scraper.engine.SocialAdapter")
@patch("scraper.engine.PortalAdapter")
def test_real_job_skips_duplicate_url(mock_portal, mock_social, mock_rss, fresh_db):
    item = {
        "title": "Promo Zalora",
        "description": "Sale 70% off",
        "category": "fashion",
        "brand_name": "Zalora",
        "source_platform": "Zalora Sale",
        "source_url": "https://zalora.co.id/sale/1",
        "promo_code": "SALE70",
        "discount_value": "70%",
        "min_transaction": None,
        "expired_date": "2026-09-01",
    }
    mock_portal.return_value.fetch.return_value = [item, item]
    mock_social.return_value.fetch.return_value = []
    mock_rss.return_value.fetch.return_value = []

    run_scraping_job(fresh_db, use_mock_source=False)

    conn = sqlite3.connect(fresh_db)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM promos WHERE source_url=?", (item["source_url"],))
    assert cur.fetchone()[0] == 1
    conn.close()

@patch("scraper.engine.validate_promo", return_value=False)
@patch("scraper.engine.RssAdapter")
@patch("scraper.engine.SocialAdapter")
@patch("scraper.engine.PortalAdapter")
def test_real_job_skips_invalid_promo(mock_portal, mock_social, mock_rss, mock_validate, fresh_db):
    mock_portal.return_value.fetch.return_value = [{
        "title": "Berita Umum",
        "description": "Artikel tanpa promo",
        "category": "food",
        "brand_name": None,
        "source_platform": "RSS",
        "source_url": "https://news.com/artikel-1",
        "promo_code": None,
        "discount_value": None,
        "min_transaction": None,
        "expired_date": None,
    }]
    mock_social.return_value.fetch.return_value = []
    mock_rss.return_value.fetch.return_value = []

    run_scraping_job(fresh_db, use_mock_source=False)

    conn = sqlite3.connect(fresh_db)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM promos")
    assert cur.fetchone()[0] == 0
    conn.close()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_engine.py -v
```

Expected: Multiple FAIL — engine imports `fetch_rss_entries` etc. directly; new adapter structure not there.

- [ ] **Step 3: Replace `scraper/engine.py`**

```python
import os
from scraper.db_manager import DatabaseManager
from scraper.config import FEED_SOURCES, PORTAL_SOURCES, SOCIAL_ACCOUNTS
from scraper.adapters.portal_adapter import PortalAdapter
from scraper.adapters.social_adapter import SocialAdapter
from scraper.adapters.rss_adapter import RssAdapter
from scraper.ai_parser import parse_with_gemini
from scraper.parser import parse_promo_text
from scraper.validator import validate_promo

_MOCK_SOURCES = [
    {
        "title": "AirAsia Liburan Sekolah Flash Promo",
        "text": "Promo Liburan Sekolah! KODE PROMO: AIRASIASCHOOL. Dapatkan diskon 20% tiket penerbangan AirAsia dari Jakarta ke Bali! S&K: Promo berlaku hingga 2026-07-15.",
        "source_url": "https://www.youtube.com/watch?v=mockairasia",
        "platform": "YouTube",
        "category": "flight",
    },
    {
        "title": "KFC Feast Hemat Akhir Pekan",
        "text": "Weekend hemat di KFC! Gunakan kode promo KFCFEAST untuk diskon hemat 50% di KFC dengan minimal pembelian Rp 100.000. Berlaku s.d 2026-08-30.",
        "source_url": "https://tiktok.com/@kfcindonesia/video/98765",
        "platform": "TikTok",
        "category": "food",
    },
]

def run_scraping_job(db_path: str = "promo.db", use_mock_source: bool = False) -> None:
    if use_mock_source:
        _run_mock_job(db_path)
        return

    print("Starting Ingestion Engine...")
    adapters = [
        PortalAdapter(PORTAL_SOURCES),
        SocialAdapter(SOCIAL_ACCOUNTS),
        RssAdapter(FEED_SOURCES),
    ]

    with DatabaseManager(db_path) as db_mgr:
        for adapter in adapters:
            name = type(adapter).__name__
            print(f"Running {name}...")
            try:
                raw_items = adapter.fetch()
            except Exception as e:
                print(f"[engine] {name} failed: {e}")
                continue

            for item in raw_items:
                try:
                    url = item.get("source_url", "")
                    if not url or db_mgr.url_exists(url):
                        continue

                    article_text = item.get("description") or item.get("title", "")
                    category = item.get("category", "food")

                    parsed = None
                    if os.environ.get("GEMINI_API_KEY"):
                        parsed = parse_with_gemini(article_text, category=category)

                    if not parsed:
                        parsed = parse_promo_text(article_text, category=category)

                    if not parsed:
                        continue

                    # Normalize airline → brand_name for flight promos
                    if not parsed.get("brand_name") and parsed.get("airline"):
                        parsed["brand_name"] = parsed["airline"]

                    parsed.update({
                        "title": item.get("title") or parsed.get("title", ""),
                        "description": article_text[:500],
                        "source_platform": item.get("source_platform", "Unknown"),
                        "source_url": url,
                        "category": category,
                    })

                    if validate_promo(parsed):
                        db_mgr.insert_promo(parsed)
                        print(f"[engine] Inserted: {parsed.get('title', '')[:60]}")
                    else:
                        print(f"[engine] Skipped (no promo signal): {item.get('title', '')[:60]}")
                except Exception as e:
                    print(f"[engine] Error processing '{item.get('title', '')}': {e}")

    print("Ingestion Engine finished.")

def _run_mock_job(db_path: str) -> None:
    with DatabaseManager(db_path) as db_mgr:
        for src in _MOCK_SOURCES:
            try:
                parsed = parse_promo_text(src["text"], category=src["category"])
                if not parsed.get("brand_name") and parsed.get("airline"):
                    parsed["brand_name"] = parsed["airline"]
                parsed.update({
                    "title": src["title"],
                    "description": src["text"],
                    "source_platform": src["platform"],
                    "source_url": src["source_url"],
                    "category": src["category"],
                })
                db_mgr.insert_promo(parsed)
            except Exception as e:
                print(f"[engine] Mock error: {e}")

if __name__ == "__main__":
    import sys
    from db.init_db import init_database
    init_database()
    use_mock = "--mock" in sys.argv
    run_scraping_job(use_mock_source=use_mock)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_engine.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 5: Run the full test suite to confirm no regressions**

```bash
pytest --tb=short
```

Expected: All tests PASS. If `test_config.py` fails (it checks `food` and `flight` in `FEED_SOURCES`), verify those categories still exist in the updated `FEED_SOURCES`.

- [ ] **Step 6: Commit**

```bash
git add scraper/engine.py tests/test_engine.py
git commit -m "feat: update engine to orchestrate PortalAdapter + SocialAdapter + RssAdapter with unified insert_promo"
```

---

## Final Verification

- [ ] **Run full test suite one more time**

```bash
pytest -v
```

Expected: All tests PASS.

- [ ] **Smoke-test real scraping on one portal source**

```bash
source .venv/bin/activate && python -c "
from scraper.adapters.portal_adapter import PortalAdapter
sources = [{'name':'Loket Event','url':'https://www.loket.com/event','category':'event','selector':'.event-card, .event-item, article'}]
adapter = PortalAdapter(sources)
results = adapter.fetch()
print(f'Found {len(results)} items')
for r in results[:2]:
    print(r.get('title',''))
"
```

Expected: Prints item count (may be 0 if portal uses heavy JS — that's expected and handled gracefully).

- [ ] **Start the web app and verify the dashboard loads all 5 tabs**

```bash
npm run dev
```

Open `http://localhost:3000` and click each tab (Penerbangan, Makanan, Fashion, Hiburan, Event). All should load without API errors.
