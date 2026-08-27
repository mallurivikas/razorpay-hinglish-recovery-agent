import asyncio
import audioop
import base64
import json
import os
import wave

from dotenv import load_dotenv
from fastapi import FastAPI, Response, WebSocket
from google import genai
from google.genai import types
from twilio.twiml.voice_response import Connect, Stream, VoiceResponse

load_dotenv()

app = FastAPI()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing")

client = genai.Client(api_key=GEMINI_API_KEY)

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-live-preview")
NGROK_HOST = os.getenv("NGROK_HOST", "unstentorian-indigestive-alvin.ngrok-free.dev").replace("https://", "").replace("http://", "").strip("/")

SAMPLE_WIDTH = 2
CHANNELS = 1

TWILIO_RATE = 8000
GEMINI_INPUT_RATE = 16000
GEMINI_OUTPUT_RATE = 24000

OUTBOUND_FRAME_SIZE = 160
FRAME_DURATION_SEC = 0.02
INTERRUPT_RMS_THRESHOLD = int(os.getenv("INTERRUPT_RMS_THRESHOLD", "700"))
MEDIA_LOG_INTERVAL = 50


@app.get("/voice")
@app.post("/voice")
async def voice():
    response = VoiceResponse()
    connect = Connect()
    connect.append(Stream(url=f"wss://{NGROK_HOST}/media"))
    response.append(connect)
    return Response(content=str(response), media_type="application/xml")


def twilio_to_gemini(data: bytes, state):
    pcm_8k = audioop.ulaw2lin(data, SAMPLE_WIDTH)
    pcm_16k, new_state = audioop.ratecv(
        pcm_8k, SAMPLE_WIDTH, CHANNELS, TWILIO_RATE, GEMINI_INPUT_RATE, state
    )
    return pcm_16k, new_state


def gemini_to_twilio(data: bytes, state):
    pcm_8k, new_state = audioop.ratecv(
        data, SAMPLE_WIDTH, CHANNELS, GEMINI_OUTPUT_RATE, TWILIO_RATE, state
    )
    mulaw = audioop.lin2ulaw(pcm_8k, SAMPLE_WIDTH)
    return mulaw, new_state


class OutboundState:
    def __init__(self):
        self.resample_state = None
        self.model_is_speaking = False


async def outbound_pacer(websocket, stream_sid_holder, audio_queue: asyncio.Queue, out_state: OutboundState):
    """Worker task that paces outbound audio frames to Twilio without blocking receiver loops."""
    try:
        while True:
            frame = await audio_queue.get()
            if frame is None:
                audio_queue.task_done()
                break

            stream_sid = stream_sid_holder["sid"]
            if stream_sid and out_state.model_is_speaking:
                payload = base64.b64encode(frame).decode("ascii")
                message = {
                    "event": "media",
                    "streamSid": stream_sid,
                    "media": {"payload": payload}
                }
                await websocket.send_text(json.dumps(message))
                await asyncio.sleep(FRAME_DURATION_SEC)

            audio_queue.task_done()
    except asyncio.CancelledError:
        pass


async def clear_twilio_buffer(websocket, stream_sid: str, audio_queue: asyncio.Queue, out_state: OutboundState):
    """Flushes local queue and tells Twilio to clear its current playback buffer."""
    out_state.model_is_speaking = False
    
    # Empty pending items in queue
    while not audio_queue.empty():
        try:
            audio_queue.get_nowait()
            audio_queue.task_done()
        except asyncio.QueueEmpty:
            break

    if stream_sid:
        clear_msg = json.dumps({"event": "clear", "streamSid": stream_sid})
        await websocket.send_text(clear_msg)
        print("Interruption detected: sent clear event to Twilio")


async def gemini_receiver(session, websocket, stream_sid_holder, out_state: OutboundState, audio_queue: asyncio.Queue):
    print("Gemini receiver started")

    try:
        async for response in session.receive():
            if response.server_content is None:
                if getattr(response, "error", None):
                    print(f"Gemini error: {response.error}")
                else:
                    try:
                        print(f"Non-server-content message: {response.model_dump(exclude_none=True)}")
                    except Exception:
                        print(f"Non-server-content message (raw): {response}")
                continue

            if response.server_content.interrupted:
                print("Gemini turn interrupted by server VAD")
                await clear_twilio_buffer(websocket, stream_sid_holder["sid"], audio_queue, out_state)

            if response.server_content.turn_complete:
                print("Gemini turn complete")
                out_state.model_is_speaking = False

            if response.server_content.input_transcription:
                text = response.server_content.input_transcription.text
                if text:
                    print(f"Customer: {text}")

            if response.server_content.output_transcription:
                text = response.server_content.output_transcription.text
                if text:
                    print(f"Gemini: {text}")

            model_turn = response.server_content.model_turn
            if model_turn is None:
                continue

            for part in model_turn.parts:
                if part.inline_data is None or not isinstance(part.inline_data.data, bytes):
                    continue

                audio = part.inline_data.data
                mulaw, out_state.resample_state = gemini_to_twilio(audio, out_state.resample_state)
                out_state.model_is_speaking = True

                for i in range(0, len(mulaw), OUTBOUND_FRAME_SIZE):
                    frame = mulaw[i:i + OUTBOUND_FRAME_SIZE]
                    if frame:
                        await audio_queue.put(frame)

    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Gemini receiver error: {e}")


@app.websocket("/media")
async def media_stream(websocket: WebSocket):
    await websocket.accept()
    print("Twilio WebSocket connected")

    stream_sid_holder = {"sid": None}
    out_state = OutboundState()
    audio_queue = asyncio.Queue()
    input_resample_state = None
    
    gemini_task = None
    pacer_task = None
    
    media_frame_count = 0
    input_audio_buffer = bytearray()

    try:
        async with client.aio.live.connect(
            model=GEMINI_MODEL,
            config=types.LiveConnectConfig(
                response_modalities=["AUDIO"],
                system_instruction="""
You are a friendly human sales agent.
Have a normal natural conversation with the caller.
Be casual, warm and conversational.
Keep responses short.
Do not sound robotic.
Speak English or Hinglish depending on the caller.
""",
                input_audio_transcription={},
                output_audio_transcription={},
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
                    )
                ),
                realtime_input_config=types.RealtimeInputConfig(
                    automatic_activity_detection=types.AutomaticActivityDetection(
                        disabled=False,
                        start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_HIGH,
                        end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_HIGH,
                        prefix_padding_ms=120,
                        silence_duration_ms=450,
                    )
                ),
            )
        ) as session:

            print("Gemini Live connected")

            while True:
                message = await websocket.receive_text()
                data = json.loads(message)
                event = data.get("event")

                if event == "start":
                    stream_sid_holder["sid"] = data["start"]["streamSid"]
                    print(f"Twilio stream started: {stream_sid_holder['sid']}")

                    pacer_task = asyncio.create_task(
                        outbound_pacer(websocket, stream_sid_holder, audio_queue, out_state)
                    )
                    gemini_task = asyncio.create_task(
                        gemini_receiver(session, websocket, stream_sid_holder, out_state, audio_queue)
                    )

                    await session.send_realtime_input(
                        text="Greet the caller naturally and briefly."
                    )

                elif event == "media":
                    if not stream_sid_holder["sid"]:
                        continue

                    payload = data["media"]["payload"]
                    mulaw = base64.b64decode(payload)

                    pcm_16k, input_resample_state = twilio_to_gemini(mulaw, input_resample_state)
                    rms = audioop.rms(pcm_16k, SAMPLE_WIDTH)

                    # Interruption check: caller speaking while model is returning audio
                    if out_state.model_is_speaking and rms >= INTERRUPT_RMS_THRESHOLD:
                        await clear_twilio_buffer(websocket, stream_sid_holder["sid"], audio_queue, out_state)

                    await session.send_realtime_input(
                        audio=types.Blob(data=pcm_16k, mime_type="audio/pcm;rate=16000")
                    )
                    input_audio_buffer.extend(pcm_16k)

                    media_frame_count += 1
                    if media_frame_count % MEDIA_LOG_INTERVAL == 0:
                        print(f"Received {media_frame_count} frames (rms={rms})")

                elif event == "stop":
                    print(f"Twilio stream stopped (total inbound frames: {media_frame_count})")
                    if input_audio_buffer:
                        debug_path = "debug_input_audio.wav"
                        with wave.open(debug_path, "wb") as wf:
                            wf.setnchannels(CHANNELS)
                            wf.setsampwidth(SAMPLE_WIDTH)
                            wf.setframerate(GEMINI_INPUT_RATE)
                            wf.writeframes(bytes(input_audio_buffer))
                        print(f"Saved audio log to {debug_path}")
                    break

    except Exception as e:
        print(f"WebSocket error: {e}")

    finally:
        if gemini_task:
            gemini_task.cancel()
        if pacer_task:
            pacer_task.cancel()
        print("Call connection closed")