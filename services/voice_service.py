from services.calendar_service import add_event
from services.weather_service import get_weather
from services.news_service import get_news
from services.crypto_service import get_crypto_prices
from services.facial_recognition_service import add_face_vocally, recognize_faces_vocally, load_known_faces
from services.user_profile_service import get_user_profile, create_profile_interactively
from services.product_search_service import handle_tryon_command
from services.datetime_service import get_time_date
from services.recommendation_service import generate_personal_recommendation
from util.session_state import set_active_profile, get_session_attribute
import pvporcupine
from pvrecorder import PvRecorder
from util.voice_utils import speak_response, listen_command
from dotenv import load_dotenv
from util.logger import logger
import random
import time
import os
import re
from datetime import datetime, timedelta
import threading
import speech_recognition as sr
from util.command_interrupt import set_stop_requested, is_stop_requested, reset_stop_requested
from util.audio_state import is_audio_playing

# Load environment variables
load_dotenv()

# --- Stop Listener Components ---
stop_listener_thread = None
stop_thread_stop_event = threading.Event()

def listen_for_stop_command_thread(): # runs in the background thread
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 0.5
    recognizer.non_speaking_duration = 0.5
    
    with sr.Microphone() as source:
        logger.info("Stop command listener thread started.")
        while not stop_thread_stop_event.is_set():
            if is_audio_playing():
                time.sleep(0.5)
                continue

            try:
                audio = recognizer.listen(source, timeout=1, phrase_time_limit=2)
                command = recognizer.recognize_google(audio).lower()
                if "stop" in command:
                    logger.info("Stop command detected by listener.")
                    set_stop_requested(True)
                    break 
            except sr.WaitTimeoutError:
                continue
            except (sr.UnknownValueError, sr.RequestError):
                continue
            except Exception as e:
                logger.error(f"An unexpected error occurred in the stop listener: {e}")
                break
    logger.info("Stop command listener thread finished.")

def start_stop_command_listener(): # starts the stop command listener thread
    global stop_listener_thread, stop_thread_stop_event
    if stop_listener_thread is None or not stop_listener_thread.is_alive():
        stop_thread_stop_event.clear()
        stop_listener_thread = threading.Thread(target=listen_for_stop_command_thread, daemon=True)
        stop_listener_thread.start()

def stop_stop_command_listener(): # stops the stop listener thread
    global stop_thread_stop_event
    if stop_listener_thread and stop_listener_thread.is_alive():
        stop_thread_stop_event.set()
# --- End of Stop Listener Components ---

FOLLOW_UP_ASK = [
    "Anything else?",
    "Would you like me to do something else?",
    "Is there anything else I can help you with?",
    "Do you need anything else?"
]

FOLLOW_UP_YES = [
    "What's on your mind?",
    "Go ahead, I'm listening.",
    "What would you like to do next?",
    "I'm here for you, what's next?"
]

RECOMMENDATION_KEYWORDS = [
    "recommendation","recommend", "suggest", "advice",
    "what should I do", "what should I wear",
    "any ideas", "give me a tip"
]

def wake_word_detected(): # Detect wake word using Porcupine.
    access_key = os.getenv("PORCUPINE_ACCESS_KEY")
    custom_model_path = os.path.join(os.path.dirname(__file__), "../hey_adonis.ppn")

    porcupine = pvporcupine.create(access_key=access_key, keyword_paths=[custom_model_path])
    recorder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)

    logger.info("Wake word listener started. Listening for 'Hey Adonis'...")

    try:
        recorder.start()
        while True:
            pcm = recorder.read()
            keyword_index = porcupine.process(pcm)
            if keyword_index >= 0:
                return True
    except Exception as e:
        logger.exception(f"Wake word detection failed: {e}")
    finally:
        recorder.stop()
        porcupine.delete()
        logger.debug("Porcupine recorder stopped and cleaned up.")

def process_command(command, user_profile=None):
    logger.debug(f"Processing command: {command}")

    if is_stop_requested():
        logger.info("Command processing aborted by user stop request.")
        # No reset here, reset is handled where the stop is consumed.
        return "Command stopped by user."

    # Check for event creation command
    if "add an event" in command.lower():
        if user_profile and user_profile.get("name", "").lower() != "alex":
            logger.warning(f"Unauthorized calendar access attempt by: {user_profile.get('name')}")
            return "Sorry, calendar access is restricted."

        logger.info("Detected calendar event creation command.")
        event_data = handle_command(command)
        if not event_data:
            logger.warning("Event parsing failed.")
            return "I couldn't understand the event details. Please try again."

        try:
            result = add_event(
                summary=event_data["summary"],
                start_time=event_data["start_time"],
                end_time=event_data["end_time"]
            )
            if is_stop_requested():
                return "Command stopped by user."
            if result.get("status") == "success":
                logger.info(f"Event '{event_data['summary']}' added successfully.")
                return f"Event '{event_data['summary']}' added successfully."
            else:
                logger.warning("Event creation failed in calendar service.")
                return "Failed to add the event. Please try again."
        except Exception as e:
            logger.exception(f"Error adding event: {e}")
            return "An error occurred while adding the event."

    elif "time" in command or "date" in command:
        logger.info("Detected time/date request.")
        time_data = get_time_date()
        if is_stop_requested():
            return "Command stopped by user."
        return f"The time is {time_data['time']} and the date is {time_data['date']}."

    elif "weather" in command:
        logger.info("Detected weather request.")
        location = user_profile["preferences"].get("location", "Bucharest") if user_profile else "Bucharest"
        weather_data = get_weather(location=location)
        if is_stop_requested():
            return "Command stopped by user."
        return f"The current weather is {weather_data['weather'][0]['description']}, {weather_data['main']['temp']} degrees Celsius."

    elif "news" in command:
        logger.info("Detected news request.")
        topics = user_profile["preferences"].get("news_topics", ["technology"]) if user_profile else ["technology"]
        news_data = get_news(topics=topics)
        if is_stop_requested():
            return "Command stopped by user."
        return f"Here's the latest news headline: {news_data['articles'][0]['title']}."

    elif "crypto" in command:
        logger.info("Detected crypto price request.")
        crypto_data = get_crypto_prices()
        if is_stop_requested():
            return "Command stopped by user."
        return f"Bitcoin is ${crypto_data['bitcoin']}, Ethereum is ${crypto_data['ethereum']}."

    elif "start facial recognition" in command:
        logger.info("Starting facial recognition process.")
        result = recognize_faces_vocally()
        if is_stop_requested():
            return "Command stopped by user."
        return result

    elif "add my face" in command:
        logger.info("Starting face registration process.")
        result = add_face_vocally()
        if is_stop_requested():
            return "Command stopped by user."
        return result

    # Check for dismissal before selection to catch negative responses.
    elif get_session_attribute('tryon_active') and any(keyword in command for keyword in ["none", "neither", "don't like", "dislike", "not these"]):
        logger.info("User dismissed try-on options.")
        from services.product_search_service import handle_tryon_dismissal
        result = handle_tryon_dismissal()
        if is_stop_requested():
            return "Command stopped by user."
        return result

    elif any(keyword in command for keyword in ["try option", "select option", "first one", "second one", "third one"]):
        logger.info("Detected option selection command.")
        from services.product_search_service import handle_tryon_selection_command
        result = handle_tryon_selection_command(command)
        if is_stop_requested():
            return "Command stopped by user."
        return result

    elif "try on" in command or "try a" in command:
        logger.info("Detected try-on product command.")
        result = handle_tryon_command(command)
        if is_stop_requested():
            return "Command stopped by user."
        return result

    elif any(keyword in command for keyword in RECOMMENDATION_KEYWORDS):
        logger.info("Detected recommendation request.")
        if not user_profile or user_profile.get("name", "unknown").lower() == "unknown":
            return "I can't give a recommendation without knowing who you are. Please log in first."
        result = generate_personal_recommendation(user_profile)
        if is_stop_requested():
            return "Command stopped by user."
        return result
        
    else:
        logger.info("Command not recognized. Falling back to GPT.")
        if is_stop_requested():
            logger.info("Command processing aborted before GPT call.")
            return "Command stopped by user."
        return chat_with_gpt(command)

def handle_command(command):
    try:
        title_match = re.search(
            r"(?:add|create)(?: an)? event(?: called)? (.+?) (?:today|tomorrow|on \w+day)? at \d+(:\d+)? ?(am|pm)?",
            command, re.IGNORECASE
        )
        if not title_match:
            raise ValueError("Event title not found in command.")

        raw_title = title_match.group(1).strip(" '\"").strip()

        time_match = re.search(
            r"(today|tomorrow|on \w+day) at (\d+)(:\d+)? ?(AM|PM)?",
            command, re.IGNORECASE
        )
        if not time_match:
            raise ValueError("Date and time not found in command.")

        day, hour, minutes, meridian = time_match.groups()
        now = datetime.now()

        # Determine event date
        if "tomorrow" in day.lower():
            event_date = now + timedelta(days=1)
        elif "today" in day.lower():
            event_date = now
        else:
            raise ValueError("Only 'today' and 'tomorrow' are supported.")

        # Clean and convert minutes
        minutes = minutes[1:] if minutes else "0"
        hour = int(hour)
        minutes = int(minutes)

        # Validate and adjust AM/PM
        if meridian:
            if meridian.upper() == "PM" and hour != 12:
                hour += 12
            elif meridian.upper() == "AM" and hour == 12:
                hour = 0
        else:
            if hour < 9:
                hour += 12

        # Format start and end times
        start_time = event_date.replace(hour=hour, minute=minutes, second=0).isoformat()
        end_time = (event_date + timedelta(hours=1)).replace(hour=hour, minute=minutes, second=0).isoformat()

        logger.debug(f"Parsed event: '{raw_title}' from command.")
        return {
            "summary": raw_title,
            "start_time": start_time,
            "end_time": end_time
        }

    except ValueError as ve:
        logger.warning(f"Error parsing command: {ve}")
        return None


def random_phrase(phrases):
    return random.choice(phrases)


def wait_for_wake_and_command():
    user_name = None
    current_user_profile = None
    last_recognition_time = 0

    while True:
        if wake_word_detected():
            logger.info("Wake word detected.")
            current_time = time.time()
            
            # Recognition is needed if no user is set, if the user is a guest, or if the session has expired (15 mins)
            needs_recognition = user_name is None or user_name.lower() in ["unknown", "ghost"] or (current_time - last_recognition_time > 900)

            if needs_recognition:
                user_name = recognize_faces_vocally()
                last_recognition_time = current_time
                logger.info(f"Recognized user: {user_name}")

                if user_name == "ghost":
                    logger.info("No face detected. Restarting loop.")
                    speak_response("Must have been the wind.")
                    user_name = None  # Reset user to force re-authentication
                    continue

                known_faces = load_known_faces()

                if user_name == "Unknown":
                    speak_response("I don't recognize you. Would you like to register?")
                    user_response = listen_command()
                    user_response = user_response.lower() if user_response else ""

                    if any(word in user_response for word in ["yes", "sure", "okay", "yeah"]):
                        speak_response("Please state your name clearly.")
                        user_name = listen_command()

                        if user_name in known_faces:
                            speak_response("This username is taken. Try another one.")
                            logger.warning(f"Registration blocked — name already taken: {user_name}")
                            continue

                        if user_name and user_name != "Unknown":
                            speak_response(f"Registering {user_name}. Please look at the camera.")
                            add_face_vocally(user_name)
                            speak_response(f"Face registered successfully. Hello {user_name}!")
                            
                            profile = create_profile_interactively(user_name)
                            current_user_profile = profile
                            set_active_profile(profile)
                            logger.info(f"New user registered and profile saved: {user_name}")
                        else:
                            speak_response("I didn't catch a name. We can try again later.")
                            continue
                    else:
                        speak_response("Alright. You can use the mirror with limited access.")
                        user_name = "unknown"
                        current_user_profile = get_user_profile("unknown")
                        set_active_profile(current_user_profile)
                        logger.info("'Unknown' profile used for unregistered user.")
                else:
                    # Recognized a known face
                    profile = get_user_profile(user_name)
                    if not profile:
                        speak_response(f"I don't have a profile for you, {user_name}. Would you like to create one?")
                        answer = listen_command().lower()
                        if any(word in answer for word in ["yes", "sure", "okay", "yeah"]):
                            profile = create_profile_interactively(user_name)
                            logger.info(f"New profile created for: {user_name}")
                        else:
                            profile = get_user_profile("unknown") # Fallback
                            logger.info(f"User {user_name} declined profile creation, using 'unknown'.")
                    
                    current_user_profile = profile
                    set_active_profile(profile)
                    speak_response(f"Hello {user_name}, ready to start?")

                    confirmation = listen_command().lower()
                    if any(word in confirmation for word in ["no", "not now", "later", "stop"]):
                        speak_response("Alright, I'll be here if you need me.")
                        continue
            
            # Session starts here
            session_active = True
            start_stop_command_listener() # Start listener for the whole session
            speak_response(random_phrase(FOLLOW_UP_YES))

            no_command_count = 0

            while session_active:
                command = listen_command()
                command = command.lower() if command else ""

                if "no command detected" in command:
                    no_command_count += 1
                    if no_command_count >= 2:
                        speak_response("I'll be here if you need me.")
                        session_active = False
                    else:
                        speak_response("I didn't hear you, can you repeat?")
                    continue
                
                no_command_count = 0

                if any(phrase in command for phrase in ["no thanks", "that's all", "stop", "nothing", "goodbye"]):
                    speak_response("Alright, see you later.")
                    logger.info("Session ended by user.")
                    session_active = False
                    continue

                # Start the stop listener only when a command is being processed or spoken.
                start_stop_command_listener()
                
                logger.info(f"Processing command: {command}")
                response_container = {"response": None}
                def command_task():
                    response_container["response"] = process_command(command, current_user_profile)

                command_thread = threading.Thread(target=command_task)
                command_thread.start()

                # Monitor the command thread and the stop flag simultaneously.
                while command_thread.is_alive():
                    if is_stop_requested():
                        logger.info("Stop request detected while command was running. Abandoning command.")
                        break
                    time.sleep(0.1)
                
                # If stop was requested, end the session immediately.
                if is_stop_requested():
                    reset_stop_requested()
                    speak_response("Ok, bye.")
                    session_active = False
                    # The listener will be stopped at the end of the session loop.
                    continue

                response = response_container["response"]
                if response:
                    speak_response(response) # This is a blocking call. The stop listener is active.

                # If stop was requested during speech, end the session.
                if is_stop_requested():
                    reset_stop_requested()
                    # Don't speak, the audio handler already stopped the playback.
                    session_active = False
                    continue

                # Stop the listener before asking for the next command to avoid mic conflict.
                stop_stop_command_listener()

                # Follow-up prompt
                is_tryon_search = "try on" in command or "try a" in command
                if not (is_tryon_search and response and "Sorry" not in response):
                    time.sleep(1)
                    speak_response(random_phrase(FOLLOW_UP_ASK))

            # End of session, ensure listener is stopped.
            stop_stop_command_listener()

def chat_with_gpt(prompt):
    from openai import OpenAI
    # Interact with OpenAI's GPT model for general queries.
    try:
        if is_stop_requested():
            logger.info("GPT interaction cancelled by user stop request.")
            return "Command stopped by user."

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Add a fallback for misunderstood commands
        enhanced_prompt = (
            f"{prompt}\n\n"
            "If the text so far didn't make sense, just respond with: "
            "\"I didn't get that, can you repeat?\""
        )
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": enhanced_prompt}]
        )
        message = response.choices[0].message.content
        logger.debug(f"GPT response: {message}")
        return message
    except Exception as e:
        logger.exception(f"GPT interaction failed: {e}")
        return "Sorry, I couldn't process that request."

