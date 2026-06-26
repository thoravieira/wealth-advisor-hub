# SPEC-003 — Proactive Outbound Voice Call

| Field | Value |
|---|---|
| ID | SPEC-003 |
| Status | SPEC ONLY (no implementation — explain in pitch) |
| Feature | Churn-prevention outbound call for acquirers |
| Scenarios covered | Scenario 3 |
| ElevenLabs features used | Conversational AI Agent, Outbound Calls (phone) |
| Diagram | [`docs/diagrams/outbound-flow.md`](../diagrams/outbound-flow.md) |
| Plan required | **Paid (phone number provisioning not available on free tier)** |

## User Story

> As a retention manager at a payment acquirer, I want the system to automatically call
> merchants who haven't processed transactions in 7+ days with a human-sounding voice,
> understand their concern in real-time, and escalate to a human agent only when churn
> risk is confirmed, so my team focuses only on the highest-risk cases.

## Acceptance Criteria

- [ ] AC-001: System identifies merchants inactive for ≥ 7 days from a batch job
- [ ] AC-002: Outbound call is placed via ElevenLabs phone API
- [ ] AC-003: Agent greets merchant by name and references inactivity period
- [ ] AC-004: If merchant expresses cancellation intent → agent flags for human escalation
- [ ] AC-005: Call summary (transcript + intent classification) is stored per call
- [ ] AC-006: If no answer → retry once after 4 hours, then mark for human follow-up

## Technical Design

### Trigger

```
Batch job (daily, 09:00) →
  Query: merchants with last_transaction_date < today - 7 days
  For each merchant:
    budget_check() → place_outbound_call(merchant)
```

### Outbound Call Configuration

```python
OutboundCall(
    agent_id=ADVISOR_AGENT_ID,
    to_number=merchant.phone,
    first_message=f"Olá {merchant.name}, aqui é o assistente da {acquirer}. "
                  f"Notamos que sua maquininha não processou transações nos últimos "
                  f"{days_inactive} dias. Está tudo bem?",
)
```

### Escalation Logic (agent system prompt rule)

```
SE cliente disser: "quero cancelar" | "não uso mais" | "vou para outro" →
    RESPONDA: "Vou conectá-lo com um especialista agora. Um momento."
    ENCERRE a conversa com flag: escalate=true
```

### Post-call

```
call_ended →
  transcript = get_transcript(call_id)
  intent = classify(transcript)   # external NLP
  store(merchant_id, intent, transcript, timestamp)
```

## What Requires a Paid Plan

| Feature | Plan required |
|---|---|
| Phone number provisioning | Starter+ |
| Outbound call API | Starter+ |
| Call volume > 10/day | Business |

## Business Impact

| Metric | Today | With ElevenLabs |
|---|---|---|
| Cost per retention call (human) | R$12–45 | R$0.50–1.50 |
| Calls handled per day (per agent) | 40–60 | Unlimited |
| Escalation rate (human needed) | 100% | ~15–25% |
| Churn reduction (estimated) | baseline | 20–35% |

## Out of Scope

- CRM integration (Salesforce / HubSpot)
- Real-time transaction data pipeline
- WhatsApp fallback channel
