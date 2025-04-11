from flask_socketio import SocketIO
from util.audio_state import set_audio_playing

set_audio_playing(False)
socketio = SocketIO(cors_allowed_origins="*")