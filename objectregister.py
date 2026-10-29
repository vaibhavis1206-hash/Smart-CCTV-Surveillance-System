import cv2
import json
from pathlib import Path

OBJECT_FOLDER = Path("registered_objects")
OBJECT_FOLDER.mkdir(exist_ok=True)

OBJECT_DATA_FILE = OBJECT_FOLDER / "objects.json"


def make_safe_name(name):
    return name.strip().replace(" ", "_").lower()


def load_object_data():
    if OBJECT_DATA_FILE.exists():
        with open(OBJECT_DATA_FILE, "r") as file:
            return json.load(file)

    return {}


def save_object_data(data):
    with open(OBJECT_DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)


def register_object(camera):
    object_name = input("Enter object name: ").strip()

    if not object_name:
        raise RuntimeError("Object name cannot be empty")

    safe_name = make_safe_name(object_name)

    print("Place the object clearly in front of the camera.")
    print("Press S when the object is clear.")
    print("Press Q to cancel.")

    selected_frame = None

    while True:
        success, frame = camera.read()

        if not success:
            raise RuntimeError("Could not read camera frame")

        display = frame.copy()

        cv2.putText(
            display,
            "Place object clearly | Press S to capture | Q to cancel",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )

        cv2.imshow("Register Object Camera", display)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("s"):
            selected_frame = frame.copy()
            cv2.destroyWindow("Register Object Camera")
            break

        elif key == ord("q"):
            cv2.destroyWindow("Register Object Camera")
            raise RuntimeError("Object registration cancelled")

    crop_display = selected_frame.copy()

    cv2.putText(
        crop_display,
        "Select object with mouse, then press ENTER or SPACE",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 255),
        2
    )

    object_box = cv2.selectROI(
        "Select Object Crop",
        crop_display,
        fromCenter=False,
        showCrosshair=True
    )

    cv2.destroyWindow("Select Object Crop")

    x, y, width, height = map(int, object_box)

    if width == 0 or height == 0:
        raise RuntimeError("No object selected")

    object_crop = selected_frame[y:y + height, x:x + width]

    if object_crop.size == 0:
        raise RuntimeError("Selected object crop is empty")

    object_path = OBJECT_FOLDER / f"{safe_name}.jpg"
    cv2.imwrite(str(object_path), object_crop)

    center_x = x + width // 2
    center_y = y + height // 2

    all_objects = load_object_data()

    all_objects[safe_name] = {
        "name": object_name,
        "image_path": str(object_path),
        "location": {
            "x": x,
            "y": y,
            "w": width,
            "h": height,
            "center": [center_x, center_y]
        }
    }

    save_object_data(all_objects)

    print("Object image saved:", object_path)
    print("Object data saved:", OBJECT_DATA_FILE)

    return object_path