"""
FSI Cockpit — Backend
3 endpoints: /tts, /stt, /agent/token
Run: uvicorn main:app --reload --port 8000
"""

import os
import json
import urllib.request
import urllib.error
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI(title="FSI Cockpit API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY   = os.environ.get("ELEVENLABS_API_KEY", "")
AGENT_ID  = os.environ.get("ELEVENLABS_AGENT_ID", "")
VOICE_ID  = os.environ.get("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
BASE      = "https://api.elevenlabs.io/v1"


def _headers() -> dict:
    return {"xi-api-key": API_KEY, "Content-Type": "application/json"}


# ── TTS ───────────────────────────────────────────────────────────────────────

class TTSRequest(BaseModel):
    text: str
    voice_id: str | None = None

@app.post("/tts")
def text_to_speech(req: TTSRequest):
    """Convert text to MP3 audio using ElevenLabs TTS."""
    voice = req.voice_id or VOICE_ID
    payload = json.dumps({
        "text": req.text,
        "model_id": "eleven_turbo_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.8},
    }).encode()

    request = urllib.request.Request(
        f"{BASE}/text-to-speech/{voice}",
        data=payload,
        headers={**_headers(), "Accept": "audio/mpeg"},
    )
    try:
        response = urllib.request.urlopen(request)
        audio = response.read()
    except urllib.error.HTTPError as e:
        raise HTTPException(status_code=e.code, detail=e.read().decode())

    return StreamingResponse(
        iter([audio]),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "inline; filename=message.mp3"},
    )


# ── STT ───────────────────────────────────────────────────────────────────────

@app.post("/stt")
async def speech_to_text(file: UploadFile):
    """Transcribe an audio file using ElevenLabs STT (Scribe v2)."""
    audio_bytes = await file.read()

    boundary = b"----FormBoundary"
    body = (
        b"--" + boundary + b"\r\n"
        b'Content-Disposition: form-data; name="model_id"\r\n\r\n'
        b"scribe_v2\r\n"
        b"--" + boundary + b"\r\n"
        + f'Content-Disposition: form-data; name="file"; filename="{file.filename}"\r\n'.encode()
        + f"Content-Type: {file.content_type or 'audio/mpeg'}\r\n\r\n".encode()
        + audio_bytes + b"\r\n"
        b"--" + boundary + b"--\r\n"
    )

    request = urllib.request.Request(
        f"{BASE}/speech-to-text",
        data=body,
        headers={
            "xi-api-key": API_KEY,
            "Content-Type": f"multipart/form-data; boundary={boundary.decode()}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as r:
            result = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise HTTPException(status_code=e.code, detail=e.read().decode())

    return JSONResponse({"transcript": result.get("text", ""), "words": result.get("words", [])})


# ── AGENT TOKEN ───────────────────────────────────────────────────────────────

@app.get("/agent/token")
def get_agent_token():
    """Return a signed conversation URL so the frontend never exposes the API key."""
    if not AGENT_ID:
        raise HTTPException(status_code=500, detail="ELEVENLABS_AGENT_ID not set")

    request = urllib.request.Request(
        f"{BASE}/convai/conversation/get_signed_url?agent_id={AGENT_ID}",
        headers={"xi-api-key": API_KEY},
    )
    try:
        with urllib.request.urlopen(request) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise HTTPException(status_code=e.code, detail=e.read().decode())

    return JSONResponse({"signed_url": data.get("signed_url"), "agent_id": AGENT_ID})


@app.get("/health")
def health():
    return {"status": "ok", "agent_id": AGENT_ID}
