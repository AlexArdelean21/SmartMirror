import requests
from util.cache import get_cached_data, set_cache
from util.logger import logger


def get_crypto_prices():
    logger.info("Checking crypto price cache...")
    cached_data = get_cached_data("crypto")
    if cached_data:
        logger.debug(f"Using cached crypto data: {cached_data}")
        return cached_data

    logger.info("Fetching crypto prices from CoinGecko...")

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
            logger.info("Successfully fetched and cached crypto prices.")
            return prices
        else:
            logger.warning("⚠CoinGecko response missing expected data keys.")
            raise ValueError("Incomplete data from Crypto API")

    except requests.RequestException as e:
        logger.error(f"Network error while fetching crypto data: {e}")
        return {"error": "Failed to fetch cryptocurrency prices"}

    except Exception as e:
        logger.exception(f"Unexpected error in get_crypto_prices: {e}")
        return {"error": "Unexpected error occurred"}
