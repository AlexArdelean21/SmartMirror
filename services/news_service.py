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
        api_key = os.environ.get("NEWS_API_KEY")
        if not api_key:
            return {"error": "Missing News API key"}, 400

        country = os.getenv("NEWS_COUNTRY", "us")
        news_url = f"https://gnews.io/api/v4/top-headlines?country={country}&token={api_key}"
        response = requests.get(news_url)

        if response.status_code == 401:
            return {"error": "Invalid API key"}, 401
        elif response.status_code == 403:
            return {"error": "Access denied to GNews API"}, 403
        elif response.status_code >= 500:
            return {"error": "News service unavailable"}, 503

        response.raise_for_status()
        data = response.json()

        if "articles" in data:
            set_cache("news", {"articles": data["articles"]})
            return {"articles": data["articles"]}
        else:
            return {"error": "Unexpected response format"}, 502

    except requests.RequestException as e:
        logging.error(f"News API error: {e}")
        return {"error": "Failed to fetch news"}, 500
