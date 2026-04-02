def convert_price(val, target_currency):
    """
    Konverterar ett värde från basvalutan (SEK) till vald målvaluta.
    Baserat på fasta växelkurser (våren 2024-ish).
    """
    # Vi utgår från att 1 SEK är basen i din databas.
    # Kurserna här är: Hur mycket är 1 SEK värd i den valutan?
    rates = {
        "SEK": 1.0,
        "USD": 0.094,  # 1 SEK ≈ 0.094 USD
        "EUR": 0.087,  # 1 SEK ≈ 0.087 EUR
    }
    
    try:
        # Om värdet är None eller inte ett tal, returnera 0.0
        if val is None:
            return 0.0
            
        multiplier = rates.get(target_currency, 1.0)
        return float(val) * multiplier
        
    except (ValueError, TypeError):
        return 0.0