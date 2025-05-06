import os
import json
from util.logger import logger
from util.voice_utils import speak_response, listen_command

PROFILE_DIR = "user_profiles"
def get_user_profile(username):
    filepath = os.path.join(PROFILE_DIR, f"{username.lower()}.json")

    if not os.path.exists(filepath):
        logger.warning(f"User profile not found for: {username}")
        return None

    try:
        with open(filepath, "r", encoding="utf-8") as file:
            profile = json.load(file)
            logger.info(f"Loaded profile for user: {username}")
            return profile
    except Exception as e:
        logger.exception(f"Failed to load profile for {username}: {e}")
        return None


def save_user_profile(username, profile_data):
    os.makedirs(PROFILE_DIR, exist_ok=True)
    filepath = os.path.join(PROFILE_DIR, f"{username.lower()}.json")

    try:
        with open(filepath, "w", encoding="utf-8") as file:
            json.dump(profile_data, file, indent=4)
            logger.info(f"Saved profile for user: {username}")
    except Exception as e:
        logger.exception(f"Failed to save profile for {username}: {e}")


def create_default_profile(username):
    logger.info(f"Creating default profile for: {username}")
    return {
        "name": username,
        "preferences": {
            "location": "Bucharest",
            "language": "en",
            "theme": "dark",
            "news_topics": ["technology", "us"]
        }
    }

def create_profile_interactively(username):
    speak_response(f"Welcome {username}! Let's set up your profile.")

    # Location
    speak_response("What city are you in?")
    location = listen_command()
    if not location or "no command detected" in location.lower():
        location = "Bucharest"
        speak_response("I didn't catch that. I'll use Bucharest as default.")
    else:
        location = location.strip().title()

    # News Topics
    ALLOWED_TOPICS = {"technology", "tech", "world", "sports", "business", "stock", "music", "science", "gaming"}

    speak_response("What kind of news would you like? Say tech, sports, world, etc.")
    raw_topics = listen_command()

    if not raw_topics or "no command detected" in raw_topics.lower():
        news_topics = ["technology", "world"]
        speak_response("I didn't catch that. I'll pick technology and world news for now.")
    else:
        parsed = [topic.strip().lower() for topic in raw_topics.split(",")]
        valid = [t for t in parsed if t in ALLOWED_TOPICS]

        if not valid:
            news_topics = ["technology", "world"]
            speak_response("That topic isn't recognized. I'll use technology and world for now.")
        else:
            news_topics = valid

    profile = {
        "name": username,
        "preferences": {
            "location": location.title(),
            "language": "en",
            "theme": "dark",
            "news_topics": news_topics
        }
    }

    save_user_profile(username, profile)
    speak_response("Great, your profile was saved!")
    logger.info(f"Interactive profile created for {username}: {profile}")
    return profile

