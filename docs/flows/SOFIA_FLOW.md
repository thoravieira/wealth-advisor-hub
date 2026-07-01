# Flow — Sofia Voice Interaction

The core feature of the cockpit: the advisor has a real-time voice conversation with Sofia, who can read client data, navigate the dashboard, and draft messages for approval — all mid-conversation.

---

## Sequence Diagram

```mermaid
sequenceDiagram
    actor Advisor as Advisor (Thiago)
    participant UI as Cockpit UI
    participant Backend as Backend API
    participant EL as ElevenLabs Cloud
    participant Sofia as Sofia (AI Agent)

    Note over Advisor,Sofia: Session Start

    Advisor->>UI: Taps EQ icon → opens side panel
    Advisor->>UI: Taps phone button
    UI->>Backend: GET /agent/token
    Backend->>EL: GET /convai/conversation/get_signed_url
    EL-->>Backend: { signed_url: "wss://..." }
    Backend-->>UI: { signed_url, agent_id }
    UI->>EL: WebSocket connect (signed_url)
    EL->>Sofia: Session initialized
    Sofia-->>Advisor: 🔊 "Good morning Thiago. I went through your book..."

    Note over Advisor,Sofia: Navigation Tool

    Advisor->>Sofia: "Show me the clients"
    Sofia->>UI: navigate({ route: "clients" })
    UI->>UI: setState({ route: "alerts" })
    Note right of UI: Dashboard switches to Alerts view
    Sofia-->>Advisor: 🔊 "Here are today's alerts..."

    Note over Advisor,Sofia: Client Detail Tool

    Advisor->>Sofia: "Pull up Ricardo's profile"
    Sofia->>UI: open_client({ clientName: "Ricardo" })
    UI->>UI: setState({ route: "client", clientId: "ricardo" })
    Note right of UI: Ricardo Tanaka detail panel opens
    Sofia-->>Advisor: 🔊 "Ricardo's at 71% equity, above his threshold..."

    Note over Advisor,Sofia: Data Lookup (silent fallback)

    Advisor->>Sofia: "What's his exact fixed income allocation?"
    Sofia->>UI: get_client_data({ clientId: "ricardo" })
    UI-->>Sofia: { allocation: { fixedIncome: "14%", ... } }
    Note over Sofia: Tool returns instantly (in-memory JS read)
    Sofia-->>Advisor: 🔊 "Fixed income is at 14%..."

    Note over Advisor,Sofia: Recommendation Card

    Advisor->>Sofia: "What do you recommend?"
    Sofia->>UI: show_recommendation({ clientId: "ricardo", text: "Ricardo, your portfolio..." })
    UI->>UI: setState({ approvalCard: text })
    Note right of UI: Approval card overlay appears with editable textarea
    Sofia-->>Advisor: 🔊 "I've put a draft on screen — feel free to edit it."

    Note over Advisor,Sofia: Voice Message Generation

    Advisor->>UI: Edits text in textarea
    Advisor->>UI: Clicks "Generate voice"
    UI->>Backend: POST /tts { text: editedText }
    Backend->>EL: POST /v1/text-to-speech/EXAVITQu4vr4xnSDxMaL
    EL-->>Backend: audio/mpeg stream
    Backend-->>UI: MP3 blob
    UI->>UI: Creates blob URL → adds VOICE card to transcript panel
    Note right of UI: Approval card closes, VOICE card appears in side panel

    Note over Advisor,Sofia: Preview Playback (agent muted)

    Advisor->>UI: Clicks ▶ on VOICE card
    UI->>EL: setVolume({ volume: 0 })  [mute agent output]
    UI->>UI: new Audio(url).play()
    Note right of UI: Preview plays without Sofia interrupting
    UI->>UI: audio.onended → setVolume({ volume: 1 }) [unmute]

    Note over Advisor,Sofia: Send & Next Suggestion

    Advisor->>Sofia: "Sounds good, send it"
    Sofia->>UI: send_whatsapp({ clientId: "ricardo" })
    UI->>UI: setState({ toastMsg: "Sent via WhatsApp ✓" })
    Note right of UI: Toast appears for 3.5s
    Sofia-->>Advisor: 🔊 "Sent. Next — Beatriz, suitability expires today..."

    Note over Advisor,Sofia: Session End

    Advisor->>UI: Taps red × button
    UI->>EL: conversation.endSession()
    UI->>UI: setState({ agentStatus: "idle", agentTranscript: [] })
    Note right of UI: Side panel returns to phone button (idle state)
```

---

## State Machine — Agent Status

```mermaid
stateDiagram-v2
    [*] --> idle: Page loads
    idle --> connecting: Tap phone button
    connecting --> connected: WebSocket open + Sofia speaks
    connecting --> idle: Error / timeout
    connected --> idle: Tap × button\nor session ends
    connected --> connected: Tool call\nor transcript update
```

---

## Client Tool Registry

| Tool | Trigger | UI effect | Returns |
|---|---|---|---|
| `navigate` | "Go to X" | Route changes — overview, clients, alerts, opportunities, allocation | `"navigated to X"` |
| `open_client` | "Pull up [client]" | Client detail panel opens (by name or ID) | `"opened client X"` |
| `open_client_tab` | "Switch to recommendations" | Left panel tab switches — overview or recommendations | `"switched to tab X"` |
| `open_conversation_tab` | "Show transcript" | Right panel tab switches — transcript, summary, messages | `"switched tab to X"` |
| `list_clients` | "Who are your clients?" | Silent read | JSON array of {id, name, aum} |
| `get_client_data` | Any specific data question | Reads `_clientsById` JS map silently | JSON client object |
| `show_opportunity` | Legacy alias for open_client | Client detail panel opens | `"opened client X"` |
| `show_recommendation` | Sofia drafts a message | Approval card with editable textarea | `"recommendation shown"` |
| `edit_recommendation` | "Edit the message" | Approval card opens with current text for editing | `"editing recommendation"` |
| `generate_voice_message` | Agent-initiated TTS | Calls `/tts`, saves playable VOICE card | `"voice message generated"` |
| `send_whatsapp` | After advisor approves | Toast "Sent via WhatsApp ✓", clears card | `"sent via whatsapp"` |

---

## Voice Preview UX Detail

```mermaid
flowchart LR
    A[Approval card\nappears] --> B[Advisor edits\ntextarea]
    B --> C[Click Generate voice]
    C --> D[POST /tts]
    D --> E[Blob URL created]
    E --> F[VOICE card\nin side panel]
    F --> G{Tap ▶}
    G --> H[Agent output muted]
    H --> I[Audio plays]
    I --> J[Audio ends]
    J --> K[Agent output restored]
    K --> L[Advisor responds\nto Sofia]
    L --> M{Approved?}
    M -->|Yes| N[say send it]
    M -->|No| O[say edit or regenerate]
    N --> P[send_whatsapp tool]
    P --> Q[Toast ✓ + next suggestion]
```
