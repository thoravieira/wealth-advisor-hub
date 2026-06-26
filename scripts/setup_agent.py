#!/usr/bin/env python3
"""
One-time setup: creates the Investment Advisor Agent and attaches its knowledge base.
Safe to run multiple times (idempotent).
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from elevenlabs import ElevenLabs
from elevenlabs_fsi.agent.advisor_agent import AdvisorAgent
from elevenlabs_fsi.agent.knowledge_base import KnowledgeBaseManager
from elevenlabs_fsi.budget.tracker import CreditTracker

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    print("ERROR: ELEVENLABS_API_KEY environment variable not set.")
    sys.exit(1)

client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
tracker = CreditTracker()

print(f"Budget: {tracker.remaining} characters remaining")
if tracker.should_warn:
    print("WARNING: Less than 3,000 characters remaining!")

print("\n[1/3] Setting up advisor agent...")
advisor = AdvisorAgent(client=client)
agent_id = advisor.get_or_create()
print(f"      Agent ID: {agent_id}")

print("\n[2/3] Setting up knowledge base...")
kb_manager = KnowledgeBaseManager(client=client)
docs = kb_manager.get_default_documents()
kb_ids = []
for doc in docs:
    kb_id = kb_manager.create(name=f"FSI - {doc['name']}", content=doc["content"])
    print(f"      KB created: {doc['name']} → {kb_id}")
    kb_ids.append(kb_id)

print("\n[3/3] Attaching knowledge base to agent...")
for kb_id in kb_ids:
    client.conversational_ai.agents.update(
        agent_id=agent_id,
        knowledge_base=[{"type": "file", "id": kb_id}],
    )
print("      Done.")

print(f"\nSetup complete. Agent ID: {agent_id}")
print(f"Budget remaining: {tracker.remaining} characters")
print(f"\nNext step: python scripts/demo.py")
