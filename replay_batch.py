import json
from collections import Counter
from decision_engine import check_attempts

INPUT_FILE = "data/failed_payments.json"

def main():
    with open(INPUT_FILE, "r") as f:
        records = json.load(f)

    counts = Counter()

    for record in records:
        decision = check_attempts(record)

        record["action"] = decision["action"]
        record["reason"] = decision["reason"]

        if record["action"] == "escalate_human" and record.get("status") == "stopped_max_retries":
            record["status"] = "stopped_max_retries"
        else:
            record["status"] = record["action"]

        counts[record["action"]] += 1

    with open(INPUT_FILE, "w") as f:
        json.dump(records, f, indent=2)

    print(f"Processed {len(records)} records")
    print(f"instant_retry_link: {counts['instant_retry_link']}")
    print(f"delayed_call: {counts['delayed_call']}")
    print(f"escalate_human: {counts['escalate_human']}")
    print(f"sms_only: {counts['sms_only']}")


if __name__ == "__main__":
    main()