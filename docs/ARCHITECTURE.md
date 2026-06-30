# Architecture

## Overview

Three layers: static HTML frontend, a thin FastAPI proxy that keeps the API key server-side, and ElevenLabs Cloud for all AI processing.

```
┌─────────────────────────────────────────────────────────────┐
│  Browser                                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Cockpit B.dc.html                                  │   │
│  │  ─ dc template engine (reactive state)             │   │
│  │  ─ DCLogic class  (renderVals + handlers)          │   │
│  │  ─ @11labs/client SDK  (WebSocket to ElevenLabs)   │   │
│  └─────────────────────────────────────────────────────┘   │
│           │ fetch                        │ WebSocket        │
└───────────┼──────────────────────────────┼─────────────────┘
            │                              │
   ┌─────────────────┐          ┌──────────────────────────┐
   │  Backend        │          │  ElevenLabs Cloud        │
   │  FastAPI        │          │                          │
   │  /tts    ───────┼──────────► TTS API (Sarah voice)   │
   │  /stt    ───────┼──────────► STT API (Scribe v1)     │
   │  /agent/token ──┼──────────► Signed URL endpoint     │
   └─────────────────┘          │                          │
                                │  Conversational AI       │
                                │  ┌────────────────────┐  │
                                │  │ Sofia agent         │  │
                                │  │ Gemini 2.0 Flash   │  │
                                │  │ FSI Compliance KB  │  │
                                │  │ 6 client tools     │  │
                                │  └────────────────────┘  │
                                └──────────────────────────┘
```

---

## Components

### Frontend — `front/Cockpit B.dc.html`

Single HTML file (~1,200 lines). No build step, no framework, no npm.

| Concern | Implementation |
|---|---|
| Reactivity | `dc` template engine — `DCLogic` class with `renderVals()` returning computed values, `setState()` triggers re-render |
| Routing | In-memory `state.route` string — `overview \| clients \| client \| conversations \| alerts \| opportunities \| allocation` |
| Styling | Inline styles with OKLCH CSS custom properties (`--bg`, `--ink`, `--green`, `--red`, `--amber`, `--blue`) |
| ElevenLabs | `@11labs/client` loaded via CDN ESM import; `Conversation.startSession()` in `toggleAgent` handler |
| Client tools | Plain async functions returned from `renderVals()`, passed to `Conversation.startSession({clientTools})` |
| Audio | `URL.createObjectURL(blob)` → `new Audio(url).play()` with volume mute/unmute via `_activeConv.setVolume()` |

**Key design decisions:**
- `dc` ternary expressions do not evaluate inside `style=""` attributes — display values must be pre-computed in `renderVals()` (e.g. `fabDisplay: S.chatOpen ? 'none' : 'flex'`)
- Form inputs (textarea) are set imperatively via `document.getElementById` + `setTimeout(60ms)` after state update, not reactively, to avoid cursor-reset on re-render
- Client state exposed via `window._cockpit = this` so tool closures can call `setState` from outside the render cycle

### Backend — `backend/main.py`

FastAPI application with 4 endpoints. Zero database, zero auth (demo only). All ElevenLabs calls use `urllib` stdlib — no SDK dependency.

```
POST /tts          TTSRequest(text, voice_id?) → StreamingResponse(audio/mpeg)
POST /stt          UploadFile(audio) → {transcript, words}
GET  /agent/token  → {signed_url, agent_id}
GET  /health       → {status, agent_id}
```

CORS is open (`allow_origins=["*"]`) for demo convenience.

### ElevenLabs Agent — Sofia

Created via `setup/create_agent.py` and configured via REST API.

| Parameter | Value | Rationale |
|---|---|---|
| Voice | Sarah (`EXAVITQu4vr4xnSDxMaL`) | Mature, confident — FSI appropriate |
| LLM | Gemini 2.0 Flash | Low latency, structured reasoning |
| Temperature | 0.4 | Consistent for financial context |
| Knowledge Base | FSI Compliance Guide v2.1 | Grounding for suitability rules |
| Context strategy | Book snapshot in system prompt | Zero tool-call latency for 95% of queries |
| Fallback | `get_client_data` client tool | Silent lookup for specific details |

---

## Data Flow — Voice Call

```
User taps phone button
        │
        ▼
toggleAgent() in DCLogic
        │
        ├─► fetch /agent/token
        │         │
        │         └─► ElevenLabs GET /convai/conversation/get_signed_url
        │                   │
        │                   └─► { signed_url: "wss://..." }
        │
        └─► Conversation.startSession({ signedUrl, clientTools })
                  │
                  └─► WebSocket opens to ElevenLabs
                            │
                            ├─► Sofia speaks first message (TTS streamed)
                            │
                            ├─► User speaks → STT → LLM → TTS response
                            │
                            └─► LLM calls client tool
                                      │
                                      ├─► navigate() → setState({route})
                                      ├─► show_opportunity() → setState({route:'client'})
                                      ├─► show_recommendation() → setState({approvalCard})
                                      ├─► generate_voice_message() → _addVoicePreview()
                                      │         └─► fetch /tts → blob URL saved in state
                                      ├─► send_whatsapp() → toast → suggests next
                                      └─► get_client_data() → reads _clientsById map
```

---

## Design Decisions

### Why a static HTML file instead of React/Vue?
The previous iteration used React + FastAPI + PostgreSQL — three services to maintain, build steps, and no meaningful advantage for a demo. The dc template engine provides reactive UI in a single file that's trivially deployed via nginx or any static host.

### Why a backend proxy instead of calling ElevenLabs directly from the browser?
- `/tts` and `/stt` require the API key, which cannot be exposed in client-side code
- `/agent/token` returns a time-limited signed URL so the conversation WebSocket never carries the raw API key to the browser

### Why embed the client book snapshot in the system prompt?
Tool calls add latency even when the tool itself is instant (LLM must process the result before generating tokens). Embedding ~2,400 chars of compact client data in the system prompt gives Sofia instant recall for 95% of questions. `get_client_data` remains as a silent fallback for edge cases.

### Why OKLCH colors?
Perceptually uniform color space — adjusting lightness is predictable across hues. All tokens use OKLCH so dark/light mode or tint adjustments need only change one value, not recompute hex combinations.

---

## Security Notes (demo only)

- API key is server-side only — never reaches the browser
- CORS is open — acceptable for a local demo, must be restricted in production
- `get_signed_url` tokens expire — the signed URL is single-use and short-lived
- WhatsApp send is mocked — no real message is sent
