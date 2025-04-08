import os
import requests
from dotenv import load_dotenv
from util.cache import get_cached_data, set_cache
from util.logger import logger

load_dotenv()

def get_news(topics=None):
    logger.info("Checking news cache...")

    # Build a cache key that changes based on topic
    if not topics:
        topics = ["technology"]
    cache_key = f"news_{'_'.join(topics)}"

    cached_data = get_cached_data(cache_key)
    if cached_data:
        logger.debug(f"Using cached news data: {cached_data}")
        return cached_data

    logger.info(f"Fetching news from GNews for topics: {topics}")

    try:
        api_key = os.getenv("NEWS_API_KEY")
        query = " OR ".join(topics)
        news_url = f"https://gnews.io/api/v4/search?q={query}&lang=en&max=10&token={api_key}"

        response = requests.get(news_url)
        response.raise_for_status()
        data = response.json()

        if 'articles' in data:
            result = {"articles": data['articles']}
            set_cache(cache_key, result)
            logger.info("News data fetched and cached successfully.")
            return result
        else:
            logger.warning("⚠ Unexpected structure in GNews API response.")
            raise ValueError("Missing 'articles' in news API response.")

    except requests.RequestException as e:
        logger.error(f"Failed to fetch news data: {e}")
        return {"error": "Failed to fetch news data"}, 500

    except Exception as e:
        logger.exception(f"Unexpected error in get_news: {e}")
        return {"error": "Unexpected error occurred"}, 500
