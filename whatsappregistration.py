import json
import re
from pathlib import Path

CONFIG_FILE = Path("whatsapp_config.json")


def normalize_indian_number(number):
    digits = re.sub(r"\D", "", number)

    if len(digits) == 10:
        digits = "91" + digits

    if not digits.startswith("91"):
        raise ValueError("Use Indian number with 10 digits or +91 format.")

    if len(digits) != 12:
        raise ValueError("Invalid mobile number.")

    return f"whatsapp:+{digits}"


def register_whatsapp_number():
    mobile_number = input("Enter WhatsApp mobile number: ").strip()
    camera_location = input("Enter camera location: ").strip()

    if not camera_location:
        camera_location = "CCTV Camera 1"

    whatsapp_to = normalize_indian_number(mobile_number)

    config = {
        "whatsapp_to": whatsapp_to,
        "camera_location": camera_location
    }

    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)

    print("WhatsApp number registered successfully.")
    print("To:", whatsapp_to)
    print("Location:", camera_location)

    return config


def load_whatsapp_config():
    if not CONFIG_FILE.exists():
        raise RuntimeError(
            "WhatsApp number not registered. Run register_whatsapp_number() first."
        )

    with open(CONFIG_FILE, "r") as file:
        return json.load(file)