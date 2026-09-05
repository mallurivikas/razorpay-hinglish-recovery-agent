# dashboard_app.py

## Purpose
This file runs the FastAPI dashboard backend for payment recovery data.

## What it does
- Loads call data from `data/completed_calls.json`.
- Loads Gemini analysis from `data/transcription.json`.
- Merges raw call data with analysis data for dashboard views.
- Builds summary metrics, funnels, breakdowns, customer views, and call detail data.
- Serves the dashboard HTML at `/`.

## Data handling
- Converts timestamps to IST for display.
- Formats durations and empty values for UI use.
- Cleans transcript text by replacing placeholder names and values.

## Output
This module returns dashboard-ready JSON for the frontend and a rendered HTML page from `templates/dashboard.html`.