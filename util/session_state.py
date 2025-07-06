_current_profile = None
_session_attributes = {}

def set_active_profile(profile):
    global _current_profile
    _current_profile = profile

def get_active_profile():
    return _current_profile

def set_session_attribute(key, value):
    """Sets a key-value pair in the session attributes."""
    global _session_attributes
    _session_attributes[key] = value

def get_session_attribute(key):
    """Gets a value by key from the session attributes."""
    return _session_attributes.get(key)

def clear_session_attribute(key):
    """Removes a key from the session attributes."""
    global _session_attributes
    if key in _session_attributes:
        del _session_attributes[key]
