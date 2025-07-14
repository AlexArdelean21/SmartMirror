from datetime import datetime
import time
from util.cache import get_cached_data, set_cache
from util.logger import logger

CACHE_TIMEOUT = 30

def get_time_date():
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    current_date = now.strftime("%Y-%m-%d")
    data = {"time": current_time, "date": current_date}

    set_cache("time_date", data)
    return data

