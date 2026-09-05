# decision_engine.py

## Purpose
This file contains the rule-based logic for deciding how to handle a failed payment.

## What it does
- Chooses an action based on payment amount and decline reason.
- Returns simple action labels such as `sms_only`, `instant_retry_link`, `delayed_call`, and `escalate_human`.
- Stops automation after three attempts by marking the record as `stopped_max_retries`.

## Decision rules
- Small amounts under 300 go to SMS only.
- OTP failures and bank timeouts go to an instant retry link.
- Insufficient funds before 6 PM can delay the call.
- Risk blocks and unmatched cases escalate to a human.

## Output
The functions return a dictionary with an action and a reason string.