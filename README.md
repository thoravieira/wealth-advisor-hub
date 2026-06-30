# Wealth Advisor Hub

Real-time voice cockpit for wealth advisors. Sofia, an AI advisor built on ElevenLabs Conversational AI, joins the session and can navigate the dashboard, pull up client profiles, draft and generate voice messages, and suggest next actions — all mid-conversation, through natural voice.

---

## Architecture

```mermaid
graph LR
    subgraph Browser["Browser"]
        UI["cockpit.html\ndc template engine"]
        SDK["@11labs/client\nWebSocket"]
    end

    subgraph Compose["Docker Compose Stack"]
        FRONT["front :8080\nnginx"]
        BACK["backend :8000\nFastAPI + psycopg2"]
        PG["postgres :5432\nPostgreSQL 16"]
        AN["analytics :8001\nDuckDB + FastAPI"]
    end

    subgraph ElevenLabs["ElevenLabs Cloud"]
        CONV["Conversational AI\nSofia · Gemini 2.0 Flash"]
        TTSAPI["TTS · Sarah voice"]
        STTAPI["STT · Scribe v2"]
        KB["Knowledge Base"]
    end

    Browser -->|"HTTP"| FRONT
    UI -->|"fetch :8000"| BACK
    SDK <-->|"WebSocket"| CONV
    BACK -->|"psycopg2"| PG
    BACK -->|"HTTP proxy"| AN
    BACK -->|"TTS/STT/token"| ElevenLabs
    CONV --- KB
```

**Stack:** nginx · FastAPI · PostgreSQL 16 · DuckDB · ElevenLabs (Conversational AI, TTS, STT)

| Container | Port | Purpose |
|---|---|---|
| `front` | 8080 | Static HTML cockpit via nginx |
| `backend` | 8000 | API gateway — ElevenLabs proxy + postgres integration |
| `postgres` | 5432 | Agent sessions, memory, advisor action log |
| `analytics` | 8001 | DuckDB lakehouse — client book, recommendations, alerts |

---

## What Sofia Can Do

| Action | Implementation |
|---|---|
| Navigate the cockpit | `navigate({route})` updates the dashboard view |
| Open a client panel | `show_opportunity({clientId})` routes to client detail |
| Show a recommendation | `show_recommendation({text})` opens an editable approval card |
| Generate a voice preview | `generate_voice_message({text})` calls `/tts`, saves playable card |
| Send via WhatsApp | `send_whatsapp({clientId})` confirms delivery (mock) |
| Look up client data | `get_client_data({clientId})` reads live cockpit state |
| Suggest next action | Built into system prompt, fires after every send |

```mermaid
sequenceDiagram
    actor Advisor
    participant UI as Cockpit UI
    participant Backend
    participant EL as ElevenLabs

    Advisor->>UI: Tap phone button
    UI->>Backend: GET /agent/token
    Backend->>EL: GET signed_url
    EL-->>UI: WebSocket URL
    UI->>EL: Connect (WebSocket)
    EL-->>Advisor: 🔊 "Good morning. Ricardo Tanaka needs action today..."

    Advisor->>EL: "Pull up Ricardo"
    EL->>UI: show_opportunity({ clientId: "ricardo" })
    UI->>UI: Client detail opens

    Advisor->>EL: "Draft a message for him"
    EL->>UI: show_recommendation({ text: "Ricardo, seu portfólio..." })
    UI->>UI: Editable approval card appears

    Advisor->>UI: Edits text → clicks Generate voice
    UI->>Backend: POST /tts
    Backend->>EL: TTS request
    EL-->>UI: MP3 audio
    UI->>UI: Playable VOICE card in side panel

    Advisor->>UI: Tap ▶ to preview
    UI->>EL: setVolume(0)
    UI->>UI: Audio plays → setVolume(1)

    Advisor->>EL: "Send it"
    EL->>UI: send_whatsapp({ clientId: "ricardo" })
    UI->>UI: Toast "Sent ✓"
    EL-->>Advisor: 🔊 "Sent. Next — Beatriz, suitability expires today..."
```

---

## Setup

### Prerequisites

- Docker + Docker Compose
- ElevenLabs account (free tier works)
- Agent created via `setup/create_agent.py`

### 1. Configure environment

```bash
cp .env.example .env
# add your ELEVENLABS_API_KEY
```

### 2. Create the ElevenLabs agent (run once)

```bash
ELEVENLABS_API_KEY=sk_... python setup/create_agent.py
# writes AGENT_ID, KB_ID, VOICE_ID to .env
```

### 3. Start

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Cockpit | http://localhost:8080/cockpit.html |
| Backend | http://localhost:8000/health |
| Analytics | http://localhost:8001/health |

---

## Project Structure

```
.
├── front/
│   ├── cockpit.html           # single-file cockpit (dc template engine)
│   ├── support.js             # dc runtime
│   ├── index.html             # redirect to cockpit.html
│   └── Dockerfile             # nginx
│
├── backend/
│   ├── main.py                # FastAPI: ElevenLabs proxy + postgres integration
│   ├── requirements.txt
│   └── Dockerfile
│
├── analytics/
│   ├── main.py                # DuckDB FastAPI: clients, recommendations, alerts
│   ├── seed.py                # 12 demo clients
│   ├── requirements.txt
│   └── Dockerfile
│
├── db/
│   └── init.sql               # PostgreSQL schema (sessions, memory, actions)
│
├── setup/
│   ├── create_agent.py        # idempotent ElevenLabs agent + KB setup
│   └── compliance_guide.txt   # FSI knowledge base content
│
├── tests/
│   ├── conftest.py
│   ├── test_01_backend_current.py    # 21 tests: health, TTS, STT, agent token
│   ├── test_02_frontend_current.py   # 11 tests: pages load, old filenames gone
│   ├── test_03_postgres.py           #  6 tests: schema, memory API
│   ├── test_04_analytics.py          # 32 tests: clients, recommendations, alerts
│   └── test_05_backend_pg_integration.py  # 13 tests: postgres integration, proxies
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── flows/
│   │   ├── SOFIA_FLOW.md
│   │   └── COCKPIT_FLOWS.md
│   └── specs/
│       └── SPEC-007-cockpit-v2.md
│
├── .env.example
├── docker-compose.yml
└── README.md
```

---

## Backend API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | `{status, agent_id, postgres, analytics}` |
| `GET` | `/agent/token` | ElevenLabs signed WebSocket URL; writes session to postgres |
| `POST` | `/tts` | `{text, voice_id?, client_id?}` → `audio/mpeg`; logs action |
| `POST` | `/stt` | audio file → `{transcript, words}` via Scribe v2 |
| `GET` | `/memory/long/{client_id}` | Facts Sofia learned about a client |
| `POST` | `/memory/long` | Save a fact to long-term memory |
| `GET` | `/actions` | Advisor action audit log |
| `GET` | `/clients[/{id}]` | Proxy to analytics service |

## Analytics API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/clients` | All 12 demo clients |
| `GET` | `/clients/{id}` | Single client profile |
| `GET` | `/clients/{id}/snapshots` | Portfolio time series |
| `GET/POST` | `/recommendations` | Recommendation lifecycle |
| `PATCH` | `/recommendations/{id}` | Update status (approved/sent) |
| `GET/POST` | `/voice-messages` | TTS message history |
| `GET` | `/alerts` | Risk and compliance alerts |

---

## ElevenLabs Agent

| | |
|---|---|
| Agent ID | `agent_7501kwap3zrre9wr5h20vdqbtz7n` |
| Voice | Sarah (`EXAVITQu4vr4xnSDxMaL`) |
| LLM | Gemini 2.0 Flash |
| STT | Scribe v2 |
| Knowledge Base | FSI Advisory Compliance Guide v2.1 |
| Client tools | navigate, show_opportunity, show_recommendation, generate_voice_message, send_whatsapp, get_client_data |

---

## Docs

- [Architecture](docs/ARCHITECTURE.md)
- [Sofia interaction flow](docs/flows/SOFIA_FLOW.md)
- [Cockpit navigation flows](docs/flows/COCKPIT_FLOWS.md)
- [Design spec (SPEC-007)](docs/specs/SPEC-007-cockpit-v2.md)
