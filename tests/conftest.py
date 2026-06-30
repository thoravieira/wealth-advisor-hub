"""
Shared fixtures and constants for all test suites.
"""
import io
import struct
import wave

import httpx
import pytest

BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:8080"
ANALYTICS_URL = "http://localhost:8001"
POSTGRES_DSN = "postgresql://cockpit:cockpit@localhost:5432/cockpit"

AGENT_ID = "agent_7501kwap3zrre9wr5h20vdqbtz7n"

SHORT_TEXT = "Hello, this is a test of the text to speech system."


def make_silent_wav(duration_seconds: float = 0.5, sample_rate: int = 16000) -> bytes:
    """Generate a minimal valid WAV file with silence — used for STT tests."""
    num_samples = int(sample_rate * duration_seconds)
    buf = io.BytesIO()
    with wave.open(buf, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * num_samples)
    return buf.getvalue()


@pytest.fixture(scope="session")
def backend():
    return httpx.Client(base_url=BACKEND_URL, timeout=30)


@pytest.fixture(scope="session")
def frontend():
    return httpx.Client(base_url=FRONTEND_URL, timeout=10, follow_redirects=True)


@pytest.fixture(scope="session")
def analytics():
    return httpx.Client(base_url=ANALYTICS_URL, timeout=10)
