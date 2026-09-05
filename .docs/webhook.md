# webhook.py

## Purpose
This file receives Ringg webhook events and stores completed call data locally.

## What it does
- Exposes `/webhooks/ringg` as a POST endpoint.
- Reads the incoming JSON payload.
- Accepts only the `all_processing_completed` event type.
- Stores call records in `data/completed_calls.json`.
- Prevents duplicate storage for the same `call_id` under the same caller.

## Notes
- The code loads `RINGG_WEBHOOK_SECRET`, but the current handler does not verify signatures.
- The data file is created automatically if it does not exist.

## Output
The webhook returns a small JSON response that shows whether the event was stored, ignored, or treated as a duplicate.