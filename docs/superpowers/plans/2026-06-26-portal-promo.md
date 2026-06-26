# Portal Promo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Membangun web portal agregator promo tiket pesawat dan makanan yang otomatis di-scrape dua kali sehari oleh script Python dan disajikan menggunakan Next.js dengan arsitektur database bersama (Shared DB SQLite).

**Architecture:** Data ditarik oleh Python scraper dari data feeds/RSS/media sosial, dibersihkan dan diparse menjadi data terstruktur, lalu disimpan langsung ke database SQLite. Aplikasi Next.js akan membaca database SQLite secara real-time untuk dirender langsung di antarmuka web interaktif dengan filter pencarian dan visual tabbed modern.

**Tech Stack:** Next.js (App Router), Vanilla CSS, SQLite (better-sqlite3 / sqlite3), Python 3, Pytest.

---

### Task 1: Inisialisasi Database & Skema SQL

**Files:**
- Create: `db/schema.sql`
- Create: `db/init_db.py`
- Test: `tests/test_db.py`

- [ ] **Step 1: Tulis unit test untuk verifikasi inisialisasi database**
  Buat file `tests/test_db.py` dengan kode pengujian menggunakan pytest:
  ```python
  # filepath: tests/test_db.py
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
  ```

- [ ] **Step 2: Jalankan test dan pastikan gagal**
  Jalankan perintah:
  ```bash
  pytest tests/test_db.py -v
  ```
  Expected: FAIL (ModuleNotFoundError: No module named 'db')

- [ ] **Step 3: Tulis skema database SQL dan script Python inisialisasi**
  Buat file `db/schema.sql`:
  ```sql
  -- filepath: db/schema.sql
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
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
  ```
  Buat file `db/init_db.py`:
  ```python
  # filepath: db/init_db.py
  import os
  import sqlite3

  def init_database(db_path="promo.db"):
      schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
      with open(schema_path, "r") as f:
          schema_sql = f.read()
          
      conn = sqlite3.connect(db_path)
      cursor = conn.cursor()
      cursor.executescript(schema_sql)
      conn.commit()
      conn.close()

  if __name__ == "__main__":
      init_database()
      print("Database initialized successfully.")
  ```

- [ ] **Step 4: Jalankan test dan pastikan berhasil**
  Jalankan perintah:
  ```bash
  pytest tests/test_db.py -v
  ```
  Expected: PASS

- [ ] **Step 5: Komit hasil kerja**
  ```bash
  git add db/schema.sql db/init_db.py tests/test_db.py
  git commit -m "feat: add database schema and init script"
  ```

---

### Task 2: Implementasi Database Manager Python

**Files:**
- Create: `scraper/db_manager.py`
- Test: `tests/test_db_manager.py`

- [ ] **Step 1: Tulis unit test untuk DB Manager**
  Buat file `tests/test_db_manager.py`:
  ```python
  # filepath: tests/test_db_manager.py
  import os
  import sqlite3
  import pytest
  from db.init_db import init_database
  from scraper.db_manager import DatabaseManager

  DB_FILE = "test_promo_mgr.db"

  @pytest.fixture
  def db_manager():
      if os.path.exists(DB_FILE):
          os.remove(DB_FILE)
      init_database(DB_FILE)
      mgr = DatabaseManager(DB_FILE)
      yield mgr
      mgr.close()
      if os.path.exists(DB_FILE):
          os.remove(DB_FILE)

  def test_insert_flight_promo(db_manager):
      promo_data = {
          "title": "Diskon 20% Garuda Indonesia",
          "description": "Terbang keliling Indonesia",
          "airline": "Garuda Indonesia",
          "origin_city": "Jakarta",
          "destination_city": "Bali",
          "promo_code": "GARUDA20",
          "discount_value": "20%",
          "terms_and_conditions": "Min pembelian 2 tiket",
          "source_platform": "News",
          "source_url": "https://news.com/garuda-promo",
          "expired_date": "2026-07-31"
      }
      
      # Test insert baru
      db_manager.insert_flight_promo(promo_data)
      conn = sqlite3.connect(DB_FILE)
      cursor = conn.cursor()
      cursor.execute("SELECT title, promo_code, terms_and_conditions FROM flight_promos WHERE source_url=?", (promo_data["source_url"],))
      row = cursor.fetchone()
      assert row is not None
      assert row[0] == promo_data["title"]
      assert row[1] == promo_data["promo_code"]
      assert row[2] == promo_data["terms_and_conditions"]
      conn.close()

      # Test ignore duplicate
      db_manager.insert_flight_promo(promo_data)
      conn = sqlite3.connect(DB_FILE)
      cursor = conn.cursor()
      cursor.execute("SELECT COUNT(*) FROM flight_promos")
      count = cursor.fetchone()[0]
      assert count == 1
      conn.close()
  ```

- [ ] **Step 2: Jalankan test dan pastikan gagal**
  Jalankan perintah:
  ```bash
  pytest tests/test_db_manager.py -v
  ```
  Expected: FAIL (ModuleNotFoundError: No module named 'scraper')

- [ ] **Step 3: Implementasi DatabaseManager**
  Buat file `scraper/db_manager.py`:
  ```python
  # filepath: scraper/db_manager.py
  import sqlite3
  from datetime import datetime

  class DatabaseManager:
      def __init__(self, db_path="promo.db"):
          self.conn = sqlite3.connect(db_path)
          self.conn.row_factory = sqlite3.Row

      def insert_flight_promo(self, data):
          cursor = self.conn.cursor()
          query = """
          INSERT OR IGNORE INTO flight_promos (
              title, description, airline, origin_city, destination_city,
              promo_code, discount_value, terms_and_conditions,
              source_platform, source_url, expired_date, scraped_at
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
          """
          now = datetime.now().isoformat()
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
          cursor = self.conn.cursor()
          query = """
          INSERT OR IGNORE INTO food_promos (
              title, description, brand_name, category, min_transaction,
              promo_code, discount_value, terms_and_conditions, locations,
              source_platform, source_url, expired_date, scraped_at
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
          """
          now = datetime.now().isoformat()
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
  ```

- [ ] **Step 4: Jalankan test dan pastikan berhasil**
  Jalankan perintah:
  ```bash
  pytest tests/test_db_manager.py -v
  ```
  Expected: PASS

- [ ] **Step 5: Komit hasil kerja**
  ```bash
  git add scraper/db_manager.py tests/test_db_manager.py
  git commit -m "feat: implement database manager in python"
  ```

---

### Task 3: Implementasi Parser Promo dengan Regex

**Files:**
- Create: `scraper/parser.py`
- Test: `tests/test_parser.py`

- [ ] **Step 1: Tulis unit test untuk parsing teks promo**
  Buat file `tests/test_parser.py`:
  ```python
  # filepath: tests/test_parser.py
  import pytest
  from scraper.parser import parse_promo_text

  def test_parse_flight_promo():
      text = "KODE PROMO: AIRASIASCHOOL. Dapatkan diskon 20% tiket penerbangan AirAsia dari Jakarta ke Bali! S&K: Promo berlaku hingga 2026-07-15 dengan pembelian minimal 2 tiket."
      result = parse_promo_text(text, category="flight")
      
      assert result["promo_code"] == "AIRASIASCHOOL"
      assert result["discount_value"] == "20%"
      assert "AirAsia" in result["airline"]
      assert result["expired_date"] == "2026-07-15"
      assert "minimal 2 tiket" in result["terms_and_conditions"]

  def test_parse_food_promo():
      text = "Nikmati diskon hemat 50% di KFC dengan minimal pembelian Rp 100.000 menggunakan kode promo KFCFEAST. Promo berlaku s.d 2026-08-30 secara nasional."
      result = parse_promo_text(text, category="food")
      
      assert result["promo_code"] == "KFCFEAST"
      assert result["discount_value"] == "50%"
      assert result["brand_name"] == "KFC"
      assert result["expired_date"] == "2026-08-30"
      assert "Rp 100.000" in result["min_transaction"]
      assert "nasional" in result["terms_and_conditions"].lower()
  ```

- [ ] **Step 2: Jalankan test dan pastikan gagal**
  Jalankan perintah:
  ```bash
  pytest tests/test_parser.py -v
  ```
  Expected: FAIL (ModuleNotFoundError: No module named 'scraper.parser')

- [ ] **Step 3: Implementasi logika parsing teks di parser.py**
  Buat file `scraper/parser.py`:
  ```python
  # filepath: scraper/parser.py
  import re

  def parse_promo_text(text, category="flight"):
      # Regex patterns
      code_pattern = re.search(r'(?:KODE PROMO|KODE|PROMO|CODE):\s*([A-Z0-9]+)', text, re.IGNORECASE)
      discount_pattern = re.search(r'(\d+%\s*(?:diskon|potongan)?|diskon\s*\d+%|potongan\s*(?:Rp\s*\d+[\d.,]*|\d+[\d.,]*\s*ribu))', text, re.IGNORECASE)
      date_pattern = re.search(r'(\d{4}-\d{2}-\d{2})', text)
      
      promo_code = code_pattern.group(1).strip() if code_pattern else None
      discount_value = discount_pattern.group(1).strip() if discount_pattern else None
      expired_date = date_pattern.group(1).strip() if date_pattern else None
      
      # Extract terms & conditions (sentence after S&K or Syarat)
      terms_match = re.search(r'(?:S&K|Syarat & Ketentuan|Syarat|T&C):\s*(.*?)(?:\.|$)', text, re.IGNORECASE)
      terms = terms_match.group(1).strip() if terms_match else ""
      
      result = {
          "promo_code": promo_code,
          "discount_value": discount_value,
          "expired_date": expired_date,
          "terms_and_conditions": terms
      }
      
      if category == "flight":
          # Airline extraction
          airlines = ["Garuda Indonesia", "AirAsia", "Batik Air", "Lion Air", "Citilink", "Singapore Airlines"]
          extracted_airline = None
          for airline in airlines:
              if airline.lower() in text.lower():
                  extracted_airline = airline
                  break
          
          result.update({
              "airline": extracted_airline or "Unknown Airline",
              "origin_city": "Jakarta", # Default fallback
              "destination_city": "Bali" # Default fallback
          })
      else:
          # Food brand extraction
          brands = ["KFC", "McDonald", "Starbucks", "Kopi Kenangan", "Pizza Hut", "Burger King"]
          extracted_brand = None
          for brand in brands:
              if brand.lower() in text.lower():
                  extracted_brand = brand
                  break
                  
          min_tx_match = re.search(r'(?:minimal pembelian|min transaksi|min purchase)\s*(Rp\s*\d+[\d.,]*|\d+[\d.,]*)', text, re.IGNORECASE)
          min_tx = min_tx_match.group(1).strip() if min_tx_match else None
          
          result.update({
              "brand_name": extracted_brand or "Unknown Brand",
              "category": "F&B",
              "min_transaction": min_tx,
              "locations": "Nasional"
          })
          
      return result
  ```

- [ ] **Step 4: Jalankan test dan pastikan berhasil**
  Jalankan perintah:
  ```bash
  pytest tests/test_parser.py -v
  ```
  Expected: PASS

- [ ] **Step 5: Komit hasil kerja**
  ```bash
  git add scraper/parser.py tests/test_parser.py
  git commit -m "feat: add promo text parser with regex extraction"
  ```

---

### Task 4: Pembuatan Script Penjadwalan & Ingestion Engine

**Files:**
- Create: `scraper/engine.py`
- Test: `tests/test_engine.py`

- [ ] **Step 1: Tulis unit test untuk verifikasi engine**
  Buat file `tests/test_engine.py`:
  ```python
  # filepath: tests/test_engine.py
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
  ```

- [ ] **Step 2: Jalankan test dan pastikan gagal**
  Jalankan perintah:
  ```bash
  pytest tests/test_engine.py -v
  ```
  Expected: FAIL (ModuleNotFoundError: No module named 'scraper.engine')

- [ ] **Step 3: Implementasi engine scraping dengan data mock & simulasi API**
  Buat file `scraper/engine.py`:
  ```python
  # filepath: scraper/engine.py
  import sys
  from scraper.db_manager import DatabaseManager
  from scraper.parser import parse_promo_text

  # Mock raw content sources
  MOCK_FLIGHT_SOURCES = [
      {
          "title": "AirAsia Liburan Sekolah Flash Promo",
          "text": "Promo Liburan Sekolah! KODE PROMO: AIRASIASCHOOL. Dapatkan diskon 20% tiket penerbangan AirAsia dari Jakarta ke Bali! S&K: Promo berlaku hingga 2026-07-15 dengan pembelian minimal 2 tiket.",
          "source_url": "https://www.youtube.com/watch?v=mockairasia",
          "platform": "YouTube"
      },
      {
          "title": "Garuda Indonesia Gajian Deals",
          "text": "Spesial Akhir Bulan! Nikmati diskon potongan Rp 300.000 rute domestik Garuda Indonesia tanpa kode promo. Syarat: Berlaku s.d 2026-07-28 nasional.",
          "source_url": "https://twitter.com/garudapromo/status/12345",
          "platform": "Twitter"
      }
  ]

  MOCK_FOOD_SOURCES = [
      {
          "title": "KFC Feast Hemat Akhir Pekan",
          "text": "Weekend hemat di KFC! Gunakan kode promo KFCFEAST untuk diskon hemat 50% di KFC dengan minimal pembelian Rp 100.000. Syarat: Berlaku s.d 2026-08-30 secara nasional.",
          "source_url": "https://tiktok.com/@kfcindonesia/video/98765",
          "platform": "TikTok"
      },
      {
          "title": "Starbucks Coffee Break promo",
          "text": "Dapatkan diskon potongan Rp 15.000 di Starbucks menggunakan kode promo SBXCOFFEE. S&K: Min transaksi Rp 50.000 berlaku s.d 2026-07-10.",
          "source_url": "https://detik.com/food/starbucks-juni-promo",
          "platform": "News"
      }
  ]

  def run_scraping_job(db_path="promo.db", use_mock_source=True):
      db_mgr = DatabaseManager(db_path)
      
      print("Starting ingestion engine...")
      
      # Process Flight Promos
      for src in MOCK_FLIGHT_SOURCES:
          parsed = parse_promo_text(src["text"], category="flight")
          parsed.update({
              "title": src["title"],
              "description": src["text"],
              "source_platform": src["platform"],
              "source_url": src["source_url"]
          })
          db_mgr.insert_flight_promo(parsed)
          print(f"Ingested flight promo: {src['title']}")

      # Process Food Promos
      for src in MOCK_FOOD_SOURCES:
          parsed = parse_promo_text(src["text"], category="food")
          parsed.update({
              "title": src["title"],
              "description": src["text"],
              "source_platform": src["platform"],
              "source_url": src["source_url"]
          })
          db_mgr.insert_food_promo(parsed)
          print(f"Ingested food promo: {src['title']}")
          
      db_mgr.close()
      print("Ingestion engine execution finished.")

  if __name__ == "__main__":
      # Inisialisasi database lokal jika dijalankan mandiri
      from db.init_db import init_database
      init_database()
      run_scraping_job()
  ```

- [ ] **Step 4: Jalankan test dan pastikan berhasil**
  Jalankan perintah:
  ```bash
  pytest tests/test_engine.py -v
  ```
  Expected: PASS

- [ ] **Step 5: Komit hasil kerja**
  ```bash
  git add scraper/engine.py tests/test_engine.py
  git commit -m "feat: implement main scraping ingestion engine"
  ```

---

### Task 5: Inisialisasi Project Next.js Frontend

**Files:**
- Create: `./package.json`
- Create: `./next.config.mjs`
- Create: `./app/layout.js`

- [ ] **Step 1: Setup project Next.js non-interaktif**
  Inisialisasi aplikasi Next.js langsung pada direktori utama (`./`) menggunakan `create-next-app` terbaru.
  Jalankan perintah:
  ```bash
  npx -y create-next-app@14.2.3 ./ --js --tailwind false --eslint false --app --src-dir false --import-alias "@/*" --use-npm
  ```
  Expected: Inisialisasi berhasil di workspace saat ini.

- [ ] **Step 2: Menambahkan library SQLite untuk Node.js**
  Jalankan perintah:
  ```bash
  npm install sqlite3 sqlite
  ```

- [ ] **Step 3: Setup file next.config.mjs**
  Ubah file `next.config.mjs` agar menonaktifkan kompilasi native modules serverless jika ada kendala binary sqlite:
  ```javascript
  // filepath: next.config.mjs
  /** @type {import('next').NextConfig} */
  const nextConfig = {
    webpack: (config, { isServer }) => {
      if (isServer) {
        config.externals.push('sqlite3');
      }
      return config;
    },
  };

  export default nextConfig;
  ```

- [ ] **Step 4: Komit hasil inisialisasi framework**
  ```bash
  git add package.json next.config.mjs app/
  git commit -m "feat: initialize next.js app with sqlite node integration"
  ```

---

### Task 6: Implementasi API Data Promo & Database Client di Next.js

**Files:**
- Create: `lib/db.js`
- Create: `app/api/promos/route.js`

- [ ] **Step 1: Tulis database client Node.js**
  Buat file `lib/db.js` untuk mengkoneksikan Next.js ke file `promo.db`:
  ```javascript
  // filepath: lib/db.js
  import sqlite3 from 'sqlite3';
  import { open } from 'sqlite';
  import path from 'path';

  let db = null;

  export async function getDbConnection() {
    if (!db) {
      db = await open({
        filename: path.join(process.cwd(), 'promo.db'),
        driver: sqlite3.Database
      });
    }
    return db;
  }
  ```

- [ ] **Step 2: Implementasi API Endpoint Route**
  Buat file `app/api/promos/route.js` untuk menyajikan data promo dalam format JSON:
  ```javascript
  // filepath: app/api/promos/route.js
  import { NextResponse } from 'next/server';
  import { getDbConnection } from '@/lib/db';

  export async function GET(request) {
    try {
      const { searchParams } = new URL(request.url);
      const category = searchParams.get('category') || 'flight'; // flight atau food
      const search = searchParams.get('search') || '';
      
      const db = await getDbConnection();
      let promos = [];

      if (category === 'flight') {
        let query = 'SELECT * FROM flight_promos WHERE 1=1';
        const params = [];
        if (search) {
          query += ' AND (title LIKE ? OR description LIKE ? OR airline LIKE ?)';
          params.push(`%${search}%`, `%${search}%`, `%${search}%`);
        }
        query += ' ORDER BY created_at DESC';
        promos = await db.all(query, params);
      } else {
        let query = 'SELECT * FROM food_promos WHERE 1=1';
        const params = [];
        if (search) {
          query += ' AND (title LIKE ? OR description LIKE ? OR brand_name LIKE ?)';
          params.push(`%${search}%`, `%${search}%`, `%${search}%`);
        }
        query += ' ORDER BY created_at DESC';
        promos = await db.all(query, params);
      }

      return NextResponse.json({ success: true, data: promos });
    } catch (error) {
      console.error('API Promos Error:', error);
      return NextResponse.json({ success: false, error: error.message }, { status: 500 });
    }
  }
  ```

- [ ] **Step 3: Uji jalankan inisialisasi DB lokal & API**
  Jalankan Python script untuk mengisi data mock:
  ```bash
  python scraper/engine.py
  ```
  Lalu verifikasi database `promo.db` telah terbentuk dan data mock terisi.

- [ ] **Step 4: Komit modul database & API**
  ```bash
  git add lib/db.js app/api/promos/route.js
  git commit -m "feat: add next.js database connector and API route"
  ```

---

### Task 7: Pembangunan UI Portal & CSS Premium System

**Files:**
- Create: `app/globals.css`
- Create: `components/PromoCard.js`
- Modify: `app/page.js`

- [ ] **Step 1: Definisikan CSS Premium System**
  Buat / overwrite file `app/globals.css` dengan desain custom vanilla CSS berdasar spesifikasi UI:
  ```css
  /* filepath: app/globals.css */
  :root {
    --bg-main: #0b1116;
    --bg-card: #151e24;
    --text-main: #f5f6f7;
    --text-muted: #8a99ad;
    --primary: #2196f3;
    --accent: #ff5722;
    --border: #23313d;
    --success: #8bc34a;
  }

  body {
    background-color: var(--bg-main);
    color: var(--text-main);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    margin: 0;
    padding: 0;
  }

  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border);
    padding-bottom: 20px;
    margin-bottom: 30px;
  }

  .title-logo {
    font-size: 1.5em;
    font-weight: bold;
    color: #fff;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .badge-scraper {
    font-size: 0.8em;
    background-color: var(--primary);
    color: white;
    padding: 4px 10px;
    border-radius: 4px;
  }

  .tabs {
    display: flex;
    border-bottom: 1px solid var(--border);
    margin-bottom: 20px;
    gap: 5px;
  }

  .tab {
    padding: 12px 24px;
    cursor: pointer;
    font-weight: bold;
    color: var(--text-muted);
    border-bottom: 3px solid transparent;
    transition: all 0.3s ease;
  }

  .tab.active {
    color: var(--primary);
    border-bottom-color: var(--primary);
    background: rgba(33, 150, 243, 0.05);
  }

  .search-box {
    width: 100%;
    padding: 12px;
    border: 1px solid var(--border);
    background: var(--bg-card);
    color: #fff;
    border-radius: 8px;
    margin-bottom: 25px;
    font-size: 1em;
    box-sizing: border-box;
  }

  .promo-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 20px;
  }

  .card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    transition: transform 0.2s, box-shadow 0.2s;
  }

  .card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    border-color: rgba(33, 150, 243, 0.3);
  }

  .card-header {
    padding: 12px 15px;
    background: rgba(255,255,255,0.02);
    border-bottom: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .card-body {
    padding: 15px;
    flex: 1;
  }

  .promo-code-container {
    background: rgba(139, 195, 74, 0.05);
    border: 1px dashed var(--success);
    color: var(--success);
    font-family: monospace;
    padding: 8px;
    border-radius: 6px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 15px;
    font-weight: bold;
  }

  .btn-copy {
    background: none;
    border: none;
    color: var(--success);
    cursor: pointer;
    text-decoration: underline;
    font-size: 0.9em;
  }

  .discount-tag {
    font-size: 1.5em;
    font-weight: bold;
    color: var(--accent);
    margin: 10px 0;
  }

  .card-footer {
    padding: 12px 15px;
    border-top: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.9em;
  }

  .btn-link {
    color: var(--primary);
    text-decoration: none;
    font-weight: bold;
  }
  ```

- [ ] **Step 2: Buat komponen PromoCard**
  Buat file `components/PromoCard.js`:
  ```javascript
  // filepath: components/PromoCard.js
  'use client';

  export default function PromoCard({ promo, category }) {
    const handleCopy = (code) => {
      navigator.clipboard.writeText(code);
      alert('Kode promo berhasil disalin: ' + code);
    };

    const isFlight = category === 'flight';
    const sourceLabel = promo.source_platform || 'Web';
    const subLabel = isFlight ? promo.airline : promo.brand_name;
    const detailRoute = isFlight 
      ? `${promo.origin_city || 'Jakarta'} ➔ ${promo.destination_city || 'Bali'}` 
      : `Min: ${promo.min_transaction || 'Tidak ada minimum'}`;

    return (
      <div className="card">
        <div className="card-header">
          <span style={{ fontSize: '0.8em', color: 'var(--text-muted)', fontWeight: 'bold' }}>
            {sourceLabel}
          </span>
          {promo.expired_date && (
            <span style={{ fontSize: '0.75em', background: 'var(--accent)', color: '#fff', padding: '2px 6px', borderRadius: '4px' }}>
              Hingga: {promo.expired_date}
            </span>
          )}
        </div>
        <div className="card-body">
          <div style={{ fontSize: '0.8em', textTransform: 'uppercase', color: 'var(--primary)', fontWeight: 'bold', marginBottom: '5px' }}>
            {subLabel}
          </div>
          <h3 style={{ margin: '0 0 10px 0', fontSize: '1.1em', color: '#fff', lineHeight: '1.3' }}>
            {promo.title}
          </h3>
          <p style={{ fontSize: '0.9em', color: 'var(--text-muted)', margin: '0 0 10px 0' }}>
            {promo.description}
          </p>
          
          {promo.discount_value && (
            <div className="discount-tag">{promo.discount_value}</div>
          )}

          {promo.promo_code ? (
            <div className="promo-code-container">
              <span>{promo.promo_code}</span>
              <button className="btn-copy" onClick={() => handleCopy(promo.promo_code)}>Copy</button>
            </div>
          ) : (
            <div style={{ fontSize: '0.8em', color: 'var(--text-muted)', marginTop: '15px' }}>
              *Tidak memerlukan kode promo
            </div>
          )}

          {promo.terms_and_conditions && (
            <div style={{ marginTop: '10px', fontSize: '0.8em', color: 'var(--text-muted)', borderTop: '1px solid var(--border)', paddingTop: '8px' }}>
              <strong>S&K:</strong> {promo.terms_and_conditions}
            </div>
          )}
        </div>
        <div className="card-footer">
          <span style={{ color: 'var(--text-muted)' }}>{detailRoute}</span>
          {promo.source_url && (
            <a href={promo.source_url} target="_blank" rel="noopener noreferrer" className="btn-link">
              Lihat Sumber ➔
            </a>
          )}
        </div>
      </div>
    );
  }
  ```

- [ ] **Step 3: Modifikasi file app/page.js**
  Ubah isi file `app/page.js` untuk memuat data dari API secara dinamis:
  ```javascript
  // filepath: app/page.js
  'use client';
  import { useState, useEffect } from 'react';
  import PromoCard from '@/components/PromoCard';
  import '@/app/globals.css';

  export default function Home() {
    const [category, setCategory] = useState('flight'); // flight atau food
    const [search, setSearch] = useState('');
    const [promos, setPromos] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchPromos = async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api/promos?category=${category}&search=${encodeURIComponent(search)}`);
        const result = await res.json();
        if (result.success) {
          setPromos(result.data);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    useEffect(() => {
      fetchPromos();
    }, [category, search]);

    return (
      <div className="container">
        {/* Header */}
        <header className="header">
          <div className="title-logo">🎟 PromoPortal</div>
          <div>
            <span className="badge-scraper">Sync: 8:00 & 15:00 WIB</span>
          </div>
        </header>

        {/* Tab Switcher */}
        <div className="tabs">
          <div 
            className={`tab ${category === 'flight' ? 'active' : ''}`}
            onClick={() => { setCategory('flight'); setSearch(''); }}
          >
            ✈ Penerbangan (Flights)
          </div>
          <div 
            className={`tab ${category === 'food' ? 'active' : ''}`}
            onClick={() => { setCategory('food'); setSearch(''); }}
          >
            🍔 Makanan & Minuman (Food)
          </div>
        </div>

        {/* Search */}
        <input 
          type="text" 
          className="search-box"
          placeholder={`Cari promo ${category === 'flight' ? 'maskapai, kota, rute' : 'brand, kategori kuliner'}...`}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />

        {/* Promo List */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
            Sedang memuat promo terbaik...
          </div>
        ) : promos.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
            Tidak ada promo ditemukan.
          </div>
        ) : (
          <div className="promo-grid">
            {promos.map((promo) => (
              <PromoCard key={promo.id} promo={promo} category={category} />
            ))}
          </div>
        )}
      </div>
    );
  }
  ```

- [ ] **Step 4: Uji Coba Build Aplikasi Next.js**
  Jalankan perintah build untuk memastikan tidak ada kesalahan kompilasi atau dependensi:
  ```bash
  npm run build
  ```
  Expected: Build production berhasil tanpa error.

- [ ] **Step 5: Komit UI Dashboard**
  ```bash
  git add app/globals.css components/PromoCard.js app/page.js
  git commit -m "feat: build dashboard portal ui using vanilla css"
  ```
