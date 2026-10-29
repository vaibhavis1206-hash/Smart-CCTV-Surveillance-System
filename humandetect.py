from ultralytics import YOLO

model = YOLO("yolo26n.pt")


def detect_humans(frame):
    result = model.track(
        source=frame,
        persist=True,
        tracker="bytetrack.yaml",
        classes=[0],
        conf=0.5,
        verbose=False
    )[0]

    humans = []
    track_ids = result.boxes.id

    for index, box in enumerate(result.boxes):
        if track_ids is None:
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0])
        track_id = int(track_ids[index].item())

        humans.append({
            "track_id": track_id,
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "bottom_center": ((x1 + x2) // 2, y2)
        })

    return humans