# RSS Deep Scraper & Gemini AI Parser Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Menggantikan data mock dengan sistem penarikan data riil yang mengunduh artikel dari RSS berita, mengekstrak artikel halaman penuh, dan melakukan parsing promo terstruktur menggunakan Gemini AI (dengan fallback otomatis ke Regex lokal).

**Architecture:** Modul ingesti secara berkala mengambil RSS feed, memverifikasi apakah URL baru, mengunduh halaman penuh artikel menggunakan `requests`, dan menyaring teks artikel utama menggunakan `BeautifulSoup`. Teks tersebut dikirim ke API Gemini (model `gemini-1.5-flash`) dengan Structured Outputs untuk diubah menjadi JSON promo terstruktur, lalu disimpan via `DatabaseManager`. Jika kunci API tidak ada, sistem otomatis mengalihkan ke Regex parser lokal.

**Tech Stack:** Python 3, feedparser, beautifulsoup4, requests, google-generativeai, pytest.

---

### Task 1: Setup Dependensi & Konfigurasi Feed

**Files:**
- Create: `requirements.txt`
- Create: `scraper/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Tulis requirements.txt**
  Buat file `requirements.txt` di root directory:
  ```text
  feedparser>=6.0.10
  beautifulsoup4>=4.12.3
  requests>=2.31.0
  google-generativeai>=0.5.4
  pytest>=8.0.0
  ```

- [ ] **Step 2: Install dependensi baru**
  Jalankan perintah:
  ```bash
  .venv/bin/pip install -r requirements.txt
  ```
  Expected: Semua paket terinstal dengan sukses.

- [ ] **Step 3: Tulis unit test untuk konfigurasi feed**
  Buat file `tests/test_config.py`:
  ```python
  # filepath: tests/test_config.py
  from scraper.config import FEED_SOURCES

  def test_feed_sources_config():
      assert len(FEED_SOURCES) >= 2
      
      # Pastikan terdapat feed penerbangan dan makanan
      categories = [feed["category"] for feed in FEED_SOURCES]
      assert "flight" in categories
      assert "food" in categories
      
      for feed in FEED_SOURCES:
          assert "url" in feed
          assert "selector" in feed
          assert feed["url"].startswith("http")
  ```

- [ ] **Step 4: Jalankan test dan pastikan gagal**
  Jalankan perintah:
  ```bash
  PYTHONPATH=. .venv/bin/pytest tests/test_config.py -v
  ```
  Expected: FAIL (ModuleNotFoundError: No module named 'scraper.config')

- [ ] **Step 5: Tulis konfigurasi di scraper/config.py**
  Buat file `scraper/config.py` untuk mendefinisikan target RSS beserta selector tag teks artikel utamanya:
  ```python
  # filepath: scraper/config.py

  FEED_SOURCES = [
      {
          "name": "Detik Travel",
          "url": "https://rss.detik.com/index.php/travel",
          "category": "flight",
          "selector": "article.detail, .detail__body-text"
      },
      {
          "name": "Detik Food",
          "url": "https://rss.detik.com/index.php/food",
          "category": "food",
          "selector": "article.detail, .detail__body-text"
      },
      {
          "name": "Antara News Lifestyle",
          "url": "https://www.antaranews.com/rss/lifestyle.xml",
          "category": "food",
          "selector": "article.post, .post-content, .entry-content"
      }
  ]
  ```

- [ ] **Step 6: Jalankan test dan pastikan berhasil**
  Jalankan perintah:
  ```bash
  PYTHONPATH=. .venv/bin/pytest tests/test_config.py -v
  ```
  Expected: PASS

- [ ] **Step 7: Komit hasil kerja**
  ```bash
  git add requirements.txt scraper/config.py tests/test_config.py
  git commit -m "feat: add dependencies and feed sources configuration"
  ```

---

### Task 2: Implementasi RSS Checker & BeautifulSoup Extractor

**Files:**
- Create: `scraper/rss_scraper.py`
- Test: `tests/test_rss_scraper.py`

- [ ] **Step 1: Tulis unit test untuk penarikan artikel**
  Buat file `tests/test_rss_scraper.py` dengan mock XML feed dan halaman HTML:
  ```python
  # filepath: tests/test_rss_scraper.py
  import pytest
  from unittest.mock import patch, MagicMock
  from scraper.rss_scraper import fetch_rss_entries, extract_article_text

  def test_fetch_rss_entries():
      mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
      <rss version="2.0">
          <channel>
              <item>
                  <title>Promo Tiket AirAsia 2026</title>
                  <link>https://travel.detik.com/promo-airasia</link>
                  <description>Diskon heboh tengah tahun</description>
              </item>
          </channel>
      </rss>"""
      
      with patch('requests.get') as mock_get:
          mock_get.return_value.status_code = 200
          mock_get.return_value.content = mock_xml.encode('utf-8')
          
          entries = fetch_rss_entries("https://mock-rss-url.xml")
          assert len(entries) == 1
          assert entries[0]["title"] == "Promo Tiket AirAsia 2026"
          assert entries[0]["link"] == "https://travel.detik.com/promo-airasia"

  def test_extract_article_text():
      html_content = """
      <html>
          <body>
              <div class="nav">Menu Navigasi</div>
              <article class="detail">
                  <h1 class="title">Judul Promo</h1>
                  <div class="detail__body-text">
                      <p>Dapatkan potongan Rp 50.000 di Starbucks!</p>
                      <script>alert('ads')</script>
                  </div>
              </article>
              <div class="footer">Footer Info</div>
          </body>
      </html>
      """
      text = extract_article_text(html_content, "article.detail, .detail__body-text")
      assert "Dapatkan potongan" in text
      assert "Menu Navigasi" not in text
      assert "alert" not in text
  ```

- [ ] **Step 2: Jalankan test dan pastikan gagal**
  Jalankan perintah:
  ```bash
  PYTHONPATH=. .venv/bin/pytest tests/test_rss_scraper.py -v
  ```
  Expected: FAIL (ModuleNotFoundError: No module named 'scraper.rss_scraper')

- [ ] **Step 3: Implementasi logika scraping di scraper/rss_scraper.py**
  Buat file `scraper/rss_scraper.py`:
  ```python
  # filepath: scraper/rss_scraper.py
  import requests
  import feedparser
  from bs4 import BeautifulSoup

  USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

  def fetch_rss_entries(feed_url):
      try:
          headers = {"User-Agent": USER_AGENT}
          response = requests.get(feed_url, headers=headers, timeout=15)
          if response.status_code != 200:
              return []
          
          feed = feedparser.parse(response.content)
          entries = []
          for entry in feed.entries:
              entries.append({
                  "title": entry.get("title", ""),
                  "link": entry.get("link", ""),
                  "description": entry.get("summary", entry.get("description", ""))
              })
          return entries
      except Exception as e:
          print(f"Error fetching RSS {feed_url}: {e}")
          return []

  def extract_article_text(html_content, css_selector):
      try:
          soup = BeautifulSoup(html_content, "html.parser")
          
          # Hapus elemen skrip, gaya, iframe, dan iklan
          for element in soup(["script", "style", "iframe", "noscript"]):
              element.decompose()
              
          # Cari area teks artikel utama
          target_area = None
          selectors = [s.strip() for s in css_selector.split(",")]
          for selector in selectors:
              target_area = soup.select_one(selector)
              if target_area:
                  break
                  
          if not target_area:
              target_area = soup.body if soup.body else soup
              
          text = target_area.get_text(separator=" ")
          # Bersihkan whitespace berlebih
          cleaned_text = " ".join(text.split())
          return cleaned_text
      except Exception as e:
          print(f"Error extracting article text: {e}")
          return ""

  def download_page_html(url):
      try:
          headers = {"User-Agent": USER_AGENT}
          response = requests.get(url, headers=headers, timeout=15)
          if response.status_code == 200:
              return response.text
          return ""
      except Exception as e:
          print(f"Error downloading page {url}: {e}")
          return ""
  ```

- [ ] **Step 4: Jalankan test dan pastikan berhasil**
  Jalankan perintah:
  ```bash
  PYTHONPATH=. .venv/bin/pytest tests/test_rss_scraper.py -v
  ```
  Expected: PASS

- [ ] **Step 5: Komit hasil kerja**
  ```bash
  git add scraper/rss_scraper.py tests/test_rss_scraper.py
  git commit -m "feat: implement RSS feed fetcher and BeautifulSoup article text extractor"
  ```

---

### Task 3: Implementasi Gemini AI Parser Terstruktur

**Files:**
- Create: `scraper/ai_parser.py`
- Test: `tests/test_ai_parser.py`

- [ ] **Step 1: Tulis unit test untuk AI Parser dengan Mock API**
  Buat file `tests/test_ai_parser.py`:
  ```python
  # filepath: tests/test_ai_parser.py
  import os
  import json
  import pytest
  from unittest.mock import patch, MagicMock
  from scraper.ai_parser import parse_with_gemini

  def test_parse_with_gemini_no_api_key():
      # Tanpa API key, harus mengembalikan None agar fallback ke regex berjalan
      if "GEMINI_API_KEY" in os.environ:
          del os.environ["GEMINI_API_KEY"]
          
      result = parse_with_gemini("Teks artikel promo", category="flight")
      assert result is None

  @patch('google.generativeai.GenerativeModel')
  def test_parse_with_gemini_success(mock_model_class):
      os.environ["GEMINI_API_KEY"] = "mock_key_here"
      
      mock_model = MagicMock()
      mock_response = MagicMock()
      mock_response.text = json.dumps({
          "title": "Promo AirAsia Murah",
          "description": "Diskon 20% tiket pesawat",
          "airline": "AirAsia",
          "origin_city": "Jakarta",
          "destination_city": "Bali",
          "promo_code": "AASCHOOL",
          "discount_value": "20%",
          "terms_and_conditions": "Min 2 tiket",
          "expired_date": "2026-07-31"
      })
      mock_model.generate_content.return_value = mock_response
      mock_model_class.return_value = mock_model
      
      result = parse_with_gemini("Teks artikel", category="flight")
      assert result is not None
      assert result["promo_code"] == "AASCHOOL"
      assert result["discount_value"] == "20%"
      assert result["airline"] == "AirAsia"
  ```

- [ ] **Step 2: Jalankan test dan pastikan gagal**
  Jalankan perintah:
  ```bash
  PYTHONPATH=. .venv/bin/pytest tests/test_ai_parser.py -v
  ```
  Expected: FAIL (ModuleNotFoundError: No module named 'scraper.ai_parser')

- [ ] **Step 3: Implementasi Gemini API parser terstruktur**
  Buat file `scraper/ai_parser.py`:
  ```python
  # filepath: scraper/ai_parser.py
  import os
  import json
  import google.generativeai as genai

  JSON_SCHEMA = {
      "type": "object",
      "properties": {
          "title": {"type": "string"},
          "description": {"type": "string"},
          "airline": {"type": "string", "nullable": True},
          "brand_name": {"type": "string", "nullable": True},
          "origin_city": {"type": "string", "nullable": True},
          "destination_city": {"type": "string", "nullable": True},
          "promo_code": {"type": "string", "nullable": True},
          "discount_value": {"type": "string", "nullable": True},
          "min_transaction": {"type": "string", "nullable": True},
          "locations": {"type": "string", "nullable": True},
          "terms_and_conditions": {"type": "string", "nullable": True},
          "expired_date": {"type": "string", "description": "Date format YYYY-MM-DD", "nullable": True}
      },
      "required": ["title", "description"]
  }

  def parse_with_gemini(text, category="flight"):
      api_key = os.environ.get("GEMINI_API_KEY")
      if not api_key:
          # Mengembalikan None agar memicu fallback otomatis ke Regex Parser lokal
          return None
          
      try:
          genai.configure(api_key=api_key)
          model = genai.GenerativeModel(
              model_name="gemini-1.5-flash",
              generation_config={
                  "response_mime_type": "application/json",
                  "response_schema": JSON_SCHEMA
              }
          )
          
          prompt = f"""
          Ekstrak informasi promosi kategori '{category}' dari artikel berita Indonesia berikut ini.
          Isi kolom fields sesuai skema JSON yang diberikan:
          - Jika kategori 'flight', cari informasi 'airline', 'origin_city', 'destination_city', dll.
          - Jika kategori 'food', cari informasi 'brand_name', 'min_transaction', 'locations', dll.
          - Terjemahkan tanggal masa berlaku promo ke format YYYY-MM-DD pada field 'expired_date'.
          - Masukkan syarat & ketentuan khusus ke 'terms_and_conditions'.
          
          Artikel Berita:
          ---
          {text}
          ---
          """
          
          response = model.generate_content(prompt)
          data = json.loads(response.text)
          return data
      except Exception as e:
          print(f"Error parsing with Gemini: {e}")
          return None
  ```

- [ ] **Step 4: Jalankan test dan pastikan berhasil**
  Jalankan perintah:
  ```bash
  PYTHONPATH=. .venv/bin/pytest tests/test_ai_parser.py -v
  ```
  Expected: PASS

- [ ] **Step 5: Komit hasil kerja**
  ```bash
  git add scraper/ai_parser.py tests/test_ai_parser.py
  git commit -m "feat: implement Gemini AI Parser with JSON Structured Outputs"
  ```

---

### Task 4: Integrasi Modul RSS & AI ke Ingestion Engine

**Files:**
- Modify: `scraper/engine.py`
- Test: `tests/test_engine.py`

- [ ] **Step 1: Tulis unit test integrasi**
  Ubah file `tests/test_engine.py` untuk menguji integrasi riil (atau simulasi penarikan riil via mock):
  ```python
  # filepath: tests/test_engine.py
  # Tambahkan pengujian baru untuk real ingestion flow
  import os
  import sqlite3
  import pytest
  from unittest.mock import patch, MagicMock
  from db.init_db import init_database
  from scraper.engine import run_scraping_job

  DB_FILE = "test_engine_integration.db"

  def setup_function():
      if os.path.exists(DB_FILE):
          os.remove(DB_FILE)
      init_database(DB_FILE)

  def teardown_function():
      if os.path.exists(DB_FILE):
          os.remove(DB_FILE)

  @patch('scraper.engine.fetch_rss_entries')
  @patch('scraper.engine.download_page_html')
  @patch('scraper.engine.extract_article_text')
  def test_run_scraping_job_real_flow(mock_extract, mock_download, mock_fetch):
      # Mock RSS entry
      mock_fetch.return_value = [
          {
              "title": "Diskon 50% KFC Akhir Pekan",
              "link": "https://food.detik.com/kfc-promo",
              "description": "KFC diskon heboh"
          }
      ]
      mock_download.return_value = "<html><body>Teks Lengkap KFC</body></html>"
      mock_extract.return_value = "KFC diskon 50% kode promo KFCFEAST s.d 2026-08-30."
      
      # Jalankan job riil (tanpa use_mock_source)
      run_scraping_job(DB_FILE, use_mock_source=False)
      
      conn = sqlite3.connect(DB_FILE)
      cursor = conn.conn = conn.cursor()
      cursor.execute("SELECT brand_name, promo_code, discount_value, source_url FROM food_promos")
      row = cursor.fetchone()
      assert row is not None
      assert row[0] == "KFC"
      assert row[1] == "KFCFEAST"
      assert row[2] == "50%"
      assert row[3] == "https://food.detik.com/kfc-promo"
      conn.close()
  ```

- [ ] **Step 2: Jalankan test dan pastikan gagal**
  Jalankan perintah:
  ```bash
  PYTHONPATH=. .venv/bin/pytest tests/test_engine.py -k test_run_scraping_job_real_flow -v
  ```
  Expected: FAIL (karena engine masih mem-bypass flow non-mock)

- [ ] **Step 3: Modifikasi scraper/engine.py untuk mengintegrasikan RSS & AI**
  Ubah file `scraper/engine.py` untuk mengintegrasikan `rss_scraper` dan `ai_parser` dengan skema fallback:
  ```python
  # filepath: scraper/engine.py
  import os
  import sqlite3
  from scraper.db_manager import DatabaseManager
  from scraper.parser import parse_promo_text
  from scraper.config import FEED_SOURCES
  from scraper.rss_scraper import fetch_rss_entries, download_page_html, extract_article_text
  from scraper.ai_parser import parse_with_gemini

  MOCK_FLIGHT_SOURCES = [
      # ... (data mock tetap dipertahankan untuk backward compatibility / testing) ...
  ]

  MOCK_FOOD_SOURCES = [
      # ... (data mock tetap dipertahankan) ...
  ]

  def run_scraping_job(db_path="promo.db", use_mock_source=True):
      if use_mock_source:
          # Logika mock tetap sama seperti sebelumnya
          _run_mock_scraping_job(db_path)
          return

      print("Starting real RSS Ingestion Engine...")
      with DatabaseManager(db_path) as db_mgr:
          
          # Loop target RSS feed dari config
          for source in FEED_SOURCES:
              print(f"Processing feed source: {source['name']}")
              entries = fetch_rss_entries(source["url"])
              
              for entry in entries:
                  url = entry["link"]
                  title = entry["title"]
                  
                  # Cek apakah URL sudah pernah di-scrape (Deduplikasi awal)
                  cursor = db_mgr.conn.cursor()
                  if source["category"] == "flight":
                      cursor.execute("SELECT id FROM flight_promos WHERE source_url=?", (url,))
                  else:
                      cursor.execute("SELECT id FROM food_promos WHERE source_url=?", (url,))
                      
                  if cursor.fetchone():
                      # Sudah pernah diproses, lewati
                      continue
                      
                  print(f"Scraping new article: {title} ({url})")
                  
                  # 1. Download Halaman Artikel Penuh
                  html = download_page_html(url)
                  if not html:
                      continue
                      
                  # 2. Ekstrak Teks Utama
                  article_text = extract_article_text(html, source["selector"])
                  if not article_text:
                      # Fallback menggunakan summary RSS jika web gagal diekstrak
                      article_text = entry["description"]
                      
                  # 3. Parsing Data (Hybrid: AI -> Regex)
                  parsed = None
                  if os.environ.get("GEMINI_API_KEY"):
                      print("Attempting to parse with Gemini AI...")
                      parsed = parse_with_gemini(article_text, category=source["category"])
                      
                  if not parsed:
                      print("Fallback: Parsing with local Regex Parser...")
                      parsed = parse_promo_text(article_text, category=source["category"])
                      
                  # 4. Tambahkan metadata sumber
                  parsed.update({
                      "title": title,
                      "description": article_text[:500],  # Simpan ringkasan teks artikel
                      "source_platform": "News",
                      "source_url": url
                  })
                  
                  # 5. Simpan ke Database
                  if source["category"] == "flight":
                      db_mgr.insert_flight_promo(parsed)
                  else:
                      db_mgr.insert_food_promo(parsed)
                      
      print("Real Ingestion Engine finished successfully.")

  def _run_mock_scraping_job(db_path):
      # Pindahkan logika mock lama ke fungsi pembantu internal ini
      with DatabaseManager(db_path) as db_mgr:
          for src in MOCK_FLIGHT_SOURCES:
              try:
                  parsed = parse_promo_text(src["text"], category="flight")
                  parsed.update({
                      "title": src["title"],
                      "description": src["text"],
                      "source_platform": src["platform"],
                      "source_url": src["source_url"]
                  })
                  db_mgr.insert_flight_promo(parsed)
              except Exception as e:
                  print(f"Error: {e}")
          for src in MOCK_FOOD_SOURCES:
              try:
                  parsed = parse_promo_text(src["text"], category="food")
                  parsed.update({
                      "title": src["title"],
                      "description": src["text"],
                      "source_platform": src["platform"],
                      "source_url": src["source_url"]
                  })
                  db_mgr.insert_food_promo(parsed)
              except Exception as e:
                  print(f"Error: {e}")
  ```

- [ ] **Step 4: Jalankan seluruh test dan pastikan semuanya lulus**
  Jalankan perintah:
  ```bash
  PYTHONPATH=. .venv/bin/pytest -v
  ```
  Expected: Semua unit test (termasuk test integrasi baru) lulus.

- [ ] **Step 5: Komit hasil integrasi**
  ```bash
  git add scraper/engine.py tests/test_engine.py
  git commit -m "feat: integrate RSS Deep Scraper and AI Parser into main Ingestion Engine"
  ```
