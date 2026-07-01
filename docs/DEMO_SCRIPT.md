# Demo Script — sofIA Cockpit
**Duration:** ~7 minutes  
**Scenario:** Thiago, senior wealth advisor, opens the cockpit on Monday morning before 9am. Markets open in 45 minutes. He has 45 clients in his book.

---

## Prep

1. Open `http://localhost:8080/cockpit.html`
2. Make sure the Overview screen is showing (default)
3. Use headphones — Sofia's voice is part of the demo
4. Click the `···` button (bottom-right corner) → click the phone icon to connect Sofia

---

## ACT 1 — Good morning, the book is waiting
_~90 seconds_

**[Sofia opens the session unprompted — she speaks first]**

> **Sofia:** "Good morning Thiago. I went through your book. Three things need you today: Ricardo Tanaka is showing withdrawal intent with equity at 71% — baby's arriving in September and he wants to de-risk. Fernando Costa has a compliance flag that's been open for six weeks. And Beatriz Oliveira's suitability document expires this week. Where do you want to start?"

**[The screen already shows the Overview with At risk / Opportunities / Pending / Awaiting cards]**

---

**Thiago:** "Start with Ricardo."

**[Sofia calls `open_client({ clientName: "Ricardo" })` — Ricardo Tanaka's panel opens automatically]**

> **Sofia:** "Ricardo Tanaka, VIP client since 2018. R$ 12.8 million, aggressive profile. Equity is at 71% — above his 55% target. He called last week worried about the market. He's having a baby in September and wants to pull back."

---

## ACT 2 — The real call, the transcript, the message
_~2 minutes_

**[Ricardo is open. The carousel shows Jun 14 selected. The custom audio player is visible]**

**Thiago:** "Play the Jun 14 call."

**[Presenter clicks the play button. Audio starts. The waveform bars advance. The transcript highlights the line being spoken in real time]**

> **[~15 seconds of audio]** — Ricardo's voice, worried about the baby; advisor proposing to trim from 71% to 55%

**Thiago:** _(pauses audio)_ "Got it. Draft me a message to send him."

> **Sofia:** "On it."

**[Sofia calls `show_recommendation({ clientId: "ricardo", text: "..." })` — the approval card appears with pre-filled text]**

> **Sofia:** "Something like: 'Ricardo, good morning. Following our call — I've prepared the rebalancing plan we discussed. I'll trim equity from 71 to 55%, building your 12-month Tesouro Selic reserve. Sending the full breakdown to your email today. No action needed from you yet.' Want me to adjust the tone?"

**Thiago:** "Shorter. Remove the last sentence."

**[Thiago edits the text in the approval card]**

**Thiago:** "Generate the voice."

**[Generate voice fires POST /tts → Sarah's voice reads the message — Thiago hears the preview]**

**Thiago:** "Send it."

> **Sofia:** "Sent to Ricardo via WhatsApp. Next — Fernando Costa has had a compliance flag open for six weeks. His equity is at 71%, same as Ricardo, but he's been pushing back on rebalancing. Want me to pull up his profile?"

---

## ACT 3 — The compliance radar
_~90 seconds_

**Thiago:** "Show me the alerts first."

**[Sofia calls `navigate({ route: "alerts" })` — screen switches to Alerts]**

> **Sofia:** "Five active alerts. Two equity concentration flags — Fernando and André Lima, both at 71% and 74%. One suitability expiry — Beatriz Oliveira, document expires this Friday. Two withdrawal signals — Ricardo and André."

**[Screen shows the alert list grouped by type]**

**Thiago:** "Fernando's been dragging this for six weeks. Pull him up."

**[Sofia calls `open_client({ clientName: "Fernando" })` — Fernando Costa opens]**

> **Sofia:** "Fernando Costa, VIP, R$ 23 million, aggressive. Equity at 71% against a 60% policy band. He knows. He's been saying performance justifies the concentration. I documented three conversations where he refused to rebalance. The committee was formally notified last week."

**Thiago:** "Draft a formal notification for him."

> **Sofia:** "Fernando, following our conversation on Jun 10 — your equity position remains at 71%, above our agreed 60% band. Regulatory compliance requires we formalize this in writing. I'm requesting your decision on the rebalancing proposal by June 30th. Let me know how you'd like to proceed."

**[Approval card appears]**

**Thiago:** "Good. I'll review before sending. Now Beatriz."

**[Sofia calls `open_client({ clientName: "Beatriz" })` — Beatriz Oliveira opens]**

> **Sofia:** "Beatriz Oliveira, R$ 8.5 million, moderate profile. Suitability document expires this Friday — June 30. I suggest we reach out today to schedule the renewal. She's been with you since 2020, conservative investor nearing retirement. Tone should be reassuring."

**Thiago:** "Generate a message for her."

> **Sofia:** "Beatriz, I hope you're well. Your investor profile review is due this week — it's a routine annual update that takes about 20 minutes. Would Thursday morning work for a quick call? I'll have everything prepared. This keeps us aligned on your goals and fully compliant."

**Thiago:** "Perfect. Voice and send."

---

## ACT 4 — The opportunity of the month
_~60 seconds_

**Thiago:** "Show me opportunities."

**[Sofia calls `navigate({ route: "opportunities" })` — screen switches to Opportunities]**

> **Sofia:** "Two active opportunities this month. Otávio Mendes — R$ 500k inflow confirmed for July 15th, infrastructure fund window closes June 30th. Mariana Castro — she's eligible for a pension product migration, been awaiting response for four days."

**Thiago:** "Otávio. What's the play?"

**[Sofia calls `open_client({ clientName: "Otávio" })` — Otávio Mendes opens]**

> **Sofia:** "Otávio Mendes, VIP, R$ 7.6 million, mod-aggressive. The inflow is 500k on July 15th. I'd suggest 30% into the infrastructure credit fund at CDI plus 3.2% — entry closes June 30th. He already expressed interest in the last call. You have a week to confirm."

**[Click Jun 9 in the carousel — the audio player appears with the transcript from that conversation]**

**Thiago:** "He mentioned it here?"

> **Sofia:** "Yes — turn three. He called CDI plus 3.2% 'very attractive' and asked specifically about the entry window."

**[The transcript highlights turn 3: "Very attractive. I have R$80k idle. Can I enter now?"]**

**Thiago:** "Book a call for this week. Send him the proposal first."

> **Sofia:** "On it. Generating the voice message for Otávio now."

---

## ACT 5 — Close the loop
_~45 seconds_

**Thiago:** "How's the rest of the book looking today?"

**[Sofia calls `navigate({ route: "clients" })` — screen goes to Clients with the full table]**

> **Sofia:** "Twelve clients covered this morning. Three actions sent — Ricardo, Beatriz, and the Fernando notification drafted. One recommendation pending your approval for Fernando. Otávio's call queued. The rest of the book is green — healthy allocation, no flags. You've cleared the three priorities before the market opens."

**[Screen shows the Clients table with Last Contact, AUM, Perf, Risk columns]**

**Thiago:** "Good morning."

> **Sofia:** "Good morning, Thiago."

---

## Key moments to highlight for the audience

| Moment | What it demonstrates |
|---|---|
| Sofia opens the session unprompted | Proactivity — she read the book, didn't wait to be asked |
| "Pull up Ricardo" → screen changes | Voice navigation — zero clicks |
| Audio player + synchronized transcript | Real conversations, not notes — ElevenLabs STT |
| "Draft me a message" → card appears | Editable AI draft — advisor stays in control before anything sends |
| "Generate voice" → Sarah previews it | Personalized TTS — client hears a natural voice, not a robot |
| 5 alerts surfaced without a query | Continuous monitoring across the entire book |
| 7 minutes = 3 clients handled | Scale — what would take a morning happens before 9am |

---

## Alternative phrases to test (Sofia understands all of these)

```
"Open Fernando"
"Go to alerts"
"What's André's allocation?"
"List all my VIP clients"
"Show me Otávio's recommendations"
"Switch to transcript"
"Send it to Ricardo"
"Edit the message — make it shorter"
```

---

## Quick troubleshooting

| Issue | Fix |
|---|---|
| Sofia won't connect | Check backend is running on `:8000`; hit `/health` |
| Audio player doesn't load | Analytics must be on `:8001`; `GET /audio/ricardo_20260614.mp3` should return 200 |
| Transcript doesn't appear | Wait for `/conversations/{id}` fetch to complete (~500ms) |
| Sofia doesn't navigate | The `agent_id` in `.env` must match the agent with the updated tools |
