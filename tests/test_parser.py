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
