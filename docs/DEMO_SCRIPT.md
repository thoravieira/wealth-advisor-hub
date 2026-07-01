# Demo Script — sofIA Cockpit
**Duração:** ~7 minutos  
**Cenário:** Thiago, assessor sênior, abre o cockpit segunda de manhã antes das 9h. Mercado abre em 45 minutos. Ele tem 45 clientes no livro.

---

## Prep

1. Abrir `http://localhost:8080/cockpit.html`
2. Garantir que o Overview está na tela (padrão)
3. Ter fone de ouvido — a voz da Sofia é parte do demo
4. Clicar no botão `···` (canto inferior direito) → clicar no telefone para conectar a Sofia

---

## ACT 1 — Bom dia, o livro está esperando
_~90 segundos_

**[Sofia abre a sessão — ela fala primeiro, sem que Thiago diga nada]**

> **Sofia:** "Good morning Thiago. I went through your book. Three things need you today: Ricardo Tanaka is showing withdrawal intent with equity at 71% — baby's arriving in September and he wants to de-risk. Fernando Costa has a compliance flag that's been open for six weeks. And Beatriz Oliveira's suitability document expires this week. Where do you want to start?"

**[A tela já mostra o Overview com os cards At risk / Opportunities / Pending / Awaiting]**

---

**Thiago:** "Start with Ricardo."

**[Sofia chama `open_client({ clientName: "Ricardo" })` — o painel de Ricardo Tanaka abre automaticamente]**

> **Sofia:** "Ricardo Tanaka, VIP client since 2018. R$ 12.8 million, aggressive profile. Equity is at 71% — above his 55% target. He called last week worried about the market. He's having a baby in September and wants to pull back."

---

## ACT 2 — A chamada real, o transcript, a mensagem
_~2 minutos_

**[Ricardo está aberto. Carousel mostra Jun 14 selecionado. O custom audio player está visível]**

**Thiago:** "Play the Jun 14 call."

**[Demonstrador clica no play button do player. O áudio começa. As barras do waveform avançam. O transcript destaca a frase que está sendo falada em tempo real]**

> **[~15 segundos de áudio]** — voz do Ricardo preocupado com o bebê, voz do advisor propondo reduzir de 71% para 55%

**Thiago:** _(pausa o áudio)_ "Got it. Draft me a message to send him."

> **Sofia:** "On it."

**[Sofia chama `show_recommendation({ clientId: "ricardo", text: "..." })` — o card de aprovação aparece com o texto pré-preenchido]**

> **Sofia:** "Something like: 'Ricardo, good morning. Following our call — I've prepared the rebalancing plan we discussed. I'll trim equity from 71 to 55%, building your 12-month Tesouro Selic reserve. Sending the full breakdown to your email today. No action needed from you yet.' Want me to adjust the tone?"

**Thiago:** "Shorter. Remove the last sentence."

**[Thiago edita o texto no card]**

**Thiago:** "Generate the voice."

**[O botão Generate voice dispara POST /tts → a voz da Sarah lê a mensagem — Thiago ouve o preview]**

**Thiago:** "Send it."

> **Sofia:** "Sent to Ricardo via WhatsApp. Next — Fernando Costa has had a compliance flag open for six weeks. His equity is at 71%, same as Ricardo, but he's been pushing back on rebalancing. Want me to pull up his profile?"

---

## ACT 3 — O radar de compliance
_~90 segundos_

**Thiago:** "Show me the alerts first."

**[Sofia chama `navigate({ route: "alerts" })` — a tela muda para Alerts]**

> **Sofia:** "Five active alerts. Two equity concentration flags — Fernando and André Lima, both at 71% and 74%. One suitability expiry — Beatriz Oliveira, document expires this Friday. Two withdrawal signals — Ricardo and André."

**[A tela mostra a lista de alertas agrupados]**

**Thiago:** "Fernando's been dragging this for six weeks. Pull him up."

**[Sofia chama `open_client({ clientName: "Fernando" })` — Fernando Costa abre]**

> **Sofia:** "Fernando Costa, VIP, R$ 23 million, aggressive. Equity at 71% against a 60% policy band. He knows. He's been saying performance justifies the concentration. I documented three conversations where he refused to rebalance. The committee was formally notified last week."

**Thiago:** "Draft a formal notification for him."

> **Sofia:** "Fernando, following our conversation on Jun 10 — your equity position remains at 71%, above our agreed 60% band. Regulatory compliance requires we formalize this in writing. I'm requesting your decision on the rebalancing proposal by June 30th. Let me know how you'd like to proceed."

**[Card de aprovação aparece]**

**Thiago:** "Good. I'll review before sending. Now Beatriz."

**[Sofia chama `open_client({ clientName: "Beatriz" })` — Beatriz Oliveira abre]**

> **Sofia:** "Beatriz Oliveira, R$ 8.5 million, moderate profile. Suitability document expires this Friday — June 30. I suggest we reach out today to schedule the renewal. She's been with you since 2020, conservative investor nearing retirement. Tone should be reassuring."

**Thiago:** "Generate a message for her."

> **Sofia:** "Beatriz, I hope you're well. Your investor profile review is due this week — it's a routine annual update that takes about 20 minutes. Would Thursday morning work for a quick call? I'll have everything prepared. This keeps us aligned on your goals and fully compliant."

**Thiago:** "Perfect. Voice and send."

---

## ACT 4 — A oportunidade do mês
_~60 segundos_

**Thiago:** "Show me opportunities."

**[Sofia chama `navigate({ route: "opportunities" })` — tela muda para Opportunities]**

> **Sofia:** "Two active opportunities this month. Otávio Mendes — R$ 500k inflow confirmed for July 15th, infrastructure fund window closes June 30th. Mariana Castro — she's eligible for a pension product migration, been awaiting response for four days."

**Thiago:** "Otávio. What's the play?"

**[Sofia chama `open_client({ clientName: "Otávio" })` — Otávio Mendes abre]**

> **Sofia:** "Otávio Mendes, VIP, R$ 7.6 million, mod-aggressive. The inflow is 500k on July 15th. I'd suggest 30% into the infrastructure credit fund at CDI plus 3.2% — entry closes June 30th. He already expressed interest in the last call. You have a week to confirm."

**[Clicar em Jun 9 no carousel — o player de Otávio aparece com a transcrição da conversa]**

**Thiago:** "He mentioned it here?"

> **Sofia:** "Yes — turn three. He called CDI plus 3.2% 'very attractive' and asked specifically about the entry window."

**[O transcript destaca o turn 3 de Otávio: "Very attractive. I have R$80k idle. Can I enter now?"]**

**Thiago:** "Book the call for this week. Send him the proposal first."

> **Sofia:** "On it. Generating the voice message for Otávio now."

---

## ACT 5 — Fechar o loop
_~45 segundos_

**Thiago:** "How's the rest of the book looking today?"

**[Sofia chama `navigate({ route: "clients" })` — tela vai para Clients com a tabela completa]**

> **Sofia:** "Twelve clients covered this morning. Three actions sent — Ricardo, Beatriz, and the Fernando notification drafted. One recommendation pending your approval for Fernando. Otávio's call queued. The rest of the book is green — healthy allocation, no flags. You've cleared the three priorities before the market opens."

**[A tela mostra a tabela de clients com Last Contact, AUM, Perf, Risk columns]**

**Thiago:** "Good morning."

> **Sofia:** "Good morning, Thiago."

---

## Momentos-chave para destacar para a audiência

| Momento | O que demonstra |
|---|---|
| Sofia abre a sessão sem pergunta | Proatividade — ela leu o livro, não esperou ser acionada |
| Falar "Pull up Ricardo" → tela muda | Navegação por voz — zero clique |
| Audio player + transcript sincronizado | Conversas reais, não notas — ElevenLabs STT |
| "Draft me a message" → card aparece | AI draft editável — o advisor controla antes de enviar |
| "Generate voice" → preview em Sarah | TTS personalizado — o cliente ouve a voz do assessor |
| 5 alertas surfaçados sem query | Monitoramento contínuo do livro inteiro |
| 7 minutos = 3 clientes tratados | Escala — o que levaria uma manhã acontece antes das 9h |

---

## Frases alternativas para testar (Sofia entende todas)

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

## Troubleshooting rápido

| Problema | Solução |
|---|---|
| Sofia não conecta | Verificar se o backend está rodando em `:8000`; checar `/health` |
| Áudio do player não carrega | Analytics deve estar em `:8001`; `GET /audio/ricardo_20260614.mp3` deve retornar 200 |
| Transcript não aparece | Aguardar o fetch de `/conversations/{id}` completar (~500ms) |
| Sofia não navega | O `agent_id` no `.env` deve corresponder ao agente com as tools atualizadas |
