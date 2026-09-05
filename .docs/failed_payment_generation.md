# failed_payment_generation.py

## Purpose
This script generates synthetic failed payment records for testing.

## What it does
- Creates random customer names and phone numbers.
- Picks a payment amount and failure reason from fixed lists.
- Assigns a random failure timestamp within the last 72 hours.
- Writes the generated data to `data/failed_payments.json`.

## Output
When run as a script, it prints the record count and the failure reason distribution.