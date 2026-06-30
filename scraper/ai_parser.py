import os
import json
import google.generativeai as genai

JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "is_promo": {"type": "boolean", "description": "True if this article contains a specific, active promo, discount, or deal. False if it is just a general news article, tips, recipe, or lifestyle post without any active offer."},
        "category": {"type": "string", "enum": ["flight", "food", "fashion", "event", "entertainment"], "description": "Classify the promo into one of these categories based on its content."},
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
    "required": [
        "title", 
        "description", 
        "is_promo", 
        "category",
        "airline", 
        "brand_name", 
        "origin_city", 
        "destination_city", 
        "promo_code", 
        "discount_value", 
        "min_transaction", 
        "locations", 
        "terms_and_conditions", 
        "expired_date"
    ]
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
        Ekstrak informasi promosi dari artikel berita Indonesia berikut ini.
        Isi kolom fields sesuai skema JSON yang diberikan:
        - Tentukan apakah artikel ini benar-benar berisi promo aktif pada field 'is_promo'. Jika hanya berisi berita umum, resep, atau tips tanpa penawaran/diskon khusus, set 'is_promo' ke false.
        - Klasifikasikan kategori promo ke dalam salah satu dari: 'flight' (penerbangan), 'food' (makanan & minuman), 'fashion' (pakaian/sepatu/tas), 'event' (pameran/bazaar/festival), atau 'entertainment' (nonton/bioskop/tiket rekreasi/wisata) pada field 'category'.
        - Jika kategori 'flight', cari informasi 'airline', 'origin_city', 'destination_city', dll.
        - Jika kategori 'food', 'fashion', 'event', atau 'entertainment', cari informasi 'brand_name', 'min_transaction', 'locations', dll.
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
