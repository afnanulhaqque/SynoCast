import requests
import logging
import sqlite3
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def get_exchange_rates(api_key=None, base_currency="USD"):
    from app.database import get_db
    
    try:
        with get_db() as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT rate, target_currency FROM currency_rates WHERE base_currency = ? AND last_updated > ?", 
                      (base_currency, (datetime.now() - timedelta(hours=24)).isoformat()))
            cached_rows = c.fetchall()
            cached_rates = {row['target_currency']: row['rate'] for row in cached_rows}
            if cached_rates: return cached_rates
    except Exception as e:
        logger.error(f"Error fetching cached rates: {e}")

    default_rates = {
        "USD": 1.0, "EUR": 0.92, "GBP": 0.79, "JPY": 150.25, "CNY": 7.21, 
        "PKR": 278.50, "INR": 82.95, "AUD": 1.53, "CAD": 1.35
    }
    
    if not api_key: return default_rates
        
    try:
        url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base_currency}"
        res = requests.get(url, timeout=10)
        if res.ok:
            data = res.json()
            rates = data.get('conversion_rates', {})
            from app.database import get_db
            with get_db() as conn:
                for target, rate in rates.items():
                    conn.execute("""
                        INSERT OR REPLACE INTO currency_rates (base_currency, target_currency, rate, last_updated)
                        VALUES (?, ?, ?, ?)
                    """, (base_currency, target, rate, datetime.now().isoformat()))
                conn.commit()
            return rates
    except Exception as e:
        logger.error(f"Error fetching exchange rates from API: {e}")
        
    return default_rates

def convert_currency(amount, from_curr, to_curr, rates=None):
    if from_curr == to_curr: return amount
    if not rates: rates = get_exchange_rates()
    
    if from_curr != "USD":
        from_rate = rates.get(from_curr, 1)
        amount_usd = amount / from_rate if from_rate else amount
    else:
        amount_usd = amount
        
    to_rate = rates.get(to_curr, 1)
    return amount_usd * to_rate

def get_travel_cost_insights(lat, lon, currency_pref="USD"):
    base_prices = {
        "umbrella": 15.0,
        "sunscreen": 12.0,
        "winter_jacket": 80.0,
        "cold_drink": 3.0,
        "hot_coffee": 4.0
    }
    rates = get_exchange_rates()
    return {item: round(convert_currency(price, "USD", currency_pref, rates), 2) 
            for item, price in base_prices.items()}
