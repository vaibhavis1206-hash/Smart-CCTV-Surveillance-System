import cv2
import time
from pathlib import Path
from datetime import datetime

from detector import detect_and_track_people
from comparedata import load_authorized_faces, check_face_authorization

from restrictedarea import (
    load_area,
    mouse_callback,
    draw_area,
    point_inside_area,
    close_area,
    reset_area
)

from suspecious import SuspiciousDetector
from detectfighting import FightDetector

from objectregister import register_object
from detectobject import load_registered_object, detect_registered_object
from thief import ObjectTheftDetector

try:
    from storedatamongodb import store_unknown_person_data
except ImportError:
    store_unknown_person_data = None


known_encodings, known_names = load_authorized_faces()

if not known_encodings:
    raise RuntimeError("No authorized faces found.")

load_area()

suspicious_detector = SuspiciousDetector()
fight_detector = FightDetector()
object_theft_detector = ObjectTheftDetector()

RESTRICTED_FOLDER = Path("restricted_screenshots")
RESTRICTED_FOLDER.mkdir(exist_ok=True)

restricted_screenshot_time = {}
RESTRICTED_COOLDOWN = 10

camera = cv2.VideoCapture(1, cv2.CAP_DSHOW)

if not camera.isOpened():
    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not camera.isOpened():
    raise RuntimeError("Could not open webcam")


registered_object = None
object_detection_enabled = False

choice = input("Do you want to use theft/object detection? y/n: ").strip().lower()

if choice == "y":
    object_choice = input("Register new precious object? y/n: ").strip().lower()

    if object_choice == "y":
        object_path = register_object(camera)
        print("Registered object saved at:", object_path)

    try:
        registered_object = load_registered_object()
        object_detection_enabled = True
        print(f"Object detection enabled: {registered_object['name']}")

    except RuntimeError as error:
        print("Object detection disabled:", error)
        registered_object = None
        object_detection_enabled = False

else:
    print("Object/theft detection skipped.")


cv2.namedWindow("AI CCTV System", cv2.WINDOW_NORMAL)
cv2.setMouseCallback("AI CCTV System", mouse_callback)

print("AI CCTV System started.")
print("C = confirm/save restricted area")
print("R = reset restricted area")
print("Q = quit")

frame_counter = 0
known_people_status = {}

while True:
    success, frame = camera.read()

    if not success:
        break

    frame_counter += 1

    draw_area(frame)

    people = detect_and_track_people(frame)

    object_found = False
    object_data = None

    if object_detection_enabled:
        object_found, object_data = detect_registered_object(
            frame,
            registered_object
        )

    if object_detection_enabled and object_found:
        corners = object_data["corners"]

        cv2.polylines(
            frame,
            [corners],
            isClosed=True,
            color=(255, 0, 0),
            thickness=2
        )

        cv2.putText(
            frame,
            f"{object_data['name']} moved:{object_data['moved']}",
            (object_data["x1"], max(30, object_data["y1"] - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 0, 0),
            2
        )

    elif object_detection_enabled:
        cv2.putText(
            frame,
            "Registered object not found",
            (20, 150),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2
        )

    people_status = []
    alert = False

    for person in people:
        track_id = person["track_id"]
        x1 = person["x1"]
        y1 = person["y1"]
        x2 = person["x2"]
        y2 = person["y2"]
        person_center = person["center"]
        bottom_center = person["bottom_center"]

        person_crop = frame[y1:y2, x1:x2]

        if frame_counter % 5 == 0 or track_id not in known_people_status:
            is_authorized, name = check_face_authorization(
                person_crop,
                known_encodings,
                known_names
            )

            known_people_status[track_id] = {
                "is_authorized": is_authorized,
                "name": name
            }

        else:
            is_authorized = known_people_status[track_id]["is_authorized"]
            name = known_people_status[track_id]["name"]

        inside = point_inside_area(bottom_center)

        person_status = {
            "track_id": track_id,
            "is_authorized": is_authorized,
            "name": name,
            "center": person_center,
            "bottom_center": bottom_center,
            "inside_restricted": inside,
            "bbox": (x1, y1, x2, y2)
        }

        suspicious, standing_time = suspicious_detector.check_suspicious(
            frame,
            person_status
        )

        person_status["suspicious"] = suspicious
        person_status["standing_time"] = standing_time

        people_status.append(person_status)

    frame, fight_pairs = fight_detector.detect_fight(frame, people_status)

    theft_ids = []

    if object_detection_enabled:
        theft_ids = object_theft_detector.check_theft(
            frame,
            object_found,
            object_data,
            people_status
        )

    fight_ids = set()

    for pair_key in fight_pairs:
        id_a, id_b = pair_key.split("_")
        fight_ids.add(int(id_a))
        fight_ids.add(int(id_b))

    for person_status in people_status:
        track_id = person_status["track_id"]
        is_authorized = person_status["is_authorized"]
        name = person_status["name"]
        inside = person_status["inside_restricted"]
        suspicious = person_status["suspicious"]
        standing_time = person_status["standing_time"]
        x1, y1, x2, y2 = person_status["bbox"]

        if track_id in fight_ids:
            alert = True
            color = (0, 0, 255)
            label = f"ID {track_id} FIGHTING"

        elif track_id in theft_ids:
            alert = True
            color = (0, 0, 255)
            label = f"ID {track_id} UNKNOWN THIEF"

        elif suspicious:
            alert = True
            color = (0, 0, 255)
            label = f"ID {track_id} UNKNOWN SUSPICIOUS: {int(standing_time)}s"

        elif inside and not is_authorized:
            alert = True
            color = (0, 0, 255)
            label = f"ID {track_id} UNKNOWN: RESTRICTED"

            current_time = time.time()
            last_time = restricted_screenshot_time.get(track_id, 0)

            if current_time - last_time >= RESTRICTED_COOLDOWN:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = (
                    RESTRICTED_FOLDER
                    / f"unknown_restricted_id_{track_id}_{timestamp}.jpg"
                )

                cv2.imwrite(str(screenshot_path), frame)
                print("Restricted screenshot saved:", screenshot_path)

                if store_unknown_person_data is not None:
                    try:
                        store_unknown_person_data(
                            screenshot_path,
                            alert_type="RESTRICTED_AREA"
                        )
                    except Exception as error:
                        print("MongoDB save failed:", error)

                restricted_screenshot_time[track_id] = current_time

        elif inside and is_authorized:
            color = (0, 255, 0)
            label = f"ID {track_id} AUTHORIZED: {name}"

        elif is_authorized:
            color = (255, 255, 0)
            label = f"ID {track_id} AUTHORIZED: {name}"

        else:
            color = (0, 255, 255)
            label = f"ID {track_id} UNKNOWN: {int(standing_time)}s"

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.circle(frame, person_status["bottom_center"], 6, color, -1)

        cv2.putText(
            frame,
            label,
            (x1, max(30, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2
        )

    if alert or fight_pairs:
        cv2.putText(
            frame,
            "ALERT: CCTV ACTIVITY DETECTED",
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            3
        )

    cv2.imwrite("live_frame.jpg", frame)
    cv2.imshow("AI CCTV System", frame)

    key = cv2.waitKey(1) & 0xFF

    if key in (ord("c"), ord("C")):
        close_area()

    elif key in (ord("r"), ord("R")):
        reset_area()
        suspicious_detector.reset()
        object_theft_detector.reset()
        known_people_status.clear()
        restricted_screenshot_time.clear()

    elif key in (ord("q"), ord("Q")):
        break

camera.release()
cv2.destroyAllWindows()