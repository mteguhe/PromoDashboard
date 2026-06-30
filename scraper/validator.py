def validate_promo(parsed: dict) -> bool:
    if not isinstance(parsed, dict):
        return False
    if not parsed.get("title"):
        return False
    return any([
        parsed.get("promo_code"),
        parsed.get("discount_value"),
        parsed.get("expired_date"),
    ])
