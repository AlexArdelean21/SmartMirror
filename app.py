from flask import Flask, jsonify, render_template, request
from threading import Thread

from services.calendar_service import get_upcoming_events, add_event as calendar_add_event
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
    # No longer triggering the infinite loop here
    return jsonify({"text": "Voice assistant is running in the background.", "audio_url": None})

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
def add_event_route():
    data = request.json
    summary = data.get('summary')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    description = data.get('description')

    if not all([summary, start_time, end_time]):
        return jsonify({"error": "Missing required event details"}), 400

    result = calendar_add_event(summary, start_time, end_time, description)
    return jsonify(result)

@app.route('/add_face', methods=['POST'])
def add_face_route():
    data = request.json
    name = data.get("name")
    result = add_face_vocally(name)
    return jsonify(result)

@app.route('/recognize_faces', methods=['GET'])
def recognize_faces_route():
    recognize_faces_vocally()
    return jsonify({"status": "success", "message": "Recognition session completed"})

if __name__ == '__main__':
    # Launch voice assistant ONCE in background
    Thread(target=wait_for_wake_and_command, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
