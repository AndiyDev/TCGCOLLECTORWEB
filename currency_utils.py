def convert_price(val, target):
    rates = {"SEK": 11.50, "USD": 1.08, "EUR": 1.00}
    try:
        return float(val) * rates.get(target, 1.0)
    except (ValueError, TypeError):
        return 0.0