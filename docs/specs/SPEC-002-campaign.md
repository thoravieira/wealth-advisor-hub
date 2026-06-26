# SPEC-002 — Multi-Market Voice Campaign

| Field | Value |
|---|---|
| ID | SPEC-002 |
| Status | SPEC ONLY (no implementation — explain in pitch) |
| Feature | Personalized TTS campaign across languages and markets |
| Scenarios covered | Scenario 2 |
| ElevenLabs features used | TTS Multilingual v2 / Eleven v3, Voice Library |
| Diagram | [`docs/diagrams/campaign-flow.md`](../diagrams/campaign-flow.md) |
| Estimated credit cost | ~600 chars (3 languages × ~200 chars per script) |

## User Story

> As a marketing manager at a financial institution, I want to produce a personalized
> voice campaign for account opening simultaneously in Brazil, Mexico, the US, and the UK,
> delivered in 48 hours instead of 6 weeks, using a consistent brand voice across all markets.

## Acceptance Criteria

- [ ] AC-001: Same base script is rendered in PT-BR, ES-MX, EN-US and EN-GB
- [ ] AC-002: Client's first name is injected into each audio ("Olá, Maria…")
- [ ] AC-003: Audio is produced using `eleven_multilingual_v2` or `eleven_v3`
- [ ] AC-004: Output files are named `{market}_{client_id}.mp3`
- [ ] AC-005: Entire batch for 4 markets completes under 60 seconds
- [ ] AC-006: Credit cost is estimated and logged before batch starts

## Technical Design

### Input

```json
{
  "client_name": "Maria",
  "markets": ["pt-BR", "es-MX", "en-US", "en-GB"],
  "base_script": "Olá, {name}. Sua conta no {bank} está a um passo de ser aberta.",
  "model": "eleven_multilingual_v2"
}
```

### Flow

```
Input script (PT)
     │
     ├─▶ Translate to ES-MX (external LLM or human)
     ├─▶ Translate to EN-US
     └─▶ Translate to EN-GB
           │
           ▼
     ElevenLabs TTS
     (eleven_multilingual_v2)
     one premade voice per market
           │
           ▼
     Output: {market}_{client}.mp3
```

### Voices per Market (premade — free tier compatible)

| Market | Voice ID | Persona |
|---|---|---|
| PT-BR | `EXAVITQu4vr4xnSDxMaL` (Sarah) | Madura, confiante |
| ES-MX | `bIHbv24MWmeRgasZH58o` (Will) | Relaxado, otimista |
| EN-US | `XrExE9yKIg1WjnnlVkGX` (Matilda) | Profissional |
| EN-GB | `CwhRBWXzGAHq8TQ4Fs17` (Roger) | Casual, ressonante |

> With a paid plan: single cloned brand voice rendered natively in each language.

## What Requires a Paid Plan

| Feature | Why blocked |
|---|---|
| Single cloned voice across all markets | `can_use_instant_voice_cloning: false` |
| Commercial use of generated audio | Free tier has no commercial license |

## Business Impact

| Metric | Today | With ElevenLabs |
|---|---|---|
| Time to produce 4-market campaign | 4–6 weeks | 48 hours |
| Cost per audio variant | $500–2,000 (studio) | ~$0.30 |
| Personalization at scale | Manual/impossible | Automated per client name |

## Out of Scope

- Translation service (handled externally)
- WhatsApp / email delivery pipeline
- A/B testing framework
