from services.calendar_service import add_event
from services.weather_service import get_weather
from services.news_service import get_news
from services.crypto_service import get_crypto_prices
from services.facial_recognition_service import add_face_vocally, recognize_faces_vocally, load_known_faces
from services.user_profile_service import get_user_profile, create_profile_interactively
from services.product_search_service import handle_tryon_command
from util.session_state import set_active_profile
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

# Load environment variables
load_dotenv()

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

def wake_word_detected():
    # Detect wake word using Porcupine.
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
            if result.get("status") == "success":
                logger.info(f"Event '{event_data['summary']}' added successfully.")
                return f"Event '{event_data['summary']}' added successfully."
            else:
                logger.warning("Event creation failed in calendar service.")
                return "Failed to add the event. Please try again."
        except Exception as e:
            logger.exception(f"Error adding event: {e}")
            return "An error occurred while adding the event."

    elif "weather" in command:
        logger.info("Detected weather request.")
        location = user_profile["preferences"].get("location", "Bucharest") if user_profile else "Bucharest"
        weather_data = get_weather(location=location)
        return f"The current weather is {weather_data['weather'][0]['description']}, {weather_data['main']['temp']} degrees Celsius."

    elif "news" in command:
        logger.info("Detected news request.")
        topics = user_profile["preferences"].get("news_topics", ["technology"]) if user_profile else ["technology"]
        news_data = get_news(topics=topics)

        return f"Here's the latest news headline: {news_data['articles'][0]['title']}."

    elif "crypto" in command:
        logger.info("Detected crypto price request.")
        crypto_data = get_crypto_prices()
        return f"Bitcoin is ${crypto_data['bitcoin']}, Ethereum is ${crypto_data['ethereum']}."

    elif "start facial recognition" in command:
        logger.info("Starting facial recognition process.")
        return recognize_faces_vocally()

    elif "add my face" in command:
        logger.info("Starting face registration process.")
        return add_face_vocally()

    elif "try on" in command or "try a" in command:
        logger.info("Detected try-on product command.")
        return handle_tryon_command(command)

    elif any(keyword in command for keyword in ["try option", "select option", "first one", "second one", "third one"]):
        logger.info("Detected option selection command.")
        from services.product_search_service import handle_tryon_selection_command
        return handle_tryon_selection_command(command)

    else:
        logger.info("Command not recognized. Falling back to GPT.")
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
            needs_recognition = user_name is None or (current_time - last_recognition_time > 600)

            if needs_recognition:
                user_name = recognize_faces_vocally()
                last_recognition_time = current_time
                logger.info(f"Recognized user: {user_name}")

                if user_name == "ghost":
                    logger.info("No face detected. Restarting loop.")
                    speak_response("Maybe I'm hearing things!")
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
            speak_response(random_phrase(FOLLOW_UP_YES))

            while session_active:
                command = listen_command()
                command = command.lower() if command else ""

                if not command or "no command" in command:
                    speak_response("I didn't catch that. Could you repeat?")
                    continue

                if any(phrase in command for phrase in ["no thanks", "that's all", "stop", "nothing", "goodbye"]):
                    speak_response("Alright, see you later.")
                    logger.info("Session ended by user.")
                    session_active = False
                    continue

                logger.info(f"Processing command: {command}")
                response = process_command(command, current_user_profile)
                if response:
                    speak_response(response)
                else:
                    logger.warning("No response generated for the command.")
                
                time.sleep(1)
                speak_response(random_phrase(FOLLOW_UP_ASK))

def chat_with_gpt(prompt):
    from openai import OpenAI
    # Interact with OpenAI's GPT model for general queries.
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        message = response.choices[0].message.content
        logger.debug(f"GPT response: {message}")
        return message
    except Exception as e:
        logger.exception(f"GPT interaction failed: {e}")
        return "Sorry, I couldn't process that request."

