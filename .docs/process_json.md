# process_json.py

## Purpose
This script reads failed payment records, applies the decision engine, and writes the result back.

## What it does
- Loads records from `data/failed_payments.json`.
- Calls `check_attempts()` for each record.
- Stores the selected action and reason in each record.
- Updates the record status.
- Writes the processed list back to the same file.

## Output
The script prints a short summary of how many records were assigned to each action.