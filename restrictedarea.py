import cv2
import json
import numpy as np
from pathlib import Path

AREA_FILE = Path(__file__).with_name("restricted_area.json")

polygon_points = []
polygon_closed = False


def load_area():
    global polygon_points, polygon_closed

    if AREA_FILE.exists():
        try:
            with open(AREA_FILE, "r") as file:
                polygon_points = [tuple(point) for point in json.load(file)]

            if len(polygon_points) >= 3:
                polygon_closed = True
                print("Loaded saved restricted area:", polygon_points)
            else:
                polygon_points = []
                polygon_closed = False
                print(
                    "Saved restricted area is invalid (less than 3 points).",
                    "Please select points again."
                )
        except Exception as error:
            print("Failed to load saved restricted area:", error)
            polygon_points = []
            polygon_closed = False
    else:
        polygon_points = []
        polygon_closed = False
        print("No saved restricted area found. Click points to create one.")

    return polygon_points, polygon_closed


def save_area():
    if len(polygon_points) < 3:
        print("Select at least 3 points before saving.")
        return

    with open(AREA_FILE, "w") as file:
        json.dump(polygon_points, file)

    print("Restricted area saved:", polygon_points)


def reset_area():
    global polygon_points, polygon_closed

    polygon_points = []
    polygon_closed = False

    if Path(AREA_FILE).exists():
        Path(AREA_FILE).unlink()

    print("Restricted area reset. Click new points to create another area.")


def mouse_callback(event, x, y, flags, param):
    global polygon_points

    if event == cv2.EVENT_LBUTTONDOWN:
        if polygon_closed:
            print("Area already saved. Press R to reset before drawing a new area.")
            return

        polygon_points.append((x, y))
        print("Point added:", (x, y))


def close_area():
    global polygon_closed

    if len(polygon_points) >= 3:
        polygon_closed = True
        save_area()
    else:
        print("Select at least 3 points.")


def draw_area(frame):
    for point in polygon_points:
        cv2.circle(frame, point, 5, (0, 0, 255), -1)

    if len(polygon_points) > 1:
        for i in range(len(polygon_points) - 1):
            cv2.line(
                frame,
                polygon_points[i],
                polygon_points[i + 1],
                (0, 0, 255),
                2
            )

    if polygon_closed and len(polygon_points) > 2:
        cv2.line(
            frame,
            polygon_points[-1],
            polygon_points[0],
            (0, 0, 255),
            2
        )

    if polygon_closed:
        cv2.putText(
            frame,
            "Restricted area active | R: reset",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2
        )
    elif polygon_points:
        cv2.putText(
            frame,
            f"Selected points: {len(polygon_points)} | C: save | R: reset",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )
    else:
        cv2.putText(
            frame,
            "Click points, then press C to save restricted area",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 0),
            2
        )


def point_inside_area(point):
    if not polygon_closed or len(polygon_points) < 3:
        return False

    polygon_array = np.array(polygon_points, dtype=np.int32)
    return cv2.pointPolygonTest(polygon_array, point, False) >= 0