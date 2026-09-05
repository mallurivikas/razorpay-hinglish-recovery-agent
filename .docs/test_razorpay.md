# test_razorpay.py

## Purpose
This script checks Razorpay credentials by creating a test payment link.

## What it does
- Loads Razorpay API keys from environment variables.
- Creates a Razorpay client.
- Sends a request to create a payment link for a test amount.
- Prints the created link and the short payment URL.

## Required environment variables
- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`

## Output
Use this script to verify that the Razorpay account credentials work before running payment workflows.