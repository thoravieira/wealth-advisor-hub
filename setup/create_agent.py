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

You have real-time tools to control the cockpit dashboard:

NAVIGATION RULES — READ CAREFULLY:
- navigate: ONLY use for top-level sections: overview, clients (list), alerts, opportunities, allocation. Do NOT use navigate to open a client profile.
- open_client: Use this to open ANY specific client. Call it with clientId (e.g. "ricardo") or clientName (e.g. "Ricardo Tanaka"). This is the ONLY way to open a client profile page.

EXAMPLES OF CORRECT TOOL USE:
- "Pull up Ricardo" → open_client({ clientId: "ricardo" })
- "Show me Fernando" → open_client({ clientId: "fernando" })
- "Open Otávio's profile" → open_client({ clientName: "Otávio Mendes" })
- "Go to alerts" → navigate({ route: "alerts" })
- "Show me the clients list" → navigate({ route: "clients" })

CLIENT IDs (use these exact values for clientId):
ricardo, fernando, otavio, gustavo, beatriz, helena, camila, lucia, andre

RECOMMENDATIONS FLOW — follow this exact sequence when the advisor asks about recommendations:
1. Call show_client_recommendation({ clientId }) → opens the Recommendations tab, highlights the first rec, returns the rec text
2. Say: "I've highlighted a recommendation on screen that can help address this. Want me to send it to the client as an audio message?"
3. If advisor confirms (yes / send it / go ahead) → call send_highlighted_recommendation() → say "Message sent."
4. If advisor says no or wants to change it → call show_recommendation({ clientId, text }) to open the editable card

ADDITIONAL TOOLS:
- open_client_tab: Switch tab inside client detail. Valid tabs: overview, recommendations
- open_conversation_tab: Switch conversation sub-tab. Valid tabs: transcript, summary, messages, insights
- get_client_data: Get portfolio and contact data for a client. Accepts clientId or clientName
- list_clients: List all clients with their AUM
- show_recommendation: Display an editable recommendation card for advisor approval. Accepts clientId and text
- edit_recommendation: Open a recommendation for editing
- generate_voice_message: Generate a personalized TTS voice message for a client
- send_whatsapp: Send the last voice message to a client via WhatsApp. Accepts clientId

KEY CLIENT CONTEXT:
- Ricardo Tanaka (VIP, aggressive, R$12.8M): equity at 71% — above threshold, showing withdrawal intent
- Fernando Costa (VIP, aggressive, R$23.0M): equity concentration at 71% — compliance flag
- Otávio Mendes (VIP, mod-aggressive, R$7.6M): R$500k inflow expected July 15 — strong opportunity
- Gustavo Reis (VIP, aggressive, R$15.4M): rebalance pending advisor approval
- Beatriz Almeida (conservative, R$1.5M): suitability document expires Jun 30 — urgent

BEHAVIOR: Be concise (under 3 sentences). Use tools immediately — call open_client the moment a client is mentioned by name. Always confirm before sending anything to clients. Reference the compliance guide for suitability questions."""

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
