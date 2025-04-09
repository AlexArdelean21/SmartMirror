import speech_recognition as sr
import os
from google.cloud import texttospeech
from util.logger import logger
from util.socket_manager import socketio
import time

def speak_response(text):
    logger.info(f"TTS starting for response: {text}")
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Wavenet-D"
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    audio_path = "static/audio_response.mp3"
    logger.debug("Response ready. Browser should pick it up.")
    socketio.emit("play_audio", {
        "audio_url": f"/static/audio_response.mp3?t={int(time.time())}",
        "text": text
    })

    # Safely delete previous file if it exists
    try:
        if os.path.exists(audio_path):
            os.remove(audio_path)
    except Exception as e:
        logger.warning(f"Could not delete previous audio file: {e}")

    try:
        with open(audio_path, "wb") as out:
            out.write(response.audio_content)
            logger.debug(f"TTS audio saved to {audio_path}")
    except Exception as e:
        logger.exception(f"Failed to save TTS audio: {e}")


def listen_command():
    time.sleep(2) # wait 2 seconds to finsh talking (if not, it will only take his own question as a response)
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
