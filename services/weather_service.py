import os
import requests
from dotenv import load_dotenv
from util.cache import get_cached_data, set_cache
from util.logger import logger

load_dotenv()

def get_weather():
    logger.info("Checking weather cache...")
    cached_data = get_cached_data("weather")
    if cached_data:
        logger.debug(f"Using cached weather data: {cached_data}")
        return cached_data

    logger.info("Fetching current weather data from OpenWeatherMap...")

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
            logger.info("Weather data fetched and cached successfully.")
            return weather_data
        else:
            logger.warning("Incomplete data received from weather API.")
            raise ValueError("Missing keys in weather API response.")

    except requests.RequestException as e:
        logger.error(f"Failed to fetch weather data: {e}")
        return {"error": "Failed to fetch weather data"}, 500

    except Exception as e:
        logger.exception(f"Unexpected error in get_weather: {e}")
        return {"error": "Unexpected error occurred"}, 500
