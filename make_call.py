import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("RINGG_BASE_URL")
API_KEY = os.getenv("RINGG_API_KEY")
AGENT_ID = os.getenv("AGENT_ID")
FROM_NUMBER_ID = os.getenv("FROM_NUMBER_ID")

customer_name = input("Customer name: ")
customer_number = input("Customer phone number (+91...): ").strip()

payload = {
    "name": customer_name,
    "mobile_number": customer_number,
    "agent_id": AGENT_ID,
    "from_number_id": FROM_NUMBER_ID,
    "custom_args_values": {
        "callee_name": customer_name,
        "account_id": "ACC-42"
    },
    "call_config": {
        "call_time": {
            "call_start_time": "09:00",
            "call_end_time": "20:00",
            "timezone": "Asia/Kolkata"
        },
        "call_retry_config": {
            "retry_count": 1,
            "retry_busy": 30,
            "retry_not_picked": 30,
            "retry_failed": 30
        }
    }
}

response = requests.post(
    f"{BASE_URL}/calling/outbound/individual",
    headers={
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json"
    },
    json=payload
)

print(response.status_code)
print(response.text)