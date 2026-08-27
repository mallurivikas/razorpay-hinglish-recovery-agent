import os
import time

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv()

client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

sentences = [
    "Koi baat nahi, main aapko kal ke liye ek reminder bhej deta hoon.",
    "Aap tension mat lijiye, payment dobara try karne se pehle main aapki details check kar leta hoon.",
    "Agar aap chahein, main abhi aapko payment complete karne mein help kar sakta hoon."
]

voice_id = os.getenv("ELEVENLABS_VOICE_ID")

for i, text in enumerate(sentences, 1):
    start = time.perf_counter()

    audio = client.text_to_speech.convert(
        voice_id=voice_id,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
        text=text
    )

    audio_data = b"".join(audio)
    elapsed = time.perf_counter() - start

    filename = f"eleven_{i}.mp3"

    with open(filename, "wb") as f:
        f.write(audio_data)

    print(f"Sentence {i}: {elapsed:.2f}s -> {filename}")