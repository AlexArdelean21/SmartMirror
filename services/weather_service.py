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

def get_weather():
    try:
        api_key = os.getenv("WEATHER_API_KEY")
        location = os.getenv("LOCATION")
        weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
        response = requests.get(weather_url)
        response.raise_for_status()
        data = response.json()

        # Validate response keys
        if 'main' in data and 'temp' in data['main']:
            temp_celsius = data['main']['temp']
            description = data['weather'][0]['description'] if 'weather' in data else "No description"
            icon = f"http://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png"
            return {
                "main": {"temp": temp_celsius},
                "weather": [{"description": description, "icon": icon}]
            }
        else:
            raise ValueError("Incomplete data in Weather API response")


    except (requests.RequestException, ValueError) as e:
        logging.error(f"Error fetching weather data: {e}")
        logging.error(f"Weather API Response: {response.text if 'response' in locals() else 'No response'}")
        return {"error": "Failed to fetch weather data"}, 500
