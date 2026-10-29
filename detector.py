from ultralytics import YOLO

model = YOLO("yolo26n.pt")


def detect_and_track_people(frame):
    result = model.track(
        source=frame,
        persist=True,
        tracker="bytetrack.yaml",
        classes=[0],
        conf=0.5,
        verbose=False
    )[0]

    people = []
    track_ids = result.boxes.id

    if track_ids is None:
        return people

    for index, box in enumerate(result.boxes):
        track_id = int(track_ids[index].item())
        x1, y1, x2, y2 = map(int, box.xyxy[0])

        people.append({
            "track_id": track_id,
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "bbox": (x1, y1, x2, y2),
            "center": ((x1 + x2) // 2, (y1 + y2) // 2),
            "bottom_center": ((x1 + x2) // 2, y2)
        })

    return people