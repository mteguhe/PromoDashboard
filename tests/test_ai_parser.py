import os
import json
import pytest
from unittest.mock import patch, MagicMock
from scraper.ai_parser import parse_with_gemini

def test_parse_with_gemini_no_api_key(monkeypatch):
    # Tanpa API key, harus mengembalikan None agar fallback ke regex berjalan
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        
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
