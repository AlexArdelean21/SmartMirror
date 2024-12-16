import os
from dotenv import load_dotenv
import requests
from flask import jsonify

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
        print(f"Error fetching weather data: {e}")
        print("Weather API Response:", response.text)  # Log the raw response for debugging
        return {"error": "Failed to fetch weather data"}, 500

