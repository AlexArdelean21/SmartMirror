import os
from dotenv import load_dotenv
import requests
import logging
from util.cache import get_cached_data, set_cache

load_dotenv()

def get_weather():
    cached_data = get_cached_data("weather")
    if cached_data:
        return cached_data  # Return cached weather data if available

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

            set_cache("weather", weather_data)  # Save data to cache
            return weather_data
        else:
            raise ValueError("Incomplete data in Weather API response")

    except (requests.RequestException, ValueError) as e:
        logging.error(f"Error fetching weather data: {e}")
        return {"error": "Failed to fetch weather data"}, 500
