import cv2
import time
from pathlib import Path
from datetime import datetime

try:
    from storedatamongodb import store_unknown_person_data
except ImportError:
    store_unknown_person_data = None


class FightDetector:
    def __init__(self):
        self.previous_positions = {}
        self.fight_counter = {}
        self.screenshot_taken = {}

        self.SPEED_THRESHOLD = 120
        self.DISTANCE_THRESHOLD = 180
        self.IOU_THRESHOLD = 0.08
        self.FIGHT_CONFIRM_FRAMES = 12
        self.SCREENSHOT_COOLDOWN = 10

        self.screenshot_folder = Path("fight_screenshots")
        self.screenshot_folder.mkdir(exist_ok=True)

    def calculate_distance(self, p1, p2):
        return ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2) ** 0.5

    def calculate_iou(self, box_a, box_b):
        ax1, ay1, ax2, ay2 = box_a
        bx1, by1, bx2, by2 = box_b

        inter_x1 = max(ax1, bx1)
        inter_y1 = max(ay1, by1)
        inter_x2 = min(ax2, bx2)
        inter_y2 = min(ay2, by2)

        inter_width = max(0, inter_x2 - inter_x1)
        inter_height = max(0, inter_y2 - inter_y1)
        intersection = inter_width * inter_height

        area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
        area_b = max(0, bx2 - bx1) * max(0, by2 - by1)

        union = area_a + area_b - intersection

        if union == 0:
            return 0

        return intersection / union

    def save_fight_screenshot(self, frame, pair_key):
        current_time = time.time()
        last_time = self.screenshot_taken.get(pair_key, 0)

        if current_time - last_time < self.SCREENSHOT_COOLDOWN:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = self.screenshot_folder / f"fight_{pair_key}_{timestamp}.jpg"

        cv2.imwrite(str(screenshot_path), frame)
        print(f"Fight screenshot saved: {screenshot_path}")

        if store_unknown_person_data is not None:
            store_unknown_person_data(screenshot_path, alert_type="FIGHT")

        self.screenshot_taken[pair_key] = current_time

    def detect_fight(self, frame, people):
        fight_pairs = []
        current_time = time.time()

        people_with_speed = []

        for person in people:
            track_id = person["track_id"]
            center = person["center"]
            bbox = person["bbox"]

            speed = 0

            if track_id in self.previous_positions:
                old_center, old_time = self.previous_positions[track_id]
                time_diff = current_time - old_time

                if time_diff > 0:
                    speed = self.calculate_distance(old_center, center) / time_diff

            self.previous_positions[track_id] = (center, current_time)

            people_with_speed.append({
                "track_id": track_id,
                "bbox": bbox,
                "center": center,
                "speed": speed
            })

        for i in range(len(people_with_speed)):
            for j in range(i + 1, len(people_with_speed)):
                person_a = people_with_speed[i]
                person_b = people_with_speed[j]

                id_a = person_a["track_id"]
                id_b = person_b["track_id"]

                pair_key = f"{min(id_a, id_b)}_{max(id_a, id_b)}"

                distance = self.calculate_distance(
                    person_a["center"],
                    person_b["center"]
                )

                iou = self.calculate_iou(
                    person_a["bbox"],
                    person_b["bbox"]
                )

                both_fast = (
                    person_a["speed"] >= self.SPEED_THRESHOLD
                    and person_b["speed"] >= self.SPEED_THRESHOLD
                )

                close_enough = distance <= self.DISTANCE_THRESHOLD
                boxes_colliding = iou >= self.IOU_THRESHOLD

                possible_fight = close_enough and boxes_colliding and both_fast

                if possible_fight:
                    self.fight_counter[pair_key] = self.fight_counter.get(pair_key, 0) + 1
                else:
                    self.fight_counter[pair_key] = 0

                if self.fight_counter[pair_key] >= self.FIGHT_CONFIRM_FRAMES:
                    fight_pairs.append(pair_key)
                    self.save_fight_screenshot(frame, pair_key)

        return frame, fight_pairs