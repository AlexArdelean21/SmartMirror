import os
from dotenv import load_dotenv
import requests
import logging
from util.cache import get_cached_data, set_cache

load_dotenv()

def get_weather():
    cached_data = get_cached_data("weather")
    if cached_data:
        return cached_data

    try:
        api_key = os.environ.get("WEATHER_API_KEY")
        if not api_key:
            return {"error": "Missing API key"}, 400

        location = os.getenv("LOCATION", "Bucharest")
        weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
        response = requests.get(weather_url)

        if response.status_code == 401:
            return {"error": "Invalid API key"}, 401
        elif response.status_code == 404:
            return {"error": f"City '{location}' not found"}, 404
        elif response.status_code >= 500:
            return {"error": "Weather service unavailable"}, 503

        response.raise_for_status()
        data = response.json()

        if 'main' in data and 'weather' in data:
            weather_data = {
                "main": {"temp": data['main']['temp']},
                "weather": [{"description": data['weather'][0]['description'],
                             "icon": f"http://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png"}]
            }
            set_cache("weather", weather_data)
            return weather_data
        else:
            return {"error": "Unexpected response format"}, 502

    except requests.RequestException as e:
        logging.error(f"Weather API error: {e}")
        return {"error": "Failed to retrieve weather data"}, 500