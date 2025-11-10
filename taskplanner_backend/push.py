import firebase_admin
from firebase_admin import messaging, credentials
from database import get_tokens

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

def send_push(title, body):
    tokens = get_tokens()
    if not tokens:
        return

    for token in tokens:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            token=token
        )
        messaging.send(message)
