from flask import Flask, jsonify, render_template, request, url_for
from threading import Thread
from util.session_state import get_active_profile
from services.calendar_service import get_upcoming_events, add_event as calendar_add_event
from services.weather_service import get_weather
from services.datetime_service import get_time_date
from services.news_service import get_news
from services.crypto_service import get_crypto_prices
from services.product_search_service import get_clothing_items
from util.socket_manager import socketio
from flask_caching import Cache
from services.facial_recognition_service import add_face_vocally, recognize_faces_vocally
import logging
import time
import os
from util.logger import logger

app = Flask(__name__)
socketio.init_app(app, cors_allowed_origins="*")
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300})  # 5-minute cache
werkzeug_log = logging.getLogger('werkzeug')
#werkzeug_log.setLevel(logging.WARNING)  # shows errors, needs to be  commented when i want to see endpoint calls

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
    audio_path = "static/audio_response.mp3"
    expiration_seconds = 10  # Only allow audio created in the last 10 seconds

    if os.path.exists(audio_path):
        last_modified = os.path.getmtime(audio_path)
        current_time = time.time()

        # Check if the file is fresh
        if current_time - last_modified < expiration_seconds:
            return jsonify({
                "text": "Voice assistant is responding...",
                "response_audio": url_for('static', filename='audio_response.mp3') + f"?t={int(current_time)}"
            })
        else:
            return jsonify({
                "text": "Voice assistant is running in the background.",
                "response_audio": None
            })

    return jsonify({
        "text": "Voice assistant is running in the background.",
        "response_audio": None
    })


@app.route('/refresh')
def refresh():
    cache.clear()
    return jsonify({"status": "Cache cleared", "message": "Data will refresh on next request."})


@app.route("/calendar")
#@cache.cached(timeout=300)
def calendar():
    profile = get_active_profile()
    if not profile:
        logger.info("Calendar access attempted without login.")
        return jsonify({"message": "Please log in to view your calendar."}), 200

    if profile.get("name", "").lower() != "alex":
        logger.info(f"Unauthorized calendar access by: {profile.get('name')}")
        return jsonify({"message": "This calendar is private."}), 200

    try:
        events = get_upcoming_events()
        return jsonify(events)
    except Exception as e:
        logger.exception(f"Error fetching calendar events: {e}")
        return jsonify({"error": "Failed to fetch calendar events"}), 500


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

@app.route("/find_clothing")
def find_clothing():
    profile = get_active_profile()
    if not profile:
        logger.info("Unauthorized try-on request — no user logged in.")
        return jsonify({"error": "You need to log in before using this feature."}), 403

    category = request.args.get("category", "men's clothing")
    color = request.args.get("color")
    max_price = request.args.get("max_price", type=float)

    logger.info(f"Finding clothing for {profile['name']}: category={category}, color={color}, max_price={max_price}")
    items = get_clothing_items(category=category, color=color, max_price=max_price)

    if not items:
        return jsonify({"message": "No matching items found."}), 404

    return jsonify(items)

@app.route('/test_tts')
def test_tts():
    """Test route to directly test text-to-speech"""
    from util.voice_utils import speak_response
    speak_response("Hello! This is a test of the text to speech system.")
    return jsonify({"message": "TTS test triggered"})

if __name__ == '__main__':
    from services.voice_service import wait_for_wake_and_command
    Thread(target=wait_for_wake_and_command, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)


