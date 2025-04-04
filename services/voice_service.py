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
import logging
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

        # Play the audio response
        with NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            temp_audio.write(response.audio_content)
            temp_audio.close()
            audio = AudioSegment.from_file(temp_audio.name, format="mp3")

            duration = len(audio) / 1000.0  # Duration in seconds
            try:
                play(audio)
            except OSError as e:
                logging.error(f"Audio playback failed: {e}")
            finally:
                os.remove(temp_audio.name)

        return {"text": response_text, "duration": duration, "audio_url": f"/{audio_file_path}"}

    except Exception as e:
        logging.error(f"Error in TTS response: {e}")
        return {"text": "", "duration": 0, "audio_url": ""}

def wake_word_detected():
    #Detect wake word using Porcupine.
    access_key = os.getenv("PORCUPINE_ACCESS_KEY")
    custom_model_path = os.path.join(os.path.dirname(__file__), "../hey_adonis.ppn")
    porcupine = pvporcupine.create(access_key=access_key, keyword_paths=[custom_model_path])
    recorder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)
    print("Listening for wake word...")

    try:
        recorder.start()
        while True:
            pcm = recorder.read()
            keyword_index = porcupine.process(pcm)
            if keyword_index >= 0:
                print("Wake word detected!")
                return True
    finally:
        recorder.stop()
        porcupine.delete()

def listen_command():
    #Listen for a voice command after wake word.
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for a command...")
        try:
            audio = recognizer.listen(source, timeout=5)
            command = recognizer.recognize_google(audio).lower()
            print(f"Recognized command: {command}")
            return command
        except (sr.WaitTimeoutError, sr.UnknownValueError):
            return "No command detected"
        except sr.RequestError:
            return "Error with the speech recognition service"

def process_command(command):
    # Check for event creation command
    if "add an event" in command.lower():
        event_data = handle_command(command)
        if not event_data:
            return "I couldn't understand the event details. Please try again."

        # Call add_event with parsed data
        try:
            result = add_event(
                summary=event_data["summary"],
                start_time=event_data["start_time"],
                end_time=event_data["end_time"]
            )
            if result.get("status") == "success":
                return f"Event '{event_data['summary']}' added successfully."
            else:
                return "Failed to add the event. Please try again."
        except Exception as e:
            logging.error(f"Error adding event: {e}")
            return "An error occurred while adding the event."

    # Handle weather command
    elif "weather" in command:
        weather_data = get_weather()
        return f"The current weather is {weather_data['weather'][0]['description']}, {weather_data['main']['temp']} degrees Celsius."

    # Handle news command
    elif "news" in command:
        news_data = get_news()
        return f"Here's the latest news headline: {news_data['articles'][0]['title']}."

    # Handle cryptocurrency prices command
    elif "crypto" in command:
        crypto_data = get_crypto_prices()
        return f"Bitcoin is ${crypto_data['bitcoin']}, Ethereum is ${crypto_data['ethereum']}."

    elif "start facial recognition" in command:
        return recognize_faces_vocally()

    elif "add my face" in command:
        return add_face_vocally()

    # Default fallback to chat with GPT
    else:
        return chat_with_gpt(command)

def handle_command(command):
    try:
        # Step 1: Extract the event title (without the word "called", "today", etc.)
        title_match = re.search(
            r"(?:add|create)(?: an)? event(?: called)? (.+?) (?:today|tomorrow|on \w+day)? at \d+(:\d+)? ?(am|pm)?",
            command, re.IGNORECASE
        )
        if not title_match:
            raise ValueError("Event title not found in command.")

        raw_title = title_match.group(1).strip(" '\"").strip()

        # Step 2: Extract time and day
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
            # Default to PM if meridian is missing and hour is in a reasonable range
            if hour < 9:
                hour += 12

        # Format start and end times
        start_time = event_date.replace(hour=hour, minute=minutes, second=0).isoformat()
        end_time = (event_date + timedelta(hours=1)).replace(hour=hour, minute=minutes, second=0).isoformat()

        return {
            "summary": title_match,
            "start_time": start_time,
            "end_time": end_time
        }
    except ValueError as ve:
        logging.error(f"Error parsing command: {ve}")
        return None

def random_phrase(phrases):
    return random.choice(phrases)


def wait_for_wake_and_command():
    user_name = None
    last_recognition_time = 0 # UNIX timestamp

    while True:
        # OUTER LOOP — Always running, listens for "Hey Adonis"
        if wake_word_detected():
            current_time = time.time()
            needs_recognition = user_name is None or (current_time - last_recognition_time > 600)

            if needs_recognition:
                user_name = recognize_faces_vocally()
                last_recognition_time = current_time

            while True:
                # FACE RECOGNITION LOOP — Handles known/unknown faces
                known_faces = load_known_faces()
                if user_name == "ghost":
                    speak_response("Maybe I'm hearing things!")
                    break  # Restart from the outer loop

                if user_name == "Unknown":
                    speak_response("I don't recognize you. Would you like to register?")
                    user_response = listen_command()

                    if any(word in user_response.lower() for word in ["yes", "sure", "okay", "yeah"]):
                        speak_response("Please state your name clearly.")
                        user_name = listen_command()

                        if user_name in known_faces:
                            speak_response(f"This username is taken. Try another one.")
                            continue  # Ask for a different name again

                        if user_name != "Unknown":
                            speak_response(f"Registering {user_name}. Please look at the camera.")
                            add_face_vocally(user_name)
                            speak_response(f"Face registered successfully. Hello {user_name}! How can I assist you?")
                            break
                        else:
                            speak_response("I didn't catch your name. Please try again.")
                    else:
                        speak_response("Unknown user - limited access. What can I do for you?")
                        break
                else:
                    speak_response(f"Hello {user_name}, how can I assist you?")
                    break  # Continue to command loop

            session_active = True

            while session_active:
                # COMMAND LOOP — Handles the first command and responses
                if user_name == "ghost":
                    break  # Return to outer loop

                command = listen_command()
                if not command or "no command" in command:
                    speak_response("I didn't catch that. Please repeat.")
                    continue

                if any(phrase in command for phrase in ["no", "that's all", "stop", "nothing"]):
                    speak_response("Alright, see you later.")
                    break  # End conversation and restart from wake word loop

                response = process_command(command)
                speak_response(response)

                while True:
                    # FOLLOW-UP LOOP — Offers follow-up interaction
                    time.sleep(2)
                    follow_up = random_phrase(FOLLOW_UP_ASK)
                    speak_response(follow_up)

                    follow_up_command = listen_command()
                    if not follow_up_command or "no command" in follow_up_command:
                        speak_response("I didn't understand that. Can you repeat?")
                        continue

                    if any(phrase in follow_up_command for phrase in ["no", "that's all", "stop", "nothing"]):
                        speak_response("Alright, see you later.")
                        session_active = False
                        break  # Exit follow-up loop and restart from wake word

                    if any(phrase in follow_up_command for phrase in ["yes", "sure", "yea", "yeah", "yep"]):
                        speak_response(random_phrase(FOLLOW_UP_YES))
                        break  # Ask for another command

                    speak_response("I didn't understand that. Can you repeat?")

        continue  # Go back to listening for wake word



def chat_with_gpt(prompt):
    #Interact with OpenAI's GPT model for general queries.
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error: {e}")
        return "Sorry, I couldn’t process that request."

def main():
    #Run the continuous voice assistant.
    while True:
        # Wait for wake word
        if wake_word_detected():
            print("Wake word detected, playing 'How can I assist you?'")
            speak_response("How can I assist you?")
            command = listen_command()
            if command and "no command" not in command:
                response = process_command(command)
                print(f"Response: {response}")
                speak_response(response)
