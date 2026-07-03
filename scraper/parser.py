import re

def parse_promo_text(text, category="flight"):
    # Safety guard check
    if not text or not isinstance(text, str):
        if category == "flight":
            return {
                "promo_code": None,
                "discount_value": None,
                "expired_date": None,
                "terms_and_conditions": "",
                "airline": "Unknown Airline",
                "origin_city": "Jakarta",
                "destination_city": "Bali"
            }
        else:
            return {
                "promo_code": None,
                "discount_value": None,
                "expired_date": None,
                "terms_and_conditions": "",
                "brand_name": "Unknown Brand",
                "category": "F&B",
                "min_transaction": None,
                "locations": "Nasional"
            }

    # Regex patterns
    # Tighten code_pattern to enforce a colon for single-word prefix matches (like KODE/PROMO/CODE)
    # while leaving it optional for multi-word matches (like KODE PROMO). Supports case-insensitive/mixed-case codes.
    code_pattern = re.search(
        r"(?:(?i:KODE\s+PROMO|PROMO\s+CODE|PROMO_CODE)\s*:?\s*|(?i:KODE|PROMO|CODE)\s*:\s*)\b([A-Za-z0-9_-]+)\b",
        text
    )
    
    # Support intermediate filler words, Rp. with period, K slang, and cashback/cb/hemat in discount_pattern
    discount_pattern = re.search(
        r"(\d+%\s*(?:diskon|potongan|hemat)?|diskon\s*(?:hingga|s\.?d\.?|up\s*to|sampai)?\s*\d+%|(?:potongan|diskon|hemat|cashback|cb)\s*(?:hingga|s\.?d\.?|up\s*to|sampai)?\s*(?:Rp\.?\s*\d+[\d.,]*(?:\s*(?:ribu|rb|k))?|\d+[\d.,]*\s*(?:ribu|rb|k)))",
        text,
        re.IGNORECASE
    )
    # Indonesian price shorthand for flight promos: "990ribu", "3juta", "1,4juta", "PP 3jutaan"
    if not discount_pattern:
        discount_pattern = re.search(
            r"(?:Rp\.?\s*)?\b(\d+(?:[,.]\d+)?\s*(?:juta(?:an)?|ribu|rb))\b",
            text,
            re.IGNORECASE
        )
    
    # Contextual Expiry Date Extraction
    date_match = re.search(r'(?:hingga|s\.?d\.?|sampai|berlaku|expired|exp)\s*(?:tanggal\s*)?(\d{4}-\d{2}-\d{2})', text, re.IGNORECASE)
    if not date_match:
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
    expired_date = date_match.group(1).strip() if date_match else None
    
    promo_code = code_pattern.group(1).strip() if code_pattern else None
    
    discount_value = discount_pattern.group(1).strip() if discount_pattern else None
    if discount_value:
        # Strip out keywords and filler words from the extracted discount
        discount_value = re.sub(r"(?i)(?:diskon|potongan|hemat|cashback|cb|hingga|s\.?d\.?|up\s*to|sampai)\s*", "", discount_value)
        discount_value = re.sub(r"(?i)\s*(?:diskon|potongan|hemat|cashback|cb|hingga|s\.?d\.?|up\s*to|sampai)", "", discount_value)
        # Strip Rp. (with optional period)
        discount_value = re.sub(r"(?i)Rp\.?\s*", "", discount_value).strip()
    
    # Extract terms & conditions (sentence after S&K, Syarat, or Promo berlaku)
    terms_match = re.search(r'(?:S&K|Syarat & Ketentuan|Syarat|T&C|Promo berlaku)\s*:?\s*(.*)', text, re.IGNORECASE)
    terms = terms_match.group(1).strip().rstrip('.') if terms_match else ""
    
    # Classify category based on keywords
    lowered_text = text.lower()
    if any(w in lowered_text for w in ["flight", "penerbangan", "tiket pesawat", "maskapai", "garuda", "airasia", "citilink"]):
        detected_category = "flight"
    elif any(w in lowered_text for w in ["nonton", "cinema", "bioskop", "xxi", "cgv", "dufan", "trans studio", "rekreasi", "hiburan", "konser", "tiket masuk", "timezone", "timezone", "funworld", "wahana", "wisata", "taman bermain"]):
        detected_category = "entertainment"
    elif any(w in lowered_text for w in ["baju", "sepatu", "fashion", "uniqlo", "h&m", "matahari", "zara", "celana", "pakaian", "jeans", "tas", "sale", "great sale", "belanja", "shopping", "mall", "gramedia", "lottemart", "alfamidi", "supermarket", "minimarket"]):
        detected_category = "fashion"
    elif any(w in lowered_text for w in ["pameran", "event", "expo", "festival", "bazaar", "talkshow", "jobfair", "job fair", "wedding expo"]):
        detected_category = "event"
    else:
        detected_category = category if category != "flight" else "food"

    result = {
        "promo_code": promo_code,
        "discount_value": discount_value,
        "expired_date": expired_date,
        "terms_and_conditions": terms
    }
    
    if category == "flight":
        # Airline extraction
        airlines = ["Garuda Indonesia", "AirAsia", "Batik Air", "Lion Air", "Citilink", "Singapore Airlines"]
        extracted_airline = None
        for airline in airlines:
            if airline.lower() in text.lower():
                extracted_airline = airline
                break
        
        result.update({
            "airline": extracted_airline or "Unknown Airline",
            "origin_city": "Jakarta", # Default fallback
            "destination_city": "Bali" # Default fallback
        })
    else:
        # Food brand extraction
        brands = ["KFC", "McDonald", "Starbucks", "Kopi Kenangan", "Pizza Hut", "Burger King"]
        extracted_brand = None
        for brand in brands:
            if brand.lower() in text.lower():
                extracted_brand = brand
                break
                
        min_tx_match = re.search(r'(?:minimal pembelian|min transaksi|min purchase)\s*(Rp\s*\d+[\d.,]*|\d+[\d.,]*)', text, re.IGNORECASE)
        min_tx = min_tx_match.group(1).strip() if min_tx_match else None
        
        # Extract location if mentioned
        cities = ["Jakarta", "Bogor", "Depok", "Tangerang", "Bekasi", "Bandung", "Surabaya", "Yogyakarta", "Jogja", "Semarang", "Medan", "Makassar", "Bali"]
        extracted_location = None
        for city in cities:
            if city.lower() in text.lower():
                extracted_location = city
                break

        result.update({
            "brand_name": extracted_brand or "Unknown Brand",
            "category": detected_category,
            "min_transaction": min_tx,
            "locations": extracted_location or "Nasional"
        })
        
    return result
