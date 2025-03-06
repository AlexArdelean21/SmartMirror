import cv2
import face_recognition
import pickle

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

    video_capture = cv2.VideoCapture(0)
    speak_response("Looking for faces...")

    while True:
        ret, frame = video_capture.read()
        if not ret:
            speak_response("Error accessing camera.")
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)

        # Ensure at least one face is detected
        if not face_locations:
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

        speak_response("I don't recognize you. Would you like to register?")
        video_capture.release()
        return "Unknown"


def add_face_vocally(name=None):
    from services.voice_service import listen_command, speak_response
    known_faces = load_known_faces()

    if not name:
        speak_response("Please state your name.")
        name = listen_command()

    if not name or name.lower() in ["unknown", "secret"]:
        return "I didn't catch that. Please try again."

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
        speak_response(f"Face added successfully for {name}.")
        break

    video_capture.release()
    return "Face addition process complete."


