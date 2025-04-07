from services.calendar_service import add_event
from services.weather_service import get_weather
from services.news_service import get_news
from services.crypto_service import get_crypto_prices
from services.facial_recognition_service import add_face_vocally, recognize_faces_vocally, load_known_faces
import pvporcupine
from pvrecorder import PvRecorder
import speech_recognition as sr
from google.cloud import texttospeech
from pydub import AudioSegment
from pydub.playback import play
from tempfile import NamedTemporaryFile
from openai import OpenAI
from dotenv import load_dotenv
from util.logger import logger
import random
import time
import os
import re
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()
google_credentials = os.environ.get("GOOGLE_CREDENTIALS_PATH")
if google_credentials:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_credentials
else:
    raise ValueError("Google credentials path not set.")

def initialize_google_tts_client():
    return texttospeech.TextToSpeechClient()

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

def speak_response(response_text):
    try:
        logger.info(f"TTS starting for response: {response_text}")

        client = initialize_google_tts_client()
        synthesis_input = texttospeech.SynthesisInput(text=response_text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Wavenet-F",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        # Save audio for web playback
        audio_file_path = "static/audio_response.mp3"
        with open(audio_file_path, "wb") as out:
            out.write(response.audio_content)
        logger.debug(f"TTS audio saved to {audio_file_path}")

        # Play the audio response
        with NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            temp_audio.write(response.audio_content)
            temp_audio.close()
            audio = AudioSegment.from_file(temp_audio.name, format="mp3")

            duration = len(audio) / 1000.0  # Duration in seconds
            try:
                play(audio)
                logger.debug("TTS audio played successfully.")
            except OSError as e:
                logger.error(f"Audio playback failed: {e}")
            finally:
                os.remove(temp_audio.name)
                logger.debug("Temporary audio file deleted.")

        return {"text": response_text, "duration": duration, "audio_url": f"/{audio_file_path}"}

    except Exception as e:
        logger.exception(f"TTS generation failed: {e}")
        return {"text": "", "duration": 0, "audio_url": ""}


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


def listen_command():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        logger.info("Listening for a command...")
        try:
            audio = recognizer.listen(source, timeout=5)
            command = recognizer.recognize_google(audio).lower()
            return command
        except sr.WaitTimeoutError:
            logger.warning("No voice input detected (timeout).")
            return "No command detected"
        except sr.UnknownValueError:
            logger.warning("Could not understand the voice input.")
            return "No command detected"
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return "Error with the speech recognition service"


def process_command(command):
    logger.debug(f"Processing command: {command}")

    # Check for event creation command
    if "add an event" in command.lower():
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
        weather_data = get_weather()
        return f"The current weather is {weather_data['weather'][0]['description']}, {weather_data['main']['temp']} degrees Celsius."

    elif "news" in command:
        logger.info("Detected news request.")
        news_data = get_news()
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
    last_recognition_time = 0  # UNIX timestamp

    while True:
        logger.debug("Listening for wake word...")
        if wake_word_detected():
            logger.info("Wake word detected.")
            current_time = time.time()
            needs_recognition = user_name is None or (current_time - last_recognition_time > 600)

            if needs_recognition:
                user_name = recognize_faces_vocally()
                last_recognition_time = current_time
                logger.info(f"Recognized user: {user_name}")

            while True:
                known_faces = load_known_faces()

                if user_name == "ghost":
                    logger.info("No face detected. Restarting loop.")
                    speak_response("Maybe I'm hearing things!")
                    break

                if user_name == "Unknown":
                    speak_response("I don't recognize you. Would you like to register?")
                    user_response = listen_command()

                    if any(word in user_response.lower() for word in ["yes", "sure", "okay", "yeah"]):
                        speak_response("Please state your name clearly.")
                        user_name = listen_command()

                        if user_name in known_faces:
                            speak_response("This username is taken. Try another one.")
                            logger.warning(f"Registration blocked — name already taken: {user_name}")
                            continue

                        if user_name != "Unknown":
                            speak_response(f"Registering {user_name}. Please look at the camera.")
                            add_face_vocally(user_name)
                            speak_response(f"Face registered successfully. Hello {user_name}! How can I assist you?")
                            logger.info(f"New user registered: {user_name}")
                            break
                        else:
                            speak_response("I didn't catch your name. Please try again.")
                    else:
                        speak_response("Unknown user - limited access. What can I do for you?")
                        break
                else:
                    speak_response(f"Hello {user_name}, how can I assist you?")
                    break

            session_active = True
            while session_active:
                if user_name == "ghost":
                    logger.info("Session interrupted — no face.")
                    break

                command = listen_command()
                if not command or "no command" in command:
                    logger.warning("No command detected. Asking user to repeat.")
                    speak_response("I didn't catch that. Please repeat.")
                    continue

                if any(phrase in command for phrase in ["no", "that's all", "stop", "nothing"]):
                    speak_response("Alright, see you later.")
                    logger.info("Session ended by user.")
                    break

                logger.info(f"Processing command: {command}")
                response = process_command(command)
                speak_response(response)

                while True:
                    time.sleep(2)
                    follow_up = random_phrase(FOLLOW_UP_ASK)
                    speak_response(follow_up)

                    follow_up_command = listen_command()
                    if not follow_up_command or "no command" in follow_up_command:
                        speak_response("I didn't understand that. Can you repeat?")
                        logger.warning("No follow-up command detected.")
                        continue

                    if any(phrase in follow_up_command for phrase in ["no", "that's all", "stop", "nothing"]):
                        speak_response("Alright, see you later.")
                        logger.info("Follow-up session ended.")
                        session_active = False
                        break

                    if any(phrase in follow_up_command for phrase in ["yes", "sure", "yea", "yeah", "yep"]):
                        speak_response(random_phrase(FOLLOW_UP_YES))
                        logger.info("Follow-up accepted, awaiting new command...")
                        break

                    speak_response("I didn't understand that. Can you repeat?")
                    logger.warning("Unrecognized follow-up command.")


def chat_with_gpt(prompt):
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
        return "Sorry, I couldn’t process that request."


def main():
    # Run the continuous voice assistant.
    while True:
        if wake_word_detected():
            logger.info("Wake word detected — entering interaction mode.")
            speak_response("How can I assist you?")
            command = listen_command()
            if command and "no command" not in command:
                logger.info(f"Received voice command: {command}")
                response = process_command(command)
                logger.info(f"Command response: {response}")
                speak_response(response)
