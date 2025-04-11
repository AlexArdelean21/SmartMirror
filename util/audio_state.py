_global_audio_playing = False

def set_audio_playing(value: bool):
    global _global_audio_playing
    _global_audio_playing = value

def is_audio_playing():
    return _global_audio_playing
