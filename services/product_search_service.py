import requests
from util.logger import logger
import os

FAKESTORE_API = os.getenv("FAKESTORE_API")

def get_clothing_items(category="men's clothing", color=None, max_price=None):
    try:
        response = requests.get(f"{FAKESTORE_API}/category/{category}")
        response.raise_for_status()
        items = response.json()

        filtered = []
        for item in items:
            title = item["title"].lower()

            if color and color.lower() not in title:
                continue

            if max_price and item["price"] > max_price:
                continue

            filtered.append({
                "title": item["title"],
                "price": item["price"],
                "image_url": item["image"],
                "id": item["id"]
            })

        logger.info(f"Found {len(filtered)} matching clothing items.")
        return filtered[:3]  # return top 3 matches

    except Exception as e:
        logger.exception(f"Failed to fetch clothing items: {e}")
        return []
