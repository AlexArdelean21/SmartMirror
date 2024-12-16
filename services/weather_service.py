import os
from dotenv import load_dotenv
import requests
from flask import jsonify

load_dotenv()

def get_weather():
    try:
        api_key = os.getenv("WEATHER_API_KEY")
        location = os.getenv("LOCATION")
        weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}"
        response = requests.get(weather_url)
        response.raise_for_status()
        data = response.json()

        # Validate response
        if 'main' in data and 'temp' in data['main']:
            temp_kelvin = data['main']['temp']
            temp_celsius = round(temp_kelvin - 273.15, 2)
            return {
                "main": {"temp": temp_celsius},
                "weather": [{"description": data['weather'][0]['description']}]
            }

        else:
            raise ValueError("Missing temperature data in API response")


    except (requests.RequestException, ValueError) as e:
        print(f"Error fetching weather data: {e}")
        print("Weather API Response:", response.text)  # Log full API response
        return {"error": "Failed to fetch weather data"}, 500