from flask import Flask, jsonify, render_template, request

from services.calendar_service import get_upcoming_events, add_event
from services.voice_service import wait_for_wake_and_command
from services.weather_service import get_weather
from services.datetime_service import get_time_date
from services.news_service import get_news
from services.crypto_service import get_crypto_prices
from flask_caching import Cache
from services.facial_recognition_service import add_face_vocally, recognize_faces_vocally


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
    response = wait_for_wake_and_command()
    print(f"Voice Command Response: {response}")
    return jsonify({"response": response})

@app.route('/refresh')
def refresh():
    cache.clear()
    return jsonify({"status": "Cache cleared", "message": "Data will refresh on next request."})

@app.route('/calendar')
def calendar():
    events = get_upcoming_events()
    if "error" in events:
        return jsonify(events), 500
    if len(events) == 0:
        return jsonify({"message": "No upcoming events"}), 200
    return jsonify(events)


@app.route('/add_event', methods=['POST'])
def add_event():
    data = request.json
    summary = data.get('summary')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    description = data.get('description')

    if not all([summary, start_time, end_time]):
        return jsonify({"error": "Missing required event details"}), 400

    result = add_event(summary, start_time, end_time, description)
    return jsonify(result)

@app.route('/add_face', methods=['POST'])
def add_face_route():
    data = request.json
    name = data.get("name")
    image_path = data.get("image_path")
    result = add_face(name, image_path)
    return jsonify(result)

@app.route('/recognize_faces', methods=['GET'])
def recognize_faces_route():
    recognize_faces()
    return jsonify({"status": "success", "message": "Recognition session completed"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
