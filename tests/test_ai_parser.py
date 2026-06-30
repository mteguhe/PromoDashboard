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
