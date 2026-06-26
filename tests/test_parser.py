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

def test_parse_rupiah_discount_using_diskon():
    text = "Dapatkan diskon Rp 50.000 untuk tiket Citilink. Promo code: CITILINK-50. S&K: berlaku s.d 2026-10-10."
    result = parse_promo_text(text, category="flight")
    
    assert result["promo_code"] == "CITILINK-50"
    assert result["discount_value"] == "Rp 50.000"
    assert result["airline"] == "Citilink"
    assert result["expired_date"] == "2026-10-10"

def test_parse_promo_code_special_characters():
    text = "Gunakan kode promo KFC_FEAST-99 untuk dapat diskon Rp 50.000 di KFC. Syarat: Berlaku s.d 2026-12-31."
    result = parse_promo_text(text, category="food")
    
    assert result["promo_code"] == "KFC_FEAST-99"
    assert result["discount_value"] == "Rp 50.000"
    assert result["brand_name"] == "KFC"
    assert result["expired_date"] == "2026-12-31"

def test_parse_safety_guard():
    # Test None
    res1 = parse_promo_text(None, category="flight")
    assert res1["promo_code"] is None
    assert res1["airline"] == "Unknown Airline"
    assert res1["origin_city"] == "Jakarta"
    
    # Test non-string input (integer)
    res2 = parse_promo_text(12345, category="food")
    assert res2["promo_code"] is None
    assert res2["brand_name"] == "Unknown Brand"
    assert res2["min_transaction"] is None
    
    # Test empty string
    res3 = parse_promo_text("", category="flight")
    assert res3["promo_code"] is None
