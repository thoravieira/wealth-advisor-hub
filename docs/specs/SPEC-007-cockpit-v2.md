# SPEC-007 — sofIA

**Status:** Implemented  
**Author:** Thiago da Hora  
**Date:** 2026-06-30  
**Implementation:** `front/cockpit.html` · `backend/main.py` · `analytics/main.py` · `db/init.sql`

---

## 1. Problem Statement

A wealth advisor managing 45+ clients needs to:
1. Know at a glance who needs action today (compliance risk, pending approvals, opportunities)
2. Act on those clients without context-switching between tools
3. Communicate with clients via voice-first messages that feel personal, not AI-generated

Existing tools (CRM, portfolio platforms) are reactive — the advisor queries them. This cockpit flips the model: Sofia, the AI advisor, proactively surfaces what matters and executes actions on voice command.

---

## 2. Solution Design

### Guiding principles

| Principle | Implementation |
|---|---|
| **ElevenLabs-first** | Every AI feature uses ElevenLabs APIs |
| **Voice as primary UI** | Sofia navigates the screen; text is secondary |
| **Editable AI output** | All Sofia-generated text passes through advisor review before delivery |
| **Scalable separation** | Front and backend are independent containers |
| **Persistent memory** | Agent sessions and learned facts survive across conversations |

### What is real vs. mock

| Feature | Status | Technology |
|---|---|---|
| Sofia voice conversation | **Real** | ElevenLabs Conversational AI |
| Voice message generation | **Real** | ElevenLabs TTS (Sarah voice) |
| Speech-to-text | **Real** | ElevenLabs STT (Scribe v2) |
| Cockpit navigation by voice | **Real** | Client-side tools + dc state |
| Agent session persistence | **Real** | PostgreSQL |
| Long-term advisor memory | **Real** | PostgreSQL |
| Client book data | **Seed** | DuckDB analytics service (mirrors frontend data) |
| Compliance knowledge base | **Real** | ElevenLabs KB (FSI Compliance Guide) |
| WhatsApp delivery | **Mock** | Toast notification only |
| Call transcription | **Mock** | Static demo data |

---

## 3. Components

### 3.1 Frontend — `front/cockpit.html`

Single HTML file (~1,200 lines). Served via nginx container. No build step.

**Engine:** `dc` template engine (reactive HTML, no VDOM)  
**Pattern:** Single `DCLogic` class — `state` + `renderVals()` returns all computed values and handlers

#### State schema

```javascript
state = {
  lang: 'en',              // 'en' | 'pt'
  menuOpen: true,          // sidebar collapsed?
  chatOpen: false,         // Sofia side panel open?
  route: 'overview',       // current view
  prevRoute: 'overview',   // for back button
  clientId: 'ricardo',     // selected client
  convoView: 'transcript', // 'transcript' | 'messages'
  clientFilter: 'all',
  convFilter: 'all',
  recFilter: 'all',
  query: '',
  agentStatus: 'idle',     // 'idle' | 'connecting' | 'connected'
  agentTranscript: [],     // [{ who: 'AI'|'YOU', text }]
  voicePreviews: [],       // [{ url, text, preview, clientId, play, btnBg }]
  playingVoice: null,
  approvalCard: null,
  approvalClientId: null,
  toastMsg: null,
  analyticsClients: {},    // keyed by client_id; populated by _initData() on first render
  memoryFacts: {}          // keyed by client_id; populated by _fetchMemory() when client detail opens
}
```

#### dc rendering constraints

Ternary expressions do NOT evaluate inside `style=""` attributes. Pre-compute in `renderVals()`:

```javascript
// wrong
<div style="display:{{ chatOpen ? 'none' : 'flex' }}">

// correct — pre-compute fabDisplay: S.chatOpen ? 'none' : 'flex'
<div style="display:{{ fabDisplay }}">
```

Textarea `value` resets on every re-render if bound reactively. Set imperatively after state change:

```javascript
self.setState({ approvalCard: text });
setTimeout(() => {
  const ta = document.getElementById('voice-edit-ta');
  if (ta) { ta.value = text; ta.focus(); }
}, 60);
```

---

### 3.2 Backend — `backend/main.py`

**Framework:** FastAPI + psycopg2  
**Dependencies:** `fastapi`, `uvicorn[standard]`, `python-multipart`, `psycopg2-binary`

#### Endpoint contracts

```
GET  /health
     Response: { status, agent_id, postgres, analytics }

GET  /agent/token
     Response: { signed_url: "wss://...", agent_id }
     Side effect: INSERT INTO agent_sessions

POST /tts
     Body: { text, voice_id?, client_id? }
     Response: audio/mpeg stream
     Side effect: INSERT INTO advisor_actions (voice_generated)

POST /stt
     Body: multipart/form-data file
     Response: { transcript, words }

GET  /memory/long/{client_id}
     Response: [{ id, client_id, category, fact, confidence, created_at }]

POST /memory/long
     Body: { client_id, category, fact, confidence }
     Response: { id, status }

GET  /actions?client_id=&limit=
     Response: [{ id, session_id, client_id, action_type, payload, created_at }]

GET  /clients[/{client_id}]
     Proxy to analytics service

GET  /internal/analytics-health
     Response: { analytics: "ok" | "unavailable" }
```

---

### 3.3 PostgreSQL — `db/init.sql`

Agent memory and operational state.

```sql
agent_sessions      -- one row per voice session (id, conversation_id, client_id, status, timestamps)
agent_memory_short  -- conversation turns during a session (role, content, expires with session)
agent_memory_long   -- facts learned across sessions (category, fact, confidence, is_active)
advisor_actions     -- audit log (action_type, payload, client_id, session_id)
```

---

### 3.4 Analytics — `analytics/main.py`

DuckDB embedded in FastAPI. Tables stored in Docker volume `lake_data`.

```
GET  /health
GET  /clients           → list of 12 demo clients
GET  /clients/{id}      → single client
GET  /clients/{id}/snapshots
GET  /recommendations
POST /recommendations
GET  /recommendations/{id}
PATCH /recommendations/{id}
GET  /voice-messages
POST /voice-messages
GET  /alerts
```

---

### 3.5 ElevenLabs Agent — Sofia

**Created by:** `setup/create_agent.py` — idempotent, writes `ELEVENLABS_AGENT_ID` back to `.env`

#### Guardrails (active)

Three guardrail layers are enabled on the agent. Configured via `platform_settings.guardrails`:

| Guardrail | Status | Behavior |
|---|---|---|
| **Focus** | ✓ enabled | Reinforces system prompt alignment throughout the conversation |
| **Manipulation** (`prompt_injection`) | ✓ enabled | Detects and blocks prompt injection / instruction override attempts |
| **Content** | ✓ enabled (blocking) | Screens all responses before delivery; redirects off-topic with a fixed message |

Content thresholds (FSI professional context):

| Category | Threshold | Trigger action |
|---|---|---|
| Sexual, Violence, Harassment, Self-harm | `low` | Retry with: *"I can't help with that. Let me refocus on your portfolio."* |
| Profanity, Religion/politics, Medical/legal | `medium` | Same retry message |

#### System prompt strategy

Compact book snapshot (~2,400 chars) for 12 clients embedded in prompt — zero tool-call latency for 95% of questions. `get_client_data` is a silent fallback.

```
Style: Never say "let me check" or "please wait".
       You know this book cold. 2 sentences max, then act.
       After sending, always suggest the next priority client.
```

#### Client tools

| Tool | Latency | Side effect |
|---|---|---|
| `navigate` | ~0ms | setState({route}) |
| `show_opportunity` | ~0ms | setState({route:'client', clientId}) |
| `show_recommendation` | ~0ms | setState({approvalCard}), sets textarea via DOM |
| `generate_voice_message` | 300–800ms | POST /tts → VOICE card in side panel |
| `send_whatsapp` | ~0ms | Clears approval card, shows toast |
| `get_client_data` | <1ms | Reads `_clientsById` JS map silently |

---

## 4. Compose Stack

```yaml
services:
  front:      nginx · :8080 · builds from ./front
  backend:    FastAPI · :8000 · builds from ./backend
  postgres:   postgres:16-alpine · :5432 · init from db/init.sql
  analytics:  DuckDB FastAPI · :8001 · builds from ./analytics
```

Start everything:
```bash
cp .env.example .env   # add ELEVENLABS_API_KEY, ELEVENLABS_AGENT_ID, ELEVENLABS_VOICE_ID
docker compose up --build
```

| Service | URL |
|---|---|
| Cockpit | http://localhost:8080/cockpit.html |
| Backend | http://localhost:8000 |
| Analytics | http://localhost:8001 |
| Health | http://localhost:8000/health |

---

## 5. Test Suite

106 tests across 6 files. Run with:

```bash
cd tests && python3 -m pytest -v
```

| File | Tests | Covers |
|---|---|---|
| `test_01_backend_current.py` | 21 | Health, agent token, TTS, STT, error handling |
| `test_02_frontend_current.py` | 11 | Index redirect, cockpit.html loads, old filenames gone |
| `test_03_postgres.py` | 6 | Connectivity, schema, memory API via backend |
| `test_04_analytics.py` | 32 | Clients (all 12), recommendations lifecycle, voice messages, alerts |
| `test_05_backend_pg_integration.py` | 13 | Health with deps, session creation, memory CRUD, action log, proxies |
| `test_06_data_integration.py` | 24 | Analytics→cockpit data flow, postgres seed facts, Sofia memory in UI |

---

## 6. Acceptance Criteria

### Sofia conversation

- [ ] Phone button connects to Sofia in < 5 seconds
- [ ] Sofia speaks her opening line automatically, starting with highest-risk client
- [ ] "Show me the alerts" navigates the cockpit to Alerts view
- [ ] "Pull up Ricardo" opens Ricardo Tanaka's client detail
- [ ] Sofia generates a recommendation card with editable text
- [ ] "Generate voice" creates a playable VOICE card in the side panel
- [ ] Playing the VOICE card mutes Sofia; after it ends she is unmuted
- [ ] "Send it" triggers send_whatsapp and shows a toast
- [ ] After sending, Sofia suggests the next priority client unprompted
- [ ] Red × ends the session cleanly; side panel returns to idle state

### Cockpit navigation

- [ ] All 6 sidebar sections render without errors
- [ ] Back button returns to the originating screen (not always overview)
- [ ] Language toggle switches all strings between EN and PT instantly
- [ ] Client filter chips narrow the client list correctly

### Conversations

- [ ] VIP clients appear in a dedicated frame above regular clients
- [ ] Channel filter chips (All / Calls / WhatsApp / E-mail) apply to both frames simultaneously
- [ ] VIP frame hides when the active filter yields no VIP rows
- [ ] Regular frame hides when the active filter yields no regular rows
- [ ] Clicking any row opens the client detail with `prevRoute = conversations`

### Alerts

- [ ] Three severity sections rendered vertically: High → Medium → Low
- [ ] Each section header shows severity label (colored) + alert count
- [ ] Alerts within each section scroll horizontally as a card carousel
- [ ] Each card shows: client initials + name + VIP diamond (if applicable) + time + type badge + description
- [ ] Clicking a card opens the client detail (no separate Review button)
- [ ] Sofia live call panel is absent from Conversations; session control is via EQ FAB only

### Data layer

- [ ] `GET /health` reports postgres and analytics as "ok"
- [ ] Each voice session creates a row in `agent_sessions`
- [ ] `/memory/long` stores and retrieves facts about clients
- [ ] `/actions` returns the audit log of advisor actions
- [ ] `/clients/ricardo` returns Ricardo Tanaka's profile from analytics

---

## 7. Known Limitations (demo scope)

- Client portfolio data is seeded/static — no live market or CRM feed
- WhatsApp delivery is mocked — no real message leaves the system
- Voice previews are lost on page reload (in-memory blob URLs only)
- agent_memory_short is never read back into Sofia's context (Phase 3 work)
- No authentication — anyone with the URL can use the cockpit
- CORS open on backend — must restrict in production
- ElevenLabs free tier: 10 min/month agent voice, 10k TTS chars/month
