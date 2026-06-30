"""
FSI Cockpit — Backend API
Endpoints: /tts, /stt, /agent/token, /health
           /memory/long, /actions, /clients (proxy), /internal/analytics-health
"""

import json
import os
import urllib.error
import urllib.request
from datetime import date, datetime
from typing import Optional

import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

# ─── Config ───────────────────────────────────────────────────────────────────

API_KEY       = os.environ.get("ELEVENLABS_API_KEY", "")
AGENT_ID      = os.environ.get("ELEVENLABS_AGENT_ID", "")
VOICE_ID      = os.environ.get("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
BASE          = "https://api.elevenlabs.io/v1"
POSTGRES_DSN  = os.environ.get("POSTGRES_DSN", "")
ANALYTICS_URL = os.environ.get("ANALYTICS_URL", "http://localhost:8001")


def _jsonable(obj):
    """Recursively convert psycopg2 rows to JSON-serializable dicts."""
    if isinstance(obj, list):
        return [_jsonable(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return obj


def _el_headers() -> dict:
    return {"xi-api-key": API_KEY, "Content-Type": "application/json"}


# ─── Database helpers ─────────────────────────────────────────────────────────

def _get_db():
    if not POSTGRES_DSN:
        return None
    try:
        return psycopg2.connect(POSTGRES_DSN)
    except Exception:
        return None


def _pg_ok() -> bool:
    conn = _get_db()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1")
        conn.close()
        return True
    except Exception:
        return False


def _analytics_ok() -> bool:
    try:
        req = urllib.request.Request(f"{ANALYTICS_URL}/health")
        with urllib.request.urlopen(req, timeout=3) as r:
            data = json.loads(r.read())
            return data.get("status") == "ok"
    except Exception:
        return False


def _log_action(action_type: str, payload: dict, client_id: str = None, session_id: str = None):
    conn = _get_db()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO advisor_actions (session_id, client_id, action_type, payload) VALUES (%s, %s, %s, %s)",
            (session_id, client_id, action_type, json.dumps(payload))
        )
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


# ─── App ─────────────────────────────────────────────────────────────────────

app = FastAPI(title="FSI Cockpit API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status": "ok",
        "agent_id": AGENT_ID,
        "postgres": "ok" if _pg_ok() else "unavailable",
        "analytics": "ok" if _analytics_ok() else "unavailable",
    }


# ─── TTS ─────────────────────────────────────────────────────────────────────

class TTSRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None
    client_id: Optional[str] = None


@app.post("/tts")
def text_to_speech(req: TTSRequest):
    voice = req.voice_id or VOICE_ID
    payload = json.dumps({
        "text": req.text,
        "model_id": "eleven_turbo_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.8},
    }).encode()

    request = urllib.request.Request(
        f"{BASE}/text-to-speech/{voice}",
        data=payload,
        headers={**_el_headers(), "Accept": "audio/mpeg"},
    )
    try:
        response = urllib.request.urlopen(request)
        audio = response.read()
    except urllib.error.HTTPError as e:
        raise HTTPException(status_code=e.code, detail=e.read().decode())

    _log_action("voice_generated", {"text": req.text[:100], "voice_id": voice}, client_id=req.client_id)

    return StreamingResponse(
        iter([audio]),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "inline; filename=message.mp3"},
    )


# ─── STT ─────────────────────────────────────────────────────────────────────

@app.post("/stt")
async def speech_to_text(file: UploadFile):
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


# ─── Agent token ─────────────────────────────────────────────────────────────

@app.get("/agent/token")
def get_agent_token():
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

    signed_url = data.get("signed_url", "")

    # Persist session to postgres
    conn = _get_db()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO agent_sessions (status) VALUES ('active') RETURNING id",
            )
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    return JSONResponse({"signed_url": signed_url, "agent_id": AGENT_ID})


# ─── Long-term memory ─────────────────────────────────────────────────────────

class MemoryIn(BaseModel):
    client_id: str
    category: str
    fact: str
    confidence: float = 1.0


@app.get("/memory/long/{client_id}")
def get_memory(client_id: str):
    conn = _get_db()
    if not conn:
        raise HTTPException(status_code=503, detail="Database unavailable")
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT id, client_id, category, fact, confidence, created_at FROM agent_memory_long "
            "WHERE client_id = %s AND is_active = TRUE ORDER BY created_at DESC",
            (client_id,)
        )
        rows = cur.fetchall()
        return JSONResponse(_jsonable([dict(r) for r in rows]))
    finally:
        conn.close()


@app.post("/memory/long", status_code=201)
def save_memory(body: MemoryIn):
    conn = _get_db()
    if not conn:
        raise HTTPException(status_code=503, detail="Database unavailable")
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO agent_memory_long (client_id, category, fact, confidence) VALUES (%s, %s, %s, %s) RETURNING id",
            (body.client_id, body.category, body.fact, body.confidence)
        )
        row_id = cur.fetchone()[0]
        conn.commit()
        return {"id": row_id, "status": "saved"}
    finally:
        conn.close()


# ─── Advisor actions ──────────────────────────────────────────────────────────

@app.get("/actions")
def list_actions(client_id: Optional[str] = None, limit: int = 50):
    conn = _get_db()
    if not conn:
        raise HTTPException(status_code=503, detail="Database unavailable")
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if client_id:
            cur.execute(
                "SELECT * FROM advisor_actions WHERE client_id = %s ORDER BY created_at DESC LIMIT %s",
                (client_id, limit)
            )
        else:
            cur.execute(
                "SELECT * FROM advisor_actions ORDER BY created_at DESC LIMIT %s",
                (limit,)
            )
        rows = cur.fetchall()
        return JSONResponse(_jsonable([dict(r) for r in rows]))
    finally:
        conn.close()


# ─── Proxy / internal ────────────────────────────────────────────────────────

@app.get("/internal/analytics-health")
def internal_analytics_health():
    ok = _analytics_ok()
    return JSONResponse(
        {"analytics": "ok" if ok else "unavailable"},
        status_code=200 if ok else 503,
    )


@app.get("/clients/{client_id}")
def proxy_client(client_id: str):
    """Proxy to analytics service — keeps frontend talking to a single backend."""
    try:
        req = urllib.request.Request(f"{ANALYTICS_URL}/clients/{client_id}")
        with urllib.request.urlopen(req, timeout=5) as r:
            return JSONResponse(json.loads(r.read()))
    except urllib.error.HTTPError as e:
        raise HTTPException(status_code=e.code, detail=f"Analytics: {e.read().decode()}")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Analytics unreachable: {e}")


@app.get("/clients")
def proxy_clients():
    try:
        req = urllib.request.Request(f"{ANALYTICS_URL}/clients")
        with urllib.request.urlopen(req, timeout=5) as r:
            return JSONResponse(json.loads(r.read()))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Analytics unreachable: {e}")
