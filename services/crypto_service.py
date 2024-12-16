import requests
from flask import jsonify

def get_crypto_prices():
    try:
        crypto_url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"
        response = requests.get(crypto_url)
        response.raise_for_status()
        data = response.json()

        # Extract prices
        return {
            "bitcoin": data["bitcoin"]["usd"],
            "ethereum": data["ethereum"]["usd"]
        }
    except requests.RequestException as e:
        print(f"Error fetching cryptocurrency data: {e}")
        return {"error": "Failed to fetch cryptocurrency prices"}
