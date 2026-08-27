from fastapi import FastAPI, Response
from twilio.twiml.voice_response import VoiceResponse
from fastapi import FastAPI, HTTPException, Response
app = FastAPI()

@app.post("/voice")
@app.get("/voice")
async def voice():
    response = VoiceResponse()
    response.say(
        "Namaste, main Meraki Store se bol raha hoon. Aapki kaise madad kar sakta hoon?",
        language="hi-IN"
    )
    return Response(content=str(response), media_type="application/xml")