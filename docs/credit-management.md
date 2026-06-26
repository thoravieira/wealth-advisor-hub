# Credit Management — Free Tier Budget

## Account Status

| Metric | Value |
|---|---|
| Plan | Free |
| Character limit / month | 10,000 |
| Characters used | 187 |
| **Characters available** | **9,813** |
| Reset | Monthly |

## Budget Allocation

| Feature | Allocated | Notes |
|---|---|---|
| SPEC-001 Agent setup (knowledge base ingestion) | 0 | KB ingestion does not consume TTS chars |
| SPEC-001 Agent demo conversation (5–6 exchanges) | 4,000 | ~600–800 chars per agent response |
| SPEC-001 TTS personalized alert message | 500 | Short proactive message |
| SPEC-002 Campaign TTS (3 languages × ~200 chars) | 600 | PT-BR, EN-US, ES-MX |
| **Safety reserve (never spend)** | **2,000** | Prevent accidental exhaustion |
| **Uncommitted buffer** | **2,713** | Available for iteration |

## Character Cost Estimation Rules

Before any API call that consumes characters, the `CreditEstimator` must:

1. Count characters in the payload
2. Check `remaining_characters >= required + SAFETY_RESERVE`
3. If insufficient → raise `InsufficientCreditsError` with context
4. If sufficient → log the planned spend and proceed

### Estimation formulas

| Operation | Cost |
|---|---|
| TTS (`text_to_speech`) | `len(text)` characters |
| Agent conversation turn | Estimated by agent response length — not pre-knowable; use average 700 chars as upper bound per turn |
| Speech-to-text | Does **not** consume TTS characters |
| Knowledge base upload | Does **not** consume TTS characters |

## Cost Log

| Date | Feature | Operation | Chars spent | Remaining |
|---|---|---|---|---|
| 2026-06-26 | — | Baseline | — | 9,813 |

> Update this table after every API call that consumes characters.

## Alerts

- **< 3,000 chars remaining** → warn before every API call
- **< 2,000 chars remaining** → block all calls, raise `SafetyReserveError`
