# ElevenLabs FSI Demo — Investment Advisor Agent

Proof-of-concept demonstrating ElevenLabs Conversational AI applied to Financial Services (FSI).
Built with **Specification-Driven Development (SDD)** and **Test-Driven Development (TDD)**.

## Scenarios

| # | Scenario | Status | Demo |
|---|---|---|---|
| 1 | **Investment Advisor Agent** — real-time conversational AI for client advisory | ✅ Built | Live agent |
| 2 | **Multi-Market Campaign** — same campaign, multi-language audio in 48h | 📄 Spec + Diagram | Excalidraw flow |
| 3 | **Proactive Outbound** — churn prevention via voice for acquirers | 📄 Spec + Diagram | Excalidraw flow |

## Account Constraints (Free Tier)

| Resource | Limit | Used | Remaining |
|---|---|---|---|
| Characters/month | 10,000 | 187 | **9,813** |
| Voice slots | 3 | 0 | 3 |
| Voice cloning | ❌ Not available | — | — |
| Outbound calls | ❌ Not available | — | — |

> Credit budget is tracked per feature in [`docs/credit-management.md`](docs/credit-management.md).

## Repository Structure

```
.
├── docs/
│   ├── specs/              # SDD — one spec per feature (written before code)
│   ├── diagrams/           # Excalidraw flow diagrams
│   ├── architecture.md     # System design overview
│   └── credit-management.md # Credit budget per feature
├── src/
│   └── elevenlabs_fsi/
│       ├── agent/          # Conversational agent management
│       └── budget/         # Credit tracking & pre-flight estimator
├── tests/
│   ├── unit/               # Unit tests (written before implementation)
│   └── integration/        # Integration tests against real API
└── scripts/
    ├── setup_agent.py      # One-time agent + knowledge base setup
    └── demo.py             # Interactive demo runner
```

## Development Approach

### SDD — Specification-Driven Development
Each feature starts as a spec in `docs/specs/SPEC-XXX-*.md` covering:
- User story and acceptance criteria
- Technical design and API calls
- Credit cost estimate (pre-flight budget check)
- Out of scope

### TDD — Test-Driven Development
Tests in `tests/` are written **before** implementation:
1. **Red** — write failing test that describes expected behavior
2. **Green** — implement minimum code to pass
3. **Refactor** — clean up without breaking tests

## Setup

### Prerequisites
- Python 3.11+
- ElevenLabs account (free tier sufficient for Scenario 1)

### Install

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Configure

```bash
cp .env.example .env
# Edit .env with your ELEVENLABS_API_KEY
```

### Run tests

```bash
pytest tests/unit/          # Fast, no API calls
pytest tests/integration/   # Requires ELEVENLABS_API_KEY + real API
```

### Setup agent (one-time)

```bash
python scripts/setup_agent.py
```

### Run demo

```bash
python scripts/demo.py
```

## Specs Index

- [SPEC-001 — Investment Advisor Agent](docs/specs/SPEC-001-advisor-agent.md)
- [SPEC-002 — Multi-Market Campaign](docs/specs/SPEC-002-campaign.md)
- [SPEC-003 — Proactive Outbound Call](docs/specs/SPEC-003-outbound.md)
