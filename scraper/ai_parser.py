import os
import json
from typing import Optional
import google.generativeai as genai

_CATEGORY_HINTS = {
    "flight": "Fokus ekstrak: maskapai (brand_name), kota asal, kota tujuan, kode promo, diskon, tanggal kedaluwarsa.",
    "food": "Fokus ekstrak: nama brand/restoran (brand_name), minimal transaksi, lokasi berlaku, kode promo, besaran diskon.",
    "fashion": "Fokus ekstrak: nama brand pakaian/sepatu/tas (brand_name), persentase diskon, periode sale, minimal pembelian.",
    "entertainment": "Fokus ekstrak: nama venue/bioskop (brand_name), harga tiket, tanggal acara, kode promo.",
    "event": "Fokus ekstrak: nama event/pameran (brand_name), tanggal pelaksanaan, lokasi, harga tiket masuk.",
}

_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "is_promo": {"type": "boolean"},
        "confidence": {"type": "number", "description": "Confidence 0.0–1.0 that this is an active promo"},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "category": {"type": "string", "enum": ["flight", "food", "fashion", "event", "entertainment"]},
        "brand_name": {"type": "string", "nullable": True},
        "promo_code": {"type": "string", "nullable": True},
        "discount_value": {"type": "string", "nullable": True},
        "min_transaction": {"type": "string", "nullable": True},
        "expired_date": {"type": "string", "description": "Format YYYY-MM-DD", "nullable": True},
        "terms_and_conditions": {"type": "string", "nullable": True},
    },
    "required": [
        "is_promo", "confidence", "title", "description", "category",
        "brand_name", "promo_code", "discount_value", "min_transaction",
        "expired_date", "terms_and_conditions",
    ],
}

def parse_with_gemini(text: str, category: str = "flight") -> Optional[dict]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": _JSON_SCHEMA,
            },
        )
        hint = _CATEGORY_HINTS.get(category, "")
        prompt = f"""Analisis teks berikut dan tentukan apakah ini adalah artikel promo/diskon aktif.

ATURAN PENTING:
- Jika artikel hanya berisi berita umum, resep, tips, atau opini TANPA penawaran diskon/promo aktif yang spesifik, set is_promo=false dan confidence di bawah 0.5.
- Jika artikel berisi promo aktif dengan diskon nyata atau kode promo, set is_promo=true.
- {hint}
- Terjemahkan tanggal kedaluwarsa ke format YYYY-MM-DD.

Teks:
---
{text}
---"""
        response = model.generate_content(prompt)
        data = json.loads(response.text)

        if not data.get("is_promo"):
            return None
        if data.get("confidence", 0) < 0.7:
            return None

        return data
    except Exception as e:
        print(f"[ai_parser] Gemini error: {e}")
        return None
