import json
import os
import time
from dotenv import load_dotenv

load_dotenv()
CACHE_FILE = os.getenv("CACHE_FILE")
CACHE_TIMEOUT = 300  # Cache expiry time (5 minutes)

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            return {}
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w") as file:
        json.dump(cache, file)

cache = load_cache()

def get_cached_data(key):
    if key in cache and (time.time() - cache[key]["timestamp"] < CACHE_TIMEOUT):
        return cache[key]["data"] # Retrieve cached data if it's still valid
    return None

def set_cache(key, data):
    cache[key] = {"data": data, "timestamp": time.time()}
    save_cache(cache)  # Persist cache to file
