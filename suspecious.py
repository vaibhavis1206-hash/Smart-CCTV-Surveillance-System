import cv2
import time
from pathlib import Path
from datetime import datetime

try:
    from storedatamongodb import store_unknown_person_data
except ImportError:
    store_unknown_person_data = None


class SuspiciousDetector:
    def __init__(self):
        self.person_states = {}

        self.STANDING_TIME_LIMIT = 10  # seconds
        self.MOVEMENT_LIMIT = 50

        self.screenshot_folder = Path("suspicious_screenshots")
        self.screenshot_folder.mkdir(exist_ok=True)

    def distance(self, point1, point2):
        x1, y1 = point1
        x2, y2 = point2
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    def check_suspicious(self, frame, person_status):
        track_id = person_status["track_id"]
        bottom_center = person_status["bottom_center"]
        is_authorized = person_status["is_authorized"]

        if is_authorized:
            self.person_states.pop(track_id, None)
            return False, 0

        current_time = time.time()

        if track_id not in self.person_states:
            self.person_states[track_id] = {
                "start_position": bottom_center,
                "start_time": current_time,
                "screenshot_taken": False
            }

        state = self.person_states[track_id]
        movement = self.distance(bottom_center, state["start_position"])

        if movement > self.MOVEMENT_LIMIT:
            state["start_position"] = bottom_center
            state["start_time"] = current_time
            state["screenshot_taken"] = False

        standing_time = current_time - state["start_time"]

        if standing_time >= self.STANDING_TIME_LIMIT:
            if not state["screenshot_taken"]:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = (
                    self.screenshot_folder
                    / f"unknown_suspicious_id_{track_id}_{timestamp}.jpg"
                )

                cv2.imwrite(str(screenshot_path), frame)
                print(f"Suspicious screenshot saved: {screenshot_path}")

                if store_unknown_person_data is not None:
                    store_unknown_person_data(screenshot_path, alert_type="SUSPICIOUS")

                state["screenshot_taken"] = True

            return True, standing_time

        return False, standing_time

    def reset(self):
        self.person_states.clear()