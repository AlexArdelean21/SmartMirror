import os
import speech_recognition as sr
from google.cloud import texttospeech
from pydub import AudioSegment
from pydub.playback import play
from tempfile import NamedTemporaryFile
from dotenv import load_dotenv

load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

def initialize_google_tts_client():
    return texttospeech.TextToSpeechClient()

def speak_response(response_text):
    """
    Convert text to speech using Google Cloud TTS and play the response.
    """
    client = initialize_google_tts_client()

    # Configure voice settings
    synthesis_input = texttospeech.SynthesisInput(text=response_text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Wavenet-F",  # High-quality female voice
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

    # Generate speech
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # Save and play the generated speech
    with NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
        temp_audio.write(response.audio_content)
        temp_audio.close()  # Explicitly close the file

        # Play the audio using pydub
        audio = AudioSegment.from_file(temp_audio.name, format="mp3")
        play(audio)

    # Delete the temporary file after playback
    os.remove(temp_audio.name)


def listen_command():
    #Listen for a voice command and return it as text.
    recognizer = sr.Recognizer()
    speak_response("I'm listening")

    with sr.Microphone() as source:
        print("Listening for a command...")
        try:
            audio = recognizer.listen(source, timeout=5)
            command = recognizer.recognize_google(audio).lower()
            print(f"Recognized command: {command}")
            return command
        except sr.WaitTimeoutError:
            return "No command detected"
        except sr.UnknownValueError:
            return "Sorry, I did not understand that"
        except sr.RequestError:
            return "Error with the speech recognition service"

def process_command(command):
   # Process the voice command and provide a response.

    from services.weather_service import get_weather
    from services.news_service import get_news
    from services.crypto_service import get_crypto_prices

    if "weather" in command:
        weather_data = get_weather()
        if "error" in weather_data:
            return "Sorry, I couldn't fetch the weather information."
        description = weather_data['weather'][0]['description']
        temp = weather_data['main']['temp']
        return f"The current weather is {description}, with a temperature of {temp} degrees Celsius."

    elif "news" in command:
        news_data = get_news()
        if "error" in news_data:
            return "Sorry, I couldn't fetch the latest news."
        headline = news_data['articles'][0]['title']
        return f"Here's the latest news headline: {headline}"

    elif "crypto" in command or "bitcoin" in command or "ethereum" in command:
        crypto_data = get_crypto_prices()
        if "error" in crypto_data:
            return "Sorry, I couldn't fetch cryptocurrency prices."
        bitcoin_price = crypto_data['bitcoin']
        ethereum_price = crypto_data['ethereum']
        return f"Bitcoin is currently priced at {bitcoin_price} dollars. Ethereum is at {ethereum_price} dollars."

    return "I'm sorry, I didn't understand that command."

def main():
    #Run the voice assistant: listen for commands, process them, and speak the response.

    while True:
        command = listen_command()
        response = process_command(command)
        print(f"Response: {response}")
        speak_response(response)

if __name__ == "__main__":
    main()
