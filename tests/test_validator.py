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
