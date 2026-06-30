-- PostgreSQL schema: agent memory and operational state
-- Runs automatically on first container start via Docker entrypoint.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- One row per Sofia voice session (each phone button tap)
CREATE TABLE IF NOT EXISTS agent_sessions (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id TEXT,                          -- ElevenLabs conversation ID (set after WS connects)
    client_id       TEXT,                          -- client in focus when session started (nullable)
    advisor_id      TEXT        NOT NULL DEFAULT 'thiago',
    status          TEXT        NOT NULL DEFAULT 'active'
                                CHECK (status IN ('active', 'completed', 'interrupted')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at        TIMESTAMPTZ
);

-- Conversation turns during a session (expires with session, kept for in-session context)
CREATE TABLE IF NOT EXISTS agent_memory_short (
    id          SERIAL      PRIMARY KEY,
    session_id  UUID        NOT NULL REFERENCES agent_sessions(id) ON DELETE CASCADE,
    client_id   TEXT,
    role        TEXT        NOT NULL CHECK (role IN ('user', 'assistant')),
    content     TEXT        NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Persistent facts Sofia learns about clients across sessions
CREATE TABLE IF NOT EXISTS agent_memory_long (
    id             SERIAL      PRIMARY KEY,
    client_id      TEXT        NOT NULL,
    category       TEXT        NOT NULL,   -- preference | life_event | risk_signal | objective | note
    fact           TEXT        NOT NULL,
    confidence     FLOAT       NOT NULL DEFAULT 1.0 CHECK (confidence BETWEEN 0 AND 1),
    source_session UUID        REFERENCES agent_sessions(id) ON DELETE SET NULL,
    is_active      BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Audit log of every advisor action (approved recommendation, sent message, etc.)
CREATE TABLE IF NOT EXISTS advisor_actions (
    id          SERIAL      PRIMARY KEY,
    session_id  UUID        REFERENCES agent_sessions(id) ON DELETE SET NULL,
    client_id   TEXT,
    action_type TEXT        NOT NULL,   -- recommendation_approved | whatsapp_sent | voice_generated | navigate
    payload     JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_memory_short_session ON agent_memory_short(session_id);
CREATE INDEX IF NOT EXISTS idx_memory_long_client   ON agent_memory_long(client_id) WHERE is_active;
CREATE INDEX IF NOT EXISTS idx_advisor_actions_client ON advisor_actions(client_id);
CREATE INDEX IF NOT EXISTS idx_sessions_created     ON agent_sessions(created_at DESC);

-- Seed: facts Sofia learned from prior advisor sessions (demo data)
INSERT INTO agent_memory_long (client_id, category, fact, confidence) VALUES
  ('ricardo', 'risk_signal',  'Equity at 71%, above 65% personal threshold. Mentioned wanting to withdraw funds in last call.',      0.95),
  ('ricardo', 'life_event',   'Baby on the way — wants a larger safety reserve. Short-term liquidity concern raised explicitly.',     0.90),
  ('beatriz', 'risk_signal',  'Suitability assessment expires 2026-06-30. Advisor signature required before expiry.',                1.00),
  ('beatriz', 'preference',   'Conservative profile but open to CDBs at 120%+ CDI. Not receptive to equity fund proposals.',         0.80),
  ('fernando', 'preference',  'Prefers WhatsApp for communication. Usually responds within 2 hours.',                                0.85),
  ('fernando', 'objective',   'Targeting 15% annual return. Interested in private credit and infrastructure fund allocations.',       0.90),
  ('lucia',   'objective',    'Planning partial liquidity event in Q4 2026 for a real estate purchase. Amount TBD.',                  0.85),
  ('andre',   'risk_signal',  'Equity at 74%, approaching 80% policy limit. A market correction could trigger mandatory rebalance.',  0.90),
  ('roberto', 'life_event',   'Recently divorced. Reviewing investment objectives and beneficiary designations on all positions.',     0.75),
  ('ana',     'objective',    'Interested in ESG funds. Potential R$800k inflow expected from business sale in Q3 2026.',             0.80)
ON CONFLICT DO NOTHING;
