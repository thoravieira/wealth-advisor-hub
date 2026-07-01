# SPEC-008 — Real Conversations, Audio Generation & Data Alignment

**Status:** Implemented  
**Author:** Thiago da Hora  
**Date:** 2026-06-30  
**Implementation:** `analytics/main.py` · `analytics/seed_conversations.py` · `front/cockpit.html` · `audio/`

---

## 1. Problem Statement

The cockpit currently shows static, hardcoded conversation data in `cockpit.html`. This means:
- Conversations cannot be maintained or extended without editing the HTML
- No alignment between conversations and the alerts/opportunities/recommendations shown
- No real audio — the player is a visual mock with no actual MP3
- The date carousel shows only one date per client, not a real history

This spec defines:
1. A conversation data model stored in the DuckDB analytics service
2. Narrative design for all 12 clients (5+ conversations each)
3. Generation of 2 real audio files (Ricardo Jun 14 + Otávio Jun 9) simulating 2-person calls
4. API endpoints for conversations and audio streaming
5. Frontend integration to fetch and render conversations dynamically
6. Full alignment between conversations and what is shown in alerts, opportunities, and recommendations

---

## 2. Narrative Design

### 2.1 Client Profiles Summary

| Client | Profile | Status | Story Arc |
|---|---|---|---|
| Ricardo Tanaka | Aggressive → Moderate | at_risk | Baby coming → risk aversion → rebalancing |
| Fernando Costa | Aggressive (compliance) | attention | Equity concentration → repeated policy breaches |
| Helena Vasconcelos | Moderate | awaiting | Conservative → opening to multimercado |
| Otávio Mendes | Mod-Aggressive | opportunity | Consistent inflows → strategic allocation |
| Beatriz Almeida | Conservative | pending | Near retirement → suitability expiry |
| Lúcia Prado | Moderate | opportunity | Satisfied → cross-sell pension |
| Gustavo Reis | Aggressive | pending | Rebalance blocked → governance problem |
| André Lima | Mod-Aggressive | attention | Equity drift → policy breach |
| Camila Rezende | Conservative | awaiting | Pension migration decision |
| Paulo Esteves | Moderate | ok | Routine healthy client |
| Tereza Bittencourt | Moderate | ok | Routine healthy client |
| Sofia Marques | Conservative | ok | New client, onboarding phase |

---

### 2.2 Conversation Narratives

#### RICARDO TANAKA — Arc: Baby → Risk Aversion → Rebalancing

**Conv 1 — 2026-06-14 — Phone call (08:32) — Negative sentiment**  
*Baby's coming, I need security*  
Ricardo calls alarmed after IBOVESPA drops 2.1%. With the baby arriving in 3 months he wants to reduce equity exposure. Advisor proposes reducing from 71% → 55%, building 12-month emergency reserve in Tesouro Selic. Ricardo agrees and asks for a written plan.  
→ **Triggers alert**: Withdrawal intent  
→ **Triggers opportunity**: Emergency reserve (Tesouro Selic R$770k)  
→ **Triggers recommendation**: "Ricardo, sua carteira valorizou 2,3%..."

**Conv 2 — 2026-06-09 — WhatsApp — Neutral sentiment**  
*IBOVESPA flash crash*  
Ricardo sends message worried about a sudden 1.8% intraday drop. Advisor responds: portfolio within limits, no action needed today. Mentions the upcoming review call scheduled for Jun 14.

**Conv 3 — 2026-05-28 — Phone call (12:15) — Neutral sentiment**  
*Q2 review — first mention of baby*  
Routine quarterly review. Ricardo's portfolio up +2.3% YTD. First time he mentions the baby is coming. Says "we'll need to revisit the plan." No action yet, advisor notes the signal.

**Conv 4 — 2026-05-15 — Email — Neutral sentiment**  
*Suitability renewal sent*  
Advisor sends updated suitability questionnaire. Ricardo's responses show lower risk tolerance than his current aggressive profile. Flags profile change assessment for next meeting. Ricardo acknowledges by email.

**Conv 5 — 2026-04-30 — Phone call (09:04) — Positive sentiment**  
*Strong Q1 results — wants more equities*  
Ricardo is happy with Q1 +8.2% returns. Asks about increasing equity allocation. Advisor notes current 71% is already near policy band and logs the conversation. Last conversation before the risk signal develops.

---

#### FERNANDO COSTA — Arc: Concentration → Compliance → Formal Warning

**Conv 1 — 2026-06-10 — Phone call (12:04) — Neutral sentiment**  
*"I won't reduce equities — they're performing"*  
Compliance flag triggered: equity at 71%, above agreed 60% band. Fernando pushes back, says performance justifies the concentration. Advisor explains regulatory obligation. Fernando agrees to "review" but not act. Formal documentation issued.  
→ **Triggers alert**: Compliance flag / equity concentration

**Conv 2 — 2026-06-05 — WhatsApp — Negative sentiment**  
*Wants to add R$500k in tech stocks*  
Fernando asks advisor to add a tech position (would push equity to 74%). Advisor declines via WhatsApp citing policy, proposes an alternative in multimarket. Fernando responds: "talk later."

**Conv 3 — 2026-05-20 — Phone call (10:30) — Neutral sentiment**  
*Second compliance review — six weeks post-breach*  
Equity still at 71% after six weeks. Portfolio committee formally notified. Advisor walks Fernando through the options: trim equities or file a policy exception. Fernando says he'll "think about it."

**Conv 4 — 2026-05-10 — Email — Neutral sentiment**  
*Portfolio drift report Q1*  
Quarterly drift analysis: Fernando's equity drifted from agreed 60% target to 68% over Q1 (bull market). First formal documentation of the breach. Advisor sent proposed rebalancing plan.

**Conv 5 — 2026-04-25 — Phone call (14:20) — Positive sentiment**  
*"Move all fixed income to equities"*  
Fernando calls bullish after a strong Q1. Wants to liquidate his entire fixed income position (18%) and go 100% equities. Advisor declines, negotiates to 71% max, documents the conversation. This is when the current concentration was established.

---

#### HELENA VASCONCELOS — Arc: Conservative → Opening to Multimercado

**Conv 1 — 2026-06-12 — WhatsApp — Neutral sentiment**  
*Reviewing your reallocation proposal*  
Advisor had sent proposal to move 10% from fixed income to multimarket funds (CDI+1.8% projected). Helena is reviewing and says she'll have an answer by Friday.

**Conv 2 — 2026-06-08 — Email — Neutral sentiment**  
*Reallocation proposal: RF → Multimercado*  
Advisor sends detailed proposal with 3-year projection. Current: 100% RF yielding CDI+0.9%. Proposed: 10% in multimercado, projecting blended CDI+1.4%. Helena acknowledges receipt.

**Conv 3 — 2026-05-30 — Phone call (15:45) — Neutral sentiment**  
*"What exactly are multimarket funds?"*  
Helena asks for a deep-dive on multimercado before deciding. Advisor explains structure, historical performance, liquidity terms. Helena is warmer to the idea but wants to verify with her accountant.

**Conv 4 — 2026-05-22 — WhatsApp — Positive sentiment**  
*"How are my funds this month?"*  
Helena asks about May MTD performance. Advisor responds: +0.4%, in line with CDI. Helena satisfied. Briefly mentions she may be open to "something slightly better."  
→ **Triggers opportunity**: Multimercado migration

**Conv 5 — 2026-05-15 — Phone call (11:00) — Neutral sentiment**  
*Annual review — five years as client*  
Annual portfolio review. Helena satisfied with conservative approach but notes fixed income real returns are compressed. Advisor identifies the opportunity for multimarket diversification and schedules a proposal follow-up.

---

#### OTÁVIO MENDES — Arc: Inflow Planning → Strategic Allocation

**Conv 1 — 2026-06-09 — Phone call (06:18) — Positive sentiment**  
*R$500k inflow — allocation plan*  
Otávio confirms July 15 inflow of R$500k. Advisor presents plan: 50% equities (IBOV ETF + tech), 30% infra credit fund (CDI+3.2%), 20% multimarket. Otávio approves in principle, asks for written plan.  
→ **Triggers opportunity**: New infra credit fund allocation  
→ **Triggers recommendation**: "Otávio, tudo pronto pro aporte de julho..."

**Conv 2 — 2026-06-02 — WhatsApp — Positive sentiment**  
*"Inflow confirmed July 15, R$500k"*  
Otávio sends quick confirmation of the inflow date and amount. Asks about the infrastructure fund subscription window.

**Conv 3 — 2026-05-28 — Phone call (09:12) — Positive sentiment**  
*"Tell me about this infra credit fund"*  
Advisor proactively calls about a new infrastructure credit fund. CDI+3.2% projected, subscription closes Jun 30. Otávio very interested. Decides to wait for July inflow rather than using current cash.

**Conv 4 — 2026-05-20 — WhatsApp — Neutral sentiment**  
*"R$28k dividends received — reinvest?"*  
Otávio receives dividends from his equity portfolio. Asks whether to reinvest or keep as cash. Advisor recommends reinvesting in the fixed income sleeve given current yield curve.

**Conv 5 — 2026-05-10 — Phone call (14:00) — Positive sentiment**  
*Q2 review — portfolio up +2.3%*  
Q2 review. Portfolio at R$7.6M, up +2.3%. Otávio very happy. Discusses Q3 strategy. First mention of July inflow. Strong client relationship signal.

---

#### BEATRIZ ALMEIDA — Arc: Near-Retirement → Suitability Urgency

**Conv 1 — 2026-06-11 — Email — Neutral sentiment**  
*Suitability assessment expires Jun 30 — urgent renewal*  
Advisor sends urgent notice: suitability expires in 19 days. If not renewed, Beatriz cannot trade or rebalance. Requests appointment before Jun 30.  
→ **Triggers alert**: Suitability expiry (High)

**Conv 2 — 2026-06-07 — WhatsApp — Neutral sentiment**  
*"When can we schedule the renewal?"*  
Beatriz asks to schedule the suitability call. She's in exam season at school and has limited availability. They tentatively set Jun 25.

**Conv 3 — 2026-05-28 — Phone call (16:00) — Neutral sentiment**  
*"Should I stay conservative given low real returns?"*  
Beatriz questions whether conservative profile makes sense given compressed real returns on fixed income. Advisor explains the retirement timeline (2 years) and capital preservation rationale. Beatriz confirms conservative profile.

**Conv 4 — 2026-05-20 — WhatsApp — Positive sentiment**  
*"+3.4% YTD — am I on track for retirement?"*  
Beatriz asks about her YTD returns. Advisor confirms +3.4%, CDI-aligned. She's on track for her R$2M retirement target if contributions continue.

**Conv 5 — 2026-05-10 — Phone call (10:30) — Neutral sentiment**  
*Retirement planning analysis — 2 years out*  
First formal retirement planning conversation. With R$1.5M today and 2 years of continued contributions, she reaches her target. Beatriz relieved. Establishes the retirement date goal formally.

---

#### LÚCIA PRADO — Arc: Satisfaction → Pension Cross-Sell

**Conv 1 — 2026-06-08 — WhatsApp — Positive sentiment**  
*"Loving the results 😍"*  
Lúcia sees May statement. Portfolio up +0.9% for the month. Very happy. Advisor responds and mentions birthday coming up. Opens the door for a call.  
→ **Triggers opportunity**: Birthday outreach → pension pitch

**Conv 2 — 2026-06-03 — Phone call (11:20) — Positive sentiment**  
*"Tell me about PGBL pension plans"*  
Lúcia proactively asks about pension. Advisor explains: PGBL allows 12% gross income deduction, ideal for her tax bracket (27.5%). Projects she could save R$18k/year in taxes with a R$65k annual contribution.  
→ **Triggers recommendation**: Pension plan introduction

**Conv 3 — 2026-05-28 — Email — Positive sentiment**  
*Monthly report May — +0.9%*  
Advisor sends monthly report. Portfolio at R$3.1M, YTD +4.2%. No action needed. Lúcia replies with a emoji 🙏.

**Conv 4 — 2026-05-20 — WhatsApp — Neutral sentiment**  
*"I need R$50k for a business investment"*  
Lúcia asks about withdrawing R$50k from the portfolio for a business opportunity. Advisor discusses the impact (1.6% of total) and tax implications. Lúcia decides to proceed.

**Conv 5 — 2026-05-10 — Phone call (15:30) — Positive sentiment**  
*Quarterly review — first pension mention*  
Q1 review. Lúcia happy with +3.3% YTD. Mentions she's been thinking about starting a pension plan for the last year. Advisor notes this as an opportunity to follow up in the coming months.

---

#### GUSTAVO REIS — Arc: Rebalance Blocked by Governance

**Conv 1 — 2026-06-13 — Phone call (09:41) — Negative sentiment**  
*"The investment committee won't approve the rebalance"*  
Gustavo's company has an investment committee that must approve personal account rebalances over R$1M. The committee rejected the proposal due to "current market conditions." Portfolio stuck at 68% equity. Advisor documents and marks as compliance risk.  
→ **Triggers alert**: Rebalance pending / governance block (Medium)

**Conv 2 — 2026-06-07 — WhatsApp — Neutral sentiment**  
*"Is now a good time to rebalance despite the committee?"*  
Gustavo asking if there's an alternative path. Advisor explains the options: wait for committee, file an exemption, or do a smaller rebalance below the R$1M threshold.

**Conv 3 — 2026-05-30 — Phone call (14:00) — Neutral sentiment**  
*LatAm equities — should I add exposure?*  
Gustavo interested in adding LatAm exposure after reading about inflows into the region. Advisor recommends waiting for current rebalance to be approved before adding more equities. Gustavo reluctantly agrees.

**Conv 4 — 2026-05-22 — Email — Neutral sentiment**  
*Rebalancing proposal v2 — reduced scope*  
Second rebalancing proposal submitted to investment committee. Reduced from R$2.4M to R$900k (below the R$1M threshold that requires full committee vote). Awaiting response.

**Conv 5 — 2026-05-15 — Phone call (10:00) — Negative sentiment**  
*Q2 review — portfolio down 2.9%*  
Q2 review: portfolio down 2.9% versus -1.8% for the index. Gustavo frustrated. Concentrated international equity position underperformed. Advisor explains macro context and rebalancing rationale. First discussion of the governance constraint.

---

#### ANDRÉ LIMA — Arc: Equity Drift Above Policy Band

**Conv 1 — 2026-06-13 — Phone call (11:15) — Neutral sentiment**  
*"I know it's above band, I'm watching it carefully"*  
André acknowledges his equity position is at 62% vs 60% policy band. Wants to wait for market recovery before trimming. Advisor formally documents the conversation. Second policy breach in two quarters.  
→ **Triggers alert**: Equity drift above policy (Medium)

**Conv 2 — 2026-06-07 — WhatsApp — Neutral sentiment**  
*"What's my actual policy band for equities?"*  
André asks to confirm his current approved policy. Advisor confirms: 60% max equity, currently at 62%. Suggests a small trim (R$150k) to come back within band. André says he'll decide next week.

**Conv 3 — 2026-05-28 — Phone call (13:30) — Neutral sentiment**  
*Fintech IPO — can we participate?*  
André asks about a fintech IPO. Advisor notes this would push equity from 62% to ~65%. Declines to recommend given current policy breach. André disappointed but understands.

**Conv 4 — 2026-05-20 — Email — Neutral sentiment**  
*Policy breach notification — Q1*  
Formal written notification that equity allocation has exceeded approved band by 2pp for 45 consecutive days. André acknowledges. Says he will "address it in Q3."

**Conv 5 — 2026-05-10 — Phone call (09:00) — Neutral sentiment**  
*Annual review — strong long-term track record*  
Annual review. 5-year CAGR of +12.4% (vs Ibovespa +8.9%). André happy with long-term performance. Current quarter challenging (-1.8%). Discussion of the drift starts here: bull market in Q1 pushed equities above band organically.

---

#### CAMILA REZENDE — Arc: Pension Migration Decision

**Conv 1 — 2026-06-09 — WhatsApp — Neutral sentiment**  
*"Still thinking about migrating to PGBL"*  
Camila has been considering migrating her existing VGBL pension to a PGBL plan for 3 months. Says she spoke with her accountant. Awaiting final decision.  
→ **Triggers alert**: Pending decision / awaiting confirmation

**Conv 2 — 2026-06-03 — Email — Neutral sentiment**  
*Migration summary and tax impact*  
Advisor sends updated migration analysis: PGBL saves Camila R$6.4k/year in income tax. Net benefit over 10 years: R$84k. Camila acknowledges but wants a second opinion.

**Conv 3 — 2026-05-25 — Phone call (16:30) — Neutral sentiment**  
*"What happens if I migrate and then need the money?"*  
Camila worried about liquidity during migration. Advisor explains: 60-day transition period, access to funds throughout, no capital at risk. Camila more comfortable.

**Conv 4 — 2026-05-15 — WhatsApp — Neutral sentiment**  
*"Is there a deadline?"*  
Camila asks if there's a tax year deadline for the PGBL benefit. Advisor confirms: must be enrolled before Dec 31 to claim 2026 deduction. Creates urgency for decision.

**Conv 5 — 2026-05-05 — Phone call (10:15) — Neutral sentiment**  
*Initial pension migration conversation*  
First discussion of the pension migration opportunity. Camila was previously on VGBL with a generic provider. Advisor identifies the tax arbitrage opportunity and proposes switching to PGBL through their platform.

---

#### PAULO ESTEVES — Arc: Steady On-Track Client

**Conv 1 — 2026-06-18 — Email — Positive sentiment**  
*Q2 check-in — on track*  
Quarterly check-in. Portfolio +3.6% YTD, ahead of blended benchmark. No action required. Paulo confirms everything is fine.

**Conv 2 — 2026-06-05 — WhatsApp — Positive sentiment**  
*Dividend received — reinvested automatically*  
Dividend of R$12k received and auto-reinvested per standing instruction. Paulo confirms he saw the notification.

**Conv 3 — 2026-05-20 — Phone call (11:00) — Positive sentiment**  
*Q1 review — satisfied client*  
Annual review. Paulo happy with moderate approach, +3.6% vs CDI+Ibovespa blend. No changes requested. Q3 review scheduled for July.

**Conv 4 — 2026-05-10 — Email — Neutral sentiment**  
*Monthly report April*  
Monthly report sent. +0.6% for April. Below benchmark marginally. Paulo acknowledges, no concerns.

**Conv 5 — 2026-04-15 — Phone call (14:30) — Neutral sentiment**  
*"Should I increase my monthly contribution?"*  
Paulo asks about increasing monthly DCA from R$5k to R$8k. Advisor models the impact: target date improves by 2 years. Paulo confirms R$7k increase starting June.

---

#### TEREZA BITTENCOURT — Arc: Stable Income-Focused Client

**Conv 1 — 2026-06-15 — WhatsApp — Positive sentiment**  
*Portfolio update — stable month*  
Tereza checks in monthly via WhatsApp. +0.7% for June. She's happy with the income-focused approach.

**Conv 2 — 2026-06-02 — Email — Neutral sentiment**  
*May report — slight underperformance*  
May report: +0.5%, slight underperformance vs CDI+0.2pp. Advisor explains: short-term duration impact. No action needed.

**Conv 3 — 2026-05-20 — Phone call (10:00) — Positive sentiment**  
*"My daughter is starting university — planning ahead"*  
Tereza's daughter starting university in 2028. Wants to plan a R$200k education reserve. Advisor proposes a dedicated fixed income ladder.

**Conv 4 — 2026-05-10 — Email — Neutral sentiment**  
*Q1 annual review*  
Annual review. Tereza's portfolio at R$6.7M, +3.8% YTD. Well-positioned. No major changes. Next review scheduled Oct 2026.

**Conv 5 — 2026-04-20 — WhatsApp — Positive sentiment**  
*"When does the Tesouro IPCA mature?"*  
Tereza asks about maturity dates for her Tesouro IPCA positions. Advisor sends a summary: 3 tranches maturing in 2027, 2029, and 2033.

---

#### SOFIA MARQUES — Arc: New Client Onboarding

**Conv 1 — 2026-06-20 — Phone call (11:30) — Positive sentiment**  
*Onboarding check — first 90 days*  
90-day onboarding review. Sofia joined in March. Portfolio at R$2.2M, all in conservative fixed income. Very happy with the onboarding experience. Still learning the platform.

**Conv 2 — 2026-06-10 — WhatsApp — Neutral sentiment**  
*"How do I read my monthly statement?"*  
Sofia asks for help interpreting her portfolio statement. Advisor explains the key numbers: total value, monthly return, YTD, benchmark comparison.

**Conv 3 — 2026-05-28 — Email — Neutral sentiment**  
*Onboarding completion — suitability signed*  
Formal onboarding completion email. All documents signed, suitability completed (conservative), investment policy agreed. Welcome package sent.

**Conv 4 — 2026-05-15 — Phone call (14:00) — Positive sentiment**  
*First portfolio review — 60 days in*  
60-day check. Sofia comfortable with conservative approach. +1.8% since inception. No concerns. Advisor notes she may consider moderate profile in 12 months.

**Conv 5 — 2026-03-20 — Phone call (10:00) — Positive sentiment**  
*First meeting — onboarding*  
Initial onboarding call. Sofia referred by a colleague. Transferred R$2.2M from another bank. Goals: capital preservation, some income, retirement in 15 years. Conservative profile confirmed.

---

## 3. Data Schema

### 3.1 New Tables

```sql
-- conversations (one row per interaction)
CREATE TABLE conversations (
    conv_id       VARCHAR PRIMARY KEY,
    client_id     VARCHAR NOT NULL,
    channel       VARCHAR NOT NULL,     -- call | whatsapp | email
    conv_date     DATE NOT NULL,
    duration_s    INTEGER,              -- seconds (NULL for text channels)
    sentiment     VARCHAR DEFAULT 'neutral',  -- positive | neutral | negative
    summary_en    TEXT,
    summary_pt    TEXT,
    has_audio     BOOLEAN DEFAULT FALSE,
    audio_file    VARCHAR,              -- filename served under /audio/
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- conversation_turns (the actual dialog)
CREATE TABLE conversation_turns (
    turn_id       VARCHAR PRIMARY KEY,
    conv_id       VARCHAR NOT NULL REFERENCES conversations(conv_id),
    speaker       VARCHAR NOT NULL,     -- advisor | client
    turn_order    INTEGER NOT NULL,
    text_en       TEXT,
    text_pt       TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.2 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/conversations?client_id=<id>` | All conversations for a client, ordered by date desc |
| `GET` | `/conversations/<conv_id>` | Full conversation with all turns |
| `GET` | `/audio/<filename>` | Stream/download audio MP3 file |

### 3.3 Response Shapes

```json
// GET /conversations?client_id=ricardo
[
  {
    "conv_id": "conv-ricardo-20260614",
    "client_id": "ricardo",
    "channel": "call",
    "conv_date": "2026-06-14",
    "duration_s": 512,
    "sentiment": "negative",
    "summary_en": "Ricardo alarmed by market drop. Baby coming. Proposes rebalancing 71→55%.",
    "summary_pt": "Ricardo alarmado com queda do mercado. Bebê chegando. Proposta de rebalanceamento 71→55%.",
    "has_audio": true,
    "audio_file": "ricardo_20260614.mp3"
  },
  ...
]

// GET /conversations/conv-ricardo-20260614
{
  "conv_id": "...",
  ...all fields above...,
  "turns": [
    { "turn_id": "...", "speaker": "advisor", "turn_order": 1, "text_en": "Oi Ricardo...", "text_pt": "..." },
    ...
  ]
}
```

---

## 4. Audio Generation Plan

### 4.1 Scope

| File | Client | Conversation | Length | Priority |
|---|---|---|---|---|
| `ricardo_20260614.mp3` | Ricardo | Jun 14 phone call | ~2:30 | P0 — main demo |
| `otavio_20260609.mp3` | Otávio | Jun 9 phone call | ~1:45 | P1 — second demo |

### 4.2 Generation Method

1. Select 2 ElevenLabs voices: one for advisor (warm, professional), one for client
2. Generate each turn as a separate MP3 chunk via `/v1/text-to-speech`
3. Concatenate raw MP3 bytes (MPEG frame-level concatenation)
4. Store under `analytics/audio/` and serve via `/audio/<filename>`

### 4.3 Scripts for Ricardo (Jun 14) — Portuguese

```
[Advisor - turn 1]
"Oi Ricardo, bom dia. Obrigado por atender. Vi aqui que sua posição em renda variável subiu para 71% com o movimento de ontem. Queria entender como você está se sentindo sobre isso."

[Cliente - turn 2]
"Pois é, tô vendo aqui. Tô bem preocupado. Com o bebê chegando em setembro, não tô confortável com esse nível de exposição."

[Advisor - turn 3]
"Entendo completamente, Ricardo. Essa sensação faz todo sentido num momento de transição de vida. Me conta: o que te preocupa mais — a queda do mercado de curto prazo, o tamanho total da posição, ou a reserva de emergência?"

[Cliente - turn 4]
"É tudo junto, mas a reserva é o que me tira o sono. Hoje tenho uns 4 meses. Com criança chegando, quero pelo menos 12."

[Advisor - turn 5]
"Certo. Então a proposta que tenho pra você equilibra as duas coisas. Reduzimos sua renda variável de 71% para 55% — ainda uma posição relevante mas bem mais confortável — e usamos os 16 pontos percentuais para montar uma reserva de emergência sólida em Tesouro Selic, líquida a qualquer momento."

[Cliente - turn 6]
"Quanto isso representa em reais saindo da bolsa?"

[Advisor - turn 7]
"Com seu patrimônio de R$ 12,8 milhões, você passaria de aproximadamente R$ 9 milhões em ações para R$ 7 milhões. A reserva ficaria em torno de R$ 770 mil — cobrindo seus 12 meses tranquilamente."

[Cliente - turn 8]
"Isso me deixa bem mais confortável. E a execução — como funciona?"

[Advisor - turn 9]
"Faço o plano de execução hoje ainda e mando pra você antes das três da tarde. Sugiro fazer em tranches ao longo de 2 semanas pra não pressionar o mercado. Você aprova cada movimento antes de executar."

[Cliente - turn 10]
"Perfeito. Pode mandar. Obrigado como sempre."

[Advisor - turn 11]
"Fica tranquilo. Cuida bem da família. Até mais, Ricardo."
```

### 4.4 Script for Otávio (Jun 9) — Portuguese

```
[Advisor - turn 1]
"Otávio! Boa tarde, tudo bem? Vi que o aporte de julho tá confirmado — R$ 500 mil é isso?"

[Cliente - turn 2]
"Isso mesmo, dia 15 de julho. Tava querendo conversar justamente sobre onde alocar bem esse dinheiro."

[Advisor - turn 3]
"Perfeito. Já preparei uma proposta alinhada com seu perfil. Com o cenário de mercado atual, pensaria em três blocos: 50% em renda variável — uma combinação de ETF de Ibovespa e uma posição em tech — 30% num fundo de crédito de infraestrutura que acabou de abrir, com retorno projetado de CDI mais 3 e 2, e 20% em multimercado para dar flexibilidade."

[Cliente - turn 4]
"CDI mais 3,2% no fundo de infraestrutura? Isso é bem interessante. A janela fecha quando?"

[Advisor - turn 5]
"Fecha dia 30 de junho. Sendo um dos primeiros cotistas você entra no melhor patamar. Você tem posição em caixa hoje se quiser entrar antes do aporte de julho?"

[Cliente - turn 6]
"Tenho uns R$ 80 mil parados. Mas prefiro esperar o aporte pra entrar com o volume maior. Vale a pena?"

[Advisor - turn 7]
"Vale, sim. O fundo tem captação mínima de R$ 50 mil, então você já teria acesso com os 80. Mas se preferir esperar, ainda dá tempo — a janela vai até 30 de junho e você confirma semana que vem."

[Cliente - turn 8]
"Então manda o plano por escrito que eu assino semana que vem. Ficou bem estruturado."

[Advisor - turn 9]
"Mando ainda hoje. Qualquer dúvida me chama no WhatsApp. Abraço, Otávio."

[Cliente - turn 10]
"Combinado! Obrigado."
```

---

## 5. Frontend Integration

### 5.1 New State Fields

```javascript
state = {
  ...existing...,
  clientConvos: {},       // { clientId: [conv, ...] } — loaded from API
  convoIdx: 0,            // index within clientConvos[clientId] array (replaces convoDateIdx)
  convosLoading: false,   // show skeleton while fetching
}
```

### 5.2 Data Flow

```
Client detail opens
  → _fetchConversations(clientId) called
  → GET /conversations?client_id=<id>
  → state.clientConvos[clientId] = result
  → carousel renders real dates from result
  → selected convo renders real turns
  → if has_audio: audio player shows real audio URL
```

### 5.3 Carousel Integration

- Carousel shows `conv_date` formatted as "Jun 14" for each conversation
- Dot color: channel-based (green=call, blue=whatsapp, amber=email)
- Selected convo index stored in `convoIdx`

### 5.4 Audio Player

- If `convo.has_audio`: `<audio>` element with `src="/audio/{audio_file}"`
- Actual play/pause/seek functionality via native HTML5 audio element
- If `convo.channel !== 'call'`: player hidden (same logic as `convoIsCall`)

---

## 6. Alignment: Conversations → Alerts / Opportunities / Recommendations

### 6.1 Alerts (must derive from conversations)

| Alert | Client | Source Conversation | Severity |
|---|---|---|---|
| Recurring withdrawals + risk aversion | Ricardo | Jun 14 (baby mention) | High |
| Compliance flag — equity concentration | Fernando | Jun 10 (policy breach) | High |
| Suitability expires Jun 30 | Beatriz | Jun 11 (renewal notice) | Medium |
| Rebalance pending — governance block | Gustavo | Jun 13 (committee block) | Medium |
| Equity drift above policy | André | Jun 13 (policy breach) | Medium |
| Pension migration pending | Camila | Jun 9 (awaiting decision) | Low |

### 6.2 Opportunities (must derive from conversations)

| Opportunity | Client | Source Conversation | Stage |
|---|---|---|---|
| Emergency reserve rebalancing (71%→55%) | Ricardo | Jun 14 | Proposal |
| Infra credit fund allocation (Jul inflow) | Otávio | Jun 9 | Identified |
| Multimercado migration (10% RF→MM) | Helena | Jun 12 | Proposal |
| Pension plan PGBL cross-sell | Lúcia | Jun 3 | Identified |
| Equity concentration fix | Fernando | Jun 10 | Identified |

### 6.3 Recommendations (must derive from conversations)

| Client | Recommendation Text Source | Trigger |
|---|---|---|
| Ricardo | Portfolio +2.3%, rebalancing proposal | Jun 14 call |
| Otávio | July inflow allocation plan | Jun 9 call |
| Lúcia | Birthday + pension plan intro | Jun 8 WhatsApp + Jun 3 call |

---

## 7. Acceptance Criteria

- [ ] AC-001: GET /conversations?client_id=ricardo returns at least 5 conversations
- [ ] AC-002: All 12 clients have conversations in the database
- [ ] AC-003: GET /conversations/conv-ricardo-20260614 returns full turn-by-turn dialog
- [ ] AC-004: GET /audio/ricardo_20260614.mp3 returns a valid MP3 file
- [ ] AC-005: Clicking a client in the cockpit fetches and renders their conversations
- [ ] AC-006: Carousel shows real dates (Jun 14, Jun 9, May 28, May 15, Apr 30) for Ricardo
- [ ] AC-007: Clicking Jun 14 in carousel shows Ricardo's call transcript
- [ ] AC-008: Clicking Jun 12 for Helena shows WhatsApp message bubbles (no audio player)
- [ ] AC-009: Clicking Jun 14 for Ricardo shows functional audio player with real MP3
- [ ] AC-010: Audio player plays the Ricardo conversation audio
- [ ] AC-011: Opportunities panel shows at least the 5 opportunities aligned with conversations
- [ ] AC-012: Alerts derive from conversation events (suitability, compliance, etc.)
- [ ] AC-013: All tests in test_07_conversations.py pass

---

## 8. Implementation Phases

### Phase 1 — Backend (analytics service)
1. Add `conversations` and `conversation_turns` tables to `analytics/main.py`
2. Create `analytics/seed_conversations.py` with all narratives
3. Add conversation seeding to `init_db()`
4. Add `/conversations` and `/conversations/{id}` endpoints
5. Add `/audio/{filename}` static serving endpoint

### Phase 2 — Audio Generation
1. Write `scripts/generate_audio.py`
2. Generate Ricardo Jun 14 conversation (11 turns, 2 voices)
3. Generate Otávio Jun 9 conversation (10 turns, 2 voices)
4. Store MP3s in `analytics/audio/`
5. Rebuild analytics container with audio files copied in

### Phase 3 — Frontend Integration
1. Add `_fetchConversations(clientId)` method to cockpit
2. Add `clientConvos` and `convoIdx` to state
3. Update carousel to render from `clientConvos[clientId]`
4. Update transcript/messages content to use API data
5. Wire audio player to `<audio>` element with real `src`
6. Fall back to static CONVO data when API unavailable

### Phase 4 — Data Alignment
1. Update static opportunities data in cockpit to align with conversation narratives
2. Update static alerts data to align with conversation events
3. Verify all 6 alignment pairs (Section 6) are consistent
