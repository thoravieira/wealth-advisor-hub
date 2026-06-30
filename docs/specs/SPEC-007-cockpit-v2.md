# SPEC-007 — FSI Advisor Cockpit v2

**Status:** Implemented  
**Author:** Thiago da Hora  
**Date:** 2026-06-30  
**Implementation:** `front/cockpit.html` + `backend/main.py`

---

## 1. Problem Statement

A wealth advisor managing 45+ clients needs to:
1. Know at a glance who needs action today (compliance risk, pending approvals, opportunities)
2. Act on those clients without context-switching between tools
3. Communicate with clients via voice-first messages that feel personal, not AI-generated

Existing tools (CRM, portfolio platforms) are reactive — the advisor queries them. This cockpit flips the model: the AI advisor *Sofia* proactively surfaces what matters and executes actions on voice command.

---

## 2. Solution Design

### Guiding principles

| Principle | Implementation choice |
|---|---|
| **Demo over production** | Single HTML file, no build step, hardcoded data |
| **ElevenLabs-first** | Every AI feature uses ElevenLabs APIs |
| **Voice as primary UI** | Sofia navigates the screen; text is secondary |
| **Minimal backend** | 3 proxy endpoints, no database, no auth |
| **Editable AI output** | All Sofia-generated text passes through advisor review before delivery |

### What is real vs. mock

| Feature | Status | Technology |
|---|---|---|
| Sofia voice conversation | **Real** | ElevenLabs Conversational AI |
| Voice message generation | **Real** | ElevenLabs TTS (Sarah voice) |
| Speech-to-text | **Real** | ElevenLabs STT (Scribe v2) |
| Cockpit navigation by voice | **Real** | Client-side tools + dc state |
| Client data on screen | **Mock** | Hardcoded JS data |
| Compliance knowledge base | **Real** | ElevenLabs KB (FSI Compliance Guide) |
| WhatsApp delivery | **Mock** | Toast notification only |
| Call transcription | **Mock** | Static demo data |

---

## 3. Components

### 3.1 Frontend

**File:** `front/cockpit.html`  
**Engine:** `dc` template engine (reactive HTML, no VDOM)  
**Pattern:** Single DCLogic class — `state` + `renderVals()` returns all computed values and handlers

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
  clientFilter: 'all',     // client list filter
  convFilter: 'all',       // conversations filter
  recFilter: 'all',        // recommendations filter
  query: '',               // search query
  agentStatus: 'idle',     // 'idle' | 'connecting' | 'connected'
  agentTranscript: [],     // [{ who: 'AI'|'YOU', text }]
  voicePreviews: [],       // [{ url, text, preview, clientId, play, btnBg }]
  playingVoice: null,      // URL of currently playing preview
  approvalCard: null,      // text shown in approval overlay
  approvalClientId: null,  // client for approval card
  toastMsg: null           // toast notification text
}
```

#### Rendering rule — dc template limitations

> Ternary expressions do NOT evaluate inside `style=""` attributes.  
> Pre-compute all display/color values in `renderVals()`:

```javascript
// ✗ does NOT work
<div style="display:{{ chatOpen ? 'none' : 'flex' }}">

// ✓ correct pattern
fabDisplay: S.chatOpen ? 'none' : 'flex',
// then in HTML:
<div style="display:{{ fabDisplay }}">
```

#### Form input pattern

> Textarea `value` resets on every re-render if bound reactively.  
> Pattern: set value imperatively via DOM after state change.

```javascript
// In tool handler:
self.setState({ approvalCard: text });
setTimeout(() => {
  const ta = document.getElementById('voice-edit-ta');
  if (ta) { ta.value = text; ta.focus(); }
}, 60);

// In handler reading the value:
const text = document.getElementById('voice-edit-ta')?.value || this.state.approvalCard;
```

### 3.2 Backend

**File:** `backend/main.py`  
**Framework:** FastAPI  
**Dependencies:** `fastapi`, `uvicorn[standard]`, `python-multipart` — no ElevenLabs SDK

#### Endpoint contracts

```
GET  /health
     Response: { "status": "ok", "agent_id": string }

GET  /agent/token
     Response: { "signed_url": "wss://...", "agent_id": string }
     Note: calls ElevenLabs GET /v1/convai/conversation/get_signed_url

POST /tts
     Body: { "text": string, "voice_id"?: string }
     Response: audio/mpeg stream
     Note: calls ElevenLabs POST /v1/text-to-speech/{voice_id}

POST /stt
     Body: multipart/form-data, field "file" = audio file
     Response: { "transcript": string, "words": [...] }
     Note: calls ElevenLabs POST /v1/speech-to-text with scribe_v2
```

### 3.3 ElevenLabs Agent

**Agent ID:** `agent_7501kwap3zrre9wr5h20vdqbtz7n`  
**Created by:** `setup/create_agent.py`

#### System prompt strategy

The system prompt embeds a compact book snapshot (~2,400 chars total) covering all 12 demo clients with their status, AUM, risk profile, allocation, and key alert. This eliminates tool-call latency for 95% of questions.

```
BOOK SNAPSHOT — 30 Jun 2026:
Ricardo Tanaka [VIP] · R$12.8M · Aggressive · EQ 71% (limit 80%) · AT RISK: ...
Fernando Costa [VIP] · R$23.0M · Aggressive · EQ 71% (limit 80%) · ATTENTION: ...
...
```

Style instruction forces natural language:
```
Never say "let me check", "please wait", "retrieving data". 
You know this book cold. Be sharp — 2 sentences max, then act.
```

#### Client tools (6 total)

| Tool | Type | Latency | Side effect |
|---|---|---|---|
| `navigate` | client | ~0ms | setState({route}) |
| `show_opportunity` | client | ~0ms | setState({route:'client', clientId}) |
| `show_recommendation` | client | ~0ms | setState({approvalCard}), sets textarea via DOM |
| `generate_voice_message` | client | 300–800ms | POST /tts → adds VOICE card to transcript |
| `send_whatsapp` | client | ~0ms | clears approval card, shows toast |
| `get_client_data` | client | <1ms | reads `_clientsById` JS map |

---

## 4. Key User Flows

See detailed diagrams:
- [Sofia interaction sequence](../flows/SOFIA_FLOW.md)
- [Cockpit navigation flows](../flows/COCKPIT_FLOWS.md)

---

## 5. Deployment

### Local (dev)

```bash
# 1. Setup agent (once)
ELEVENLABS_API_KEY=sk_... python setup/create_agent.py

# 2. Backend
cd backend && pip install -r requirements.txt
source ../.env && uvicorn main:app --reload --port 8000

# 3. Frontend
cd front && docker build -t fsi-front . && docker run -p 8080:80 fsi-front
```

### Docker Compose (production demo)

```bash
cp .env.example .env     # fill in API key + agent IDs
docker compose up --build
# Front: http://localhost:8080/Cockpit%20B.dc.html
# Backend: http://localhost:8000
```

---

## 6. Acceptance Criteria

### Sofia conversation

- [ ] Tapping the phone button connects to Sofia in < 5 seconds
- [ ] Sofia speaks her opening line automatically
- [ ] Saying "show me the alerts" navigates the cockpit to Alerts view
- [ ] Saying "pull up Ricardo" opens Ricardo Tanaka's client detail
- [ ] Sofia generates a recommendation card with editable text
- [ ] Clicking "Generate voice" creates a playable VOICE card in the side panel
- [ ] Playing the VOICE card mutes Sofia's output; after it ends Sofia is unmuted
- [ ] Saying "send it" triggers the send_whatsapp tool and shows a toast
- [ ] After sending, Sofia suggests the next priority client unprompted
- [ ] Tapping the red × ends the session cleanly

### Cockpit navigation

- [ ] Clicking any client card opens their detail panel
- [ ] Back button returns to the originating screen (not always clients)
- [ ] Language toggle switches all UI strings between EN and PT instantly
- [ ] All 6 sidebar sections render without errors
- [ ] Client filter chips narrow the client list correctly

### Backend

- [ ] `GET /health` returns 200 with correct agent_id
- [ ] `GET /agent/token` returns a `wss://` signed URL
- [ ] `POST /tts` returns audio/mpeg for a short text input
- [ ] `POST /stt` returns a transcript for a valid audio upload

---

## 7. Known Limitations (demo scope)

- Client data is hardcoded — no live portfolio integration
- WhatsApp delivery is mocked — no real message is sent
- `voicePreviews` are lost on page reload (no persistence)
- ElevenLabs free tier: 10 min/month agent voice + 10k TTS chars/month
- No authentication — anyone with the URL can access the cockpit
- CORS is open on the backend — restrict in any real deployment
