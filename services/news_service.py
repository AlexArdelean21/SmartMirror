import os
from dotenv import load_dotenv
import requests
import logging
from util.cache import get_cached_data, set_cache

load_dotenv()

def get_news():
    cached_data = get_cached_data("news")
    if cached_data:
        return cached_data

    try:
        api_key = os.getenv("NEWS_API_KEY")
        country = os.getenv("NEWS_COUNTRY", "us")
        news_url = f"https://gnews.io/api/v4/top-headlines?country={country}&token={api_key}"
        response = requests.get(news_url)
        response.raise_for_status()
        data = response.json()

        if 'articles' in data:
            set_cache("news", {"articles": data['articles']})  # Store in cache
            return {"articles": data['articles']}
        else:
            raise ValueError("Invalid response format from GNews")

    except (requests.RequestException, ValueError) as e:
        logging.error(f"Error fetching news data: {e}")
        return {"error": "Failed to fetch news data"}, 500
