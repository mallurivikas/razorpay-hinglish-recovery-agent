import os

from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_phone = os.getenv("TWILIO_PHONE_NUMBER")
my_phone = os.getenv("MY_PHONE_NUMBER")

client = Client(account_sid, auth_token)

call = client.calls.create(
    to=my_phone,
    from_=twilio_phone,
    url="https://unstentorian-indigestive-alvin.ngrok-free.dev/voice"
)

print(f"Call initiated: {call.sid}")