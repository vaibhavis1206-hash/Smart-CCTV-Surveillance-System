import cv2
import json
import numpy as np
from pathlib import Path

OBJECT_FOLDER = Path("registered_objects")
OBJECT_DATA_FILE = OBJECT_FOLDER / "objects.json"

OBJECT_MOVE_THRESHOLD = 40


def calculate_distance(point1, point2):
    x1, y1 = point1
    x2, y2 = point2

    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


def load_registered_object(object_name=None):
    if not OBJECT_DATA_FILE.exists():
        raise RuntimeError("objects.json not found. Register object first.")

    with open(OBJECT_DATA_FILE, "r") as file:
        all_objects = json.load(file)

    if not all_objects:
        raise RuntimeError("No registered object found.")

    if object_name is None:
        # Use the latest registered object by default.
        safe_name = list(all_objects.keys())[-1]
    else:
        safe_name = object_name.strip().replace(" ", "_").lower()

    if safe_name not in all_objects:
        raise RuntimeError(f"Object not found: {object_name}")

    object_info = all_objects[safe_name]

    object_image = cv2.imread(object_info["image_path"])

    if object_image is None:
        raise RuntimeError("Could not load registered object image.")

    orb = cv2.ORB_create(nfeatures=1500)

    object_gray = cv2.cvtColor(object_image, cv2.COLOR_BGR2GRAY)
    keypoints, descriptors = orb.detectAndCompute(object_gray, None)

    if descriptors is None or len(keypoints) < 10:
        raise RuntimeError("Object image has too few features. Use a clearer object image.")

    return {
        "name": object_info["name"],
        "safe_name": safe_name,
        "image": object_image,
        "keypoints": keypoints,
        "descriptors": descriptors,
        "width": object_image.shape[1],
        "height": object_image.shape[0],
        "original_center": tuple(object_info["location"]["center"]),
        "orb": orb
    }


def detect_registered_object(frame, registered_object):
    orb = registered_object["orb"]

    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame_keypoints, frame_descriptors = orb.detectAndCompute(frame_gray, None)

    if frame_descriptors is None or len(frame_keypoints) < 10:
        return False, None

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING)

    matches = matcher.knnMatch(
        registered_object["descriptors"],
        frame_descriptors,
        k=2
    )

    good_matches = []

    for pair in matches:
        if len(pair) < 2:
            continue

        best_match, second_best = pair

        if best_match.distance < 0.75 * second_best.distance:
            good_matches.append(best_match)

    if len(good_matches) < 12:
        return False, None

    object_points = np.float32([
        registered_object["keypoints"][match.queryIdx].pt
        for match in good_matches
    ]).reshape(-1, 1, 2)

    frame_points = np.float32([
        frame_keypoints[match.trainIdx].pt
        for match in good_matches
    ]).reshape(-1, 1, 2)

    homography, mask = cv2.findHomography(
        object_points,
        frame_points,
        cv2.RANSAC,
        5.0
    )

    if homography is None:
        return False, None

    inliers = int(mask.sum()) if mask is not None else 0

    if inliers < 10:
        return False, None

    width = registered_object["width"]
    height = registered_object["height"]

    object_corners = np.float32([
        [0, 0],
        [width, 0],
        [width, height],
        [0, height]
    ]).reshape(-1, 1, 2)

    projected_corners = cv2.perspectiveTransform(
        object_corners,
        homography
    )

    x_values = projected_corners[:, 0, 0]
    y_values = projected_corners[:, 0, 1]

    x1 = int(max(0, min(x_values)))
    y1 = int(max(0, min(y_values)))
    x2 = int(min(frame.shape[1], max(x_values)))
    y2 = int(min(frame.shape[0], max(y_values)))

    if x2 <= x1 or y2 <= y1:
        return False, None

    object_area = (x2 - x1) * (y2 - y1)
    frame_area = frame.shape[0] * frame.shape[1]

    if object_area > frame_area * 0.7:
        return False, None

    current_center = ((x1 + x2) // 2, (y1 + y2) // 2)
    original_center = registered_object["original_center"]

    movement = calculate_distance(current_center, original_center)
    moved = movement >= OBJECT_MOVE_THRESHOLD

    object_data = {
        "name": registered_object["name"],
        "x1": x1,
        "y1": y1,
        "x2": x2,
        "y2": y2,
        "center": current_center,
        "original_center": original_center,
        "movement": movement,
        "moved": moved,
        "matches": len(good_matches),
        "inliers": inliers,
        "corners": projected_corners.astype(int)
    }

    return True, object_data

