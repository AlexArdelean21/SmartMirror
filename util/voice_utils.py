import speech_recognition as sr
import os
from google.cloud import texttospeech
from util.logger import logger
from util.socket_manager import socketio
from util.audio_state import set_audio_playing, is_audio_playing
import time

def wait_for_audio_completion(text=None, max_timeout=8):
    waited = 0

    if not text:
        estimated_duration = 2  # fallback default
    else:
        word_count = len(text.split())
        estimated_duration = min(word_count * 0.5, max_timeout)

    while is_audio_playing() and waited < estimated_duration:
        time.sleep(0.2)
        waited += 0.2

    if is_audio_playing():
        logger.warning("Audio playback wait timed out.")
    else:
        logger.debug("Audio playback confirmed as finished.")


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

    set_audio_playing(True)

    audio_path = "static/audio_response.mp3"

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

    socketio.emit("play_audio", {
        "audio_url": f"/static/audio_response.mp3?t={int(time.time())}",
        "text": text
    })

    wait_for_audio_completion(text)


def listen_command():
    socketio.emit("start_listening")
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
        finally:
            socketio.emit("stop_listening")

