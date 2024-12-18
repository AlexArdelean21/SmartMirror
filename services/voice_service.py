import os
import pvporcupine
from pvrecorder import PvRecorder
import speech_recognition as sr
from google.cloud import texttospeech
from pydub import AudioSegment
from pydub.playback import play
from tempfile import NamedTemporaryFile
from openai import OpenAI
from dotenv import load_dotenv
import random
import time

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

    with NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
        temp_audio.write(response.audio_content)
        temp_audio.close()
        audio = AudioSegment.from_file(temp_audio.name, format="mp3")

        duration = len(audio) / 1000.0  # Duration in seconds
        play(audio)
        os.remove(temp_audio.name)

    return duration


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
    #Process the voice command and provide a response.
    from services.weather_service import get_weather
    from services.news_service import get_news
    from services.crypto_service import get_crypto_prices

    if "weather" in command:
        weather_data = get_weather()
        return f"The current weather is {weather_data['weather'][0]['description']}, {weather_data['main']['temp']} degrees Celsius."
    elif "news" in command:
        news_data = get_news()
        return f"Here's the latest news headline: {news_data['articles'][0]['title']}."
    elif "crypto" in command:
        crypto_data = get_crypto_prices()
        return f"Bitcoin is ${crypto_data['bitcoin']}, Ethereum is ${crypto_data['ethereum']}."
    else:
        return chat_with_gpt(command)

def random_phrase(phrases):
    return random.choice(phrases)


def wait_for_wake_and_command():
    while True:
        if wake_word_detected():
            speak_response("How can I assist you?")

            while True:
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

                    if any(phrase in follow_up_command for phrase in ["yes", "sure", "yea", "yeah", "yep"]): # dosen't understand thse yet
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
