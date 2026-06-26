# SPEC-001 — Investment Advisor Agent

| Field | Value |
|---|---|
| ID | SPEC-001 |
| Status | APPROVED |
| Feature | Conversational AI agent for investment advisory |
| Scenarios covered | Scenario 1 |
| ElevenLabs features used | Conversational AI Agent, Knowledge Base, TTS |
| Estimated credit cost | ~4,500 chars (demo session) |

## User Story

> As an investment client, I want to have a natural voice conversation with a virtual advisor
> that understands my financial profile and proactively suggests relevant products based on my
> expressed concerns, so that I feel attended to even outside business hours.

## Acceptance Criteria

- [ ] AC-001: Agent can be created and retrieved by ID without creating duplicates
- [ ] AC-002: Agent responds in Portuguese (PT-BR) by default
- [ ] AC-003: Agent has access to a knowledge base containing FSI product descriptions
- [ ] AC-004: Agent greets the client by name when name is provided in the system prompt
- [ ] AC-005: Agent recommends a specific product when client expresses a financial concern
- [ ] AC-006: Any operation estimating > available credits raises `InsufficientCreditsError` before calling the API
- [ ] AC-007: Credit usage is logged after each conversation turn

## Technical Design

### Agent Configuration

```python
AgentConfig(
    name="Assessor Virtual XP",
    language="pt",
    first_message="Olá! Sou seu assessor virtual. Como posso ajudá-lo hoje?",
    system_prompt=SYSTEM_PROMPT,  # see below
    model_id="eleven_flash_v2_5",  # lowest latency, multilingual
)
```

### System Prompt (outline)

```
Você é um assessor de investimentos virtual do banco [BANCO].
Seu perfil: consultivo, empático, objetivo.
Conhecimento: produtos de renda fixa, renda variável, fundos, previdência.
Regras:
- Nunca prometa rentabilidade garantida.
- Ao detectar preocupação com liquidez → sugira CDB/LCI curto prazo.
- Ao detectar perfil agressivo → apresente opções de renda variável.
- Encerre sempre oferecendo falar com um assessor humano.
```

### Knowledge Base Documents

| Document | Content | Size estimate |
|---|---|---|
| `products.md` | CDB, LCI, LCA, Tesouro Direto, Fundos, Previdência | ~2,000 chars |
| `faq.md` | Perguntas frequentes sobre investimentos | ~1,500 chars |
| `compliance.md` | Avisos regulatórios obrigatórios (CVM) | ~500 chars |

> Knowledge base upload does **not** consume TTS characters.

### API Calls Sequence

```
1. GET /v1/convai/agents           → check if agent exists
2. POST /v1/convai/agents          → create if not exists (0 chars)
3. POST /v1/convai/knowledge-base  → upload documents (0 chars)
4. PATCH /v1/convai/agents/{id}    → attach knowledge base (0 chars)
5. [Demo] WebSocket conversation   → ~700 chars/turn × 6 turns = ~4,200 chars
```

### Credit Pre-flight

Before each conversation turn, the estimator uses `700` chars as the upper-bound estimate.
If `remaining < 700 + 2000 (reserve)`, the turn is blocked.

## Out of Scope

- Real-time sentiment/emotion analysis (requires external STT + NLP pipeline)
- WhatsApp delivery of audio messages (requires Twilio/Meta integration)
- Voice cloning of a specific bank's brand voice (requires paid plan)
- Actual transaction execution or account access

## Test Plan

See [`tests/unit/test_advisor_agent.py`](../../tests/unit/test_advisor_agent.py) and
[`tests/unit/test_knowledge_base.py`](../../tests/unit/test_knowledge_base.py).

Integration tests: [`tests/integration/test_advisor_flow.py`](../../tests/integration/test_advisor_flow.py).
