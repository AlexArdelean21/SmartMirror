import requests
from util.logger import logger
from util.socket_manager import socketio
from util.voice_utils import speak_response, listen_command, listen_short_command_with_vosk
import re
import os
import time

FAKESTORE_API = os.getenv("FAKESTORE_API")

def get_clothing_items(category="men's clothing", color=None, max_price=None):
    try:
        safe_category = category.replace("'", "%27")
        response = requests.get(f"{FAKESTORE_API}/category/{safe_category}")
        response.raise_for_status()
        items = response.json()

        filtered = []
        for item in items:
            title = item["title"].lower()

            if color and color.lower() not in title:
                continue

            if max_price and item["price"] > max_price:
                continue

            filtered.append({
                "title": item["title"],
                "price": item["price"],
                "image_url": item["image"],
                "id": item["id"]
            })

        logger.info(f"Found {len(filtered)} matching clothing items.")
        return filtered[:3]  # return top 3 matches

    except Exception as e:
        logger.exception(f"Failed to fetch clothing items: {e}")
        return []

def handle_tryon_command(command):
    logger.info("Handling try-on voice command.")
    category = "men's clothing"
    color = None
    max_price = None

    if "women" in command:
        category = "women's clothing"

    # Extract color
    colors = ["red", "blue", "black", "white", "green", "yellow", "brown"]
    for c in colors:
        if c in command.lower():
            color = c
            break

    # Extract max price
    price_match = re.search(r"under (\d+)", command.lower())
    if price_match:
        max_price = int(price_match.group(1))

    logger.info(f"Parsed try-on: category={category}, color={color}, max_price={max_price}")

    items = get_clothing_items(category=category, color=color, max_price=max_price)

    if not items:
        response_text = f"Sorry, I couldn't find any {color or ''} items in that category."
        logger.info(f"No clothing items matched: {category}, {color}, {max_price}")
        speak_response(response_text)

        socketio.emit("trigger_tryon", {
            "category": None,
            "color": None,
            "max_price": None
        })
        return None

    socketio.emit("trigger_tryon", {
        "category": category,
        "color": color,
        "max_price": max_price
    })

    speak_response(f"Okay, here are some {color or ''} options. Would you like to try one? You can say yes, no, or wait.")

    while True:
        response = listen_short_command_with_vosk()
        logger.info(f"User said (try-on follow-up): {response}")

        rejections = ["no", "nothing", "not now", "skip", "stop", "cancel", "i'm good", "i'm fine"]
        holds = ["wait", "hold", "not yet", "later", "give me time", "not right now"]

        if any(phrase in response for phrase in rejections):
            speak_response("Alright. Just say 'Hey Adonis' when you're ready again.")
            return None

        if any(phrase in response for phrase in holds):
            speak_response("Okay, I'll check back in 20 seconds.")
            time.sleep(20)
            speak_response("Would you like to try one now?")
            continue

        selection_response = handle_tryon_selection_command(response)

        if "didn't understand" in selection_response.lower():
            speak_response(selection_response)
            speak_response("Please say option one, two, or three.")
            continue

        return selection_response


def handle_tryon_selection_command(command):
    logger.info("Handling try-on selection voice command.")
    from util.socket_manager import socketio

    index = None
    command = command.lower()

    if "option 1" in command or "first" in command:
        index = 0
    elif "option 2" in command or "second" in command:
        index = 1
    elif "option 3" in command or "third" in command:
        index = 2

    if index is not None:
        logger.info(f"Emitting try-on selection: option {index}")
        socketio.emit("try_on_selected_item", {"index": index})
        return f"Trying on option {index + 1}."
    else:
        logger.warning("Couldn't determine which option to try.")
        return "I didn't understand which option to try. Please say option one, two, or three."
