"""
Baseline tests — current backend state.
All of these must pass BEFORE any infrastructure changes are made.

Run:  pytest tests/test_01_backend_current.py -v
"""
import httpx
import pytest

from conftest import AGENT_ID, BACKEND_URL, SHORT_TEXT, make_silent_wav


# ─── Health ──────────────────────────────────────────────────────────────────

class TestHealth:
    def test_returns_200(self, backend):
        r = backend.get("/health")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"

    def test_response_is_json(self, backend):
        r = backend.get("/health")
        assert r.headers["content-type"].startswith("application/json")

    def test_status_field_is_ok(self, backend):
        r = backend.get("/health")
        assert r.json()["status"] == "ok"

    def test_agent_id_matches(self, backend):
        r = backend.get("/health")
        assert r.json()["agent_id"] == AGENT_ID, (
            f"Agent ID mismatch: got {r.json().get('agent_id')}"
        )

    def test_cors_header_present(self, backend):
        r = backend.get("/health", headers={"Origin": "http://localhost:8080"})
        assert "access-control-allow-origin" in r.headers, "CORS header missing"


# ─── Agent token ─────────────────────────────────────────────────────────────

class TestAgentToken:
    def test_returns_200(self, backend):
        r = backend.get("/agent/token")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

    def test_response_has_signed_url(self, backend):
        r = backend.get("/agent/token")
        body = r.json()
        assert "signed_url" in body, f"Missing signed_url in: {body}"

    def test_signed_url_is_websocket(self, backend):
        r = backend.get("/agent/token")
        url = r.json()["signed_url"]
        assert url.startswith("wss://"), f"Expected wss:// URL, got: {url}"

    def test_response_has_agent_id(self, backend):
        r = backend.get("/agent/token")
        body = r.json()
        assert "agent_id" in body, f"Missing agent_id in: {body}"
        assert body["agent_id"] == AGENT_ID


# ─── TTS ─────────────────────────────────────────────────────────────────────

class TestTTS:
    def test_returns_200(self, backend):
        r = backend.post("/tts", json={"text": SHORT_TEXT})
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

    def test_content_type_is_audio(self, backend):
        r = backend.post("/tts", json={"text": SHORT_TEXT})
        ct = r.headers.get("content-type", "")
        assert "audio" in ct, f"Expected audio content-type, got: {ct}"

    def test_response_has_body(self, backend):
        r = backend.post("/tts", json={"text": SHORT_TEXT})
        assert len(r.content) > 1000, (
            f"Audio response suspiciously small: {len(r.content)} bytes"
        )

    def test_mp3_magic_bytes(self, backend):
        r = backend.post("/tts", json={"text": SHORT_TEXT})
        # MP3 starts with ID3 tag (ID3) or sync word (0xFF 0xFB / 0xFF 0xF3 / 0xFF 0xF2)
        header = r.content[:3]
        is_id3 = header == b"ID3"
        is_mp3_sync = r.content[0] == 0xFF and (r.content[1] & 0xE0) == 0xE0
        assert is_id3 or is_mp3_sync, (
            f"Response doesn't look like MP3. First bytes: {r.content[:4].hex()}"
        )

    def test_custom_voice_id_accepted(self, backend):
        r = backend.post("/tts", json={
            "text": SHORT_TEXT,
            "voice_id": "EXAVITQu4vr4xnSDxMaL"  # Sarah
        })
        assert r.status_code == 200

    def test_missing_text_returns_error(self, backend):
        r = backend.post("/tts", json={})
        assert r.status_code in (400, 422), (
            f"Expected 400/422 for missing text, got {r.status_code}"
        )


# ─── STT ─────────────────────────────────────────────────────────────────────

class TestSTT:
    def test_returns_200_with_valid_audio(self, backend):
        wav = make_silent_wav()
        r = backend.post(
            "/stt",
            files={"file": ("test.wav", wav, "audio/wav")},
        )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

    def test_response_has_transcript_field(self, backend):
        wav = make_silent_wav()
        r = backend.post(
            "/stt",
            files={"file": ("test.wav", wav, "audio/wav")},
        )
        body = r.json()
        assert "transcript" in body, f"Missing transcript field in: {body}"

    def test_transcript_is_string(self, backend):
        wav = make_silent_wav()
        r = backend.post(
            "/stt",
            files={"file": ("test.wav", wav, "audio/wav")},
        )
        assert isinstance(r.json()["transcript"], str)

    def test_words_field_is_list(self, backend):
        wav = make_silent_wav()
        r = backend.post(
            "/stt",
            files={"file": ("test.wav", wav, "audio/wav")},
        )
        body = r.json()
        assert "words" in body, f"Missing words field in: {body}"
        assert isinstance(body["words"], list)

    def test_tts_output_is_transcribable(self, backend):
        """Round-trip: TTS output can be sent back to STT without error."""
        tts = backend.post("/tts", json={"text": "Testing transcription."})
        assert tts.status_code == 200

        r = backend.post(
            "/stt",
            files={"file": ("audio.mp3", tts.content, "audio/mpeg")},
        )
        assert r.status_code == 200
        body = r.json()
        assert "transcript" in body
        # The transcript should contain something (TTS generated real speech)
        assert len(body["transcript"]) > 0, "Transcript from TTS audio is empty"


# ─── Unknown routes ───────────────────────────────────────────────────────────

class TestUnknownRoutes:
    def test_unknown_route_returns_404(self, backend):
        r = backend.get("/does-not-exist")
        assert r.status_code == 404
