import requests
import logging
import time
from util.cache import get_cached_data, set_cache

def get_crypto_prices(retries=3, delay=5):
    cached_data = get_cached_data("crypto")
    if cached_data:
        return cached_data

    for attempt in range(retries):
        try:
            crypto_url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"
            response = requests.get(crypto_url)
            response.raise_for_status()
            data = response.json()

            if "bitcoin" in data and "ethereum" in data:
                prices = {
                    "bitcoin": data["bitcoin"]["usd"],
                    "ethereum": data["ethereum"]["usd"]
                }
                set_cache("crypto", prices)
                return prices
            else:
                raise ValueError("Incomplete data from Crypto API")

        except requests.RequestException as e:
            logging.error(f"Error fetching cryptocurrency data (Attempt {attempt+1}/{retries}): {e}")
            time.sleep(delay)  # Wait before retrying

    return {"error": "Failed to fetch cryptocurrency prices after multiple attempts"}
