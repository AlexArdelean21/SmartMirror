import threading

# Global flag to signal if a stop has been requested.
stop_requested = False
# Lock for thread-safe access to the stop_requested flag.
_lock = threading.Lock()

def set_stop_requested(value: bool):
    global stop_requested
    with _lock:
        stop_requested = value

def is_stop_requested() -> bool:
    with _lock:
        return stop_requested

def reset_stop_requested():
    global stop_requested
    with _lock:
        stop_requested = False 