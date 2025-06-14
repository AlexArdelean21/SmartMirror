"""
STT Configuration Settings
Adjust these values to optimize speech recognition for your environment
"""

# Google STT Settings
GOOGLE_STT_CONFIG = {
    'language': 'en-US',
    'timeout': 8,  # seconds to wait for speech
    'phrase_time_limit': 15,  # max seconds for a single phrase
    'energy_threshold': 200,  # lower = more sensitive
    'pause_threshold': 1.2,  # seconds of silence before stopping
    'phrase_threshold': 0.2,  # seconds before starting to record
    'non_speaking_duration': 0.8,  # seconds of non-speech before stopping
    'ambient_noise_duration': 1.5,  # seconds to adjust for background noise
}

# Vosk STT Settings (backup)
VOSK_STT_CONFIG = {
    'timeout': 8,
    'sample_rate': 16000,
    'frames_per_buffer': 2048,
    'silence_threshold': 300,  # audio level threshold for speech detection
    'max_silence_frames': 20,  # frames of silence before stopping
}

# Command Recognition Settings
COMMAND_CONFIG = {
    'fuzzy_match_threshold': 0.7,  # similarity threshold for fuzzy matching
    'confidence_threshold': 0.3,   # minimum confidence for command parsing
    'max_retry_attempts': 2,       # max retries for failed commands
    'follow_up_timeout': 8,        # timeout for follow-up questions
}

# Try-On Command Variations (add your own if needed)
TRY_ON_VARIATIONS = [
    "try on",
    "try a",
    "right on",    # common mishearing
    "write on",    # common mishearing  
    "throw on",    # common mishearing
    "put on",
    "wear a",
    "show me",
    "let me see",
    "can i try",
    "help me try"
]

# Audio Quality Settings
AUDIO_CONFIG = {
    'apply_noise_reduction': True,
    'use_audio_preprocessing': True,
    'prefer_google_stt': True,  # Google performs better than Vosk
    'use_vosk_fallback': False,  # Disable Vosk since it's not working well
}

# Debugging Settings
DEBUG_CONFIG = {
    'log_recognition_results': True,
    'save_failed_commands': True,
    'enable_command_training': True,
    'verbose_logging': False,
}

def get_optimized_settings():
    """Get recommended settings based on test results"""
    return {
        'use_google_primary': True,
        'use_vosk_fallback': False,  # Disabled due to poor performance
        'timeout': 8,
        'energy_threshold': 200,
        'pause_threshold': 1.2,
        'enable_fuzzy_matching': True,
        'try_on_variations': TRY_ON_VARIATIONS
    } 