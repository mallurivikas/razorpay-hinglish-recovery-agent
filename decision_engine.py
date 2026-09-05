"""
This file is not been included in prototyping but can be used and cofigured while scaling
"""
from datetime import datetime

def decide_action(record) -> dict:
    amount = record["amount"]
    decline_reason = record["decline_reason"]

    if amount < 300:
        return {
            "action": "sms_only",
            "reason": "Payment amount is below ₹300, so no call is required."
        }

    if decline_reason == "otp_failure":
        return {
            "action": "instant_retry_link",
            "reason": "OTP failure is usually a one-off mistake, so send a retry link instead of calling."
        }

    if decline_reason == "insufficient_funds":
        failed_at = datetime.fromisoformat(record["failed_at"])

        if failed_at.hour < 18:
            return {
                "action": "delayed_call",
                "reason": "Insufficient funds occurred before 6 PM, so delay the call until evening due to possible payday timing."
            }

    if decline_reason == "bank_timeout":
        return {
            "action": "instant_retry_link",
            "reason": "Bank timeout may be temporary, so provide an immediate retry link."
        }

    if decline_reason == "risk_block":
        return {
            "action": "escalate_human",
            "reason": "Risk blocks must not be automatically retried; escalate to a human for safety and compliance."
        }

    return {
        "action": "escalate_human",
        "reason": "No automated rule matched this payment, so escalate to a human."
    }


def check_attempts(record) -> dict:
    """
    Final guardrail: no record can receive another automated action
    after 3 or more attempts.
    """

    if record.get("attempts", 0) >= 3:
        record["status"] = "stopped_max_retries"

        return {
            "action": "escalate_human",
            "reason": "Maximum retry limit of 3 attempts has been reached; further automated actions are blocked."
        }

    return decide_action(record)