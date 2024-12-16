from flask import Flask, jsonify, render_template
from services.weather_service import get_weather
from services.datetime_service import get_time_date
from services.news_service import get_news

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
