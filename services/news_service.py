import os
from dotenv import load_dotenv
import requests
from flask import jsonify
import logging
from logging.handlers import RotatingFileHandler


# Configure logging
if not os.path.exists('logs'):
    os.makedirs('logs')

import logging
from logging.handlers import RotatingFileHandler

# Configure log rotation
log_handler = RotatingFileHandler(
    'logs/error.log', maxBytes=5 * 1024 * 1024, backupCount=3  # 5MB per file, keep 3 backups
)
log_handler.setLevel(logging.ERROR)
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)

logger = logging.getLogger()
logger.setLevel(logging.ERROR)
logger.addHandler(log_handler)



load_dotenv()

def get_news():
    try:
        api_key = os.getenv("NEWS_API_KEY")
        country = os.getenv("NEWS_COUNTRY", "us")
        news_url = f"https://gnews.io/api/v4/top-headlines?country={country}&token={api_key}"
        response = requests.get(news_url)
        response.raise_for_status()
        data = response.json()

        if 'articles' in data:
            return {"articles": data['articles']}
        else:
            raise ValueError("Invalid response format from GNews")

    except (requests.RequestException, ValueError) as e:
        logging.error(f"Error fetching news data: {e}")
        return {"error": "Failed to fetch news data"}, 500

