# SPEC-003 — Proactive Outbound Client Calls

| Field | Value |
|---|---|
| ID | SPEC-003 |
| Status | ROADMAP — not yet implemented |
| Feature | Sofia calls high-priority clients automatically when a risk or compliance alert fires |
| ElevenLabs features used | Conversational AI, Outbound Calling (ElevenAgents) |
| Roadmap phase | v3 |
| Plan required | Starter+ (phone number provisioning) |

---

## Problem

When a market event hits, the advisor needs to reach 8–12 clients within the same morning. Manual calling is impractical at that scale. A mass notification is impersonal and often ignored. The advisor needs a way to have substantive, personalized conversations at scale — without four hours on the phone.

---

## Solution

When the risk engine flags a priority alert (equity concentration breach, suitability expiry, major market move), Sofia initiates an outbound call to the client via ElevenLabs Outbound Calling. The conversation is grounded in the client's profile and the specific alert context. The advisor reviews call summaries and approves any follow-up actions from the cockpit.

---

## User Story

> As a wealth advisor, when a market event triggers a priority alert for multiple clients, I want Sofia to make outbound calls to affected clients automatically, grounded in each client's profile, so I can focus my personal attention only on cases that need human escalation.

---

## Acceptance Criteria

- [ ] AC-001: Alert engine triggers outbound call when a client's equity exceeds their risk threshold
- [ ] AC-002: Outbound call is placed via ElevenLabs phone API with client profile pre-loaded as context
- [ ] AC-003: Sofia greets client by name and references the specific alert type and value
- [ ] AC-004: If client requests to speak with the advisor → Sofia flags for human escalation and ends call gracefully
- [ ] AC-005: Call transcript and intent classification are stored in `agent_memory_long` and `advisor_actions`
- [ ] AC-006: Advisor sees call outcome in cockpit Alerts view with one-click follow-up action

---

## Technical Design

```
Alert fires (risk engine)
        │
        ▼
POST /outbound/call
  { client_id, alert_type, alert_value }
        │
        ├─► Query agent_memory_long for client context
        ├─► ElevenLabs: place_outbound_call({ agent_id, to_number, first_message })
        └─► INSERT agent_sessions (status: outbound)

Call ends
        │
        ├─► GET /convai/conversations/{id} → transcript
        ├─► Classify intent (escalate | resolved | no_answer)
        └─► INSERT advisor_actions (action_type: outbound_call, payload: { outcome })
```

**First message template:**
> "Hi [name], this is Sofia from [advisor]'s office. I'm calling because your portfolio has reached [X]% equity — above your [Y]% threshold. Do you have two minutes to review your options?"

---

## What Requires a Paid Plan

| Feature | Plan required |
|---|---|
| Phone number provisioning | Starter+ |
| Outbound call API | Starter+ |
| High call volume | Business |
