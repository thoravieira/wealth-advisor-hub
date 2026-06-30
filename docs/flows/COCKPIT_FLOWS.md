# Flow — Cockpit UI Navigation & Features

Overview of all screens, how to reach them, and what actions are available on each.

---

## Navigation Map

```mermaid
flowchart TD
    START([Open cockpit]) --> OV[Overview\nAction center]

    OV -->|Click client card| CD[Client Detail]
    OV -->|Sidebar: Conversations| CO[Conversations]
    OV -->|Sidebar: Alerts| AL[Alerts]
    OV -->|Sidebar: Opportunities| OP[Opportunities]
    OV -->|Sidebar: Allocation| AC[Allocation]

    CO -->|Click row| CD
    AL -->|Click Review| CD
    OP -->|Click Open| CD

    CD -->|← Back button| OV
    CD -->|← Back button| CO
    CD -->|← Back button| AL
    CD -->|← Back button| OP

    subgraph Sofia["Sofia (available on all screens)"]
        FAB[EQ icon FAB] --> SP[Side panel opens]
        SP --> CALL[Phone button → voice call]
        CALL --> TOOLS[Client tools control any screen]
    end
```

---

## Screen: Overview

**Purpose:** At-a-glance action center — what needs the advisor now.

```mermaid
flowchart LR
    OV[Overview] --> S1[4 stat tiles\nClients · Alerts · Opps · AUM]
    OV --> S2[4 group cards\nAt risk · Opportunities\nPending · Awaiting]
    S2 --> C1[Click client name]
    C1 --> CD[Client Detail\nprevRoute = overview]
```

**Stat tiles:**
| Tile | Description |
|---|---|
| Clients | Total book size (45) |
| Alerts | Active compliance/risk flags |
| Opportunities | Open revenue moments |
| AUM | Total assets under management |

**Group cards:**
| Group | Clients shown |
|---|---|
| At risk | Withdrawal intent, concentration above limit |
| Opportunities | Expected inflows, life events |
| Pending | Approvals, suitability renewals needed |
| Awaiting | Proposals sent, no client response |

---

## Screen: Client Detail

**Purpose:** Full profile of one client — allocation, last conversation, transcript, compliance flags, recommendations.

```mermaid
flowchart TD
    CD[Client Detail] --> H[Header: name · VIP badge · status dot · AUM · MTD]
    CD --> A[Allocation bar\nEQ / FI / Funds / Cash]
    CD --> S[Suitability / objectives / risk appetite]
    CD --> LC[Last conversation\nDate · channel · sentiment score]
    LC --> T{Tabs}
    T --> TR[Transcript\nauto-transcribed by ElevenLabs]
    T --> MS[Messages\nSuggested voice messages]
    CD --> REC[Recommendations\npending approval]
    CD --> BACK[← Back → previous screen]
```

**Back button** routes to `prevRoute` — the screen that opened this client (overview, conversations, alerts, opportunities). Set at click time so the return is always correct.

---

## Screen: Conversations

**Purpose:** Full log of recorded client interactions, transcribed by ElevenLabs.

```mermaid
flowchart LR
    CO[Conversations] --> SOFIA[Sofia panel\nidle → voice call → transcript]
    CO --> F[Filters: All · Calls · WhatsApp · Email]
    CO --> T[Table: client · channel · date · duration · sentiment · status]
    T --> ROW[Click row]
    ROW --> CD[Client Detail\nprevRoute = conversations]
```

**Sofia panel** (top of this screen):
- Idle: status dot + hint text + phone button
- Active: live transcript + red end-call button

---

## Screen: Alerts

**Purpose:** Risk, compliance, and behavioral signals across the full book.

```mermaid
flowchart LR
    AL[Alerts] --> CAT{Category}
    CAT --> C1[Compliance risk\nEquity above profile limit]
    CAT --> C2[Suitability expiry\nDoc renewal needed]
    CAT --> C3[Withdrawal signals\nBehavioral indicators]
    CAT --> C4[Portfolio drift\nAllocation off policy]
    C1 & C2 & C3 & C4 --> BTN[Review button]
    BTN --> CD[Client Detail\nprevRoute = alerts]
```

---

## Screen: Opportunities

**Purpose:** Revenue moments — inflows, life events, engagement triggers.

```mermaid
flowchart LR
    OP[Opportunities] --> ROW[Opportunity row\nclient · value · type · probability]
    ROW --> BTN[Open button]
    BTN --> CD[Client Detail\nprevRoute = opportunities]
```

**Opportunity types:** Expected inflow · Portfolio rebalance · Product migration · Life event (birthday, retirement) · Suitability renewal

---

## Screen: Allocation

**Purpose:** Book-level allocation overview and off-policy positions.

```mermaid
flowchart TD
    AC[Allocation] --> SUM[Book summary\nTotal AUM · RV% · RF% · Funds% · Cash%]
    AC --> BAR[Asset class bars\nwith target vs actual]
    AC --> OFF[Off-policy clients\ncurrent vs target allocation · drift]
    OFF --> CL[Click client name]
    CL --> CD[Client Detail]
```

---

## FAB → Sofia Panel Flow

The floating action button (EQ bars animation) is always visible, on every screen.

```mermaid
flowchart TD
    FAB[EQ icon\ncorner bottom-right] -->|Click| OPEN{Panel open?}
    OPEN -->|No| SHOW[Side panel slides in\nFAB hides]
    OPEN -->|Yes| HIDE[Panel closes\nFAB returns]

    SHOW --> STATUS{Agent status}
    STATUS -->|idle| IDLE[Phone button\npowered by ElevenAgent hint]
    STATUS -->|connecting| CONN[Amber button\nConnecting…]
    STATUS -->|connected| LIVE[Transcript\nRed end-call button]

    IDLE -->|Tap phone| START[Start voice session]
    LIVE -->|Tap ×| END[End voice session]
```

---

## Language Toggle

All UI strings exist in English and Portuguese. Toggle in the sidebar header switches instantly — no reload, no API call. Sofia's conversation remains in English (agent language setting).

---

## Feature Matrix by Screen

| Feature | Overview | Conversations | Client Detail | Alerts | Opportunities | Allocation |
|---|---|---|---|---|---|---|
| Sofia voice call | ✓ | ✓ (primary) | ✓ | ✓ | ✓ | ✓ |
| Navigate here via Sofia | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Client list | ✓ (grouped) | ✓ (table) | — | ✓ | ✓ | ✓ |
| Open client detail | ✓ | ✓ | — | ✓ | ✓ | ✓ |
| Approval card overlay | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Voice preview player | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Language toggle | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
