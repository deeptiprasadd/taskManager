import firebase_admin
from firebase_admin import messaging, credentials
from database import get_tokens
import os

# Correct Render secret file path
SERVICE_ACCOUNT_PATH = "/etc/secrets/serviceAccountKey.json"

# Initialize Firebase Admin only once
if not firebase_admin._apps:
    cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
    firebase_admin.initialize_app(cred)

def send_push(title, body):
    tokens = get_tokens()
    if not tokens:
        return {"status": "no_tokens"}

    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        tokens=tokens
    )

    try:
        response = messaging.send_multicast(message)
        return {"success": response.success_count, "failure": response.failure_count}
    except Exception as e:
        return {"error": str(e)}
