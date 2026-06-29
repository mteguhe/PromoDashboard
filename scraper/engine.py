import os
import sqlite3
from scraper.db_manager import DatabaseManager
from scraper.parser import parse_promo_text
from scraper.config import FEED_SOURCES
from scraper.rss_scraper import fetch_rss_entries, download_page_html, extract_article_text
from scraper.ai_parser import parse_with_gemini

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

if __name__ == "__main__":
    # Inisialisasi database lokal jika dijalankan mandiri
    from db.init_db import init_database
    init_database()
    run_scraping_job()
