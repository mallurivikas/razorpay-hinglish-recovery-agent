# make_call.py

## Purpose
This script starts an outbound call in Ringg.

## What it does
- Loads Ringg credentials and IDs from environment variables.
- Prompts for the customer name and phone number.
- Builds an outbound call request payload.
- Sends a POST request to the Ringg outbound calling endpoint.
- Prints the response status and body.

## Required environment variables
- `RINGG_BASE_URL`
- `RINGG_API_KEY`
- `AGENT_ID`
- `FROM_NUMBER_ID`

## Output
Use this script to trigger a manual test call or a one-off outbound recovery call.