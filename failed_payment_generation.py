"""
This File was used for generating synthetic dsta for testing purposes
"""
import json
import random
from datetime import datetime, timedelta

REASONS = ["insufficient_funds", "otp_failure", "bank_timeout", "risk_block"]
WEIGHTS = [0.40, 0.25, 0.20, 0.15]

FIRST_NAMES = ["Priya", "Rahul", "Ananya", "Vikram", "Sneha", "Arjun", "Kavya",
               "Rohan", "Divya", "Aditya", "Meera", "Karan", "Pooja", "Nikhil"]
LAST_NAMES = ["Sharma", "Verma", "Reddy", "Iyer", "Gupta", "Nair", "Patel", "Singh"]

def fake_phone():
    return "+91"+str(random.randint(70000,99999))+str(random.randint(10000,99999))

def generate_dataset(n=60):
    records = []
    for i in range(1,n+1):
        name=f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        amount=random.choice([199, 499, 799, 1200, 1999, 2499, 3499, 4999])  # in INR
        reason=random.choices(REASONS,weights=WEIGHTS,k=1)[0]
        failed_at=datetime.now()-timedelta(hours=random.randint(1, 72))

        records.append({
            "payment_id":f"sim_{i:04d}",
            "customer_name":name,
            "phone":fake_phone(),
            "amount":amount,
            "currency":"INR",
            "decline_reason":reason,
            "failed_at":failed_at.isoformat(),
            "attempts":0,
            "status":"pending"
        })
    return records

if __name__ == "__main__":
    data = generate_dataset(60)
    with open("data/failed_payments.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"Generated{len(data)}synthetic failed payments -> data/failed_payments.json")

    from collections import Counter
    counts=Counter(r["decline_reason"]for r in data)
    print("Distribution:",dict(counts))