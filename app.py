from flask import Flask, jsonify, render_template
from services.weather_service import get_weather
from services.datetime_service import get_time_date
from services.news_service import get_news
from services.crypto_service import get_crypto_prices

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/time_date')
def time_date():
    return jsonify(get_time_date())

@app.route('/weather')
def weather():
    weather_data = get_weather()
    if "error" in weather_data:
        return jsonify(weather_data), 500
    return jsonify(weather_data)

@app.route('/news')
def news():
    return jsonify(get_news())

@app.route('/crypto')
def crypto():
    crypto_data = get_crypto_prices()
    if "error" in crypto_data:
        return jsonify(crypto_data), 500
    return jsonify(crypto_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
