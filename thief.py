import cv2
import time
from pathlib import Path
from datetime import datetime

try:
    from storedatamongodb import store_unknown_person_data
except ImportError:
    store_unknown_person_data = None

THEFT_FOLDER = Path("theft_suspect_screenshots")
THEFT_FOLDER.mkdir(exist_ok=True)


class ObjectTheftDetector:
    def __init__(self):
        self.theft_counter = {}
        self.screenshot_taken = {}
        self.last_debug_time = 0
        self.last_status = "Theft detector waiting"

        self.NEAR_OBJECT_DISTANCE = 220
        self.THEFT_CONFIRM_FRAMES = 5
        self.SCREENSHOT_COOLDOWN = 10

    def distance(self, point1, point2):
        x1, y1 = point1
        x2, y2 = point2
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    def check_theft(self, frame, object_found, object_data, people_status):
        theft_ids = []

        if not object_found or object_data is None:
            self.set_status("OBJECT NOT FOUND - register a clear cropped object")
            self.draw_status(frame)
            return theft_ids

        object_center = object_data["center"]
        object_moved = object_data["moved"]
        object_movement = object_data.get("movement", 0)

        if not people_status:
            self.set_status(
                f"OBJECT FOUND | moved={object_moved} | movement={int(object_movement)}px | no person"
            )
            self.draw_status(frame)
            return theft_ids

        best_status = None

        for person in people_status:
            track_id = person["track_id"]
            is_authorized = person["is_authorized"]
            person_center = person["center"]

            distance_from_object = self.distance(person_center, object_center)

            if is_authorized:
                self.theft_counter[track_id] = 0
                best_status = (
                    f"ID {track_id} AUTHORIZED - theft ignored | "
                    f"object moved={object_moved} movement={int(object_movement)}px"
                )
                continue

            near_object = distance_from_object <= self.NEAR_OBJECT_DISTANCE

            if near_object and object_moved:
                self.theft_counter[track_id] = (
                    self.theft_counter.get(track_id, 0) + 1
                )
            else:
                self.theft_counter[track_id] = 0

            counter = self.theft_counter[track_id]
            best_status = (
                f"ID {track_id} UNKNOWN | moved={object_moved} "
                f"movement={int(object_movement)}px | "
                f"distance={int(distance_from_object)}px | "
                f"counter={counter}/{self.THEFT_CONFIRM_FRAMES}"
            )

            if counter >= self.THEFT_CONFIRM_FRAMES:
                theft_ids.append(track_id)
                self.save_screenshot(frame, track_id)

        if best_status is not None:
            self.set_status(best_status)

        self.draw_status(frame)
        return theft_ids

    def set_status(self, message):
        self.last_status = message
        current_time = time.time()

        if current_time - self.last_debug_time >= 1:
            print("THEFT DEBUG:", message)
            self.last_debug_time = current_time

    def draw_status(self, frame):
        cv2.putText(
            frame,
            self.last_status[:95],
            (20, 180),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 255, 255),
            2
        )

    def save_screenshot(self, frame, track_id):
        current_time = time.time()
        last_time = self.screenshot_taken.get(track_id, 0)

        if current_time - last_time < self.SCREENSHOT_COOLDOWN:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = (
            THEFT_FOLDER / f"unknown_thief_id_{track_id}_{timestamp}.jpg"
        )

        cv2.imwrite(str(screenshot_path), frame)
        print(f"Unknown thief screenshot saved: {screenshot_path}")

        if store_unknown_person_data is not None:
            try:
                store_unknown_person_data(screenshot_path, alert_type="THEFT")
            except Exception as error:
                print("MongoDB save failed:", error)

        self.screenshot_taken[track_id] = current_time

    def reset(self):
        self.theft_counter.clear()
        self.screenshot_taken.clear()
        self.last_debug_time = 0
        self.last_status = "Theft detector reset"
