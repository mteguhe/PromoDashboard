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
    # Use context manager for DatabaseManager
    with DatabaseManager(db_path) as db_mgr:
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
            
        print("Ingestion engine execution finished.")

if __name__ == "__main__":
    # Inisialisasi database lokal jika dijalankan mandiri
    from db.init_db import init_database
    init_database()
    run_scraping_job()
