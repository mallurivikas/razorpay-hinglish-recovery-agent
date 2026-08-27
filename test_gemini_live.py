import asyncio
import os
import wave

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL = "gemini-3.1-flash-live-preview"

sentences = [
    "Koi baat nahi, main aapko kal ke liye ek reminder bhej deta hoon.",
    "Aap tension mat lijiye, payment dobara try karne se pehle main aapki details check kar leta hoon.",
    "Agar aap chahein, main abhi aapko payment complete karne mein help kar sakta hoon."
]


async def generate_audio(text, filename):
    audio_data = bytearray()

    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        system_instruction=(
            "You are a friendly Indian customer support agent. "
            "Speak naturally in Hinglish. "
            "Do not sound robotic. "
            "Keep the tone warm, calm and conversational."
        ),
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name="Kore"
                )
            )
        )
    )

    async with client.aio.live.connect(
        model=MODEL,
        config=config
    ) as session:

        await session.send_client_content(
            turns=types.Content(
                role="user",
                parts=[
                    types.Part(text=text)
                ]
            ),
            turn_complete=True
        )

        async for response in session.receive():
            if response.data:
                audio_data.extend(response.data)

    with wave.open(filename, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(24000)
        wav.writeframes(audio_data)

    print(f"Created {filename}")


async def main():
    for i, sentence in enumerate(sentences, 1):
        await generate_audio(
            sentence,
            f"gemini_{i}.wav"
        )


asyncio.run(main())