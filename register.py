import cv2
from pathlib import Path

name = input("Authorized person's name: ").strip()

if not name:
    raise ValueError("Name cannot be empty")

folder = Path("authorized_people")
folder.mkdir(exist_ok=True)

image_path = folder / f"{name}.jpg"

face_detector = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not camera.isOpened():
    raise RuntimeError("Could not open webcam")

print("Face the camera clearly.")
print("Press S to save the detected face. Press Q to quit.")

while True:
    success, frame = camera.read()

    if not success:
        print("Could not read camera frame")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_detector.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(100, 100)
    )

    display = frame.copy()

    for x, y, width, height in faces:
        cv2.rectangle(
            display,
            (x, y),
            (x + width, y + height),
            (0, 255, 0),
            2
        )

    cv2.putText(
        display,
        "S: Save Face | Q: Quit",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2
    )

    cv2.imshow("Register Authorized Person", display)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("s"):
        if len(faces) == 0:
            print("No face detected. Try again.")
            continue

        if len(faces) > 1:
            print("More than one face detected. Only one person should be visible.")
            continue

        x, y, width, height = faces[0]

        padding = 30
        x1 = max(0, x - padding)
        y1 = max(0, y - padding)
        x2 = min(frame.shape[1], x + width + padding)
        y2 = min(frame.shape[0], y + height + padding)

        face_image = frame[y1:y2, x1:x2]

        cv2.imwrite(str(image_path), face_image)
        print(f"Saved face image: {image_path}")
        break

    if key == ord("q"):
        print("Cancelled")
        break

camera.release()
cv2.destroyAllWindows()