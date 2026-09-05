import os
import json
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException

load_dotenv()

app = FastAPI()

WEBHOOK_SECRET = os.getenv("RINGG_WEBHOOK_SECRET")

DATA_DIR = "data"
CALLS_FILE = os.path.join(DATA_DIR, "completed_calls.json")


def load_calls():
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(CALLS_FILE):
        return {}

    with open(CALLS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_calls(calls):
    os.makedirs(DATA_DIR, exist_ok=True)

    with open(CALLS_FILE, "w", encoding="utf-8") as file:
        json.dump(calls, file, indent=2, ensure_ascii=False)


@app.post("/webhooks/ringg")
async def ringg_webhook(request: Request):

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_type = payload.get("event_type")
    call_id = payload.get("call_id")

    if not event_type:
        raise HTTPException(status_code=400, detail="event_type missing")

    if not call_id:
        raise HTTPException(status_code=400, detail="call_id missing")

    if event_type != "all_processing_completed":
        return {
            "received": True,
            "ignored": True,
            "event_type": event_type
        }

    caller_id = payload.get("to_number") or payload.get("from_number") or "unknown"

    calls = load_calls()

    if caller_id not in calls:
        calls[caller_id] = {}

    if call_id in calls[caller_id]:
        return {
            "received": True,
            "stored": False,
            "duplicate": True,
            "call_id": call_id
        }

    calls[caller_id][call_id] = {
        "call_id": call_id,
        "event_type": event_type,
        "received_at": datetime.now(timezone.utc).isoformat(),

        "caller_id": caller_id,
        "to_number": payload.get("to_number"),
        "from_number": payload.get("from_number"),

        "call_sid": payload.get("call_sid"),
        "call_type": payload.get("call_type"),
        "status": payload.get("status"),
        "sub_status": payload.get("sub_status"),

        "call_duration": payload.get("call_duration"),
        "called_on": payload.get("called_on"),
        "created_at": payload.get("created_at"),

        "agent_id": payload.get("agent_id"),
        "agent_name": payload.get("agent_name"),
        "version_id": payload.get("version_id"),
        "version_slug": payload.get("version_slug"),

        "call_cost": payload.get("call_cost"),

        "overall_latency_seconds": payload.get(
            "overall_latency_seconds"
        ),

        "first_utterance_seconds": payload.get(
            "first_utterance_seconds"
        ),

        "custom_args_values": payload.get(
            "custom_args_values"
        ),

        "agent_message_count": payload.get(
            "agent_message_count"
        ),

        "user_message_count": payload.get(
            "user_message_count"
        ),

        "transcript": payload.get(
            "transcript", []
        ),

        "recording_url": payload.get(
            "recording_url"
        ),

        "platform_analysis": payload.get(
            "platform_analysis"
        ),

        "platform_analysis_status": payload.get(
            "platform_analysis_status"
        ),

        "client_analysis": payload.get(
            "client_analysis"
        ),

        "client_analysis_status": payload.get(
            "client_analysis_status"
        ),

        "tool_call_logs": payload.get(
            "tool_call_logs", []
        )
    }

    save_calls(calls)

    return {
        "received": True,
        "stored": True,
        "call_id": call_id
    }