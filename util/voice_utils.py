from google.cloud import texttospeech
from pydub import AudioSegment
from pydub.playback import play
from tempfile import NamedTemporaryFile
import speech_recognition as sr
from util.logger import logger
import os

def speak_response(response_text):
    try:
        logger.info(f"TTS starting for response: {response_text}")

        client = texttospeech.TextToSpeechClient()
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

        # Play audio
        with NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            temp_audio.write(response.audio_content)
            temp_audio.close()
            audio = AudioSegment.from_file(temp_audio.name, format="mp3")

            try:
                play(audio)
                logger.debug("TTS audio played successfully.")
            except OSError as e:
                logger.error(f"Audio playback failed: {e}")
            finally:
                os.remove(temp_audio.name)
                logger.debug("Temporary audio file deleted.")

        return {"text": response_text, "audio_url": f"/{audio_file_path}"}

    except Exception as e:
        logger.exception(f"TTS generation failed: {e}")
        return {"text": "", "audio_url": ""}


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
