import cv2
import face_recognition
from pathlib import Path

AUTHORIZED_FOLDER = Path("authorized_people")
TOLERANCE = 0.5


def load_authorized_faces():
    known_encodings = []
    known_names = []

    for image_path in AUTHORIZED_FOLDER.glob("*.*"):
        if image_path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue

        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)

        if encodings:
            known_encodings.append(encodings[0])
            known_names.append(image_path.stem)
            print(f"Loaded authorized person: {image_path.stem}")

    return known_encodings, known_names


def check_face_authorization(person_crop, known_encodings, known_names):
    if person_crop.size == 0:
        return False, "UNKNOWN"

    rgb_crop = cv2.cvtColor(person_crop, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb_crop)
    face_encodings = face_recognition.face_encodings(rgb_crop, face_locations)

    if not face_encodings:
        return False, "UNKNOWN"

    for face_encoding in face_encodings:
        distances = face_recognition.face_distance(known_encodings, face_encoding)
        best_index = distances.argmin()

        if distances[best_index] <= TOLERANCE:
            return True, known_names[best_index]

    return False, "UNKNOWN"