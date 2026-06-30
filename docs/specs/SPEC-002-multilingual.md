# SPEC-002 — Multilingual Client Outreach

| Field | Value |
|---|---|
| ID | SPEC-002 |
| Status | ROADMAP — not yet implemented |
| Feature | Sofia auto-detects and switches client language mid-session |
| ElevenLabs features used | Conversational AI (multilingual), TTS Multilingual v3 |
| Roadmap phase | v4 |

---

## Problem

Wealth advisors in global or cross-border wealth management serve clients who prefer different languages. Today this means separate workflows and manual configuration. In a voice-first context, forcing a language switch destroys conversational flow — the advisor has to stop, reconfigure, restart.

---

## Solution

Sofia detects the client's preferred language from a `preference` fact stored in `agent_memory_long`. When `generate_voice_message` is called for that client, the backend selects the matching voice and language automatically. The advisor never switches anything manually.

---

## User Story

> As a wealth advisor with a multilingual client book, I want Sofia to generate client communications in each client's preferred language automatically, so that outreach feels native without me managing separate workflows or voice configurations.

---

## Acceptance Criteria

- [ ] AC-001: Client language preference is stored as a `preference` fact in `agent_memory_long`
- [ ] AC-002: `/tts` endpoint reads language preference and selects the matching ElevenLabs voice
- [ ] AC-003: Advisor can tell Sofia "switch to Portuguese for this message" mid-session without reconnecting
- [ ] AC-004: Cockpit client detail shows the client's language preference in the Sofia Memory section
- [ ] AC-005: Knowledge base retrieval surfaces content relevant to the client's market (when multi-market KBs exist)

---

## Technical Design

`generate_voice_message` tool passes `client_id` to the backend. The backend queries `agent_memory_long` for a `preference` fact containing the language tag, then routes to the appropriate voice.

**Voice mapping (initial)**

| Language | Voice | ElevenLabs voice ID |
|---|---|---|
| English | Sarah | `EXAVITQu4vr4xnSDxMaL` |
| Portuguese (BR) | Sofia PT | TBD |
| Spanish | TBD | TBD |

---

## What Requires a Paid Plan

| Feature | Plan required |
|---|---|
| Voice clone in client's preferred language | Starter+ |
| Commercial use of generated audio | Starter+ |
