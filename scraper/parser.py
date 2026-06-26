import re

def parse_promo_text(text, category="flight"):
    # Regex patterns
    # Using case-insensitive keyword prefix, but case-sensitive matching for the uppercase/digit promo code
    code_pattern = re.search(r'(?i:KODE\s+PROMO|KODE|PROMO|CODE)\s*:?\s*([A-Z0-9]+)', text)
    discount_pattern = re.search(r'(\d+%\s*(?:diskon|potongan)?|diskon\s*\d+%|potongan\s*(?:Rp\s*\d+[\d.,]*|\d+[\d.,]*\s*ribu))', text, re.IGNORECASE)
    date_pattern = re.search(r'(\d{4}-\d{2}-\d{2})', text)
    
    promo_code = code_pattern.group(1).strip() if code_pattern else None
    
    discount_value = discount_pattern.group(1).strip() if discount_pattern else None
    if discount_value:
        # Clean up prefix/suffix like "diskon" or "potongan"
        discount_value = re.sub(r'(diskon|potongan)\s*', '', discount_value, flags=re.IGNORECASE)
        discount_value = re.sub(r'\s*(diskon|potongan)', '', discount_value, flags=re.IGNORECASE).strip()
    
    expired_date = date_pattern.group(1).strip() if date_pattern else None
    
    # Extract terms & conditions (sentence after S&K, Syarat, or Promo berlaku)
    terms_match = re.search(r'(?:S&K|Syarat & Ketentuan|Syarat|T&C|Promo berlaku)\s*:?\s*(.*)', text, re.IGNORECASE)
    terms = terms_match.group(1).strip().rstrip('.') if terms_match else ""
    
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
        
        result.update({
            "brand_name": extracted_brand or "Unknown Brand",
            "category": "F&B",
            "min_transaction": min_tx,
            "locations": "Nasional"
        })
        
    return result
