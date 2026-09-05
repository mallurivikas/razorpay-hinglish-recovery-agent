import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("RINGG_BASE_URL")
API_KEY = os.getenv("RINGG_API_KEY")
AGENT_ID = os.getenv("AGENT_ID")
WEBHOOK_URL = os.getenv("RINGG_WEBHOOK_URL")

payload = {
    "operation": "edit_event_subscriptions",
    "agent_id": AGENT_ID,
    "event_subscriptions": [
        {
            "event_type": ["all_processing_completed"],
            "callback_url": WEBHOOK_URL,
            "method_type": "POST",
            "headers": {
                "Content-Type": "application/json"
            }
        }
    ]
}

response = requests.patch(
    f"{BASE_URL}/agent/v1",
    headers={
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json"
    },
    json=payload
)

print(response.status_code)
print(response.text)