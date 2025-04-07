import os
import requests
from dotenv import load_dotenv
from util.cache import get_cached_data, set_cache
from util.logger import logger

load_dotenv()

def get_news():
    logger.info("Checking news cache...")
    cached_data = get_cached_data("news")
    if cached_data:
        logger.debug(f"Using cached news data: {cached_data}")
        return cached_data

    logger.info("Fetching top headlines from GNews API...")

    try:
        api_key = os.getenv("NEWS_API_KEY")
        country = os.getenv("NEWS_COUNTRY", "us")
        news_url = f"https://gnews.io/api/v4/top-headlines?country={country}&token={api_key}"

        response = requests.get(news_url)
        response.raise_for_status()
        data = response.json()

        if 'articles' in data:
            result = {"articles": data['articles']}
            set_cache("news", result)
            logger.info("News data fetched and cached successfully.")
            return result
        else:
            logger.warning("⚠nexpected structure in GNews API response.")
            raise ValueError("Missing 'articles' in news API response.")

    except requests.RequestException as e:
        logger.error(f"Failed to fetch news data: {e}")
        return {"error": "Failed to fetch news data"}, 500

    except Exception as e:
        logger.exception(f"Unexpected error in get_news: {e}")
        return {"error": "Unexpected error occurred"}, 500
