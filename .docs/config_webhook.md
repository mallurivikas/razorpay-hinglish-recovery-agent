# config_webhook.py

## Purpose
This script updates Ringg agent webhook subscriptions through the Ringg API.

## What it does
- Loads API settings from environment variables.
- Builds a subscription payload for the `all_processing_completed` event.
- Sends a PATCH request to the Ringg agent API.
- Prints the HTTP status code and response body.

## Required environment variables
- `RINGG_BASE_URL`
- `RINGG_API_KEY`
- `AGENT_ID`
- `RINGG_WEBHOOK_URL`

## Output
Use this script when the webhook URL or subscription settings need to be registered or changed.