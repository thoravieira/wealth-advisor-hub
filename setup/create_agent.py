"""
Setup script — creates ElevenLabs agent + knowledge base for the FSI Cockpit demo.
Run once before the demo: python setup/create_agent.py
Writes AGENT_ID and KB_ID to .env
"""

import json
import os
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).parent.parent
COMPLIANCE_FILE = Path(__file__).parent / "compliance_guide.txt"
ENV_FILE = ROOT / ".env"

API_KEY = os.environ.get("ELEVENLABS_API_KEY") or input("ElevenLabs API key: ").strip()
BASE = "https://api.elevenlabs.io/v1"


def api(method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        headers={"xi-api-key": API_KEY, "Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path} → {e.code}: {e.read().decode()}") from e


def create_kb() -> str:
    print("→ Creating knowledge base...")
    text = COMPLIANCE_FILE.read_text()
    resp = api("POST", "/convai/knowledge-base/text", {
        "name": "FSI Advisory Compliance Guide v2.1",
        "text": text,
    })
    kb_id = resp["id"]
    print(f"  KB created: {kb_id}")
    return kb_id


def create_agent(kb_id: str) -> str:
    print("→ Creating agent Sofia...")
    system_prompt = """You are Sofia, an AI-powered financial advisor assistant for Thiago da Hora, a senior wealth advisor at Premium Desk. You help Thiago manage his 45-client book, surface risks and opportunities, and assist with client communications.

You have access to tools that let you control the cockpit dashboard in real time:
- navigate: Go to a dashboard section (overview, conversations, alerts, opportunities, allocation)
- show_opportunity: Open a specific client's opportunity panel on screen
- show_recommendation: Display a recommendation card on screen awaiting the advisor's approval
- generate_voice_message: Generate a personalized TTS voice message for a client
- send_whatsapp: Send the last generated voice message to the client via WhatsApp

KEY CLIENT CONTEXT:
- Ricardo Tanaka (VIP, aggressive, R$12.8M): equity at 71% — above threshold, showing withdrawal intent
- Fernando Costa (VIP, aggressive, R$23.0M): equity concentration at 71% — compliance flag
- Otávio Mendes (VIP, mod-aggressive, R$7.6M): R$500k inflow expected July — strong opportunity
- Gustavo Reis (VIP, aggressive, R$15.4M): rebalance pending advisor approval
- Beatriz Almeida (conservative, R$1.5M): suitability document expires Jun 30 — urgent

BEHAVIOR: Be concise (under 3 sentences). Use tools to navigate the cockpit when asked. Always confirm before sending anything to clients. Reference the compliance guide for suitability questions."""

    resp = api("POST", "/convai/agents/create", {
        "name": "Sofia — FSI Advisor Assistant",
        "conversation_config": {
            "agent": {
                "first_message": "Hi Thiago! I reviewed your book this morning. Ricardo Tanaka is showing withdrawal intent with equity at 71% — above his risk threshold. Want me to pull up his profile?",
                "language": "en",
                "prompt": {
                    "prompt": system_prompt,
                    "knowledge_base": [{"type": "file", "id": kb_id, "name": "FSI Advisory Compliance Guide v2.1"}],
                    "llm": "gemini-2.0-flash-001",
                    "temperature": 0.4,
                },
            },
            "tts": {"voice_id": "EXAVITQu4vr4xnSDxMaL"},  # Sarah — mature, confident
        },
    })
    agent_id = resp["agent_id"]
    print(f"  Agent created: {agent_id}")
    return agent_id


def write_env(agent_id: str, kb_id: str) -> None:
    lines = [
        f"ELEVENLABS_API_KEY={API_KEY}",
        f"ELEVENLABS_AGENT_ID={agent_id}",
        f"ELEVENLABS_KB_ID={kb_id}",
        "ELEVENLABS_VOICE_ID=EXAVITQu4vr4xnSDxMaL",
    ]
    ENV_FILE.write_text("\n".join(lines) + "\n")
    print(f"  .env written → {ENV_FILE}")


if __name__ == "__main__":
    print("FSI Cockpit — ElevenLabs setup\n")
    kb_id = create_kb()
    agent_id = create_agent(kb_id)
    write_env(agent_id, kb_id)
    print("\nDone. Run the backend next:\n  cd backend && uvicorn main:app --reload")
