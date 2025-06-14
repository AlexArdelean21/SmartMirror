import requests
from util.logger import logger
from util.socket_manager import socketio
from util.voice_utils import speak_response, listen_command
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
    logger.info(f"Handling try-on voice command: '{command}'")
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

    # Trigger the try-on interface immediately
    socketio.emit("trigger_tryon", {
        "category": category,
        "color": color,
        "max_price": max_price
    })

    # Provide clear instructions for selection - single response only
    color_text = f"{color} " if color else ""
    speak_response(f"Here are some {color_text}options! Say 'try on the first one', 'try on the second one', or 'try on the third one' to select.")
    
    return None  # Don't return text response to avoid duplicate TTS

def handle_tryon_selection_command(command):
    logger.info(f"Handling try-on selection voice command: '{command}'")
    from util.socket_manager import socketio

    index = None
    command = command.lower()
    
    # More specific pattern matching to avoid conflicts
    if "first" in command or "option 1" in command or " 1" in command:
        index = 0
    elif "second" in command or "option 2" in command or " 2" in command:
        index = 1
    elif "third" in command or "option 3" in command or " 3" in command:
        index = 2
    
    # Fallback: try to extract numbers with regex
    if index is None:
        import re
        number_match = re.search(r'\b(1|2|3|one|two|three)\b', command)
        if number_match:
            number_word = number_match.group(1)
            number_mapping = {
                '1': 0, 'one': 0,
                '2': 1, 'two': 1,
                '3': 2, 'three': 2
            }
            index = number_mapping.get(number_word)

    if index is not None:
        logger.info(f"Emitting try-on selection: option {index + 1}")
        socketio.emit("try_on_selected_item", {"index": index})
        return f"Trying on option {index + 1}."
    else:
        logger.warning(f"Couldn't determine which option to try from command: '{command}'")
        return "I didn't understand which option to try. Please say something like 'try on the first one' or 'option two'."
