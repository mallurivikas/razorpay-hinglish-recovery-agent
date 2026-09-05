import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

INPUT_FILE = "data/completed_calls.json"
OUTPUT_FILE = "data/transcription.json"

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-3.6-flash"


def analyze_call(transcript):
    prompt = f"""
Analyze this payment recovery call.

Return ONLY valid JSON.

IMPORTANT:
- Preserve the complete conversation.
- Include BOTH the AI/agent and customer messages.
- Preserve the original chronological order exactly.
- Do not remove, merge, summarize, or reorder messages.
- For EVERY message, provide the original text, Romanized Hinglish transliteration, and English translation.
- For English text, keep the transliteration unchanged and translate it naturally.
- Transliteration means converting Devanagari Hindi into Roman script without translating the Hindi words.

Example:
"मैं ठीक हूँ" -> "main theek hoon"
NOT: "I am fine"

For the conversation analysis, extract:

1. Primary language
2. Secondary languages
3. Conversation style
4. Payment failure issue
5. Customer's stated reason
6. Whether the customer is willing to retry
7. Retry timeframe
8. Commitment level
9. Evidence supporting the commitment level
10. Recovery outcome
11. Recommended next action
12. Whether follow-up is required
13. Follow-up time
14. Actual customer objections
15. Customer concerns
16. Agent effectiveness
17. Agent promises or commitments
18. Whether those agent promises were actually executed according to the available tool-call information

IMPORTANT ANALYSIS RULES:

- Do NOT classify the payment failure reason itself as an objection.
- An objection is resistance, refusal, distrust, disagreement, or a concern about proceeding with payment.
- Do NOT invent actions, promises, or events that are not supported by the conversation or metadata.
- Do NOT assume that an agent promise was executed merely because the agent said it would happen.
- If the agent promises an action but there is no evidence of execution, mark execution_verified as false.
- Do not invent a payment link, callback, reminder, or other action unless it is explicitly supported.
- Commitment level must be based on the customer's actual words.
- Include evidence for important conclusions.
- Agent effectiveness should be realistic, not automatically 10.
- Identify template placeholders or other obvious agent issues.
- If information is unavailable, use null, an empty string, or an empty array instead of guessing.

Return JSON in exactly this structure:

{{
  "transcript": [
    {{
      "speaker": "ai",
      "original": "",
      "transliteration": "",
      "english_translation": ""
    }},
    {{
      "speaker": "customer",
      "original": "",
      "transliteration": "",
      "english_translation": ""
    }}
  ],
  "language": {{
    "primary": "",
    "secondary": [],
    "style": ""
  }},
  "payment": {{
    "issue": "",
    "customer_stated_reason": ""
  }},
  "customer_intent": {{
    "willing_to_retry": null,
    "retry_time": "",
    "commitment_level": "",
    "commitment_evidence": ""
  }},
  "recovery": {{
    "outcome": "",
    "recommended_action": "",
    "follow_up_required": false,
    "follow_up_time": ""
  }},
  "objections": [],
  "customer_concerns": [],
  "agent_effectiveness": {{
    "score": 0,
    "strengths": [],
    "issues": []
  }},
  "agent_promises": [
    {{
      "promise": "",
      "time": "",
      "execution_verified": false
    }}
  ]
}}

Conversation:
{json.dumps(transcript, ensure_ascii=False)}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json"
        }
    )

    return json.loads(response.text)


def main():
    os.makedirs("data", exist_ok=True)

    if not os.path.exists(INPUT_FILE):
        print(f"Input file not found: {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        calls = json.load(file)

    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as file:
            processed = json.load(file)
    else:
        processed = {}

    for caller_id, caller_calls in calls.items():
        for call_id, call_data in caller_calls.items():

            if call_id in processed:
                print(f"Skipping {call_id}")
                continue

            transcript = call_data.get("transcript", [])

            if not transcript:
                print(f"Skipping {call_id}: no transcript")
                continue

            print(f"Processing {call_id}...")

            try:
                analysis = analyze_call(transcript)

                processed[call_id] = {
                    "call_id": call_id,
                    "gemini_analysis": analysis
                }

                with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
                    json.dump(
                        processed,
                        file,
                        indent=2,
                        ensure_ascii=False
                    )

                print(f"Completed {call_id}")

            except Exception as e:
                print(f"Failed {call_id}: {e}")

    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
