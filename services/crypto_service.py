import requests
import time
import logging

cache = {}
CACHE_TIMEOUT = 300  # Cache for 5 minutes

def get_cached_data(key):
    if key in cache and (time.time() - cache[key]["timestamp"] < CACHE_TIMEOUT):
        return cache[key]["data"]
    return None

def set_cache(key, data):
    cache[key] = {"data": data, "timestamp": time.time()}


def get_crypto_prices():
    cached_data = get_cached_data("crypto")
    if cached_data:
        return cached_data

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
            set_cache("crypto", prices)  # Store in cache
            return prices
        else:
            raise ValueError("Incomplete data from Crypto API")

    except requests.RequestException as e:
        logging.error(f"Error fetching cryptocurrency data: {e}")
        return {"error": "Failed to fetch cryptocurrency prices"}

