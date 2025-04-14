import cv2
import face_recognition
import pickle
import time
import os
from util.logger import logger


def load_known_faces():
    try:
        with open("pictures/known_faces.pkl", "rb") as file:
            logger.info("Loaded known_faces.pkl successfully.")
            return pickle.load(file)
    except FileNotFoundError:
        logger.warning("known_faces.pkl not found. Returning empty dictionary.")
        return {}


def save_known_faces(known_faces):
    with open("pictures/known_faces.pkl", "wb") as file:
        pickle.dump(known_faces, file)
        logger.info("Saved known faces to known_faces.pkl.")


def recognize_faces_vocally():
    from services.voice_service import speak_response
    known_faces = load_known_faces()
    known_encodings = list(known_faces.values())
    known_names = list(known_faces.keys())
    start_time = time.time()
    wating_time = 20  # looks for a face for 20s

    video_capture = cv2.VideoCapture(0)
    speak_response("Let's see who it is...")
    logger.info("Started facial recognition...")

    while True:
        ret, frame = video_capture.read()
        if not ret:
            speak_response("Error accessing camera.")
            logger.error("Failed to access webcam.")
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)

        if not face_locations:
            if time.time() - start_time > wating_time:
                speak_response("Couldn't find a face!")
                logger.warning("Timeout: No face found within 20 seconds.")
                return "ghost"
            continue

        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        if not face_encodings:
            speak_response("Unable to extract facial features. Try again.")
            logger.warning("Face detected but no encoding could be extracted.")
            continue

        for encoding, (top, right, bottom, left) in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(known_encodings, encoding, tolerance=0.5)
            name = "Unknown"

            if True in matches:
                match_index = matches.index(True)
                name = known_names[match_index]
                video_capture.release()
                return name

        logger.info("No matching face found. Returning 'Unknown'.")
        video_capture.release()
        return name


def add_face_vocally(name=None):
    from services.voice_service import listen_command, speak_response
    known_faces = load_known_faces()

    if not name:
        speak_response("Please state your name.")
        name = listen_command()

    if name.lower() in known_faces:
        logger.info(f"Face already registered for user: {name}")
        return f"You are already registered, {name}."

    video_capture = cv2.VideoCapture(0)
    speak_response(f"Looking for your face, {name}. Please stay still.")
    logger.info(f"Starting face registration for: {name}")

    while True:
        ret, frame = video_capture.read()
        if not ret:
            speak_response("Error accessing camera.")
            logger.error("Failed to access webcam during face addition.")
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)

        if not face_locations:
            speak_response("No face detected. Try again.")
            logger.warning("No face detected during face addition.")
            continue

        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        if not face_encodings:
            speak_response("Unable to extract facial features. Try again.")
            logger.warning("Unable to encode detected face.")
            continue

        known_faces[name] = face_encodings[0]
        save_known_faces(known_faces)
        logger.info(f"Face added for user: {name}")
        break

    video_capture.release()
    return "Face addition process complete."


def list_registered_faces():  # admin function
    try:
        base_path = os.path.dirname(os.path.dirname(__file__))
        face_path = os.path.join(base_path, "pictures", "known_faces.pkl")
        with open(face_path, "rb") as f:
            known_faces = pickle.load(f)
            print("Raw known_faces loaded:", known_faces)
            print("Type:", type(known_faces))
            return list(known_faces.keys()) if isinstance(known_faces, dict) else []
    except Exception as e:
        print(f"Failed to load known_faces: {e}")
        return []


def delete_face_by_name(name):  # admin function
    try:
        base_path = os.path.dirname(os.path.dirname(__file__))
        face_path = os.path.join(base_path, "pictures", "known_faces.pkl")

        with open(face_path, "rb") as f:
            known_faces = pickle.load(f)

        if name in known_faces:
            del known_faces[name]
            with open(face_path, "wb") as f:
                pickle.dump(known_faces, f)
            print(f"Deleted face data for '{name}'.")
        else:
            print(f"No face found with the name '{name}'.")
    except Exception as e:
        print(f"Error: {e}")

print(list_registered_faces())
