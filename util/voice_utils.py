import speech_recognition as sr
import os
from google.cloud import texttospeech
from util.logger import logger
from util.socket_manager import socketio
from util.audio_state import set_audio_playing, is_audio_playing
import time
from util.command_interrupt import is_stop_requested, reset_stop_requested

def wait_for_audio_completion(timeout=60):
    """
    Waits for the audio playback to complete.

    This function polls the audio playing state, which is expected to be
    set to False by a client-side 'audio_finished' event. It includes a
    timeout to prevent indefinite waiting.
    """
    start_time = time.time()
    while is_audio_playing():
        if time.time() - start_time > timeout:
            logger.warning(f"Audio playback wait timed out after {timeout} seconds.")
            set_audio_playing(False)  # Reset state to prevent deadlock
            break

        if is_stop_requested():
            logger.info("Audio playback aborted by user stop request.")
            socketio.emit("stop_audio")
            reset_stop_requested()
            set_audio_playing(False)  # Reset state
            break

        time.sleep(0.1)

    if not is_audio_playing():
        logger.debug("Audio playback confirmed as finished.")


def speak_response(text):
    if is_stop_requested():
        logger.info(f"Speak response for '{text}' cancelled by user stop request.")
        reset_stop_requested()
        return

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

    wait_for_audio_completion()


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

