import os
import razorpay
from dotenv import load_dotenv

load_dotenv()

key_id = os.getenv("RAZORPAY_KEY_ID")
key_secret = os.getenv("RAZORPAY_KEY_SECRET")

client = razorpay.Client(auth=(key_id, key_secret))

payment_link = client.payment_link.create({
    "amount": 500,
    "currency": "INR",
    "description": "Test Razorpay Payment"
})

print("Payment Link Created Successfully!")
print(payment_link)
print("Payment URL:", payment_link["short_url"])