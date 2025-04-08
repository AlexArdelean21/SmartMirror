_current_profile = None

def set_active_profile(profile):
    global _current_profile
    _current_profile = profile

def get_active_profile():
    return _current_profile
