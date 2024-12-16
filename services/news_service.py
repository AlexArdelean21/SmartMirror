import os
from dotenv import load_dotenv
import requests
from flask import jsonify

load_dotenv()

def get_news():
    try:
        api_key = os.getenv("NEWS_API_KEY")
        country = "ro"  # Romania
        news_url = f"https://gnews.io/api/v4/top-headlines?country={country}&token={api_key}"
        response = requests.get(news_url)
        response.raise_for_status()
        data = response.json()

        if 'articles' in data:
            return {"articles": data['articles']}
        else:
            raise ValueError("Invalid response format from GNews")
    except (requests.RequestException, ValueError) as e:
        print(f"Error fetching news data: {e}")
        return jsonify({"error": "Failed to fetch news data"}), 500
