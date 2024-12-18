import os
import pvporcupine
from pvrecorder import PvRecorder
import speech_recognition as sr
from google.cloud import texttospeech
from pydub import AudioSegment
from pydub.playback import play
from tempfile import NamedTemporaryFile
from openai import OpenAI
import threading
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

def initialize_google_tts_client():
    return texttospeech.TextToSpeechClient()

def speak_response(response_text):
    #Convert text to speech using Google Cloud TTS and play the response.
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
        play(audio)
        os.remove(temp_audio.name)

def wake_word_detected():
    """Detect wake word using Porcupine."""
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
    """Listen for a voice command after wake word."""
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
    """Process the voice command and provide a response."""
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

def wait_for_wake_and_command():
    """Wait for wake word and process commands."""
    if wake_word_detected():
        response_text = "How can I assist you?"
        print(response_text)

        # Speak in a background thread
        threading.Thread(target=speak_response, args=(response_text,)).start()

        command = listen_command()
        if command and "no command" not in command:
            response = process_command(command)
            print(f"Response: {response}")

            # Speak the response in a background thread
            threading.Thread(target=speak_response, args=(response,)).start()
            return response
        return "Sorry, I didn't catch that."
    return "Wake word not detected."

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
