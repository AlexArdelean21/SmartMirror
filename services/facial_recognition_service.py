import cv2
import face_recognition
import pickle
import time
# Load or save known faces
def load_known_faces():
    try:
        with open("pictures/known_faces.pkl", "rb") as file:
            return pickle.load(file)
    except FileNotFoundError:
        return {}

def save_known_faces(known_faces):
    with open("pictures/known_faces.pkl", "wb") as file:
        pickle.dump(known_faces, file)


def recognize_faces_vocally():
    from services.voice_service import speak_response
    known_faces = load_known_faces()
    known_encodings = list(known_faces.values())
    known_names = list(known_faces.keys())
    start_time = time.time()
    wating_time = 120 # looks for a face for 20s

    video_capture = cv2.VideoCapture(0)
    speak_response("Let's see who it is...")

    while True:
        ret, frame = video_capture.read()
        if not ret:
            speak_response("Error accessing camera.")
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)

        if not face_locations:
            if time.time() - start_time > wating_time:
                speak_response("Couldn't find a face!")
                return "ghost"
            continue  # Skip processing if no faces are found

        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        if not face_encodings:
            speak_response("Unable to extract facial features. Try again.")
            continue

        for encoding, (top, right, bottom, left) in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(known_encodings, encoding, tolerance=0.5)
            name = "Unknown"

            if True in matches:
                match_index = matches.index(True)
                name = known_names[match_index]
                speak_response(f"Hello {name}, welcome back!")
                video_capture.release()
                return name

        video_capture.release()
        # return Unknown user
        return name


def add_face_vocally(name=None):
    from services.voice_service import listen_command, speak_response
    known_faces = load_known_faces()

    if not name:
        speak_response("Please state your name.")
        name = listen_command()

    if name or name.lower() in known_faces:
        return f"You are already registered, {name}."

    video_capture = cv2.VideoCapture(0)
    speak_response(f"Looking for your face, {name}. Please stay still.")

    while True:
        ret, frame = video_capture.read()
        if not ret:
            speak_response("Error accessing camera.")
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)

        if not face_locations:
            speak_response("No face detected. Try again.")
            continue

        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        if not face_encodings:
            speak_response("Unable to extract facial features. Try again.")
            continue

        known_faces[name] = face_encodings[0]
        save_known_faces(known_faces)
        # speak_response(f"Face added successfully for {name}.")
        break

    video_capture.release()
    return "Face addition process complete."


