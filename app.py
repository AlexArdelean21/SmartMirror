from flask import Flask, jsonify, render_template
from services.weather_service import get_weather
from services.datetime_service import get_time_date
from services.news_service import get_news
from services.crypto_service import get_crypto_prices
from flask_caching import Cache
from services.voice_service import listen_command, speak_response


app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300})  # 5-minute cache

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/time_date')
def time_date():
    return jsonify(get_time_date())

@app.route('/weather')
@cache.cached(timeout=300)  # Cache for 5 minutes
def weather():
    weather_data = get_weather()
    if "error" in weather_data:
        return jsonify(weather_data), 500
    return jsonify(weather_data)

@app.route('/news')
@cache.cached(timeout=300)  # Cache for 5 minutes
def news():
    return jsonify(get_news())

@app.route('/crypto')
@cache.cached(timeout=300)  # Cache for 5 minutes
def crypto():
    crypto_data = get_crypto_prices()
    if "error" in crypto_data:
        return jsonify(crypto_data), 500
    return jsonify(crypto_data)

@app.route('/voice_command')
def voice_command():
    command = listen_command()
    if "weather" in command:
        weather_data = get_weather()
        response = f"The current weather is {weather_data['weather'][0]['description']}, {weather_data['main']['temp']} degrees Celsius."
    elif "news" in command:
        news_data = get_news()
        response = f"Here’s the top news headline: {news_data['articles'][0]['title']}"
    elif "crypto" in command:
        crypto_data = get_crypto_prices()
        response = f"Bitcoin is {crypto_data['bitcoin']} dollars and Ethereum is {crypto_data['ethereum']} dollars."
    else:
        response = "Sorry, I did not understand the command."

    speak_response(response)
    return jsonify({"command": command, "response": response})


@app.route('/refresh')
def refresh():
    cache.clear()
    return jsonify({"status": "Cache cleared", "message": "Data will refresh on next request."})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
