# Architecture Overview

## System Context

```
┌─────────────────────────────────────────────────────────────┐
│                        FSI Demo System                       │
│                                                             │
│  ┌──────────────┐    ┌─────────────────┐   ┌────────────┐  │
│  │ Demo Script  │───▶│ ElevenLabs FSI  │──▶│ ElevenLabs │  │
│  │ (scripts/)   │    │ (src/)          │   │    API     │  │
│  └──────────────┘    └────────┬────────┘   └────────────┘  │
│                               │                             │
│                    ┌──────────▼──────────┐                  │
│                    │   Budget Guard       │                  │
│                    │ (pre-flight check)   │                  │
│                    └─────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### `src/elevenlabs_fsi/budget/`

Runs **before every API call** that consumes characters.

- `estimator.py` — estimates character cost for a given operation
- `tracker.py` — logs actual usage; reads/writes `.budget.json` (gitignored)

Flow:
```
caller → estimator.check(required) → [ok] → API call → tracker.log(actual)
                                   → [fail] → InsufficientCreditsError
```

### `src/elevenlabs_fsi/agent/`

Manages the Conversational AI advisor agent lifecycle.

- `advisor_agent.py` — create, get, configure agent via ElevenLabs API
- `knowledge_base.py` — upload FSI knowledge documents to agent

### `scripts/`

Entry points meant to be run by a human:

- `setup_agent.py` — idempotent: creates agent + knowledge base if not exists
- `demo.py` — interactive demo runner; prints conversation turn by turn

## Key Design Decisions

### No state stored in memory — `.budget.json` as ledger
Character usage is persisted to `.budget.json` so it survives between script runs.
This is the source of truth for remaining budget, not the API subscription endpoint
(which would cost an extra call to check).

### Idempotent setup
`setup_agent.py` checks if the agent already exists before creating one.
Safe to run multiple times without consuming credits or creating duplicates.

### Separation of unit and integration tests
Unit tests mock the ElevenLabs client and run with zero API calls.
Integration tests call the real API and require `ELEVENLABS_API_KEY` in environment.
CI should only run unit tests by default.

## Out of Scope (Free Tier)

- Voice cloning (requires paid plan)
- Outbound phone calls (requires phone number + paid plan)
- WhatsApp integration (requires external API — Twilio / Meta)
- Sentiment analysis on audio (not native to ElevenLabs — would need external STT + NLP)
