#!/usr/bin/env python3
"""
Interactive demo runner for the Investment Advisor Agent.
Prints a widget URL for the conversation. Each turn costs ~700 chars.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from elevenlabs import ElevenLabs
from elevenlabs_fsi.agent.advisor_agent import AdvisorAgent
from elevenlabs_fsi.budget.estimator import CreditEstimator, InsufficientCreditsError
from elevenlabs_fsi.budget.tracker import CreditTracker


ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    print("ERROR: ELEVENLABS_API_KEY environment variable not set.")
    sys.exit(1)

client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
tracker = CreditTracker()
estimator = CreditEstimator(available=tracker.remaining)

print("=" * 60)
print("  Investment Advisor Agent — FSI Demo")
print("=" * 60)
print(f"  Budget: {tracker.remaining} characters remaining")

if tracker.should_warn:
    print("  ⚠ WARNING: less than 3,000 characters remaining!")

print()

try:
    estimator.check(required=700)
except InsufficientCreditsError as e:
    print(f"ERROR: {e}")
    sys.exit(1)

advisor = AdvisorAgent(client=client)
agent_id = advisor.get_or_create()

widget_url = f"https://elevenlabs.io/app/talk-with?agent_id={agent_id}"

print(f"Agent ID : {agent_id}")
print(f"Widget   : {widget_url}")
print()
print("Open the Widget URL in your browser to start the conversation.")
print("Each conversation turn consumes approximately 700 characters.")
print()
print("Suggested demo script:")
print("  Turn 1 → 'Tenho R$10.000 parados na conta, o que faço?'")
print("  Turn 2 → 'Preciso do dinheiro em 6 meses'")
print("  Turn 3 → 'Quero algo seguro'")
print("  Turn 4 → 'Qual a diferença do CDB para o Tesouro?'")
print("  Turn 5 → 'Posso falar com alguém?'")
print()
print(f"Estimated cost for 5 turns: ~3,500 characters")
print(f"Remaining after demo: ~{tracker.remaining - 3500} characters")
