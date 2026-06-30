# Architecture

## Overview

Four containers, one compose stack. The frontend and backend are independent services that can scale separately. Data lives in two purpose-built stores: PostgreSQL for operational/agent state, DuckDB for analytical queries on the client book.

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Browser                                                                 │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  front/cockpit.html                                              │   │
│  │  dc template engine · DCLogic class · @11labs/client SDK        │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│         │ fetch :8000              │ WebSocket (audio)                   │
└─────────┼──────────────────────────┼───────────────────────────────────┘
          │                          │
 ┌──────────────────────────────┐    │   ┌──────────────────────────────┐
 │  backend · :8000             │    │   │  ElevenLabs Cloud            │
 │  FastAPI + psycopg2          │    │   │                              │
 │                              │    └───►  Conversational AI (Sofia)   │
 │  /tts  ──────────────────────┼────────►  TTS API (Sarah · v3)       │
 │  /stt  ──────────────────────┼────────►  STT API (Scribe v2)        │
 │  /agent/token ───────────────┼────────►  Signed URL                 │
 │  /memory/long                │        │  Knowledge Base              │
 │  /actions                    │        └──────────────────────────────┘
 │  /clients (proxy) ───────┐   │
 └──────────┬───────────────┼───┘
            │               │
 ┌──────────▼──────┐  ┌─────▼────────────────┐
 │  postgres · :5432│  │  analytics · :8001    │
 │  PostgreSQL 16   │  │  DuckDB + FastAPI     │
 │                  │  │                       │
 │  agent_sessions  │  │  clients (12 seed)    │
 │  agent_memory_   │  │  portfolio_snapshots  │
 │    short / long  │  │  recommendations      │
 │  advisor_actions │  │  voice_messages       │
 └──────────────────┘  │  alerts_history       │
                        └───────────────────────┘
```

---

## Containers

### `front` — nginx · port 8080

Static HTML served via nginx. One file: `front/cockpit.html` (~1,200 lines). No build step, no npm, no framework.

| Concern | Implementation |
|---|---|
| Reactivity | `dc` template engine — `DCLogic` class, `renderVals()`, `setState()` |
| Routing | In-memory `state.route` string |
| Styling | Inline OKLCH custom properties (`--bg`, `--ink`, `--green`, `--red`, `--amber`, `--blue`) |
| ElevenLabs | `@11labs/client` CDN ESM; `Conversation.startSession()` in `toggleAgent` |
| Client tools | Plain async functions passed in `clientTools` dict |
| Audio preview | `URL.createObjectURL(blob)` + volume mute/unmute via `_activeConv.setVolume()` |

**Known dc quirks:**
- Ternary expressions don't evaluate inside `style=""` — pre-compute display values in `renderVals()`.
- Textarea `value` resets on re-render if bound reactively — set via `document.getElementById` + `setTimeout(60ms)`.

### `backend` — FastAPI · port 8000

API gateway. Keeps the ElevenLabs API key server-side. Integrates with postgres (sessions, memory, action log) and proxies client data from analytics.

| Endpoint | Purpose |
|---|---|
| `GET /health` | Reports status of backend, postgres, analytics |
| `GET /agent/token` | Returns ElevenLabs signed WebSocket URL; writes session to postgres |
| `POST /tts` | Text → MP3 via ElevenLabs TTS; logs `voice_generated` action |
| `POST /stt` | Audio → transcript via Scribe v2 |
| `GET /memory/long/{client_id}` | Reads Sofia's learned facts about a client |
| `POST /memory/long` | Persists a fact Sofia learned |
| `GET /actions` | Advisor action history (audit log) |
| `GET /clients[/{id}]` | Proxy to analytics service |
| `GET /internal/analytics-health` | Internal connectivity check |

### `postgres` — PostgreSQL 16 · port 5432

Operational state and agent memory. Schema in `db/init.sql`.

| Table | Purpose |
|---|---|
| `agent_sessions` | One row per Sofia voice session; stores ElevenLabs conversation_id |
| `agent_memory_short` | Conversation turns during a session (expires with session) |
| `agent_memory_long` | Facts Sofia learns about clients across sessions |
| `advisor_actions` | Audit log — every approved recommendation, voice generated, message sent |

### `analytics` — DuckDB · port 8001

Lakehouse service for the client book. DuckDB embedded in a FastAPI microservice; tables stored on a named Docker volume (`lake_data`).

| Table | Purpose |
|---|---|
| `clients` | 12 demo client profiles (seed data mirrors hardcoded frontend data) |
| `portfolio_snapshots` | Point-in-time portfolio state (Iceberg-compatible time travel) |
| `recommendations` | Full lifecycle: draft → approved → sent |
| `voice_messages` | TTS-generated messages with status |
| `alerts_history` | Risk and compliance alert history |

---

## Data Flow — Voice Call

```
Advisor taps phone button
        │
        ▼
toggleAgent() in DCLogic
        │
        ├─► GET /agent/token
        │     │
        │     ├─► ElevenLabs: GET /convai/conversation/get_signed_url
        │     └─► Postgres: INSERT INTO agent_sessions
        │
        └─► Conversation.startSession({ signedUrl, clientTools })
              │
              └─► WebSocket opens to ElevenLabs
                    │
                    ├─► Sofia speaks opening (TTS streamed over WS)
                    │
                    ├─► Advisor speaks → STT → LLM → TTS response
                    │
                    └─► LLM calls a client tool
                          │
                          ├─► navigate()               → setState({route})
                          ├─► show_opportunity()        → setState({route:'client', clientId})
                          ├─► show_recommendation()     → setState({approvalCard}), sets textarea
                          ├─► generate_voice_message()  → POST /tts → voice card in side panel
                          │     └─► Postgres: advisor_actions (voice_generated)
                          ├─► send_whatsapp()           → toast + next suggestion
                          └─► get_client_data()         → reads _clientsById JS map (silent)
```

---

## Design Decisions

### Why separate front and backend containers?
Each can scale independently. The frontend is stateless — a CDN or multiple nginx replicas need no coordination. The backend holds ElevenLabs credentials and database connections; scaling it horizontally would need session-aware routing (or stateless redesign), but keeping it separate makes that upgrade path clear.

### Why DuckDB for the lakehouse instead of a second PostgreSQL?
DuckDB is an OLAP engine — it reads columnar data faster than PostgreSQL for analytical queries (portfolio aggregations, full-book risk scans, time-series returns). The Iceberg table format adds time travel: querying what a client's portfolio looked like on a specific date. PostgreSQL handles transactional writes; DuckDB handles reads and reporting.

### Why embed the client book snapshot in Sofia's system prompt?
Tool calls add ~200–500ms of latency even when the underlying lookup is instant (the LLM must stop generating, invoke the tool, and resume). Embedding ~2,400 chars of compact client summaries in the system prompt gives Sofia zero-latency recall for 95% of questions. `get_client_data` stays as a silent fallback for edge cases.

### Why a backend proxy for /clients instead of the frontend calling analytics directly?
Single origin for the frontend. The advisor's browser talks to one backend; the backend decides whether to serve from postgres, DuckDB, or cache. This also keeps the analytics service off the public internet in production.

### Why OKLCH colors?
Perceptually uniform — lightness adjustments are predictable across hues. Tint and dark/light mode changes touch one token, not hex combinations.

---

## Security Notes (demo scope)

- ElevenLabs API key is server-side only — never reaches the browser
- `get_signed_url` tokens are single-use and short-lived
- CORS is open (`allow_origins=["*"]`) — must be restricted in production
- WhatsApp send is mocked — no real message leaves the system
- No authentication — anyone with the URL can use the cockpit
