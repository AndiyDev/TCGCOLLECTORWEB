"""
currency_utils.py
-----------------
Converts a monetary value from the app's base currency (SEK) to a target currency.

Exchange rates are approximate and can be updated here as needed.
If live rates are required, replace the rates dict with an API call
(e.g. https://api.exchangerate-api.com/v4/latest/SEK).
"""

# Rates: how much 1 SEK is worth in each supported currency (updated 2026)
EXCHANGE_RATES: dict[str, float] = {
    "SEK": 1.0,
    "USD": 0.092,   # 1 SEK ≈ 0.092 USD
    "EUR": 0.085,   # 1 SEK ≈ 0.085 EUR
    "GBP": 0.073,   # 1 SEK ≈ 0.073 GBP
    "NOK": 1.06,    # 1 SEK ≈ 1.06 NOK
    "DKK": 0.63,    # 1 SEK ≈ 0.63 DKK
}

CURRENCY_SYMBOLS: dict[str, str] = {
    "SEK": "kr",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "NOK": "kr",
    "DKK": "kr",
}

SUPPORTED_CURRENCIES: list[str] = list(EXCHANGE_RATES.keys())


def convert_price(val: float | None, target_currency: str) -> float:
    """
    Convert a value from SEK to the target currency.

    Args:
        val: Numeric value in SEK. None is treated as 0.
        target_currency: ISO currency code, e.g. 'USD'.

    Returns:
        Converted float, or 0.0 on error.
    """
    if val is None:
        return 0.0
    try:
        multiplier = EXCHANGE_RATES.get(target_currency, 1.0)
        return round(float(val) * multiplier, 2)
    except (ValueError, TypeError):
        return 0.0


def format_price(val: float | None, currency: str) -> str:
    """
    Return a nicely formatted price string, e.g. '$ 12.50' or '12 kr'.

    Args:
        val: Value in SEK.
        currency: Target currency code.

    Returns:
        Formatted string.
    """
    converted = convert_price(val, currency)
    symbol = CURRENCY_SYMBOLS.get(currency, currency)
    if currency in ("SEK", "NOK", "DKK"):
        return f"{converted:,.2f} {symbol}"
    return f"{symbol} {converted:,.2f}"
