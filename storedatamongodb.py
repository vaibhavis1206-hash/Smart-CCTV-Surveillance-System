from pymongo import MongoClient
import gridfs
from datetime import datetime

MONGO_URL = "mongodb://localhost:27017/"
DATABASE_NAME = "cctv_system"

client = MongoClient(MONGO_URL)
database = client[DATABASE_NAME]
fs = gridfs.GridFS(database)


def store_unknown_person_data(image_path, person_label="UNKNOWN", alert_type="UNKNOWN"):
    with open(image_path, "rb") as image_file:
        file_id = fs.put(
            image_file,
            filename=image_path.name,
            person_label=person_label,
            alert_type=alert_type,
            created_at=datetime.now()
        )

    print(f"Image stored in MongoDB with ID: {file_id}")
    return file_id