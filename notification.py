from datetime import datetime
from twilio.rest import Client

from whatsappregistration import load_whatsapp_config

TWILIO_ACCOUNT_SID = "YOUR_ACCOUNT_SID"
TWILIO_AUTH_TOKEN = "YOUR_AUTH_TOKEN"
TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def send_whatsapp_alert(alert_type, image_path=None, image_url=None):
    config = load_whatsapp_config()

    whatsapp_to = config["whatsapp_to"]
    camera_location = config["camera_location"]

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    message_text = (
        f"AI CCTV ALERT\n"
        f"Alert: {alert_type}\n"
        f"Location: {camera_location}\n"
        f"Date & Time: {current_time}"
    )

    if image_path is not None:
        message_text += f"\nImage saved locally: {image_path}"

    if image_url:
        message = client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            to=whatsapp_to,
            body=message_text,
            media_url=[image_url]
        )
    else:
        message = client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            to=whatsapp_to,
            body=message_text
        )

    print(f"WhatsApp alert sent: {message.sid}")
    return message.sid