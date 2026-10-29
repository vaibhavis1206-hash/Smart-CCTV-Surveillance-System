import base64
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_from_directory
from flask_cors import CORS
import cv2

app = Flask(__name__)
CORS(app)

BASE_DIR = Path(__file__).parent
LATEST_FRAME = BASE_DIR / "latest_frame.jpg"
LIVE_FRAME = BASE_DIR / "live_frame.jpg"
PLACEHOLDER_FRAME = base64.b64decode(
    "R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=="
)

SCREENSHOT_FOLDERS = {
    "restricted": BASE_DIR / "restricted_screenshots",
    "suspicious": BASE_DIR / "suspicious_screenshots",
    "theft": BASE_DIR / "theft_suspect_screenshots",
    "fight": BASE_DIR / "fight_screenshots",
}


@app.route("/")
def home():
    return jsonify({
        "message": "AI CCTV backend is running"
    })


@app.route("/api/status")
def status():
    return jsonify({
        "system": "online",
        "backend": "running",
        "camera": "handled by main.py"
    })


@app.route("/api/alerts")
def get_alerts():
    alerts = []

    for alert_type, folder in SCREENSHOT_FOLDERS.items():
        folder.mkdir(exist_ok=True)

        for image_path in folder.glob("*.jpg"):
            created_time = image_path.stat().st_mtime

            alerts.append({
                "type": alert_type,
                "filename": image_path.name,
                "image_url": f"http://localhost:5000/api/screenshots/{alert_type}/{image_path.name}",
                "created_at": created_time,
                "date_time": datetime.fromtimestamp(created_time).strftime("%Y-%m-%d %H:%M:%S")
            })

    alerts.sort(key=lambda alert: alert["created_at"], reverse=True)

    return jsonify(alerts)


@app.route("/api/stats")
def get_stats():
    stats = {
        "total_alerts": 0,
        "restricted": 0,
        "suspicious": 0,
        "theft": 0,
        "fight": 0
    }

    for alert_type, folder in SCREENSHOT_FOLDERS.items():
        folder.mkdir(exist_ok=True)
        count = len(list(folder.glob("*.jpg")))

        stats[alert_type] = count
        stats["total_alerts"] += count

    return jsonify(stats)


@app.route("/api/screenshots/<alert_type>/<filename>")
def get_screenshot(alert_type, filename):
    if alert_type not in SCREENSHOT_FOLDERS:
        return jsonify({"error": "Invalid alert type"}), 400

    folder = SCREENSHOT_FOLDERS[alert_type]

    return send_from_directory(folder, filename)


@app.route("/api/register-object", methods=["POST"])
def register_object_api():
    script_file = BASE_DIR / "objectregister.py"

    data = request.get_json(silent=True) or {}
    object_name = data.get("object_name")

    command = [sys.executable, str(script_file)]

    if object_name:
        command.extend(["--name", object_name])

    try:
        subprocess.Popen(command, cwd=str(BASE_DIR))

    except OSError as error:
        return jsonify({
            "status": "error",
            "message": f"Failed to start object registration: {error}"
        }), 500

    return jsonify({
        "status": "started",
        "message": "Object registration started. Check the Python camera window."
    })


def get_latest_frame_path():
    frame_candidates = (
        LATEST_FRAME,
        LIVE_FRAME,
        Path.cwd() / "latest_frame.jpg",
        Path.cwd() / "live_frame.jpg",
    )

    for frame_path in frame_candidates:
        if frame_path.exists():
            return frame_path

    return None


def generate_latest_frames():
    last_modified_time = 0

    while True:
        if not LATEST_FRAME.exists():
            time.sleep(0.1)
            continue

        current_modified_time = LATEST_FRAME.stat().st_mtime

        if current_modified_time == last_modified_time:
            time.sleep(0.03)
            continue

        last_modified_time = current_modified_time

        try:
            with open(LATEST_FRAME, "rb") as file:
                frame_bytes = file.read()

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Cache-Control: no-cache, no-store, must-revalidate\r\n"
                b"Pragma: no-cache\r\n"
                b"Expires: 0\r\n\r\n" + frame_bytes + b"\r\n"
            )

        except PermissionError:
            time.sleep(0.03)
            continue


@app.route("/api/live")
        def live_camera():
         return Response(
             generate_latest_frames(),
             mimetype="multipart/x-mixed-replace; boundary=frame",
             headers={
                 "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        
        )

if __name__ == "__main__":
    app.run(debug=True, port=5000)