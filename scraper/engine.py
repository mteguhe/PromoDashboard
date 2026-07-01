import os
from scraper.db_manager import DatabaseManager
from scraper.config import FEED_SOURCES, PORTAL_SOURCES, SOCIAL_ACCOUNTS, OTA_SOURCES
from scraper.adapters.portal_adapter import PortalAdapter
from scraper.adapters.social_adapter import SocialAdapter
from scraper.adapters.rss_adapter import RssAdapter
from scraper.adapters.ota_adapter import OtaAdapter
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
        OtaAdapter(OTA_SOURCES),
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
