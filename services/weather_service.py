import os
from dotenv import load_dotenv
import requests
import time
import logging
from logging.handlers import RotatingFileHandler

cache = {}
CACHE_TIMEOUT = 300  # Cache for 5 minutes

# Configure logging
if not os.path.exists('logs'):
    os.makedirs('logs')

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

def get_weather():
    cached_data = get_cached_data("weather")
    if cached_data:
        return cached_data

    try:
        api_key = os.getenv("WEATHER_API_KEY")
        location = os.getenv("LOCATION")
        weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
        response = requests.get(weather_url)
        response.raise_for_status()
        data = response.json()

        if 'main' in data and 'temp' in data['main'] and 'weather' in data:
            temp_celsius = data['main']['temp']
            description = data['weather'][0]['description']
            icon = f"http://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png"

            weather_data = {
                "main": {"temp": temp_celsius},
                "weather": [{"description": description, "icon": icon}]
            }

            set_cache("weather", weather_data)
            return weather_data
        else:
            raise ValueError("Incomplete data in Weather API response")

    except (requests.RequestException, ValueError) as e:
        logging.error(f"Error fetching weather data: {e}")
        return {"error": "Failed to fetch weather data"}, 500

def get_cached_data(key):
    if key in cache and (time.time() - cache[key]["timestamp"] < CACHE_TIMEOUT):
        return cache[key]["data"]
    return None

def set_cache(key, data):
    cache[key] = {"data": data, "timestamp": time.time()}