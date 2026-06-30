#!/usr/bin/env python3
"""Generate conversation audio files for SPEC-008.
Usage: python3 scripts/generate_audio.py
Writes MP3s to analytics/audio/
"""

import os, re, sys, time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

def load_key():
    env = (ROOT / ".env").read_text()
    m = re.search(r'ELEVENLABS_API_KEY=(.+)', env)
    if not m:
        raise ValueError("ELEVENLABS_API_KEY not found in .env")
    return m.group(1).strip()

from elevenlabs import ElevenLabs

ADVISOR_VOICE  = "EXAVITQu4vr4xnSDxMaL"  # Sarah — reassuring, professional
RICARDO_VOICE  = "IKne3meq5aSn9XLyUdCD"  # Charlie — male, concerned
OTAVIO_VOICE   = "cjVigY5qzO86Huf0OWal"  # Eric — smooth, business-like

AUDIO_DIR = ROOT / "analytics" / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

RICARDO_SCRIPT = [
    ("advisor", "Ricardo, good morning. Thanks for picking up. Your equity position is at 71% after yesterday's move. I wanted to check how you're feeling about that."),
    ("client",  "Honestly, I'm worried. With the baby arriving in September, this level of risk makes me very uncomfortable."),
    ("advisor", "That makes complete sense. What concerns you most right now — the market drop itself, or your emergency reserve?"),
    ("client",  "The reserve. I only have 4 months covered. With a baby coming I need at least 12."),
    ("advisor", "Got it. My proposal addresses both. We trim equity from 71% to 55%, and use that 16% to build a solid Tesouro Selic reserve — liquid anytime."),
    ("client",  "How much does that mean pulling out of equities?"),
    ("advisor", "About 2 million reais. You'd go from 9M to 7M in stocks. The reserve lands at 770k — your full 12 months, comfortably."),
    ("client",  "That feels much better. How do we execute?"),
    ("advisor", "I'll have a written plan to you by 3pm today. I suggest tranches over two weeks — you approve each move before it goes through."),
    ("client",  "Perfect. Send it over. Thanks as always."),
    ("advisor", "Take care of yourself and the family, Ricardo. Talk soon."),
]

OTAVIO_SCRIPT = [
    ("advisor", "Otávio! Good afternoon. The July inflow is confirmed — 500k, right?"),
    ("client",  "Correct, July 15th. I wanted to talk about where to put it."),
    ("advisor", "Perfect. I've prepared a proposal: 50% equities — Ibovespa ETF plus tech — 30% in a new infrastructure credit fund at CDI plus 3.2%, and 20% multimarket."),
    ("client",  "CDI plus 3.2% on the infra fund — that's very attractive. When does the window close?"),
    ("advisor", "June 30th. Getting in early means the best entry price. You have 80k in cash today if you want to move now."),
    ("client",  "I'd rather wait for the full inflow. Is it worth it with the June 30 deadline?"),
    ("advisor", "Yes — the minimum is 50k, so you're covered. And the window doesn't close until month end. Confirm next week and we're good."),
    ("client",  "Send the written plan and I'll sign off next week. Well structured."),
    ("advisor", "Sending today. Any questions, ping me on WhatsApp. Take care, Otávio."),
    ("client",  "Deal. Thanks!"),
]

SILENCE_MS = 300  # milliseconds of silence between turns (as empty bytes — MP3 concat)


def chunks_to_bytes(generator) -> bytes:
    return b"".join(generator)


def generate_conversation(client: ElevenLabs, script: list, client_voice: str, output: Path):
    parts = []
    for i, (speaker, text) in enumerate(script):
        voice_id = ADVISOR_VOICE if speaker == "advisor" else client_voice
        print(f"  [{i+1}/{len(script)}] {speaker}: {text[:50]}...")
        gen = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
        )
        audio = chunks_to_bytes(gen)
        parts.append(audio)
        time.sleep(0.4)  # rate limit courtesy

    combined = b"".join(parts)
    output.write_bytes(combined)
    size_kb = len(combined) / 1024
    print(f"  → saved {output.name} ({size_kb:.0f} KB)")


def main():
    api_key = load_key()
    client = ElevenLabs(api_key=api_key)

    print("Generating Ricardo conversation (Jun 14)...")
    generate_conversation(client, RICARDO_SCRIPT, RICARDO_VOICE,
                          AUDIO_DIR / "ricardo_20260614.mp3")

    print("\nGenerating Otávio conversation (Jun 9)...")
    generate_conversation(client, OTAVIO_SCRIPT, OTAVIO_VOICE,
                          AUDIO_DIR / "otavio_20260609.mp3")

    print("\nDone! Files in analytics/audio/")
    for f in AUDIO_DIR.glob("*.mp3"):
        print(f"  {f.name}: {f.stat().st_size/1024:.0f} KB")


if __name__ == "__main__":
    main()
