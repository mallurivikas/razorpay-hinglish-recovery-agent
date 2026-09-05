import copy
import json
from collections import defaultdict
from datetime import datetime
from datetime import timedelta, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
TEMPLATE_PATH = BASE_DIR / "templates" / "dashboard.html"
COMPLETED_CALLS_PATH = DATA_DIR / "completed_calls.json"
TRANSCRIPTION_PATH = DATA_DIR / "transcription.json"


app = FastAPI(title="Payment Recovery Intelligence")

IST = timezone(timedelta(hours=5, minutes=30))


def load_json_file(path: Path, default):
    if not path.exists():
        return copy.deepcopy(default)

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return copy.deepcopy(default)


def parse_dt(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def to_ist(value: str | None):
    parsed = parse_dt(value)
    if not parsed:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(IST)


def format_display_time(value: str | None):
    parsed = to_ist(value)
    if not parsed:
        return value or "Unknown"
    return parsed.strftime("%d %b %Y, %I:%M %p").lstrip("0")


def format_clock_time(value: str | None):
    parsed = to_ist(value)
    if not parsed:
        return value or "--"
    return parsed.strftime("%I:%M %p").lstrip("0")


def format_duration(seconds):
    if seconds is None:
        return "--"
    if isinstance(seconds, str):
        return seconds
    total = float(seconds)
    if total < 60:
        return f"{int(round(total))} sec"
    minutes = int(total // 60)
    remaining = int(round(total % 60))
    return f"{minutes}m {remaining:02d}s"


def build_transcript_from_raw(raw_transcript):
    transcript = []
    for index, message in enumerate(raw_transcript or []):
        text = message.get("bot") or message.get("user") or ""
        speaker = "ai" if message.get("bot") else "customer"
        timestamp = message.get("timestamp")
        transcript.append(
            {
                "speaker": speaker,
                "original": text,
                "transliteration": text,
                "english_translation": text,
                "timestamp": timestamp,
                "sequence": index,
            }
        )
    return transcript


def clean_transcript_message(text: str, customer_name: str):
    return (
        text.replace("at {Callee Name}", customer_name)
        .replace("at {Merchant Name}", "merchant")
        .replace("₹ at {Amount}", "₹ amount")
        .replace("{Callee Name}", customer_name)
        .replace("{Merchant Name}", "merchant")
        .replace("{Amount}", "amount")
        .replace("  ", " ")
        .strip()
    )


def dash_if_missing(value):
    if value is None:
        return "-"
    if isinstance(value, str) and not value.strip():
        return "-"
    return value


def make_sample_analysis(
    customer_name,
    payment_issue,
    customer_reason,
    retry_time,
    commitment_level,
    outcome,
    recommended_action,
    follow_up_time,
    language_primary="Hinglish",
    language_secondary=None,
    style="Polite and conversational",
    score=7,
    strengths=None,
    issues=None,
    promise=None,
    promise_verified=False,
):
    if language_secondary is None:
        language_secondary = ["Hindi", "English"]
    if strengths is None:
        strengths = [
            "Identified the payment issue quickly",
            "Confirmed a retry window",
            "Closed the conversation cleanly",
        ]
    if issues is None:
        issues = ["Reminder execution was not verified"]

    transcript = [
        {
            "speaker": "ai",
            "original": f"Namaste {customer_name} ji, main Aditi bol rahi hoon. Aapka payment complete nahi ho paya. Do minute baat kar sakte hain?",
            "transliteration": f"Namaste {customer_name} ji, main Aditi bol rahi hoon. Aapka payment complete nahi ho paya. Do minute baat kar sakte hain?",
            "english_translation": f"Hello {customer_name} ji, I am Aditi speaking. Your payment could not be completed. Can we talk for two minutes?",
            "timestamp": "00:03",
        },
        {
            "speaker": "customer",
            "original": customer_reason,
            "transliteration": customer_reason,
            "english_translation": customer_reason,
            "timestamp": "00:10",
        },
        {
            "speaker": "ai",
            "original": "Theek hai. Kya aap abhi retry karenge ya baad mein?",
            "transliteration": "Theek hai. Kya aap abhi retry karenge ya baad mein?",
            "english_translation": "Okay. Will you retry now or later?",
            "timestamp": "00:18",
        },
        {
            "speaker": "customer",
            "original": retry_time,
            "transliteration": retry_time,
            "english_translation": retry_time,
            "timestamp": "00:26",
        },
        {
            "speaker": "ai",
            "original": f"Theek hai, main {retry_time} ke baad reminder bhej dungi.",
            "transliteration": f"Theek hai, main {retry_time} ke baad reminder bhej dungi.",
            "english_translation": f"Okay, I will send a reminder after {retry_time}.",
            "timestamp": "00:35",
        },
    ]

    return {
        "transcript": transcript,
        "language": {
            "primary": language_primary,
            "secondary": language_secondary,
            "style": style,
        },
        "payment": {
            "issue": payment_issue,
            "customer_stated_reason": customer_reason,
        },
        "customer_intent": {
            "willing_to_retry": True,
            "retry_time": retry_time,
            "commitment_level": commitment_level,
            "commitment_evidence": customer_reason,
        },
        "recovery": {
            "outcome": outcome,
            "recommended_action": recommended_action,
            "follow_up_required": True,
            "follow_up_time": follow_up_time,
        },
        "objections": [],
        "customer_concerns": [customer_reason],
        "agent_effectiveness": {
            "score": score,
            "strengths": strengths,
            "issues": issues,
        },
        "agent_promises": [
            {
                "promise": promise or f"Send a payment reminder after {retry_time}",
                "time": retry_time,
                "execution_verified": promise_verified,
            }
        ],
    }


def build_raw_stub(call_id, phone, customer_name, account_id, created_at, called_on, call_status, call_type, agent_name, version_id, version_slug, call_cost, duration_seconds, recording_url=None):
    return {
        "call_id": call_id,
        "event_type": "all_processing_completed",
        "received_at": created_at,
        "caller_id": phone,
        "to_number": phone,
        "from_number": "+18154354644",
        "call_sid": f"CA-{call_id[:20]}",
        "call_type": call_type,
        "status": call_status.lower(),
        "sub_status": "ACCEPTED" if call_status == "Completed" else "QUEUED",
        "call_duration": duration_seconds,
        "called_on": called_on,
        "created_at": created_at,
        "agent_id": "d011c8f4-2f61-4d5f-8872-a839d5f822c7",
        "agent_name": agent_name,
        "version_id": version_id,
        "version_slug": version_slug,
        "call_cost": call_cost,
        "overall_latency_seconds": 1.2,
        "first_utterance_seconds": 1.0,
        "custom_args_values": {
            "account_id": account_id,
            "callee_name": customer_name,
            "mobile_number": phone,
        },
        "agent_message_count": 6,
        "user_message_count": 8,
        "transcript": [],
        "recording_url": recording_url,
        "platform_analysis": None,
        "platform_analysis_status": "sample",
        "client_analysis": None,
        "client_analysis_status": "sample",
        "tool_call_logs": [],
    }


def merge_call(raw_call, analysis, sentiment=None, is_demo=False):
    custom_args = raw_call.get("custom_args_values") or {}
    customer_name = (custom_args.get("callee_name") or "Unknown").strip()
    if customer_name != "Unknown":
        customer_name = customer_name.title()
    phone = dash_if_missing(raw_call.get("to_number") or raw_call.get("caller_id"))
    account_id = dash_if_missing(custom_args.get("account_id"))
    call_time = raw_call.get("called_on") or raw_call.get("created_at") or raw_call.get("received_at")
    call_id = dash_if_missing(raw_call.get("call_id"))

    merged = {
        "call_id": call_id,
        "customer_name": customer_name,
        "phone": phone,
        "account_id": account_id,
        "agent_name": dash_if_missing(raw_call.get("agent_name")),
        "agent_id": dash_if_missing(raw_call.get("agent_id")),
        "agent_version": dash_if_missing(raw_call.get("version_slug")),
        "version_id": dash_if_missing(raw_call.get("version_id")),
        "call_direction": dash_if_missing(raw_call.get("call_type")),
        "call_status": dash_if_missing((raw_call.get("status") or "").capitalize()) if raw_call.get("status") else "-",
        "duration": format_duration(raw_call.get("call_duration")),
        "duration_seconds": raw_call.get("call_duration"),
        "date_time": format_display_time(call_time) if call_time else "-",
        "created_at": raw_call.get("created_at"),
        "called_on": raw_call.get("called_on"),
        "call_cost": raw_call.get("call_cost"),
        "overall_latency_seconds": raw_call.get("overall_latency_seconds"),
        "first_utterance_seconds": raw_call.get("first_utterance_seconds"),
        "agent_message_count": raw_call.get("agent_message_count"),
        "customer_message_count": raw_call.get("user_message_count"),
        "recording_url": raw_call.get("recording_url"),
        "raw_call": raw_call,
        "analysis": analysis,
        "is_demo": is_demo,
        "payment_issue": dash_if_missing(analysis.get("payment", {}).get("issue") if analysis else None),
        "customer_intent": analysis.get("customer_intent", {}) if analysis else {},
        "recovery": analysis.get("recovery", {}) if analysis else {},
        "language": analysis.get("language", {}) if analysis else {},
        "agent_evaluation": analysis.get("agent_effectiveness", {}) if analysis else {},
        "agent_promises": analysis.get("agent_promises", []) if analysis else [],
        "customer_concerns": analysis.get("customer_concerns", []) if analysis else [],
        "objections": analysis.get("objections", []) if analysis else [],
        "transcript": analysis.get("transcript") if analysis else build_transcript_from_raw(raw_call.get("transcript", [])),
        "sentiment": dash_if_missing(sentiment),
    }

    if not merged["transcript"]:
        merged["transcript"] = build_transcript_from_raw(raw_call.get("transcript", []))

    if analysis and merged["transcript"]:
        raw_transcript = raw_call.get("transcript", [])
        for index, message in enumerate(merged["transcript"]):
            if index < len(raw_transcript):
                message["timestamp"] = format_clock_time(raw_transcript[index].get("timestamp"))
            message["original"] = clean_transcript_message(message.get("original", ""), customer_name)
            message["transliteration"] = clean_transcript_message(message.get("transliteration", ""), customer_name)
            message["english_translation"] = clean_transcript_message(message.get("english_translation", ""), customer_name)

    merged["technical_metadata"] = {
        "Call ID": dash_if_missing(raw_call.get("call_id")),
        "Agent ID": dash_if_missing(raw_call.get("agent_id")),
        "Agent Version": dash_if_missing(raw_call.get("version_slug")),
        "Call Direction": dash_if_missing(raw_call.get("call_type")),
        "Call Status": dash_if_missing(raw_call.get("status")),
        "Duration": format_duration(raw_call.get("call_duration")),
        "Call Cost": f"₹{raw_call.get('call_cost'):.2f}" if raw_call.get("call_cost") is not None else "-",
        "Overall Latency": f"{raw_call.get('overall_latency_seconds')} sec" if raw_call.get("overall_latency_seconds") is not None else "-",
        "First Utterance Latency": f"{raw_call.get('first_utterance_seconds')} sec" if raw_call.get("first_utterance_seconds") is not None else "-",
        "Agent Message Count": raw_call.get("agent_message_count") if raw_call.get("agent_message_count") is not None else "-",
        "Customer Message Count": raw_call.get("user_message_count") if raw_call.get("user_message_count") is not None else "-",
        "Creation Time": format_display_time(raw_call.get("created_at")) if raw_call.get("created_at") else "-",
        "Call Time": format_display_time(raw_call.get("called_on")) if raw_call.get("called_on") else "-",
    }

    return merged


def load_actual_calls():
    calls_blob = load_json_file(COMPLETED_CALLS_PATH, {})
    analyses_blob = load_json_file(TRANSCRIPTION_PATH, {})

    calls = []

    for caller_calls in calls_blob.values():
        for raw_call in caller_calls.values():
            call_id = raw_call.get("call_id")
            analysis_entry = analyses_blob.get(call_id, {})
            analysis = analysis_entry.get("gemini_analysis") if isinstance(analysis_entry, dict) else None
            calls.append(
                merge_call(
                    raw_call,
                    analysis,
                    sentiment=(raw_call.get("platform_analysis") or {}).get("sentiment") if isinstance(raw_call.get("platform_analysis"), dict) else None,
                    is_demo=False,
                )
            )

    return calls


def build_customers(calls):
    groups = defaultdict(list)
    for call in calls:
        groups[(call["customer_name"], call["phone"])].append(call)

    rows = []
    for (customer_name, phone), items in groups.items():
        sorted_items = sorted(
            items,
            key=lambda item: to_ist(item.get("called_on") or item.get("created_at") or item.get("received_at")) or datetime.min.replace(tzinfo=IST),
        )
        latest = sorted_items[-1]
        rows.append(
            {
                "customer_name": customer_name,
                "phone": phone,
                "total_failed_payments": len(items),
                "calls": len(items),
                "last_call": latest.get("date_time"),
                "latest_payment_issue": dash_if_missing(latest.get("payment_issue")),
                "recovery_status": dash_if_missing(latest.get("recovery", {}).get("outcome")),
                "last_known_intent": dash_if_missing(latest.get("customer_intent", {}).get("commitment_level")),
                "last_known_retry": dash_if_missing(latest.get("customer_intent", {}).get("retry_time")),
            }
        )

    rows.sort(key=lambda row: row["last_call"] or "", reverse=True)
    return rows


def build_overview_metrics(calls):
    operational_calls = [call for call in calls if call.get("analysis")]
    calls_initiated = len(calls)
    customers_reached = sum(1 for call in operational_calls if call.get("transcript"))
    failed_payments = sum(1 for call in operational_calls if call.get("payment_issue") != "-")
    retry_commitments = sum(
        1
        for call in operational_calls
        if call.get("customer_intent", {}).get("willing_to_retry")
        or dash_if_missing(call.get("customer_intent", {}).get("commitment_level")) != "-"
    )
    payments_recovered = sum(
        1
        for call in operational_calls
        if call.get("recovery", {}).get("outcome") == "Payment Recovered"
    )
    commitment_rate = (retry_commitments / customers_reached * 100) if customers_reached else None
    return {
        "failed_payments": failed_payments if failed_payments else "-",
        "calls_initiated": calls_initiated if calls_initiated else "-",
        "customers_reached": customers_reached if customers_reached else "-",
        "recovery_commitment_rate": round(commitment_rate, 1) if commitment_rate is not None else "-",
        "payments_recovered": payments_recovered if payments_recovered else "-",
        "estimated_recovered_amount": "-",
        "comparison": {
            "failed_payments": "-",
            "calls_initiated": "-",
            "customers_reached": "-",
            "recovery_commitment_rate": "-",
            "payments_recovered": "-",
            "estimated_recovered_amount": "-",
        },
    }


def build_overview_funnel(calls):
    operational_calls = [call for call in calls if call.get("analysis")]
    failed_payment = len(operational_calls)
    call_initiated = len(calls)
    customer_reached = sum(1 for call in operational_calls if call.get("transcript"))
    retry_commitment = sum(
        1
        for call in operational_calls
        if call.get("customer_intent", {}).get("willing_to_retry")
        or dash_if_missing(call.get("customer_intent", {}).get("commitment_level")) != "-"
    )
    payment_recovered = sum(
        1
        for call in operational_calls
        if call.get("recovery", {}).get("outcome") == "Payment Recovered"
    )

    steps = [
        ("Failed Payment", failed_payment, 100 if failed_payment else None),
        ("Call Initiated", call_initiated, (call_initiated / failed_payment * 100) if failed_payment else None),
        ("Customer Reached", customer_reached, (customer_reached / call_initiated * 100) if call_initiated else None),
        ("Retry Commitment", retry_commitment, (retry_commitment / customer_reached * 100) if customer_reached else None),
        ("Payment Recovered", payment_recovered, (payment_recovered / retry_commitment * 100) if retry_commitment else None),
    ]
    return [
        {"label": label, "count": count if count else "-", "pct": round(pct, 1) if pct is not None else "-"}
        for label, count, pct in steps
    ]


def build_breakdown_series(calls):
    operational_calls = [call for call in calls if call.get("analysis")]

    def count_by(key_path):
        counts = defaultdict(int)
        for call in operational_calls:
            value = call
            for key in key_path:
                if not isinstance(value, dict):
                    value = None
                    break
                value = value.get(key)
            value = dash_if_missing(value)
            if value != "-":
                counts[value] += 1
        return [{"label": label, "value": count} for label, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]

    failure_reasons = count_by(["payment_issue"])
    recovery_outcomes = count_by(["recovery", "outcome"])
    language_breakdown = count_by(["language", "primary"])
    sentiment_breakdown = count_by(["sentiment"])
    time_of_day_counts = defaultdict(int)
    for call in operational_calls:
        called_on = call.get("called_on") or call.get("created_at")
        parsed = to_ist(called_on)
        if parsed:
            label = parsed.strftime("%H:00")
            time_of_day_counts[label] += 1
    time_of_day = [{"label": label, "value": count} for label, count in sorted(time_of_day_counts.items())]

    volume_over_time_counts = defaultdict(int)
    commitment_over_time_counts = defaultdict(int)
    for call in operational_calls:
        parsed = to_ist(call.get("called_on") or call.get("created_at"))
        if not parsed:
            continue
        label = parsed.strftime("%d %b")
        volume_over_time_counts[label] += 1
        if call.get("customer_intent", {}).get("willing_to_retry"):
            commitment_over_time_counts[label] += 1

    volume_over_time = [{"label": label, "value": count} for label, count in sorted(volume_over_time_counts.items())]
    commitment_over_time = [{"label": label, "value": count} for label, count in sorted(commitment_over_time_counts.items())]

    contact_rate = (len(operational_calls) / len(calls) * 100) if calls else None
    retry_commitment_rate = (
        sum(1 for call in operational_calls if call.get("customer_intent", {}).get("willing_to_retry"))
        / len(operational_calls) * 100
        if operational_calls
        else None
    )
    payment_recovery_rate = (
        sum(1 for call in operational_calls if call.get("recovery", {}).get("outcome") == "Payment Recovered")
        / len(operational_calls) * 100
        if operational_calls
        else None
    )
    avg_duration = None
    durations = [call.get("duration_seconds") for call in operational_calls if call.get("duration_seconds") is not None]
    if durations:
        avg_duration = sum(float(duration) for duration in durations) / len(durations)
    avg_effectiveness = None
    scores = [call.get("agent_evaluation", {}).get("score") for call in operational_calls if call.get("agent_evaluation", {}).get("score") is not None]
    if scores:
        avg_effectiveness = sum(float(score) for score in scores) / len(scores)

    return {
        "failure_reasons": failure_reasons or [],
        "recovery_outcomes": recovery_outcomes or [],
        "analytics": {
            "recovery_rate": round((sum(1 for call in operational_calls if call.get("recovery", {}).get("outcome") == "Payment Recovered") / len(operational_calls) * 100), 1) if operational_calls else "-",
            "contact_rate": round(contact_rate, 1) if contact_rate is not None else "-",
            "retry_commitment_rate": round(retry_commitment_rate, 1) if retry_commitment_rate is not None else "-",
            "payment_recovery_rate": round(payment_recovery_rate, 1) if payment_recovery_rate is not None else "-",
            "average_time_to_retry": "-",
            "average_call_duration": format_duration(avg_duration) if avg_duration is not None else "-",
            "average_agent_effectiveness": f"{avg_effectiveness:.1f} / 10" if avg_effectiveness is not None else "-",
            "human_escalation_rate": round((sum(1 for call in operational_calls if call.get("recovery", {}).get("outcome") == "Human Escalation") / len(operational_calls) * 100), 1) if operational_calls else "-",
        },
        "language_breakdown": language_breakdown or [],
        "sentiment_breakdown": sentiment_breakdown or [],
        "time_of_day": time_of_day or [],
        "volume_over_time": volume_over_time or [],
        "commitment_over_time": commitment_over_time or [],
    }


def build_recovery_calls(calls):
    rows = []
    for call in calls:
        rows.append(
            {
                "call_id": call["call_id"],
                "customer_name": call["customer_name"],
                "phone": call["phone"],
                "payment_issue": call["payment_issue"],
                "call_status": call["call_status"],
                "duration": call["duration"],
                "sentiment": call["sentiment"],
                "commitment": dash_if_missing(call.get("customer_intent", {}).get("commitment_level")),
                "retry_time": dash_if_missing(call.get("customer_intent", {}).get("retry_time")),
                "outcome": dash_if_missing(call.get("recovery", {}).get("outcome")),
                "timestamp": call["date_time"],
                "language": dash_if_missing(call.get("language", {}).get("primary")),
            }
        )
    return rows


def build_bootstrap():
    calls = load_actual_calls()
    operational_calls = [call for call in calls if call.get("analysis") or call.get("transcript")]
    selected = next((call for call in operational_calls if call.get("analysis")), operational_calls[0] if operational_calls else None)
    analytics = build_breakdown_series(operational_calls)
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "sample_data": False,
        "overview": {
            "title": "Payment Recovery",
            "subtitle": "Monitor payment recovery performance, AI calls, customer intent, and outcomes.",
            "date_range": "Last 30 days",
            "metrics": build_overview_metrics(operational_calls),
            "funnel": build_overview_funnel(operational_calls),
            "failure_reasons": analytics["failure_reasons"],
            "recovery_outcomes": analytics["recovery_outcomes"],
            "recent_calls": build_recovery_calls(operational_calls)[:6],
        },
        "recovery_calls": {
            "title": "Recovery Calls",
            "subtitle": "Monitor all AI recovery calls and understand their outcomes.",
            "summary": {
                "total_calls": len(operational_calls) if operational_calls else "-",
                "completed": len([call for call in operational_calls if call.get("call_status") == "Completed"]) if operational_calls else "-",
                "customers_reached": len([call for call in operational_calls if call.get("analysis") and call.get("transcript")]) if operational_calls else "-",
                "average_duration": analytics["analytics"]["average_call_duration"],
                "recovery_commitment": analytics["analytics"]["retry_commitment_rate"],
            },
            "filters": {
                "call_status": ["All", "Completed", "Pending", "Escalated"],
                "payment_issue": ["All", "Insufficient Funds", "OTP Failure", "Bank Timeout", "Risk Block", "Technical Failure", "Other"],
                "outcome": ["All", "Committed to Retry", "Payment Recovered", "Reminder Required", "Customer Refused", "Human Escalation", "Unclear"],
                "language": ["All", "Hindi", "Hinglish", "English", "Hindi + English"],
            },
            "calls": build_recovery_calls(operational_calls),
        },
        "customers": {
            "title": "Customers",
            "subtitle": "Monitor customer recovery history and payment recovery status.",
            "rows": build_customers(operational_calls),
        },
        "analytics": analytics["analytics"] | {
            "failure_reasons": analytics["failure_reasons"],
            "language_breakdown": analytics["language_breakdown"],
            "sentiment_breakdown": analytics["sentiment_breakdown"],
            "time_of_day": analytics["time_of_day"],
            "volume_over_time": analytics["volume_over_time"],
            "commitment_over_time": analytics["commitment_over_time"],
        },
        "call_detail": selected,
        "calls": operational_calls,
    }


@app.get("/", response_class=HTMLResponse)
def dashboard_page():
    return HTMLResponse(TEMPLATE_PATH.read_text(encoding="utf-8"))


@app.get("/api/bootstrap")
def bootstrap_api():
    return JSONResponse(build_bootstrap())


@app.get("/api/calls/{call_id}")
def call_detail_api(call_id: str):
    data = build_bootstrap()
    for call in data["calls"]:
        if call["call_id"] == call_id:
            return JSONResponse(call)
    return JSONResponse({"detail": "Call not found"}, status_code=404)
