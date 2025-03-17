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
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

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
        # Parse the title, excluding phrases like "event called" or "called"
        title_match = re.search(r"(?:add an event|create an event|an event called|event called|called) ['\"]?(.+?)['\"]?(?: today| tomorrow| on \w+day| at .*)?$", command, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()
        else:
            raise ValueError("Event title not found in command.")

        # Parse date and time
        time_match = re.search(r"(today|tomorrow|on \w+day) at (\d+)(:\d+)? ?(AM|PM)?", command, re.IGNORECASE)
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
            "summary": title,
            "start_time": start_time,
            "end_time": end_time
        }
    except ValueError as ve:
        logging.error(f"Error parsing command: {ve}")
        return None



def random_phrase(phrases):
    return random.choice(phrases)


def wait_for_wake_and_command():
    while True:
        if wake_word_detected():
            user_name = recognize_faces_vocally()

        while True:
            known_faces = load_known_faces()
            if user_name == "ghost":
                speak_response("Maybe I'm hearin things!")
                break

            if user_name == "Unknown":
                speak_response("I don't recognize you. Would you like to register?")
                user_response = listen_command()

                if any(word in user_response.lower() for word in ["yes", "sure", "okay", "yeah"]):
                    speak_response("Please state your name clearly.")
                    user_name = listen_command()

                    if user_name or user_name.lower() in known_faces:
                        speak_response(f"This username is taken, try another one.")
                        continue # ???????

                    if user_name:
                        speak_response(f"Registering {user_name}. Please look at the camera.")
                        add_face_vocally(user_name)
                        speak_response(f"Face registered successfully. Hello {user_name}! How can i assist you?")
                        break
                    else:
                        speak_response("I didn't catch your name. Please try again.")
                else:
                    speak_response("Unknown user - limited access.")
                    break
            else:
                speak_response(f"How can i assist you")
                break


        while True:
            if user_name == "ghost":
                break

            command = listen_command()
            if not command or "no command" in command:
                speak_response("I didn't catch that. Please repeat.")
                continue

            if any(phrase in command for phrase in ["no", "that's all", "stop", "nothing"]):
                speak_response("Alright, see you later.")
                return

            response = process_command(command)
            speak_response(response)

            while True:
                time.sleep(2)
                speak_response(random_phrase(FOLLOW_UP_ASK))

                follow_up_command = listen_command()
                if not follow_up_command or "no command" in follow_up_command:
                    speak_response("I didn't understand that. Can you repeat?")
                    continue

                if any(phrase in follow_up_command for phrase in ["no", "that's all", "stop", "nothing"]): # dosen't understand no
                    speak_response("Alright, see you later.")
                    return  # Exit back to wake word

                # dosen't understand thse yet( it dose if you say more words like "yes please")
                if any(phrase in follow_up_command for phrase in ["yes", "sure", "yea", "yeah", "yep"]):
                    speak_response(random_phrase(FOLLOW_UP_YES))
                    break

                # If not recognized
                speak_response("I didn't understand that. Can you repeat?")



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

if __name__ == "__main__":
    main()
