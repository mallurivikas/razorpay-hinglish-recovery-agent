# Razorpay Recovery Agent

This project implements an AI-powered payment recovery workflow for failed Razorpay payments. It uses Ringg AI for outbound recovery calls, FastAPI for webhook handling, Gemini for post-call analysis, and a dashboard for monitoring recovery activity.

## Main Parts

- `webhook.py` — Receives completed Ringg AI call events and stores the raw call data.
- `decision_engine.py` — Contains the payment recovery decision rules. (Used for testing)
- `failed_payment_generation.py` — Generates sample failed payment records. (Used for testing)
- `make_call.py` — Initiates an outbound Ringg AI recovery call.
- `config_webhook.py` — Configures Ringg AI webhook event subscriptions.
- `process_json.py` — Sends completed call transcripts to Gemini for post-call analysis and stores the processed results.
- `dashboard_app.py` — Serves the recovery dashboard and provides API data for the dashboard.
- `test_razorpay.py` — Tests Razorpay payment-link creation. (Used for testing)

## Project Data

- `data/completed_calls.json` — Stores raw completed Ringg AI call and webhook data.
- `data/transcription.json` — Stores Gemini-generated post-call analysis.
- `data/failed_payments.json` — Stores sample failed-payment records and recovery decisions. (Used for testing)

## Current Workflow

Razorpay failed payment
→ Recovery decision
→ Ringg AI outbound call
→ Customer conversation
→ Ringg completion webhook
→ `webhook.py`
→ `completed_calls.json`
→ `process_transcription.py`
→ Gemini
→ `transcription.json`
→ Dashboard

## Setup

1. Create a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Add the required environment variables to `.env`.
4. Configure the Ringg AI agent and caller number.
5. Configure the Ringg webhook callback URL.
6. Start the FastAPI application.
7. Run `process_transcription.py` to process completed calls with Gemini.

## Environment Variables

### Ringg AI

- `RINGG_BASE_URL`
- `RINGG_API_KEY`
- `AGENT_ID`
- `FROM_NUMBER_ID`
- `RINGG_WEBHOOK_URL`
- `RINGG_WEBHOOK_SECRET`

### Gemini

- `GEMINI_API_KEY`
- `GEMINI_MODEL`

### Razorpay

- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`

## Notes

- Ringg AI handles the live outbound voice conversation and telephony.
- Gemini is used only for post-call transcript processing and recovery intelligence.
- The application stores data locally using JSON files.
- The Ringg completion webhook requires a publicly accessible FastAPI endpoint, typically exposed using Ngrok during development.
- The old direct Twilio → FastAPI → Gemini Live audio-streaming flow is no longer part of the current architecture.
- `decision_engine.py`, `failed_payment_generation.py`, `process_json.py`, and `test_razorpay.py` are primarily testing/support utilities and are not part of the core live recovery flow.